# Jupro: Process Jupyter-notebook into latex code snippets

This is a small tool to extract code and results from a jupyter notebook into latex snippets.
It was mostly made to help us write [Computational Analysis of Communication](http://cssbook.net/), our upcoming book on compuational social science,
but maybe it can also be useful for others.

# Instructions

## Notebook

In the notebook, add tags to control how jupro processes the file

 - `snippet:XXX` will create a snippet named XXX
 - `output:table` or `output:png` will create a png or latex table file in addition to the text output
 
It is advised to do a 'restart and run all' before saving the notebook as jupro will take the notebook as is.

## Jupro

To create the snippets, install jupro and call it like this:

```
pip install jupro
python -m jupro INFILE
```

You can also call it from python (which allows you to change the output folder)

```
from pathlib import Path
import jupro
create_snippets(Path("test.ipynb"), out_folder=Path.cwd()/"out")
```

## Latex

In latex, you can directly use a code listing package to insert the snippets. You can also use our [codex.sty](codex.sty) class which might or might not be useful for your purposes. 
