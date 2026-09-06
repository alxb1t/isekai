"""The evaluator: one render against the photograph that produced it.

**This module ranks and diffs. It does not grade, and it never will.** Every
metric here compares a photograph to a drawing, and there is no zero point across
that gap: a cosine of 0.62 is not 62% of anything, it is 0.62, comparable only to
another 0.62 from the same base and the same batch. A fidelity percentage is not
available, and this says so rather than shipping a rescaled number that would be
read as one (design.md D1). There is no average of the axes, no verdict and no
threshold -- a threshold needs labels, and this version is what produces the
first ones.

**It imports nothing third-party.** The models live behind the Protocols below,
which `isekai.eval_backends` implements against torch, transformers and
onnxruntime; the whole of this module is stdlib, so every rule in it is testable
in CI with the `[eval]` extra absent. That is the same seam discipline
`ComfyTransport` is under, for the same reason: a fake is what keeps the suite
offline.

**It is not on `convert.py`'s import graph**, and the one-path rule is untouched
-- that rule is about there being one way to *render*, and an evaluator is not a
second way to render (design.md D12).
"""

from dataclasses import dataclass, field, replace
from typing import Literal, Protocol

from isekai.ciede2000 import Lab, delta_e_2000
from isekai.workflow import image_dimensions, working_resolution

# A region covering less than this fraction of the canvas is refused rather than
# scored. Measured on the photograph in front of it rather than inherited from a
# model card's numbers on somebody else's test set, which is what the per-class
# accuracy filter would have been (design.md D7).
MIN_REGION_AREA = 0.005

# A keypoint below this confidence is dropped from the PCK and counted, rather
# than being scored at whatever coordinate the model guessed.
MIN_KEYPOINT_CONFIDENCE = 0.3

# A keypoint counts as agreeing if it lands within this fraction of the person
# bounding box's diagonal. The diagonal is the normaliser rather than the image,
# so a subject filling the frame and a subject at half scale are not measured on
# different rulers.
PCK_TOLERANCE = 0.05

# What the box-IoU guard method demands before it will call a face located.
MIN_GUARD_IOU = 0.3

# What the landmark-centroid method demands, as a fraction of the face box's
# diagonal. The two are alternatives, and which one is authoritative is decided
# by measurement in phase 8, not here (design.md D9).
MAX_GUARD_CENTROID_OFFSET = 0.25

Box = tuple[float, float, float, float]
Point = tuple[float, float]


class Refusal(Exception):
    """The comparison cannot be made, and saying so is the correct output."""


@dataclass(frozen=True)
class Keypoint:
    """One pose keypoint, with the confidence that decides whether it is used."""

    x: float
    y: float
    confidence: float


@dataclass(frozen=True)
class FaceReading:
    """What a detector found, or did not find, in one image.

    `box` is None when no face was found at all. That is **absence**, and it is
    never a low score: a zero indistinguishable from a genuine zero would rank a
    render with no face in it against renders that have one.
    """

    box: Box | None
    landmarks: tuple[Point, ...] = ()


@dataclass(frozen=True)
class Region:
    """One parsed region: the fraction of the canvas it covers, and its colour.

    Derived from the **photograph only**, at the injector's working resolution,
    and applied to the render unchanged. A human parser is trained on photographs
    and its behaviour on a drawing is unknown, so parsing both sides would make
    every axis a comparison of two parsers as much as of two images.
    """

    name: str
    area: float
    colour: Lab


@dataclass(frozen=True)
class Axis:
    """One reported number, or one refusal, and what it is allowed to claim.

    `kind` is `absolute` for a quantity that means the same thing in a photograph
    and in a drawing -- colour distance, region area, keypoint agreement -- and
    `relative` for an embedding cosine, which is readable only as a ranking
    within one batch on one base.

    `falsifies_only` marks the recognizer the generator itself injects identity
    with. A high value from it is evidence that the adapter did the thing it
    optimises, measured by the loss it optimises against, and asserts nothing
    about identity; a **low** value on a run that should have preserved identity
    is a real finding. That asymmetry is printed beside the number (design.md D8).
    """

    name: str
    kind: Literal["absolute", "relative"]
    direction: Literal["higher-is-closer", "lower-is-closer"]
    value: float | None = None
    refused: str | None = None
    falsifies_only: bool = False


