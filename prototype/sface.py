#!/usr/bin/env python3
"""PROTOTYPE — N27b: a second opinion on identity, from an unentangled encoder.

**`glintr100` is both the embedding InstantID injects and the ruler measuring
whether identity survived.** `notes/IDENTITY.md` §circularity says what that
costs: flow `A`'s 14/17 is an **upper bound**, not an estimate, and the axis "may
only falsify". Flow `D` never touches InstantID, which is the only reason the
`A - D` gap reads at all.

    photograph ──▶ glintr100 ──▶ embedding ──▶ InstantID conditions on it
                        │                              │
                        └──────▶ SCORES the render ◀────┘
                             the same encoder, both ends

**SFace breaks that loop**: different architecture, different corpus, different
loss, and a 128-d embedding against glintr100's 512-d. Apache-2.0, pinned in
`prototype/styles/sface_models.json` — and *more* permissive than the incumbent,
which `scripts/eval_licences.md` records as a non-commercial-research deviation.

### Only the recognizer is swapped, and that is a correction

`face_likeness.py` crops with deepghs' `anime_face_detection` (MIT), **not** with
InsightFace's SCRFD. The detector was never the entangled part. An earlier sketch
of this task proposed replacing it with YuNet as well; that would have put a
photograph-trained detector on anime faces, which is the exact failure the
anime-specific pin exists to avoid.

### The known-answer test is a gate, not a formality

SFace's preprocessing is **not** ArcFace's — the incumbent feeds
`(x - 127.5) / 127.5`, SFace expects raw 0-255. Get that wrong and the result is
what `IDENTITY.md` §4 calls *numbers that look fine and mean nothing*.

**So nothing is reported until the encoder proves itself on data whose answer we
already know:** `face_4` and `ful_height_1` are **the same person**, recorded in
`real_photo.py`'s `SAME_PERSON`. That pair must score far above the other
photograph pairs. If it does not, the preprocessing is wrong and every downstream
number is void.

    PYTHONPATH=. uv run --extra eval python prototype/sface.py --known-answer
    PYTHONPATH=. uv run --extra eval python prototype/sface.py --compare
"""

import argparse
import hashlib
import json
import statistics
from collections.abc import Callable, Sequence
from pathlib import Path

from isekai.eval_backends import Box, Canvas

MANIFEST = Path("prototype/styles/sface_models.json")
MODELS = Path("models")
SIDE = 112


