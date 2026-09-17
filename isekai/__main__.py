"""The entry point `python -m isekai` resolves to; the command line is `isekai.cli`."""

import sys

from isekai.cli import main

if __name__ == "__main__":
    sys.exit(main())
