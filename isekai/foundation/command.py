"""The command a person is told to run, spelt once.

Imports nothing, and is on `python -m isekai`'s import graph (D20).
"""

# The words every printed command starts with; a prefix such as `uv run` is its site's.
ENTRY = "python -m isekai"


def command(verb: str, *words: str) -> str:
    """Return `verb` and `words` after the entry, joined by one space, none quoted.

    A word is its site's own text: quoted by it, or a placeholder.
    e.g. ("render", "b/runs", "f=1") -> "python -m isekai render b/runs f=1"
         ("migrate",) -> "python -m isekai migrate"
    """
    return " ".join((ENTRY, verb, *words))
