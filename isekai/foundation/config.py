"""Read a JSON config by the keys a build reads.

Stdlib and `refusal` only.
"""

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from isekai.foundation.refusal import Refusal


def read_keyed(path: Path, keys: Sequence[str]) -> Any:  # noqa: ANN401 -- the caller checks each value
    """Return the document at `path`, refusing a key outside `keys` or one missing."""
    document: Any = json.loads(path.read_text())
    unknown = sorted(key for key in document if key not in keys)
    if unknown:
        raise Refusal(
            f"{path.name} declares {', '.join(unknown)}, which this build does not "
            f"read; the keys it reads are {', '.join(keys)} -- correct the spelling"
        )
    missing = [key for key in keys if key not in document]
    if missing:
        raise Refusal(
            f"{path.name} declares no {', '.join(missing)}; add the key to {path.name}"
        )
    return document
