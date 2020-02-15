from pathlib import Path

from nose.tools import assert_equals

from jupro import create_snippets

SNIPPETS = Path(__file__).parent/"test_snippets"


def setup_module():
    for fn in ("test_py.ipynb", "test_r.ipynb"):
        create_snippets(Path(__file__).parent / fn, out_folder=SNIPPETS)


def get_snippet_output(fn):
    for ext in "py", "r":
        yield (SNIPPETS/f"{fn}.{ext}.out").open().read()


def test_simpletext():
    py, r = get_snippet_output("simpletext")
    assert_equals(py, "'simple text'")
    assert_equals(r, '[1] "simple text"')


def test_prints():
    py, r = get_snippet_output("prints")
    assert_equals(py, 'first print\nsecond print')
    assert_equals(r, "first print\nsecond print")


def test_plot():
    py, r = get_snippet_output("plot")
    assert_equals(py, 'before plot\nafter plot')
    assert_equals(r, '[1] "before plot"\n[1] "after plot"')
    assert (SNIPPETS / f"plot.py.png").exists()
    assert (SNIPPETS / f"plot.r.png").exists()


def test_table():
    assert (SNIPPETS / f"table.py.table.tex").exists()
    assert (SNIPPETS / f"table.r.table.tex").exists()
    assert (SNIPPETS / f"table.py.html.pdf").exists()
    assert (SNIPPETS / f"table.r.html.pdf").exists()


def test_stderr():
    """stderr should be excluded by default"""
    py, r = get_snippet_output("stderr")
    assert_equals(py, "Normal output")
    assert_equals(r, "Normal output")



if __name__ == '__main__':
    setup_module()
    py, r = get_snippet_output("stderr")
    print(r)
    print("---")
    print(py)
