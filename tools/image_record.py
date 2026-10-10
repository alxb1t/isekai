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

# A `COPY` from the build context: one source, one destination, no flag.
COPY = re.compile(r"^COPY\s+(?!--)(\S+)\s+(\S+)\s*$", re.M)

# Every `COPY` line, and the form that copies from another image, not the context.
COPY_LINE = re.compile(r"^COPY\b.*$", re.M)
FROM_IMAGE = re.compile(r"^COPY\s+--from=")


def copied(dockerfile: str) -> list[str]:
    """Return each source a `COPY` takes from the build context, in order.

    Raise `ValueError` naming any other `COPY` line, so no copied file leaves the
    record unseen. e.g. "COPY --chmod=755 a.py /a.py" -> ValueError
    """
    sources = []
    for line in COPY_LINE.findall(dockerfile):
        if FROM_IMAGE.match(line):
            continue
        found = COPY.match(line)
        # a continued line's next line holds the rest of its sources
        if found is None or line.rstrip().endswith("\\"):
            raise ValueError(
                f"cannot read {line!r}: a COPY from the build context takes one "
                "source, one destination and no flag"
            )
        sources.append(found[1])
    return sources


def record(root: Path = ROOT) -> dict[str, str]:
    """Return the SHA-256 of `root`'s `Dockerfile` and each file it copies, by path."""
    names = ["Dockerfile", *copied((root / "Dockerfile").read_text(encoding="utf-8"))]
    return {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in names
    }


if __name__ == "__main__":
    print(json.dumps(record(), indent=2))
