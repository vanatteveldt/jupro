import json
import logging
import sys
from base64 import b64decode
from pathlib import Path
import subprocess
from typing import Tuple
import re

from lxml import html


def run_notebook(fn: Path) -> dict:
    """Run a notebook, returning the raw json dict"""
    jupyter = Path(sys.executable).parent / "jupyter"
    if not jupyter.exists():
        raise Exception(f"Cannot find jupyter in {str(jupyter)}")
    cmd = [str(jupyter), "nbconvert", "--to", "notebook", "--stdout", str(fn)]
    out = subprocess.check_output(cmd)
    return json.loads(out)


def create_snippets(fn: Path, out_folder=None):
    nb = run_notebook(fn)
    ext = nb["metadata"]["language_info"]["file_extension"]
    if out_folder is None:
        out_folder = Path.cwd()/"snippets"/fn.parent.name
    out_folder.mkdir(exist_ok=True, parents=True)
    logging.info(f"Writing output to {out_folder}/")

    for cell in read_cells(nb):
        name = cell.snippet_name
        if cell.cell_type == "code" and name:
            logging.info(f"Found snippet: {name}")
            write(out_folder/f"{name}{ext}", cell.source)
            write(out_folder/f"{name}{ext}.out", cell.text_output())
            if 'png' in cell.requested_output:
                write_bytes(out_folder/f"{name}{ext}.png", cell.png_output())
            if 'html' in cell.requested_output:
                write_cropped_pdf(out_folder/f"{name}{ext}.html.pdf", cell.html_pdf_output())
            if 'table' in cell.requested_output:
                write(out_folder / f"{name}{ext}.table.tex", cell.table_output())


def write(file: Path, text: str):
    logging.info(f"Writing {file}")
    with file.open("w") as f:
        f.write(text)


def write_bytes(file: Path, data: bytes):
    logging.info(f"Writing {file}")
    with file.open("wb") as f:
        f.write(data)


def write_cropped_pdf(file: Path, pdf: bytes):
    pdf = pipe(["pdfcrop", "-", str(file)], pdf)


def pipe(command, input, **kargs):
    proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, **kargs)
    out, _err = proc.communicate(input)
    return out


class Cell:
    """class representing a jupyter cell"""
    def __init__(self, data):
        self.data = data

    def tags(self, filter=None):
        tags = self.data['metadata'].get('tags', [])
        if filter:
            if not filter.endswith(":"):
                filter = f"{filter}:"
            tags = [t[len(filter):] for t in tags if t.startswith(filter)]
        return tags

    @property
    def cell_type(self):
        return self.data['cell_type']
    
    @property
    def source(self):
        return "".join(self.data["source"])

    @property
    def snippet_name(self):
        snippets = self.tags(filter="snippet")
        if len(snippets) > 1:
            raise ValueError(f"Don't use multiple snippet tags! {snippets}")
        if snippets:
            return snippets[0]
        
    @property
    def requested_output(self):
        return self.tags(filter="output")

    def get_text_outputs(self):
        for output in self.data['outputs']:
            if output['output_type'] == 'stream':
                # python notebooks capture explicit prints as stdout
                # Exclude stderr (for now?)
                if output['name'] == 'stdout':
                    yield from output['text']
            elif output['output_type'] in ('display_data', 'execute_result'):
                d = output['data']
                if 'image/png' in d:
                    # Skip the "plot without title" text on graphical output
                    continue
                else:
                    yield from d['text/plain']

    def get_png_outputs(self):
        for output in self.data['outputs']:
            if output['output_type'] in {'display_data', 'execute_result'}:
                if 'image/png' in output['data']:
                    yield output['data']['image/png']

    def get_html_outputs(self):
        for output in self.data['outputs']:
            if output['output_type'] in ('display_data', 'execute_result'):
                if 'text/html' in output['data']:
                    yield from output['data']['text/html']

    def get_table_outputs(self):
        for output in self.data['outputs']:
            if output['output_type'] in ('display_data', 'execute_result'):
                if 'text/html' in output['data']:
                    html = "".join(output['data']['text/html'])
                    if "</table>" in html:
                        yield html

    def text_output(self) -> str:
        def clean(x):
            x = x.rstrip().replace("\u00d7", "x").replace("…", ".")
            x = re.sub(r"\x1b\[[\d;]+m", "", x)
            return x
        
        return "\n".join(clean(x) for x in self.get_text_outputs())

    def html_pdf_output(self):
        html = "\n".join(self.get_html_outputs())
        pdf = pipe(["wkhtmltopdf", "-", "-"], html.encode('ascii', 'xmlcharrefreplace'))
        return pdf

    def png_output(self) -> bytes:
        pngs = list(self.get_png_outputs())
        if not pngs:
            raise ValueError("No PNG data present")
        if len(pngs) > 1:
            raise ValueError("More than one PNG, cannot save as picture")
        return b64decode(pngs[0])

    def table_output(self) -> str:
        """Extract a table from the HTML and return as latex tabularx snippet"""
        tables = list(self.get_table_outputs())
        if not tables:
            raise ValueError("No table present")
        if len(tables) > 1:
            raise ValueError("More than one table, cannot save as single snippet")
        header, body = parse_table(tables[0])
        ncol = len(header[0])
        if len(header) == 2 and all(x.startswith("<") for x in header[1]):
            # This looks like a tibble :)
            TIBBLE_TYPES = {"<dbl>": "r", "<int>": "r"}
            colspec = "".join([TIBBLE_TYPES.get(x, "X") for x in header[1]])
            if "X" not in colspec:
                colspec = "X"*len(colspec)
        elif body:
            colspec = "X" * len(body[0])
        else:
            raise Exception("Silly!")
        resize = "resize" in self.tags("table:")

        def clean(x):
            return x.replace("_", "\\_").replace("#", "\\#").replace("%", "\\%").replace("$", "\\$").replace("&","\\&")
        if resize:
            colspec = colspec.replace('X', 'l')
            result = f"\\resizebox{{\\linewidth}}{{!}}{{\\begin{{tabular}}{{{colspec}}}\n  \\toprule\n"
        else:
            result = f"\\begin{{tabularx}}{{\linewidth}}{{{colspec}}}\n  \\toprule\n"
        for i, row in enumerate(header):
            fn = 'ccstablehead' if i == 0 else 'ccstablesubhead'
            row = [f'\\{fn}{{{clean(x)}}}' for x in row]
            result += f'  {" & ".join(row)}\\\\\n'
        result += "  \\midrule\n"
        for row in body:
            row = [clean(x) for x in row]
            result += f'  {" & ".join(row)}\\\\\n'
        if resize:
            result += "  \\bottomrule\n\\end{tabular}}\n"
        else:
            result += "  \\bottomrule\n\\end{tabularx}\n"
        return result

def parse_table(table_html: str) -> Tuple[list, list]:
    """Parse an html table and return (header, body), each a list of lists"""
    doc = html.fromstring(table_html)
    header = [[th.text_content() for th in row.cssselect("th")] for row in doc.cssselect("thead tr")]
    body = [[td.text_content() for td in row.cssselect("td,th")] for row in doc.cssselect("tbody tr")]
    return header, body


def read_cells(nb: dict):
    for cell in nb['cells']:
        yield Cell(cell)

