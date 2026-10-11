"""Print the build record: the SHA-256 of the `Dockerfile` and of every file it copies.

Run it from the repository root:

    uv run python -m tools.image_record
    e.g. {"Dockerfile": "<sha256>", "config/models.json": "<sha256>", ...}

`config/image.json` holds the same object under `files`, and a test re-derives
it; `build-image.yml` prints it into the build's summary from its own checkout,
so an image says which tree it was built from (D28). Stdlib only: the workflow
runs it without installing the project.
"""

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# A `COPY` from the build context: one source, one destination, no flag. An
# instruction's name is case-insensitive and may follow whitespace.
COPY = re.compile(r"^\s*COPY\s+(?!--)(\S+)\s+(\S+)\s*$", re.I)

# The forms that take nothing from the build context: a `COPY` from another
# image, and an `ADD` of a URL whose checksum the `Dockerfile` itself pins.
FROM_IMAGE = re.compile(r"^\s*COPY\s+--from=", re.I)
CHECKSUMMED_URL = re.compile(
    r"^\s*ADD\s+--checksum=sha256:[0-9a-f]{64}\s+https://\S+\s+\S+\s*$", re.I
)
# Matched against an instruction with its continuations joined, so a name wrapped
# straight after itself is still seen.
TAKES_FILES = re.compile(r"^\s*(COPY|ADD)(\s|$)", re.I)


def instructions(dockerfile: str) -> list[str]:
    r"""Return each instruction as written, its continued lines joined by newlines.

    A comment line is dropped before continuations are joined, as Docker drops it,
    so a comment ending in a backslash continues nothing.
    e.g. "RUN a \\\n  b\nCOPY c /c\n" -> ["RUN a \\\n  b", "COPY c /c"]
    """
    found: list[str] = []
    held: list[str] = []
    for line in dockerfile.splitlines():
        if line.lstrip().startswith("#"):
            continue
        held.append(line)
        if not line.rstrip().endswith("\\"):
            found.append("\n".join(held))
            held = []
    if held:
        found.append("\n".join(held))
    return found


def copies(dockerfile: str) -> list[tuple[str, str]]:
    """Return each `(source, destination)` a `COPY` takes from the build context.

    Raise `ValueError` naming any other `COPY` or `ADD`, so no copied file leaves
    the record unseen. e.g. "COPY --chmod=755 a.py /a.py" -> ValueError
    """
    pairs = []
    for written in instructions(dockerfile):
        joined = " ".join(
            part.rstrip().removesuffix("\\") for part in written.split("\n")
        )
        if not TAKES_FILES.match(joined):
            continue
        if FROM_IMAGE.match(joined) or CHECKSUMMED_URL.match(joined):
            continue
        found = COPY.match(written)
        # a continued line's next line holds the rest of its sources
        if found is None or "\n" in written or written.rstrip().endswith("\\"):
            raise ValueError(
                f"cannot read {written!r}: a COPY from the build context takes one "
                "source, one destination and no flag, and an ADD only a URL with "
                "--checksum"
            )
        pairs.append((found[1], found[2]))
    return pairs


def copied(dockerfile: str) -> list[str]:
    """Return each source a `COPY` takes from the build context, in order."""
    return [source for source, _ in copies(dockerfile)]


def record(root: Path = ROOT) -> dict[str, str]:
    """Return the SHA-256 of `root`'s `Dockerfile` and each file it copies, by path."""
    names = ["Dockerfile", *copied((root / "Dockerfile").read_text(encoding="utf-8"))]
    return {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in names
    }


if __name__ == "__main__":
    print(json.dumps(record(), indent=2))
