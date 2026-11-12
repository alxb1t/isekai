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

**A sampling sends the pod the tattoo's crop, its mask and its control, and nothing
else.** The sampled crop is stitched back and the ink's lines multiplied over it
here. The record is completed first and the image written last, so a crash between
the two leaves a request that is still pending; a failed sampling records no
failure, and the refusal names the discard.

Stdlib only at module scope: Pillow is imported inside the functions.
"""

import os
import random
import shlex
import time
from collections.abc import Callable, Collection, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from isekai.boundary.comfy import ComfyTransport, TransportFailure, submit_and_wait
from isekai.foundation.artifacts import (
    EDIT_FILE,
    SEED_BITS,
    CropRecord,
    EditRecord,
    Runtime,
    read,
    write,
)
from isekai.foundation.atomic_write import write_atomically
from isekai.foundation.edit import Edit, load_edit
from isekai.foundation.flow import Workflow, graph_digest
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    EDIT_RECORD,
    EDIT_STEM,
    delete_edits,
    digest_of,
    edit_at,
    edit_files,
    edit_numbers,
    next_edit,
    rendered_at,
)
from isekai.shared.tattoo import (
    Crop,
    Derivation,
    decode_composite,
    decode_render,
    derive,
    plan_crop,
    png_of,
    sampling_images,
    stitch,
)

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray

# The dials a request may change for one edit, in the order a record lists them.
OVERRIDES = ("denoise", "strength", "lines")

# Seconds a queued sampling may take before it gives up: a ComfyUI restarted in
# place loses the prompt, and the pod bills while the poll waits.
EDIT_DEADLINE = 600


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

    return png_of(Image.fromarray(pixels))


def _reserved(group: Path, seed: int, kept: bytes) -> tuple[int, Path, Path]:
    """Publish `kept` as the next free edit's composite; return its number and paths.

    The composite is published only where none exists, so the number is the
    request's own: one a concurrent request took since it was chosen is chosen again.
    e.g. 42.edit-1.composite.png taken meanwhile -> 42.edit-2.composite.png
    """
    while True:
        number = next_edit(group, seed)
        _, record_path, composite_path = edit_files(group, seed, number)
        try:
            write_atomically(composite_path, kept, exclusive=True)
        except FileExistsError:
            continue
        return number, record_path, composite_path


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
    number, record_path, composite_path = _reserved(group, render_seed, kept)
    write(record_path, EDIT_FILE, record)
    return Requested(composite_path, record_path, number, sampling_seed)


def records(group: Path) -> list[Path]:
    """Return the edit records in `group`, by the seed of the render, then the number.

    A record with its image beside it is as much a record as a pending one.
    e.g. a group holding 42.edit-2.json and 42.edit-1.json -> [edit-1, edit-2]
    """
    if not group.is_dir():
        return []
    found: list[tuple[int, int, Path]] = []
    for name in os.listdir(group):
        named = EDIT_STEM.fullmatch(name.removesuffix(EDIT_RECORD))
        if name.endswith(EDIT_RECORD) and named:
            found.append((int(named["seed"]), int(named["k"]), group / name))
    return [path for _, _, path in sorted(found)]


def pending(group: Path) -> list[Path]:
    """Return the records in `group` that have no image beside them, in chain order."""
    return [path for path in records(group) if not image_of(path).exists()]


def image_of(record: Path) -> Path:
    """Return the path of the image an edit record's sampling writes.

    e.g. outputs/001/42.edit-1.json -> outputs/001/42.edit-1.png
    """
    return record.with_suffix(".png")


def discard_edit(image: Path) -> list[Path]:
    """Delete an edit, pending or run, and every edit whose source chain reaches it.

    Return every path deleted, absolute. An edit whose record cannot be read is
    refused before anything is deleted, so a chain is never left half taken.
    e.g. 42.edit-1.png, with 42.edit-2 made from it -> both edits' three files
    """
    _, _, _, seed, number = edit_at(image)
    group = image.absolute().parent
    sources: dict[int, str | None] = {}
    for held in edit_numbers(group, seed):
        record = edit_files(group, seed, held)[1]
        sources[held] = read(record, EDIT_FILE)["source"] if record.is_file() else None
    taken = {number}
    while grown := {
        held
        for held, source in sources.items()
        if held not in taken
        and source in {edit_files(group, seed, each)[0].name for each in taken}
    }:
        taken |= grown
    return delete_edits(group, seed, sorted(taken))


def duration_of(record: Path) -> float | None:
    """Return the seconds a sampling recorded, or None for a request not yet run."""
    seconds = read(record, EDIT_FILE).get("duration")
    if isinstance(seconds, int | float) and not isinstance(seconds, bool):
        return float(seconds)
    return None


@dataclass(frozen=True)
class _Ready:
    """A pending edit checked and derived again, as its sampling reads it."""

    edit: Edit
    body: EditRecord
    composite: "NDArray[np.uint8]"
    derived: Derivation
    crop: Crop


def _stale(record: Path, why: str) -> Refusal:
    """Return the refusal of a pending edit that cannot run as requested."""
    image = shlex.quote(str(image_of(record)))
    return Refusal(
        f"{record.name}: {why}; run `python -m isekai discard {image}` to remove "
        "the request, then request the edit again"
    )


def _ready(record: Path) -> _Ready:
    """Return the edit `record` asks for, derived again from the files it names.

    Refused, naming the discard, when the edit's files, the source or the composite
    are not what the record holds the digests of, or the crop derives differently.
    """
    body = read(record, EDIT_FILE)
    edit = load_edit(body["edit"])
    if edit.digest != body["edit_digest"]:
        raise _stale(record, f"edit {edit.id} has changed since it was requested")
    group = record.parent
    held: dict[str, bytes] = {}
    for what, name, digest in (
        ("source", body["source"], body["source_sha256"]),
        (
            "composite",
            f"{record.name.removesuffix(EDIT_RECORD)}.composite.png",
            body["composite_sha256"],
        ),
    ):
        try:
            held[what] = (group / name).read_bytes()
        except OSError:
            raise _stale(record, f"its {what} {name} cannot be read") from None
        if digest_of(held[what]) != digest:
            raise _stale(record, f"its {what} {name} has changed since the request")
    dials = body["dials"]
    composite = decode_composite(held["composite"])
    derived = derive(decode_render(held["source"], body["source"]), composite, dials)
    crop = plan_crop(derived.mask, dials)
    recorded = body["crop"]
    if [*crop.box] != recorded["box"] or [*crop.size] != recorded["size"]:
        raise _stale(record, "its crop no longer derives as it was recorded")
    return _Ready(edit, body, composite, derived, crop)


def check(record: Path, waiting: Collection[Path] = ()) -> None:
    """Refuse a pending edit that would not run as requested, reading files alone.

    `waiting` is the images other pending edits will write: a source among them
    does not exist yet, so only the edit and the composite are checked, and the
    sampling checks the source once it does.
    """
    body = read(record, EDIT_FILE)
    if (record.parent / body["source"]) in waiting:
        edit = load_edit(body["edit"])
        if edit.digest != body["edit_digest"]:
            raise _stale(record, f"edit {edit.id} has changed since it was requested")
        return
    _ready(record)


def _patched(edit: Edit, body: EditRecord, names: tuple[str, str, str]) -> Workflow:
    """Return the edit's graph with its dials, words and the uploaded images set.

    `names` are the stored names of the crop, the mask and the control.
    """
    graph = edit.graph()
    dials = body["dials"]

    def patch(role: str, **inputs: object) -> None:
        graph[edit.node(role)]["inputs"].update(inputs)

    crop, mask, control = names
    patch("checkpoint", ckpt_name=edit.checkpoint)
    patch("clip_skip", stop_at_clip_layer=dials["clip_skip"])
    patch("positive", text=edit.prompt["positive"])
    patch("negative", text=edit.prompt["negative"])
    patch("image", image=crop)
    patch("mask", image=mask)
    patch("control", image=control)
    patch("controlnet", control_net_name=edit.controlnet)
    patch("union", type=edit.union_type)
    patch(
        "apply",
        strength=dials["strength"],
        start_percent=dials["start_percent"],
        end_percent=dials["end_percent"],
    )
    patch(
        "sampler",
        seed=body["seed"],
        steps=dials["steps"],
        cfg=dials["cfg"],
        sampler_name=dials["sampler_name"],
        scheduler=dials["scheduler"],
        denoise=dials["denoise"],
    )
    return graph


def sample(
    client: ComfyTransport,
    record: Path,
    *,
    runtime: Callable[[], Runtime],
    poll: float = 1.0,
    deadline: float = EDIT_DEADLINE,
    clock: Callable[[], float] = time.monotonic,
) -> Path:
    """Sample one pending edit on `client` and write its image, returning its path.

    The crops are derived again from the source and the composite, uploaded, and
    the edit's graph is patched from its manifest and the record. The record is
    completed with the graph's digest, the runtime and the seconds taken before the
    image is written, atomically and last. A failure leaves the request pending.
    e.g. outputs/001/42.edit-1.json -> outputs/001/42.edit-1.png
    """
    ready = _ready(record)
    image = image_of(record)
    stem = record.name.removesuffix(EDIT_RECORD)
    crop_png, mask_png, control_png = sampling_images(
        ready.composite, ready.derived, ready.crop
    )
    try:
        ran_on = runtime()
        names = (
            client.upload_image(f"{stem}.crop.png", crop_png),
            client.upload_image(f"{stem}.mask.png", mask_png),
            client.upload_image(f"{stem}.control.png", control_png),
        )
        graph = _patched(ready.edit, ready.body, names)
        started = clock()
        body = submit_and_wait(client, graph, poll, deadline)
        took = round(clock() - started, 1)
    except Refusal as failed:
        kind = failed.kind if isinstance(failed, TransportFailure) else "permanent"
        raise _stale(
            record, f"the sampling failed ({kind}) -- {failed}; it stays pending"
        ) from failed
    stitched = stitch(
        ready.composite,
        body,
        ready.derived,
        ready.crop,
        float(ready.body["dials"]["lines"]),
    )
    completed: EditRecord = {
        **ready.body,
        "graph_sha256": graph_digest(graph),
        "runtime": ran_on,
        "duration": took,
    }
    write(record, EDIT_FILE, completed)
    write_atomically(image, _kept(stitched))
    return image
