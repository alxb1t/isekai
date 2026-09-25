"""The WD14 boundary: a local ONNX session, its label index, and what it emits.

**The heavier of the pipeline's two tagger boundaries, and the only one that
reaches no network at all.** `ollama.py` reaches a model over HTTP, on the alias
the flow's manifest names in its `model` key -- a key every flow is required to
declare, so it runs for every flow; this one opens a digest-verified file and
resolves through **no manifest key at all**. They are deliberately not two
implementations of one Protocol: one is selected by a string in a frozen manifest,
because which model answers is a claim a flow makes about itself, and the other by
a pin in this build that no flow has an opinion about. A Protocol whose two
implementations resolve through different mechanisms is a shared name rather than
a seam (design.md D3).

**This file's non-stdlib imports are all function-local.** `onnxruntime`,
`numpy` and `Pillow` are declared dependencies as of v0.22.3 and are imported
inside the functions that need them, so `python -m isekai`'s import graph reaches
no wheel and the `-S` guard still passes. Because they are installed by default,
an import moved to module scope here resolves rather than failing; the `-S` guard
and `tests/test_wd14.py`'s source scan catch it. The arrangement is `ollama.py`'s:
the transport here, the adapter in `pipeline/`. There is no adapter in this file.

**Opening the session is the expensive act and it happens once, on first use.**
The graph is 467 MB and takes ~0.9 s to open, against ~0.4 s a photograph. So
`wiring` resolves a tagger per flow and nothing is constructed until a flow asks
-- a machine that never captions must not open the file anyway (design.md D14).
Nothing at module scope holds a session: an `__init__.py` in this package carries
a docstring and no code by rule, and a module-level lazy handle is that rule
broken one directory down.

**`selected_tags.csv` is not a file published beside the model, it is the model's
output layer.** Row N names output neuron N, so the CSV's *file order* is
load-bearing in a way nothing else in this repository's use of it is --
`shared/vocabulary.py` reads the same file and throws the order away, because for
mapping a phrase the order means nothing. Here a pair from two revisions mislabels
every tag silently: the vector has the right length and every name in it is a real
tag. That is why both halves are pinned in `scripts/vocabulary.json` and why both
digests are verified before the first inference (design.md D17, D18).

**Preparation sits behind the seam rather than in front of it**, so `Session`
takes a photograph and not a prepared array. That is what makes the stage itself
runnable in the suite without a wheel: `prepare` needs `numpy` and `Pillow`, the
suite keeps the stage's tests off both deliberately, and a seam beginning after
preparation would leave `tagging:seam:offline-double-satisfies-the-interface`
provable only by reaching for them.

**The one silent failure mode is the ordering**, which is exactly what the suite
asserts against a fake session: a vector whose only high value sits at index 1
must yield the tag on CSV row 1 and no other. Nothing else in this module can go
wrong without saying so.
"""

import csv
import io
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import cache
from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import Protocol

from isekai.foundation.refusal import Refusal
from isekai.shared.vocabulary import (
    DEFAULT_MODELS_DIR,
    VOCABULARY_DEST,
    VOCABULARY_REMEDY,
)

# The two destinations the vocabulary manifest declares. Both are verified before
# the first inference, because either one alone proves nothing: the graph's bytes
# say nothing about which names its neurons carry, and the list's say nothing
# about which graph it indexes.
#
# The label index's dest and the models root are `shared/vocabulary.py`'s,
# imported rather than restated: the same file is read by the sorting stage for
# a different purpose, and a re-pin that moved it must not have two places to be
# found. `VOCABULARY_REMEDY` is that module's too, for the same reason -- the
# refusals below and its own have to name one command.
LABELS_DEST = VOCABULARY_DEST
MODEL_DEST = "wd14/model.onnx"
REMEDY = VOCABULARY_REMEDY

# The tagger's own category numbering. `0` is the general tags -- what a person
# looks like -- and 4 (character names) and 9 (rating meta-tags) describe no
# part of a person's appearance, so neither is ever returned. Only the general
# number is a constant, because it is the only one anything compares against;
# the other two are excluded by *not* matching this, which is one rule rather
# than three.
#
# An `int`, where `shared/vocabulary.py`'s is the `str` `csv.DictReader` yields.
# The two are deliberately not shared: this module parses the column to an int so
# the comparison cannot silently be a no-op against the wrong type, and a single
# constant would have to be one or the other and be wrong in one place.
GENERAL_CATEGORY = 0