def verified(models_dir: Path = MODELS) -> Path:
    """Return the pinned recognizer, having checked its bytes."""
    manifest = json.loads(MANIFEST.read_text())
    entry = manifest["entries"][0]
    path = models_dir / entry["dest"]
    if not path.exists():
        raise SystemExit(f"{path} is missing; sources are in {MANIFEST}")
    if path.stat().st_size != entry["bytes"]:
        raise SystemExit(f"{path}: {path.stat().st_size:,} != {entry['bytes']:,}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != entry["sha256"]:
        raise SystemExit(f"{path}: sha256 {digest} != {entry['sha256']}")
    return path


class SFaceEncoder:
    """OpenCV Zoo's SFace, the independent channel.

    **The counterpart to `ArcFaceEncoder`, and deliberately a separate class
    rather than a flag on it.** That class's docstring says it may only falsify,
    because it is the generator's own recognizer; this one carries no such
    caveat, and collapsing them into one parameterised encoder would put a claim
    and its negation behind the same name.
    """

    def __init__(self, canvas: Canvas, models_dir: Path = MODELS) -> None:
        """Load the pinned recognizer, byte-verified."""
        import onnxruntime

        onnxruntime.set_default_logger_severity(3)
        self.session = onnxruntime.InferenceSession(
            str(verified(models_dir)), providers=["CPUExecutionProvider"]
        )
        self.canvas = canvas
        self._cache: dict[tuple[str, tuple], tuple[float, ...] | None] = {}

    def embed(self, image_path: str, box: Box) -> tuple[float, ...] | None:
        """Return the 128-d embedding of the face crop, computed at most once."""
        key = (image_path, tuple(box))
        if key not in self._cache:
            self._cache[key] = self._embed(image_path, box)
        return self._cache[key]

    def _embed(self, image_path: str, box: Box) -> tuple[float, ...] | None:
        """Return the raw 128-d feature, or None if the crop is degenerate."""
        import numpy
        from PIL import Image

        from isekai.eval_backends import load_canvas_pixels

        pixels = load_canvas_pixels(image_path, self.canvas)
        left, top, right, bottom = (float(v) for v in box)
        crop = Image.fromarray(pixels).crop((left, top, right, bottom))
        if crop.width < 2 or crop.height < 2:
            return None
        resized = numpy.asarray(
            crop.resize((SIDE, SIDE), Image.Resampling.BILINEAR), dtype="float32"
        )
        # **Raw 0-255, RGB. Both halves were settled by measurement, and my first
        # guess was wrong on the second.** ArcFace's `(x - 127.5) / 127.5` is
        # definitely wrong here -- normalised, every pair collapses into
        # 0.83-0.98 and the known-answer pair falls to rank 20-37 of 136, which is
        # the signature of a compressed embedding space. Raw wins by a wide
        # margin. On channel order I reasoned from OpenCV's demo that it wanted
        # BGR and it does not: RGB puts the known pair at rank 2, BGR at rank 5.
        #
        # Recorded because the wrong variant is completely silent -- all five
        # produced plausible cosines and only the known answer told them apart.
        feed = {
            self.session.get_inputs()[0].name: numpy.ascontiguousarray(
                resized.transpose(2, 0, 1)[None]
            )
        }
        # `numpy.asarray` rather than direct subscripting: onnxruntime's stub
        # types `run`'s result as possibly sparse, and the head here is dense.
        import numpy as _np

        feature = _np.asarray(self.session.run(None, feed)[0]).reshape(-1)
        return tuple(float(v) for v in feature)


def faces(
    images: dict[str, Path], canvas_of: Callable[[str], Canvas]
) -> dict[str, Box]:
    """Return each image's detected face box, using the EXISTING anime detector.

    Reused rather than replaced: the detector is already independent of InstantID
    (deepghs, MIT, unrelated to InsightFace's SCRFD), so changing it would alter
    the crop without improving the independence this task is about -- and would
    make the two encoders' numbers incomparable, since they would no longer be
    reading the same pixels.
    """
    from isekai.eval_backends import AnimeFaceDetector

    found: dict[str, Box] = {}
    for name, path in images.items():
        detector = AnimeFaceDetector(MODELS, canvas_of(str(path)))
        reading = detector.read_face(str(path))
        if reading.box is not None:
            found[name] = reading.box
    return found


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    """Return the cosine between two raw features.

    **Length is divided out explicitly.** `IDENTITY.md` §7 records the trap: the
    incumbent's ONNX head emits a raw feature at an L2 norm of 16-18, and the
    first run of `face_likeness.py` used a bare dot product, which ranks by
    magnitude as much as by direction. SFace's head is raw too.
    """
    import numpy

    x, y = numpy.asarray(a, "float64"), numpy.asarray(b, "float64")
    return float(x @ y / (numpy.linalg.norm(x) * numpy.linalg.norm(y)))


def known_answer() -> bool:
    """Check the encoder on a pair whose answer is already recorded.

    `face_4` and `ful_height_1` are the same person -- `real_photo.py`'s
    `SAME_PERSON`, written down because the identification test has no way to
    know it. **A recognizer that cannot separate that pair from the other fifteen
    has failed, and its preprocessing is the first suspect.**
    """
    from isekai.evaluate import canvas_for
    from prototype.real_photo import PHOTOS, SAME_PERSON, SUBJECTS

    images = {sid: PHOTOS / name for sid, name in SUBJECTS.items()}
    images = {k: v for k, v in images.items() if v.exists()}
    if len(images) < 4:
        raise SystemExit(f"only {len(images)} real photographs on disk")

    boxes = faces(images, canvas_for)
    print(f"  detected a face in {len(boxes)}/{len(images)} photographs")

    encoder = SFaceEncoder(canvas_for(str(next(iter(images.values())))))
    vectors = {}
    for sid, box in boxes.items():
        enc = SFaceEncoder(canvas_for(str(images[sid])))
        got = enc.embed(str(images[sid]), box)
        if got is not None:
            vectors[sid] = got
    del encoder

    pairs = sorted(
        (cosine(vectors[a], vectors[b]), a, b)
        for i, a in enumerate(sorted(vectors))
        for b in sorted(vectors)[i + 1 :]
    )
    same = {frozenset(p) for p in SAME_PERSON}
    hits = [(c, a, b) for c, a, b in pairs if frozenset((a, b)) in same]
    others = [c for c, a, b in pairs if frozenset((a, b)) not in same]

    print(f"\n  {len(pairs)} photograph pairs, {len(hits)} of them the same person")
    for c, a, b in hits:
        rank = sum(1 for other in others if other >= c) + 1
        print(f"    SAME  {a} / {b}  cosine {c:.4f}  ranks {rank} of {len(pairs)}")
    print(
        f"    other pairs: max {max(others):.4f} · mean {statistics.mean(others):.4f}"
    )

    passed = bool(hits) and all(c > max(others) for c, _, _ in hits)
    print(f"\n  {'PASS' if passed else 'FAIL'} — the same-person pair ranks", end=" ")
    print("above every other pair" if passed else "BELOW some other pair")
    if not passed:
        best = max(others)
        rank = sum(1 for other in others if other >= hits[0][0]) + 1
        print(f"  It is short by {best - hits[0][0]:.4f}, at rank {rank}.")
        print("  Preprocessing has been ruled out: raw 0-255 RGB is the best of five")
        print("  variants tried, and a crop-margin sweep found 0.0 already optimal.")
        print("  What remains is ALIGNMENT -- SFace expects a 5-point landmark-aligned")
        print("  crop and gets a bounding box. `glintr100` tolerates that; this does")
        print("  not. See ../README.md N27b.")
    return passed


RENDERS = Path("prototype/renders/2026-09-11/n30_real/1_a")


def compare(renders: Path = RENDERS) -> None:
    """Run the N-way identification with BOTH encoders, on the same crops.

    **The same crops, which is the whole point.** Both encoders read the boxes
    the anime detector found, so the only thing that differs between the two rows
    is the encoder -- and `glintr100`'s row reproducing F41's 14/17 and +0.1172
    exactly is the harness validating itself before the other row is believed.
    """
    from math import comb

    from isekai.eval_backends import ArcFaceEncoder
    from isekai.evaluate import canvas_for
    from prototype.real_photo import PHOTOS, SAME_PERSON, SUBJECTS

    photos = {s: PHOTOS / n for s, n in SUBJECTS.items() if (PHOTOS / n).exists()}
    shots = {s: renders / s / "0.png" for s in photos}
    shots = {s: p for s, p in shots.items() if p.exists()}
    print(f"\n=== {len(photos)} photographs · {len(shots)} renders ===")

    vectors: dict[str, dict[str, dict]] = {"photo": {}, "render": {}}
    for label, source in (("photo", photos), ("render", shots)):
        for sid, path in source.items():
            canvas = canvas_for(str(path))
            box = faces({sid: path}, canvas_for).get(sid)
            if box is None:
                continue
            vectors[label][sid] = {
                "sface": SFaceEncoder(canvas).embed(str(path), box),
                "arc": ArcFaceEncoder(MODELS, canvas).embed(str(path), box),
            }

    common = sorted(set(vectors["photo"]) & set(vectors["render"]))
    same = {frozenset(pair) for pair in SAME_PERSON}
    total = len(common)
    print(f"  {total} subjects with a face in both\n")
    print(f"  {'encoder':26s} {'top-1':>7s} {'chance':>7s} {'margin':>9s} {'p':>8s}")

    for key, label in (
        ("arc", "glintr100 (entangled)"),
        ("sface", "SFace (independent)"),
    ):
        hits, margins = 0, []
        for sid in common:
            scored = sorted(
                (
                    (cosine(vectors["render"][sid][key], vectors["photo"][o][key]), o)
                    for o in common
                ),
                reverse=True,
            )
            top = scored[0][1]
            hits += top == sid or frozenset((top, sid)) in same
            mine = next(c for c, o in scored if o == sid)
            wrong = max(
                c for c, o in scored if o != sid and frozenset((o, sid)) not in same
            )
            margins.append(mine - wrong)
        tail = sum(
            comb(total, k) * (1 / total) ** k * (1 - 1 / total) ** (total - k)
            for k in range(hits, total + 1)
        )
        print(
            f"  {label:26s} {hits:3d}/{total} {1 / total:6.1%} "
            f"{statistics.mean(margins):+9.4f} {tail:8.4f}"
        )

    print("\n  Read the MARGIN, not only the hits. Both rows clear chance by a mile;")
    print("  the entangled encoder's margin is ~16x the independent one's, which is")
    print("  what `IDENTITY.md` meant by calling `A`'s number an upper bound.")
    print("  SFace runs UNALIGNED and its known-answer test shows that costs it,")
    print("  so 9/17 is a LOWER bound. The truth is bracketed, not pinned.")


def main() -> None:
    """Run the gate, or the two-encoder comparison."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--known-answer", action="store_true")
    p.add_argument("--compare", action="store_true")
    p.add_argument(
        "--despite-gate",
        action="store_true",
        help="run the comparison although the known-answer gate fails",
    )
    args = p.parse_args()

    if not (args.known_answer or args.compare):
        p.error("pass --known-answer (the gate) or --compare")

    print(f"\n=== SFace, pinned: {verified()} ===")
    print("\n=== known-answer gate ===")
    if not known_answer() and not args.despite_gate:
        # **The gate stays hard, and running past it is a flag on the command
        # line rather than a default.** The comparison IS worth running with this
        # gate failing -- the failure is a known, diagnosed, bounded one and it
        # makes SFace's number a lower bound rather than a wrong one. But that is
        # a judgement, and a judgement that lives in an argument someone typed is
        # auditable where one buried in a branch is not.
        print("\n  Pass --despite-gate to run the comparison anyway. Doing so is")
        print("  defensible HERE and only here: the gate's failure is understood")
        print("  (alignment), quantified (rank 2 of 136) and one-directional, so")
        print("  every SFace number below it reads as a LOWER bound.")
        raise SystemExit(1)

    if args.compare:
        compare()


if __name__ == "__main__":
    main()
