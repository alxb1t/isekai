"""The WD14 boundary: a local ONNX session, its label index, and what it emits.

**The heavier of the pipeline's two tagger boundaries, and the only one that
reaches no network at all.** `ollama.py` reaches a model over HTTP and exists only
where a flow's manifest declares a `hosted` block; this one opens a file on disk
and resolves through nothing. They are deliberately not two implementations of one
Protocol: the registry that would key it is keyed on `hosted.implementation`, a
string WD14 does not have (design.md D3).

**The whole non-stdlib import of this package lives in this file and is
function-local.** `onnxruntime`, `numpy` and `Pillow` arrive through the `tagging`
extra and are imported inside the functions that need them, so
`python -m isekai`'s import graph stays stdlib-only and the `-S` guard still
passes. The arrangement is `ollama.py`'s: the transport here, the adapter in
`pipeline/`. There is no adapter in this file.

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

**The one silent failure mode is the ordering**, which is exactly what the suite
asserts against a fake session: a vector whose only high value sits at index 1
must yield the tag on CSV row 1 and no other. Nothing else in this module can go
wrong without saying so.
"""

import csv
import io
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from isekai.foundation.refusal import Refusal

# The two destinations the vocabulary manifest declares. Both are verified before
# the first inference, because either one alone proves nothing: the graph's bytes
# say nothing about which names its neurons carry, and the list's say nothing
# about which graph it indexes.
LABELS_DEST = "wd14/selected_tags.csv"
MODEL_DEST = "wd14/model.onnx"

# The models root every consumer of a manifest already defaults to. One tree, one
# provisioning rule, and `shared/vocabulary.py` reaching the same place.
DEFAULT_MODELS_DIR = Path("models")

# The one command that provisions anything in this repository, pointed at the
# manifest that declares both halves. Named once, so the two refusals below and
# `shared/vocabulary.py`'s cannot drift into naming different commands for the
# same fix.
REMEDY = "bash scripts/download_models.sh scripts/vocabulary.json"

# The tagger's own category numbering, and the same three numbers
# `shared/vocabulary.py` reads off the same file. `0` is the general tags -- what
# a person looks like. `4` is character names and `9` is the rating meta-tags;
# neither describes a person's appearance, and neither is ever returned.
GENERAL_CATEGORY = 0
CHARACTER_CATEGORY = 4
RATING_CATEGORY = 9

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


class Session(Protocol):
    """How a prepared image becomes a probability vector. Faked, so the suite runs.

    The precedent is one file away -- `ollama.Transport`, whose real
    implementation is `ollama.post` and whose double is what makes the request
    body assertable without a socket. Here the double is what makes the label
    index assertable without a 467 MB file, and the whole suite is offline
    because of it.

    `dimension` is on the seam rather than a constant because the preparation
    rule reads it: the graph declares its own input size and the fake declares a
    small one, so a test proves the resize follows the session instead of
    following a number this module guessed.
    """

    @property
    def dimension(self) -> int:
        """The square edge, in pixels, this session's input expects."""
        ...

    def run(self, prepared: object) -> Sequence[float]:
        """Return one probability per output neuron, in the index's own order."""
        ...


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


def verified_paths(models_dir: Path = DEFAULT_MODELS_DIR) -> tuple[Path, Path]:
    """Return the label index and the graph, both digest-verified, or refuse.

    **Both, before the first inference, and neither alone is worth anything.**
    Verification goes through the scorer's resolver rather than a second copy of
    it, which is the repository's single enforcement site for the containment and
    digest rules -- the same route `shared/vocabulary.py` takes to the same
    manifest.

    An absent file is a `Refusal` naming the one command that fixes it, which is
    the posture `require_binary()` takes for an absent binary. A file present with
    the wrong bytes is left to `DigestMismatch`, whose message already names the
    file, the digest expected and the digest computed -- all three, because that
    one is read by a human deciding whether a pin is stale or a file was swapped.
    """
    from isekai.boundary.provision import VOCABULARY_MANIFEST_PATH, load_manifest
    from isekai.evaluation.eval_models import resolve

    manifest = load_manifest(VOCABULARY_MANIFEST_PATH)
    resolved: list[Path] = []
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
    labels, model = resolved
    return labels, model


def prepare(photo: Path, dimension: int) -> object:
    """Return `photo` as the batched BGR array this family of graphs expects.

    Six steps, and each one is the graph's rather than a choice: composite onto
    white so a transparent PNG does not arrive as black, pad to a square so the
    resize cannot change the subject's proportions, resize with bicubic to the
    edge the **session** declares, convert RGB to BGR, widen to float32, and add
    the batch axis.

    `dimension` is a parameter rather than a constant for the reason `Session`
    carries it: a sibling tagger in the same family declares a different input
    size, and a number hard-coded here would resize correctly against the one
    graph it was written for and silently wrongly against every other.

    **The return type is `object` rather than `Any`**, and that is the honest one
    as well as the one that needs no suppression: the array is opaque to every
    caller here -- the only thing anything may do with it is hand it back to
    `Session.run` -- and `numpy.typing.NDArray` cannot be named at all, because
    the `tagging` extra is deliberately absent from the environment the gate runs
    in, so even a `TYPE_CHECKING` import would not resolve. `eval_backends.py`
    faced the same wall and waived ANN401; naming the value opaque says the same
    thing without waiving a rule.

    The non-stdlib imports are function-local, which is what keeps
    `python -m isekai`'s import graph stdlib-only.
    """
    import numpy
    from PIL import Image

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
    ordering is what the suite asserts, and the suite has neither `numpy` nor
    `Pillow` installed. Nothing here imports anything the `tagging` extra carries.

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
    """Prepare `photo`, run it through `session`, and select what it emitted.

    Three lines, and the whole of what they add over `select` is the image: the
    preparation rule and the session are the two things that need a wheel, and
    everything decidable without one is decided in `select`.
    """
    return select(session.run(prepare(photo, session.dimension)), labels, floor=floor)


class OnnxSession:
    """The real session: `onnxruntime` over the digest-verified graph.

    Constructed once per flow, by `wiring`, on first use. `onnxruntime` is
    imported in `__init__` rather than at module scope for the rule this whole
    file exists to keep: the entry point's import graph stays stdlib-only.
    """

    def __init__(self, model: Path) -> None:
        """Open `model` for inference on the CPU."""
        import onnxruntime

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

    def run(self, prepared: object) -> Sequence[float]:
        """Return the one output row this graph produces for one image."""
        outputs = self._session.run(None, {self._input.name: prepared})
        return list(outputs[0][0])


def open_session(models_dir: Path = DEFAULT_MODELS_DIR) -> tuple[Session, list[Label]]:
    """Verify both halves, then open the session and read its label index.

    The one function a caller needs, and the order inside it is the point: the
    digests are checked **before** 467 MB is opened, so a stale pin costs a
    refusal rather than a load followed by one.
    """
    labels_path, model_path = verified_paths(models_dir)
    return OnnxSession(model_path), read_labels(labels_path.read_text())


__all__: Sequence[str] = (
    "CHARACTER_CATEGORY",
    "DEFAULT_MODELS_DIR",
    "FLOOR",
    "GENERAL_CATEGORY",
    "LABELS_DEST",
    "MODEL_DEST",
    "RATING_CATEGORY",
    "REMEDY",
    "Label",
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