# Below this, a tag is not shown. Measured rather than chosen: at 0.35 the panel
# loses `blurry background 0.19`, `cowboy shot 0.20` and `head tilt 0.28`, three
# tags correction-mining measured the operator adding by hand, which is exactly
# the recall this stage exists to buy. The band also admits wrong tags --
# `black hair 0.31` on a brown-haired subject -- and that is what printing the
# number is for: sorted descending, it arrives under `brown hair 0.91` and refutes
# itself (design.md D13). Not a manifest key and not a flag; add one the day a
# flow wants a different floor, with a reason.
FLOOR = 0.15

# What the graph was trained to see. The photograph is composited onto white,
# padded to a square and resized to the session's own declared input dimension --
# read off the session rather than hard-coded, because a sibling tagger in the
# same family is a different number and a constant here would be silently wrong
# against it.
BACKGROUND = (255, 255, 255)


@dataclass(frozen=True)
class Label:
    """One row of the label index: the name of one output neuron and its kind."""

    name: str
    category: int


@dataclass(frozen=True)
class Scored:
    """One tag the session was confident enough about, and how confident."""

    tag: str
    confidence: float


@dataclass(frozen=True)
class LocalTagger:
    """An opened session, its label index, and the pins both were verified under.

    The three always travel together and never apart, so they travel as one
    value rather than as a tuple threaded through four layers.

    **The pins are carried rather than re-read**, and that is the point of
    holding them here: they are the digests `verified_paths` actually checked
    the bytes against a moment earlier. An artifact that re-read the manifest at
    write time could record a pin it was *not* produced under -- which is exactly
    the claim `pinned: true` exists to make trustworthy (design.md D17, D18).
    """

    session: "Session"
    labels: tuple[Label, ...]
    pins: Mapping[str, Mapping[str, str]]


class Session(Protocol):
    """How a photograph becomes a probability vector. Faked, so the suite runs.

    The precedent is one file away -- `ollama.Transport`, whose real
    implementation is `ollama.post` and whose double is what makes the request
    body assertable without a socket. Here the double is what makes the whole
    stage runnable without a 467 MB file, and the suite is offline because of it.

    **The seam takes the photograph rather than a prepared array**, and the
    difference is what the double is worth. `prepare` needs `numpy` and
    `Pillow`, which the environment the gate runs in deliberately does not
    install -- so a seam that began *after* preparation would leave the stage
    itself untestable and `tagging:seam:offline-double-satisfies-the-interface`
    unprovable. Preparing an image is this boundary's business in exactly the way
    encoding a request body is `ollama.post`'s: it belongs behind the seam.
    """

    def run(self, photo: Path) -> Sequence[float]:
        """Return one probability per output neuron, in the index's own order."""
        ...


@cache
def _require(module: str) -> ModuleType:
    """Import one module of the tagger's stack, or refuse naming how to get it.

    `eval_backends._require`'s shape, for `eval_backends`' reason: without it a
    machine whose environment is missing the stack gets a bare
    `ModuleNotFoundError` traceback, in a package whose rule is that every
    failure is a named `Refusal` naming its remedy.

    **The import is still function-local, and that is what this indirection is
    for now.** v0.22.3 made these three declared dependencies rather than an
    extra, so a synced checkout has them and this path is the unsynced case
    rather than the ordinary one — but the entry point still reaches no
    third-party package at module scope, which is why `isekai show` works on a
    checkout that has provisioned nothing.

    Not shared with `eval_backends`' copy, and that is the whole content of the
    difference: that one names an extra and this one no longer does, so one
    function would have to be told which sentence to print — and the sentence it
    prints is the only thing either does.

    Cached, so the import machinery is consulted once per module rather than
    once per photograph.
    """
    try:
        return import_module(module)
    except ModuleNotFoundError as absent:  # pragma: no cover - environment
        raise Refusal(
            f"the local tagger's stack is not installed ({module} is missing); "
            "run `uv sync`. It is a declared dependency of this project as of "
            "v0.22.3, so a synced checkout has it and every test runs against a "
            "fake session regardless."
        ) from absent


def read_labels(body: str) -> list[Label]:
    """Parse `selected_tags.csv` into the label index, **in file order**.

    The order is the contract. Row N of this file names output neuron N of the
    graph beside it, so a sorted, filtered or deduplicated read here would
    mislabel every tag while looking exactly like a correct one. Nothing is
    dropped and nothing is reordered; the category filtering happens after the
    vector has been indexed, never before.
    """
    rows = list(csv.DictReader(io.StringIO(body)))
    if not rows:
        raise Refusal(
            f"{LABELS_DEST} parsed to no rows, so no output neuron has a name; "
            f"re-provision it (`{REMEDY}`) and run this command again"
        )
    return [Label(name=row["name"], category=int(row["category"])) for row in rows]


