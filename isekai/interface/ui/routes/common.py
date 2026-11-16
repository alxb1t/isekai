"""What more than one resource's routes read: a body's keys and a photograph's size."""

from collections.abc import Mapping, Sequence
from typing import Any

from isekai.foundation.refusal import Refusal
from isekai.foundation.run import Run
from isekai.shared.image import dimensions_or_refuse


def _needs(payload: Mapping[str, Any], keys: Sequence[str]) -> None:
    """Refuse a body that lacks any of `keys`, naming each."""
    missing = [key for key in keys if key not in payload]
    if missing:
        raise Refusal(f"the request lacks {', '.join(missing)}; send {', '.join(keys)}")


def _dimensions(run: Run) -> tuple[int, int]:
    """Return the photograph's size, as a `Refusal` rather than an exit."""
    return dimensions_or_refuse(
        run.photo,
        "the page reads the photograph's own header to size itself and there is "
        "nothing to fall back to -- re-export it as a JPEG or PNG",
    )