@dataclass(frozen=True)
class Canvas:
    """The single canvas the photograph and the render are compared on.

    The graph scales the photo once and every pixel consumer reads that scaled
    image, so the scaled photo and the render are the same canvas exactly rather
    than approximately. That is the load-bearing assumption of the whole design.
    """

    width: int
    height: int

    @property
    def size(self) -> tuple[int, int]:
        """Return the canvas as a (width, height) pair."""
        return self.width, self.height


class Detector(Protocol):
    """Locates a face and its landmarks in one image."""

    def read_face(self, image_path: str) -> FaceReading:
        """Return what was found in `image_path`, with `box=None` for absence."""
        ...


class Encoder(Protocol):
    """Turns a face region into an embedding, or reports that it cannot."""

    def embed(self, image_path: str, box: Box) -> tuple[float, ...] | None:
        """Return a unit-normalised embedding, or None if the region is unusable."""
        ...


class Parser(Protocol):
    """Parses the photograph's regions, at the canvas the injector derived."""

    def parse(self, image_path: str, canvas: Canvas) -> dict[str, Region]:
        """Return the regions found in the photograph, keyed by name."""
        ...


class Sampler(Protocol):
    """Reads a colour out of a region that was already derived elsewhere.

    Sampling is not parsing, and the distinction is the whole of the regions
    rule: the mask still comes from the photograph, and this reads the render's
    pixels *inside that mask*. Handing the render to a parser would derive a
    second region from a drawing with a parser trained on photographs; handing it
    a mask does not.
    """

    def dominant_colour(self, image_path: str, region: Region) -> Lab | None:
        """Return the dominant CIE L*a*b* colour inside `region`, or None."""
        ...


class PoseReader(Protocol):
    """Reads pose keypoints, or reports that it read none."""

    def keypoints(self, image_path: str) -> tuple[Keypoint, ...] | None:
        """Return the keypoints found, or None if the model could not read at all."""
        ...


def canvas_for(photo_path: str) -> Canvas:
    """Return the canvas a photograph is compared on: the injector's own target.

    Asks `isekai.workflow` rather than restating the rule. A second implementation
    of the resolution rule would be a second thing to keep in step, and the graph
    is the thing that actually scaled the pixels.
    """
    width, height = working_resolution(*image_dimensions(photo_path))
    return Canvas(width, height)


def check_render_matches(canvas: Canvas, render_path: str) -> None:
    """Raise `Refusal` unless a render's dimensions are the canvas's own.

    Both sizes are named, because the reader is deciding whether the render came
    from a different photograph or the resolution rule has moved under them, and
    one size does not answer that.
    """
    actual = image_dimensions(render_path)
    if actual != canvas.size:
        raise Refusal(
            f"{render_path} is {actual[0]}x{actual[1]}, but the canvas derived "
            f"from the photograph is {canvas.width}x{canvas.height}; these two "
            "images do not share a canvas and no axis may be scored across them"
        )


def usable_regions(regions: dict[str, Region]) -> tuple[dict[str, Region], list[Axis]]:
    """Split parsed regions into those big enough to measure and refusals for the rest.

    A region below the floor refuses **naming itself and its measured area**, so
    the reader can tell "the parser found almost no hair" from "the hair did not
    change", which a small number could not.
    """
    usable: dict[str, Region] = {}
    refused: list[Axis] = []
    for name, region in sorted(regions.items()):
        if region.area < MIN_REGION_AREA:
            refused.append(
                Axis(
                    name=f"{name}_colour_delta_e",
                    kind="absolute",
                    direction="lower-is-closer",
                    refused=(
                        f"the {name} region covers {region.area:.4f} of the canvas, "
                        f"under the {MIN_REGION_AREA} floor; too few pixels to "
                        "measure a colour from"
                    ),
                )
            )
        else:
            usable[name] = region
    return usable, refused


