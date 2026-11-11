"""Stage (5): request an edit of a finished render, free and local.

An edit takes a render and a hand-made composite of it, the render with a tattoo
multiplied on, and writes beside the render what the pod will be sent: the
composite, kept as pixels alone, and a record that names every digest and dial the
sampling will read. A request with no image beside it is **pending**; the render
session runs it.

**Everything that can refuse is checked before anything is written.** A composite
that is the wrong size, transparent, lighter than its render or without ink is
refused with its fix, and the group is left as it was. The composite goes first
and the record last, so a record always has its composite.

**The photograph a tattoo was cut from never enters a run.** The request reads
the composite and the render, and nothing else.

Stdlib only at module scope: Pillow is imported inside the functions.
"""

import io
import random
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from isekai.foundation.artifacts import (
    EDIT_FILE,
    SEED_BITS,
    CropRecord,
    EditRecord,
    write,
)
from isekai.foundation.atomic_write import write_atomically
from isekai.foundation.edit import Edit
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    EDIT_STEM,
    digest_of,
    edit_at,
    edit_files,
    next_edit,
    rendered_at,
)
from isekai.shared.tattoo import decode_composite, decode_render, derive, plan_crop

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray

# The dials a request may change for one edit, in the order a record lists them.
OVERRIDES = ("denoise", "strength", "lines")


@dataclass(frozen=True)
class Requested:
    """What a request wrote: its composite and record, its number and sampling seed."""

    composite: Path
    record: Path
    number: int
    seed: int


def _located(source: Path) -> tuple[Path, int]:
    """Return the absolute path of `source` and the seed of the render it descends from.

    `source` is a render, or an edit's image to chain from.
    e.g. outputs/001/42.edit-1.png -> (that path, 42)
    """
    if EDIT_STEM.match(source.stem):
        return source.absolute(), edit_at(source)[3]
    return source.absolute(), rendered_at(source)[3]


def _read(path: Path, what: str) -> bytes:
    """Return the bytes of `path`, refusing one that cannot be read."""
    try:
        return path.read_bytes()
    except OSError as unreadable:
        raise Refusal(
            f"{what} {path.name}: cannot be read ({unreadable.strerror}); "
            "check the path and the file's permissions, then give it again"
        ) from unreadable


def _in_range(name: str, value: float) -> bool:
    """Return whether `value` is one the dial `name` takes."""
    if name == "denoise":
        return 0 < value <= 1
    if name == "lines":
        return 0 <= value <= 1
    return value >= 0


# What each override takes, as a refusal says it.
_RANGES = {"denoise": "above 0, at most 1", "strength": "0 or more", "lines": "0 to 1"}


def _dials(edit: Edit, overrides: Mapping[str, float | None]) -> dict[str, object]:
    """Return the edit's dials with each given override applied, refusing a bad one.

    e.g. `{"denoise": 0.3}` -> the edit's dials with denoise 0.3
    """
    dials = dict(edit.dials)
    for name in OVERRIDES:
        given = overrides.get(name)
        if given is None:
            continue
        if not _in_range(name, given):
            raise Refusal(
                f"--{name} {given} is outside the range the dial takes, "
                f"{_RANGES[name]}; give a value in that range"
            )
        dials[name] = given
    return dials


def _kept(pixels: "NDArray[np.uint8]") -> bytes:
    """Return `pixels` as a PNG that carries no profile and no metadata."""
    from PIL import Image

    body = io.BytesIO()
    Image.fromarray(pixels).save(body, "PNG")
    return body.getvalue()


def request(
    edit: Edit,
    source: Path,
    composite: Path,
    *,
    overrides: Mapping[str, float | None],
    seed: int | None,
    rng: random.Random,
) -> Requested:
    """Write the composite and the pending record of an edit of `source`.

    `source` is a render or an edit's image; the edit is the next free number of the
    render's seed in its group. The sampling seed is `seed`, else drawn from `rng` as
    a render's is. `overrides` names the dials changed, and the record lists them.
    Nothing is written when any check refuses.
    e.g. outputs/001/42.png -> outputs/001/42.edit-1.composite.png, then 42.edit-1.json
    """
    image, render_seed = _located(source)
    group = image.parent
    source_bytes = _read(image, "the source")
    dials = _dials(edit, overrides)
    render = decode_render(source_bytes, image.name)
    pixels = decode_composite(_read(composite, "the composite"))
    derived = derive(render, pixels, dials)
    crop = plan_crop(derived.mask, dials)

    number = next_edit(group, render_seed)
    _, record_path, composite_path = edit_files(group, render_seed, number)
    kept = _kept(pixels)
    sampling_seed = rng.getrandbits(SEED_BITS) if seed is None else seed
    cropped: CropRecord = {
        "box": list(crop.box),
        "size": list(crop.size),
        "widened": crop.widened,
        "grown": crop.grown,
    }
    record: EditRecord = {
        "schema": EDIT_FILE.schema,
        "edit": edit.id,
        "edit_digest": edit.digest,
        "source": image.name,
        "source_sha256": digest_of(source_bytes),
        "composite_sha256": digest_of(kept),
        "seed": sampling_seed,
        "dials": dials,
        "overridden": [name for name in OVERRIDES if overrides.get(name) is not None],
        "crop": cropped,
    }
    write_atomically(composite_path, kept)
    write(record_path, EDIT_FILE, record)
    return Requested(composite_path, record_path, number, sampling_seed)
