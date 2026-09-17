"""The entry point `python -m isekai` resolves to.

The command line itself is `isekai.interface.cli`. This file is the path `runpy`
pins, and nothing more.
"""

import sys

from isekai.interface.cli import main

if __name__ == "__main__":
    sys.exit(main())
