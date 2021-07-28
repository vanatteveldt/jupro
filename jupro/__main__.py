import logging
from pathlib import Path
import argparse

from . import create_snippets

logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)-5s] %(message)s')

parser = argparse.ArgumentParser()
parser.add_argument("files", nargs="+", help="File(s) to process", type=Path)
args = parser.parse_args()
for file in args.files:
    create_snippets(file)