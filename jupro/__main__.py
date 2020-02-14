import logging
from pathlib import Path

from . import create_snippets

logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)-5s] %(message)s')
import sys

create_snippets(Path(sys.argv[1]))