def _iou(first: Box, second: Box) -> float:
    """Return the intersection-over-union of two boxes, 0 when they do not overlap."""
    left = max(first[0], second[0])
    top = max(first[1], second[1])
    right = min(first[2], second[2])
    bottom = min(first[3], second[3])
    if right <= left or bottom <= top:
        return 0.0
    overlap = (right - left) * (bottom - top)
    areas = [(b[2] - b[0]) * (b[3] - b[1]) for b in (first, second)]
    union = areas[0] + areas[1] - overlap
    return overlap / union if union > 0.0 else 0.0


def _centroid(box: Box) -> Point:
    """Return a box's centre."""
    return ((box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0)


def _diagonal(box: Box) -> float:
    """Return a box's diagonal length, the normaliser both guard methods use."""
    return ((box[2] - box[0]) ** 2 + (box[3] - box[1]) ** 2) ** 0.5


@dataclass(frozen=True)
class GuardResult:
    """Whether a face is where the photograph's face is, by both methods.

    **Both are computed, and neither is yet authoritative.** Which one ships as
    the guard is decided by measuring them on real renders at the working denoise
    (design.md D9), and that decision is pre-committed: if neither holds, the
    region axes refuse and "the instrument cannot locate the face in our own
    outputs" is what this version reports. Moving `denoise` to make the meter work
    is disqualified -- the product is not tuned to flatter the instrument.
    """

    method: str
    located: bool
    iou: float | None
    centroid_offset: float | None
    detail: str


def run_guard(
    photo_face: FaceReading, render_face: FaceReading, method: str = "iou"
) -> GuardResult:
    """Confirm on the render itself that a face sits where the photograph's does.

    A render that recomposed the subject would otherwise be scored on whatever
    happens to occupy those coordinates, which is a number about the background.
    """
    if photo_face.box is None or render_face.box is None:
        missing = "photograph" if photo_face.box is None else "render"
        return GuardResult(
            method=method,
            located=False,
            iou=None,
            centroid_offset=None,
            detail=f"no face was found in the {missing}",
        )

    iou = _iou(photo_face.box, render_face.box)
    photo_centre = _centroid(photo_face.box)
    render_centre = _centroid(render_face.box)
    offset = (
        (photo_centre[0] - render_centre[0]) ** 2
        + (photo_centre[1] - render_centre[1]) ** 2
    ) ** 0.5 / _diagonal(photo_face.box)

    located = (
        iou >= MIN_GUARD_IOU if method == "iou" else offset <= MAX_GUARD_CENTROID_OFFSET
    )
    return GuardResult(
        method=method,
        located=located,
        iou=iou,
        centroid_offset=offset,
        detail=(
            f"box IoU {iou:.3f} (floor {MIN_GUARD_IOU}), "
            f"landmark-centroid offset {offset:.3f} of the face diagonal "
            f"(ceiling {MAX_GUARD_CENTROID_OFFSET}); authoritative method: {method}"
        ),
    )


def cosine(first: tuple[float, ...], second: tuple[float, ...]) -> float:
    """Return the cosine similarity of two embeddings."""
    if len(first) != len(second):
        raise Refusal(
            f"embeddings of length {len(first)} and {len(second)} are not "
            "comparable; they did not come from the same encoder"
        )
    dot = sum(a * b for a, b in zip(first, second))
    norms = [sum(v * v for v in vec) ** 0.5 for vec in (first, second)]
    if norms[0] == 0.0 or norms[1] == 0.0:
        raise Refusal("a zero embedding has no direction to compare")
    return dot / (norms[0] * norms[1])


def pck(
    photo: tuple[Keypoint, ...],
    render: tuple[Keypoint, ...],
    person_box: Box,
) -> tuple[float | None, int, int]:
    """Return the fraction of keypoints that agree, and how many were used and dropped.

    Normalised by the person bounding box's diagonal, so the tolerance means the
    same thing for a subject filling the frame and one at half scale.
    Low-confidence keypoints are **dropped and counted** rather than scored at a
    coordinate the model guessed -- a guess scored is noise reported as a
    measurement. When every keypoint is dropped the value is None, which is
    absence rather than a zero.
    """
    normaliser = _diagonal(person_box) * PCK_TOLERANCE
    used = 0
    agreed = 0
    dropped = 0
    for a, b in zip(photo, render):
        if a.confidence < MIN_KEYPOINT_CONFIDENCE or b.confidence < (
            MIN_KEYPOINT_CONFIDENCE
        ):
            dropped += 1
            continue
        used += 1
        if ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5 <= normaliser:
            agreed += 1
    return (agreed / used if used else None), used, dropped


def hair_axes(photo: Region, render_colour: Lab | None) -> list[Axis]:
    """Return the hair axes: a colour distance, and the area it was measured over.

    Both are absolute -- a colour distance and an area fraction mean the same
    thing in a photograph and in a drawing, which an embedding cosine does not.

    The area is deliberately **not** a photograph-to-render comparison. The render
    is never parsed, so the render's own hair area is not a quantity this
    evaluator has; what it has is how much of the canvas the colour above was
    averaged over, which is what a reader needs to weigh that colour. Calling it a
    ratio between two parses would be naming a comparison that was never made.
    """
    return [
        Axis(
            name="hair_colour_delta_e",
            kind="absolute",
            direction="lower-is-closer",
            value=(
                None
                if render_colour is None
                else delta_e_2000(photo.colour, render_colour)
            ),
            refused=(
                None
                if render_colour is not None
                else "no dominant colour could be read from the render inside the "
                "photograph's hair mask"
            ),
        ),
        Axis(
            name="hair_mask_area",
            kind="absolute",
            direction="higher-is-closer",
            value=photo.area,
        ),
    ]


def refuse_embedding_axes_across_bases(
    photo_base: str | None, render_base: str | None
) -> str | None:
    """Return why the embedding axes must refuse across bases, or None if they need not.

    A run recording **no** base is treated as unknown rather than as matching. The
    absent value is the case this exists for: an old manifest predates the
    provenance keys entirely, and assuming it matches would silently compare
    across bases, which is the thing being prevented.

    The refusal is per axis rather than global, because a global one would punish
    the operator for a comparison that is partly valid -- and a warning printed
    above a table of numbers is read as decoration.
    """
    if photo_base is None or render_base is None:
        missing = "the render's" if render_base is None else "the photograph's"
        return (
            f"{missing} run records no base checkpoint, so it is unknown rather "
            "than matching; an embedding is readable only within one base"
        )
    if photo_base != render_base:
        return (
            f"the two runs record different bases ({photo_base} and "
            f"{render_base}); an embedding cosine across bases ranks nothing"
        )
    return None


@dataclass
class Report:
    """One render's record: its axes, its absences, and what none of them claims."""

    render: str
    subject: str
    base: str | None
    image: str | None
    axes: list[Axis] = field(default_factory=list)
    face_detected: bool = True
    render_face_detected: bool = True
    notes: list[str] = field(default_factory=list)

    def as_record(self) -> dict[str, object]:
        """Return the machine-readable record written per render.

        Every claim the report is allowed to make is written into the record
        itself rather than left to a reader's memory: what each axis is, which
        direction is closer, that one channel only falsifies, and that no axis
        isolates a single dial.
        """
        return {
            "render": self.render,
            "subject": self.subject,
            "base": self.base,
            "image": self.image,
            "face_detected": self.face_detected,
            "render_face_detected": self.render_face_detected,
            "axes": [
                {
                    "name": axis.name,
                    "kind": axis.kind,
                    "direction": axis.direction,
                    "value": axis.value,
                    "refused": axis.refused,
                    "falsifies_only": axis.falsifies_only,
                }
                for axis in self.axes
            ],
            "notes": self.notes,
            "claims": list(CLAIMS),
        }


# Printed on every report, because each is a thing the numbers do not say and a
# reader six months from now will otherwise assume they do.
CLAIMS = (
    "The photograph reaches the render by several paths at once -- the identity "
    "embedding, the latent init, and three ControlNets -- so no axis here "
    "isolates a single dial, and a change in one is attributable to the pipeline "
    "rather than to any one component.",
    "A relative axis is an embedding cosine, readable only as a ranking within "
    "one batch on one base. It is not a percentage and there is no zero point "
    "across the photograph-to-drawing gap.",
    "An axis marked falsifies-only reports the encoder the generator itself "
    "injects identity with. A high value from it asserts nothing; only a low "
    "value is a finding.",
    "There is no combined score, no verdict and no threshold. Averaging the axes "
    "would hide the identity-versus-style trade-off they exist to expose.",
)


def table(reports: list[Report], run_name: str, base: str | None, image: str) -> str:
    """Render the run's single human-readable table.

    Names the run, the base and the image it was produced on, so a table read
    months later can be attributed to what produced it. States the direction of
    every column, and emits **no** average, verdict or percentage.
    """
    names: list[str] = []
    for report in reports:
        for axis in report.axes:
            if axis.name not in names:
                names.append(axis.name)

    directions = {
        axis.name: axis.direction for report in reports for axis in report.axes
    }
    kinds = {axis.name: axis.kind for report in reports for axis in report.axes}

    lines = [
        f"run: {run_name}",
        f"base: {base if base else 'unrecorded'}",
        f"image: {image}",
        "",
        "columns:",
    ]
    for name in names:
        lines.append(f"  {name}: {kinds[name]}, {directions[name]}")
    lines.append("")

    header = ["render", *names]
    rows = [header]
    for report in reports:
        by_name = {axis.name: axis for axis in report.axes}
        row = [report.render]
        for name in names:
            axis = by_name.get(name)
            if axis is None:
                row.append("-")
            elif axis.refused is not None:
                row.append("refused")
            elif axis.value is None:
                row.append("absent")
            else:
                row.append(f"{axis.value:.4f}")
        rows.append(row)

    widths = [max(len(row[i]) for row in rows) for i in range(len(header))]
    for row in rows:
        lines.append("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)))

    lines.append("")
    lines.extend(f"note: {claim}" for claim in CLAIMS)
    for report in reports:
        for axis in report.axes:
            if axis.refused is not None:
                lines.append(f"refused: {report.render} {axis.name} -- {axis.refused}")
    return "\n".join(lines) + "\n"


def score_render(
    photo_path: str,
    render_path: str,
    *,
    detector: Detector,
    style_encoder: Encoder,
    recognizer: Encoder,
    parser: Parser,
    sampler: Sampler,
    pose: PoseReader,
    subject: str,
    photo_base: str | None,
    render_base: str | None,
    image: str | None = None,
    guard_method: str = "iou",
) -> Report:
    """Score one render against the photograph that produced it.

    Every model arrives through a seam, so the whole of this is exercised offline
    against fakes -- which is what lets the rules here be tested in CI with the
    `[eval]` extra absent.

    The order is the order the refusals have to happen in. The canvas is settled
    first, because every coordinate below is meaningless if the two images do not
    share one. Then absence, which is its own outcome and never a low score. Then
    the guard, which decides whether the region axes may report at all -- while
    the axes that need no region are reported regardless, so a guard failure does
    not deprive the operator of the measurements it does not invalidate.
    """
    canvas = canvas_for(photo_path)
    check_render_matches(canvas, render_path)

    photo_face = detector.read_face(photo_path)
    render_face = detector.read_face(render_path)
    report = Report(
        render=render_path,
        subject=subject,
        base=render_base,
        image=image,
        face_detected=photo_face.box is not None,
        render_face_detected=render_face.box is not None,
    )

    guard = run_guard(photo_face, render_face, method=guard_method)
    report.notes.append(f"guard: {guard.detail}")
    cross_base = refuse_embedding_axes_across_bases(photo_base, render_base)

    # --- the face axes: region-dependent, and refused by a failed guard --------
    for name, encoder, falsifies in (
        ("face_styleid", style_encoder, False),
        ("face_arcface", recognizer, True),
    ):
        report.axes.append(
            _face_axis(
                name,
                encoder,
                falsifies,
                photo_path,
                render_path,
                photo_face,
                render_face,
                guard,
                cross_base,
            )
        )

    # --- the pose axis: measured over the whole image, so it survives ----------
    report.axes.append(_pose_axis(pose, photo_path, render_path, canvas, report))

    # --- the hair axes: region-dependent, so a failed guard refuses them -------
    regions = parser.parse(photo_path, canvas)
    usable, too_small = usable_regions(regions)
    report.axes.extend(too_small)
    for name, region in usable.items():
        if not guard.located:
            report.axes.append(
                Axis(
                    name=f"{name}_colour_delta_e",
                    kind="absolute",
                    direction="lower-is-closer",
                    refused=_guard_refusal(guard),
                )
            )
            continue
        report.axes.extend(
            hair_axes(region, sampler.dominant_colour(render_path, region))
        )

    return report


def _guard_refusal(guard: GuardResult) -> str:
    """Return the refusal text a failed guard puts on every region axis."""
    return (
        f"the guard could not locate a face at the photograph's face region "
        f"({guard.detail}); the pixels under this region are not known to be the "
        "subject, and scoring them would report a number about the background"
    )


def _face_axis(
    name: str,
    encoder: Encoder,
    falsifies_only: bool,
    photo_path: str,
    render_path: str,
    photo_face: FaceReading,
    render_face: FaceReading,
    guard: GuardResult,
    cross_base: str | None,
) -> Axis:
    """Build one face axis, or the refusal that stands in for it.

    Absence is checked before the guard and before the base, because "there is no
    face here" is a different statement from "we would not trust the comparison",
    and collapsing the two would report a methodology refusal for a photograph
    that simply has nobody in it.
    """
    axis = Axis(
        name=name,
        kind="relative",
        direction="higher-is-closer",
        falsifies_only=falsifies_only,
    )
    if photo_face.box is None or render_face.box is None:
        missing = "photograph" if photo_face.box is None else "render"
        # Absence, not a low score, and not a refusal about method: the value
        # stays None and the report's own `face_detected` fields say which.
        return replace(axis, refused=f"no face was found in the {missing}")
    if cross_base is not None:
        return replace(axis, refused=cross_base)
    if not guard.located:
        return replace(axis, refused=_guard_refusal(guard))

    photo_vector = encoder.embed(photo_path, photo_face.box)
    render_vector = encoder.embed(render_path, render_face.box)
    if photo_vector is None or render_vector is None:
        unusable = "photograph" if photo_vector is None else "render"
        return replace(axis, refused=f"the {unusable}'s face region is unusable")
    return replace(axis, value=cosine(photo_vector, render_vector))


def _pose_axis(
    pose: PoseReader, photo_path: str, render_path: str, canvas: Canvas, report: Report
) -> Axis:
    """Build the pose axis, which needs no face region and so survives the guard.

    When the reader cannot read one of the images at all, the axis reports that
    **absence** rather than a zero -- a pose model that failed to run and a render
    whose pose is completely wrong are not the same finding.
    """
    axis = Axis(name="pose_pck", kind="absolute", direction="higher-is-closer")
    photo_points = pose.keypoints(photo_path)
    render_points = pose.keypoints(render_path)
    if photo_points is None or render_points is None:
        unread = "photograph" if photo_points is None else "render"
        return replace(
            axis,
            refused=(
                f"the pose reader read no keypoints at all from the {unread}; "
                "this is the axis reporting its own absence, not a zero"
            ),
        )

    person = _person_box(photo_points, canvas)
    value, used, dropped = pck(photo_points, render_points, person)
    report.notes.append(
        f"pose: {used} keypoints used, {dropped} dropped below confidence "
        f"{MIN_KEYPOINT_CONFIDENCE}"
    )
    if value is None:
        return replace(
            axis,
            refused=(
                f"every one of {dropped} keypoints fell below confidence "
                f"{MIN_KEYPOINT_CONFIDENCE}; none was scored at a guessed "
                "coordinate"
            ),
        )
    return replace(axis, value=value)


def _person_box(points: tuple[Keypoint, ...], canvas: Canvas) -> Box:
    """Return the bounding box of the confident keypoints, or the whole canvas.

    The PCK normaliser. Falling back to the canvas rather than raising keeps the
    tolerance defined when a subject fills the frame, which is the case where the
    two boxes barely differ anyway.
    """
    confident = [p for p in points if p.confidence >= MIN_KEYPOINT_CONFIDENCE]
    if not confident:
        return (0.0, 0.0, float(canvas.width), float(canvas.height))
    xs = [p.x for p in confident]
    ys = [p.y for p in confident]
    return (min(xs), min(ys), max(xs), max(ys))