def verified_paths(
    models_dir: Path = DEFAULT_MODELS_DIR,
) -> tuple[Path, Path, dict[str, dict[str, str]]]:
    """Return both digest-verified paths and the pins they were verified against.

    **Both, before the first inference, and neither alone is worth anything.**
    Verification goes through the scorer's resolver rather than a second copy of
    it, which is the repository's single enforcement site for the containment and
    digest rules -- the same route `shared/vocabulary.py` takes to the same
    manifest.

    An absent file is a `Refusal` naming the one command that fixes it, which is
    the posture this repository takes for every absent dependency. A file present with
    the wrong bytes is left to `DigestMismatch`, whose message already names the
    file, the digest expected and the digest computed -- all three, because that
    one is read by a human deciding whether a pin is stale or a file was swapped.
    """
    from isekai.boundary.provision import VOCABULARY_MANIFEST_PATH, load_manifest
    from isekai.evaluation.eval_models import entry_for, resolve

    manifest = load_manifest(VOCABULARY_MANIFEST_PATH)
    resolved: list[Path] = []
    pins: dict[str, dict[str, str]] = {}
    for dest in (LABELS_DEST, MODEL_DEST):
        try:
            resolved.append(resolve(dest, models_dir, manifest))
        except FileNotFoundError as absent:
            raise Refusal(
                f"{dest} is not provisioned under {models_dir}/, and the local "
                f"tagger cannot run without it; run `{REMEDY}` from the "
                "repository root to fetch and verify it against its pinned "
                "manifest"
            ) from absent
        # `entry_for` rather than a comprehension over `entries`: a dest the
        # manifest does not declare must raise here, not quietly leave a pin out
        # -- an artifact claiming `pinned: true` with one of the two digests is
        # half a claim, and half of this one is worth nothing.
        pins[dest] = {"sha256": entry_for(manifest, dest)["sha256"]}
    return resolved[0], resolved[1], pins


def prepare(photo: Path, dimension: int) -> object:
    """Return `photo` as the batched BGR array this family of graphs expects.

    Six steps, and each one is the graph's rather than a choice: composite onto
    white so a transparent PNG does not arrive as black, pad to a square so the
    resize cannot change the subject's proportions, resize with bicubic to the
    edge the **session** declares, convert RGB to BGR, widen to float32, and add
    the batch axis.

    `dimension` is a parameter rather than a constant because `OnnxSession` reads
    it off the graph: a sibling tagger in the same family declares a different
    input size, and a number hard-coded here would resize correctly against the
    one graph it was written for and silently wrongly against every other.

    **The return type is `object` rather than `Any`**, and that is the honest one
    as well as the one that needs no suppression: the array is opaque to every
    caller here -- the only thing anything may do with it is hand it back to
    `Session.run`. `numpy.typing.NDArray` could be named now that `numpy` is a
    declared dependency, and it would say more than any caller is allowed to
    use; naming the value opaque says exactly what the seam permits, without
    waiving a rule.

    The third-party imports are function-local, which is what keeps them off
    `python -m isekai`'s import graph at module scope.
    """
    numpy = _require("numpy")
    Image = _require("PIL.Image")

    opened = Image.open(photo)
    opened.load()
    if opened.mode == "RGBA" or "transparency" in opened.info:
        canvas = Image.new("RGBA", opened.size, (*BACKGROUND, 255))
        canvas.alpha_composite(opened.convert("RGBA"))
        opened = canvas
    opened = opened.convert("RGB")

    edge = max(opened.size)
    square = Image.new("RGB", (edge, edge), BACKGROUND)
    square.paste(opened, ((edge - opened.width) // 2, (edge - opened.height) // 2))
    resized = square.resize((dimension, dimension), Image.Resampling.BICUBIC)

    pixels = numpy.asarray(resized, dtype=numpy.float32)
    return numpy.expand_dims(pixels[:, :, ::-1], axis=0)


def select(
    probabilities: Sequence[float],
    labels: Sequence[Label],
    *,
    floor: float = FLOOR,
) -> list[Scored]:
    """Return the general tags above `floor`, sorted by confidence descending.

    **The pure half of this module, and the half that can go silently wrong**, so
    it is separated from `prepare` deliberately rather than as a convenience: the
    ordering is what the suite asserts, and it asserts it without a wheel on
    purpose: `numpy` and `Pillow` are installed, so nothing but this split keeps
    the ordering decidable against a hand-written vector rather than a real
    graph. Nothing here imports any third-party package.

    **The vector is indexed before anything is filtered**, which is the whole
    ordering contract in one line: `labels[i]` names neuron `i`, so dropping the
    character and rating rows first would shift every general tag onto some other
    neuron's name. Character tags (category 4) and rating tags (category 9) are
    excluded from the *result*, never from the index.

    A vector whose length disagrees with the index is refused rather than zipped
    short. `zip` without `strict` truncates to the shorter of the two, which is
    the mismatch this module exists to catch turning into a quietly shorter tag
    list instead of a message.
    """
    if len(probabilities) != len(labels):
        raise Refusal(
            f"the tagger returned {len(probabilities)} probabilities and "
            f"{LABELS_DEST} names {len(labels)} neurons; the label index and the "
            f"graph are not from one revision -- re-provision both (`{REMEDY}`)"
        )
    above = [
        Scored(tag=label.name, confidence=float(probability))
        for label, probability in zip(labels, probabilities, strict=True)
        if label.category == GENERAL_CATEGORY and probability >= floor
    ]
    above.sort(key=lambda found: (-found.confidence, found.tag))
    return above


def scored(
    photo: Path,
    session: Session,
    labels: Sequence[Label],
    *,
    floor: float = FLOOR,
) -> list[Scored]:
    """Run `photo` through `session` and select what it emitted.

    One line, and the whole of what it adds over `select` is the session: the
    preparation rule and the graph are the two things that need a wheel, both sit
    behind `Session`, and everything decidable without one is decided in
    `select`.
    """
    return select(session.run(photo), labels, floor=floor)


class OnnxSession:
    """The real session: `onnxruntime` over the digest-verified graph.

    Constructed once per flow, by `wiring`, on first use. `onnxruntime` is
    imported in `__init__` rather than at module scope for the rule this whole
    file exists to keep: the entry point imports no third-party package at
    module scope.
    """

    def __init__(self, model: Path) -> None:
        """Open `model` for inference on the CPU."""
        onnxruntime = _require("onnxruntime")

        self._session = onnxruntime.InferenceSession(
            str(model), providers=["CPUExecutionProvider"]
        )
        self._input = self._session.get_inputs()[0]

    @property
    def dimension(self) -> int:
        """The square edge this graph's input declares, read off the graph."""
        # NHWC: (batch, height, width, channels). The batch axis is symbolic, so
        # only the spatial ones are read, and they are equal for this family.
        _, height, _width, _channels = self._input.shape
        return int(height)

    def run(self, photo: Path) -> Sequence[float]:
        """Prepare `photo` to this graph's own input size, then infer over it.

        The dimension is read off the graph rather than written down: a sibling
        tagger in the same family declares a different edge, and a constant would
        resize correctly against the one graph it was written for and silently
        wrongly against every other.
        """
        outputs = self._session.run(
            None, {self._input.name: prepare(photo, self.dimension)}
        )
        return list(outputs[0][0])


def open_session(models_dir: Path = DEFAULT_MODELS_DIR) -> LocalTagger:
    """Verify both halves, then open the session and read its label index.

    The one function a caller needs, and the order inside it is the point: the
    digests are checked **before** 467 MB is opened, so a stale pin costs a
    refusal rather than a load followed by one. The pins it checked come back
    with the session, so whatever records a provenance records what was actually
    verified rather than what the manifest says at write time.

    **Expensive, and called lazily.** Hashing the graph is a full pass over
    467 MB and opening it is ~0.9 s more, so nothing calls this until a
    photograph actually needs scoring -- `interface/cli.py` holds it behind a
    thunk for the same reason `Wiring.vocabulary` is one.
    """
    labels_path, model_path, pins = verified_paths(models_dir)
    return LocalTagger(
        session=OnnxSession(model_path),
        labels=tuple(read_labels(labels_path.read_text())),
        pins=pins,
    )


__all__: Sequence[str] = (
    "DEFAULT_MODELS_DIR",
    "FLOOR",
    "GENERAL_CATEGORY",
    "LABELS_DEST",
    "MODEL_DEST",
    "REMEDY",
    "Label",
    "LocalTagger",
    "OnnxSession",
    "Scored",
    "Session",
    "open_session",
    "prepare",
    "read_labels",
    "scored",
    "select",
    "verified_paths",
)
