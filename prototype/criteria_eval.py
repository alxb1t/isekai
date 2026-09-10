#!/usr/bin/env python3
"""PROTOTYPE — N13: score a render against its criteria sheet, criterion by criterion.

`CRITERIA.md` §1 moved the ground truth from the photograph to the **sheet**, and
§5 then left six of the seven criteria unmeasured, waiting for a reader. This is
the reader.

**The instrument is a Danbooru tagger, and that choice is the whole design.** The
sheet is written in Danbooru vocabulary; `wd-swinv2-tagger-v3` reads an image and
emits Danbooru vocabulary. Scoring is therefore a **set comparison inside one
vocabulary** rather than a translation between two -- no embedding, no distance to
a photograph, and so none of F4's or F16's disease, whose common cause was an axis
that rewarded not stylizing.

It is also why F28's canonical rewrite had to come first: **a tagger cannot score a
tag it cannot emit.** `blue-green eyes` is not in its label set, so a sheet written
in prose is unscorable in principle rather than merely scored badly.

Per criterion the score is **recall against the sheet**: of the tags the sheet
declares, what fraction did the tagger find in the render, at or above threshold.
Recall rather than F1, because a render carrying *extra* true tags -- the tagger
seeing `smile` where the sheet said nothing -- is not a fidelity failure, and
punishing it would make a sparse sheet score better than a complete one.

**The gate, from `CRITERIA.md` §5, and it runs first.** The reader is pointed at
the ten *photographs* and asked to recover their own sheets. A reader that cannot
read a photograph has no business being asked about a drawing, and round 1's first
finding was an evaluator built before the thing it judged coming back a coin flip.
The floor is stated below, before any number was seen.

    PYTHONPATH=. uv run --extra eval python prototype/criteria_eval.py --known-answer
    PYTHONPATH=. uv run --extra eval python prototype/criteria_eval.py
"""

import argparse
import csv
import json
import re
import statistics
from pathlib import Path

from prototype.fromnoise import PHOTOS, SUGGESTED
from prototype.paths import derived_dir, resolve_render, sheet_path

MODELS = Path("models")
THRESHOLD = 0.35  # the tagger card's own general-tag default
SIDE = 448

# The seven scored criteria, and the sheet field each reads.
SCORED = (
    "pose",
    "gaze",
    "hair silhouette",
    "hair colour",
    "eye colour",
    "clothes",
    "marks",
)
FLOWS = {
    "A · both legs": "prototype/renders/n12_canonical/1_full/{sid}/0.png",
    "D · prompt only": "prototype/renders/n12_canonical/4_prompt_only/{sid}/0.png",
}
# Stated before the numbers were seen, as the gate requires: the reader must
# recover this share of the sheet's tags from the PHOTOGRAPHS, or it is not
# trusted on renders. Photographs are out of its training distribution -- it was
# trained on drawings -- so the floor is deliberately not high.
KNOWN_ANSWER_FLOOR = 0.40

_ROW = re.compile(
    r"^\|\s*\d+ · (?P<name>[^|✓]+?)\s*✓?\s*\|\s*(?P<value>.*?)\s*\|$", re.M
)


def sheet_fields(sid: str) -> dict[str, list[str]]:
    """Return the sheet's fields as tag lists, keyed by field name."""
    text = (sheet_path(sid)).read_text()
    out: dict[str, list[str]] = {}
    for m in _ROW.finditer(text):
        value = m["value"]
        out[m["name"]] = (
            [] if value in ("", "*(none)*") else [t.strip() for t in value.split(",")]
        )
    return out


WD14_MANIFEST = Path("prototype/styles/wd14_models.json")


def verified(dest: str, models_dir: Path) -> Path:
    """Return the artifact's path, having checked its bytes against the manifest.

    `isekai.eval_models.resolve` is not used and must not be: it resolves against
    the **tracked** `eval_models.json`, and it correctly refuses an artifact that
    file does not declare. Weakening that refusal so a prototype could borrow it
    would trade a real guard for a convenience. This does the same verification
    against the prototype's own manifest instead, so the rule that eval artifacts
    are checked rather than trusted still holds on both sides of the branch.
    """
    import hashlib

    manifest = json.loads(WD14_MANIFEST.read_text())
    entry = next(e for e in manifest["entries"] if e["dest"] == dest)
    path = models_dir / dest
    if not path.exists():
        raise SystemExit(f"{path} is missing; sources are in {WD14_MANIFEST}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != entry["sha256"]:
        raise SystemExit(f"{path}: sha256 {digest} != the manifest's {entry['sha256']}")
    return path


class Tagger:
    """`wd-swinv2-tagger-v3`, its bytes verified against the prototype manifest."""

    def __init__(self, models_dir: Path) -> None:
        """Load the pinned tagger and its label list."""
        import onnxruntime

        self.session = onnxruntime.InferenceSession(
            str(verified("wd14/model.onnx", models_dir)),
            providers=["CPUExecutionProvider"],
        )
        with verified("wd14/selected_tags.csv", models_dir).open() as handle:
            rows = list(csv.DictReader(handle))
        # Danbooru stores `long_hair`; the sheets are written with spaces, which is
        # what Illustrious's own samples use. Normalised once, here, so the two
        # sides of every comparison are in one spelling.
        self.labels = [r["name"].replace("_", " ") for r in rows]
        self.general = [i for i, r in enumerate(rows) if r["category"] == "0"]

    def read(self, image_path: str) -> dict[str, float]:
        """Return every general tag above threshold, with its confidence."""
        import numpy as np
        from PIL import Image
        from PIL.Image import Resampling

        with Image.open(image_path) as im:
            im = im.convert("RGB")
            # The tagger takes a square; pad rather than crop, so a full-body
            # render does not lose its feet to the aspect ratio.
            side = max(im.size)
            square = Image.new("RGB", (side, side), (255, 255, 255))
            square.paste(im, ((side - im.width) // 2, (side - im.height) // 2))
            pixels = np.asarray(
                square.resize((SIDE, SIDE), Resampling.BICUBIC), dtype="float32"
            )
        # This export takes NHWC and BGR, which is the one thing about it that is
        # not obvious from the file.
        feed = {
            self.session.get_inputs()[0].name: np.ascontiguousarray(
                pixels[None, :, :, ::-1]
            )
        }
        scores = self.session.run(None, feed)[0][0]
        return {
            self.labels[i]: float(scores[i])
            for i in self.general
            if scores[i] >= THRESHOLD
        }


def recall(declared: list[str], found: dict[str, float]) -> float | None:
    """Return the share of declared tags the reader found, or None if none declared.

    None is a refusal and never a zero: a subject that declares no `marks` has
    nothing to lose, and scoring it 0.0 would drag a flow's mean down for being
    asked an empty question.
    """
    if not declared:
        return None
    return sum(1 for tag in declared if tag in found) / len(declared)


def table(rows: dict[str, dict[str, list[float]]], title: str) -> None:
    """Print one score table: criteria across, sources down."""
    print(f"\n=== {title} ===")
    print(f"{'':18s}" + "".join(f"{c[:13]:>14s}" for c in SCORED) + f"{'mean':>8s}")
    for name, by_criterion in rows.items():
        cells, seen = "", []
        for c in SCORED:
            values = by_criterion[c]
            if not values:
                cells += f"{'—':>14s}"
                continue
            cells += f"{statistics.mean(values):14.2f}"
            seen.extend(values)
        print(f"{name:18s}{cells}{statistics.mean(seen):8.2f}")


def score(tagger: Tagger, sources: dict[str, str]) -> dict[str, dict[str, list[float]]]:
    """Score every source over every subject, criterion by criterion."""
    rows: dict[str, dict[str, list[float]]] = {
        name: {c: [] for c in SCORED} for name in sources
    }
    for sid in SUGGESTED:
        fields = sheet_fields(sid)
        for name, template in sources.items():
            # `resolve_render` because a source may be a render under a UTC date
            # bucket and may be a photograph, which is not under `renders/` at all;
            # it returns anything outside that tree untouched.
            path = resolve_render(template.format(sid=sid))
            if not path.exists():
                continue
            found = tagger.read(str(path))
            for c in SCORED:
                value = recall(fields.get(c, []), found)
                if value is not None:
                    rows[name][c].append(value)
    return rows


def main() -> None:
    """Run the known-answer gate, then score the two kept flows."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--models", type=Path, default=MODELS)
    p.add_argument("--known-answer", action="store_true")
    p.add_argument("--out", type=Path, default=derived_dir() / "criteria_scores.json")
    args = p.parse_args()

    tagger = Tagger(args.models)

    photos = {"the photographs": str(PHOTOS / "synthetic_portrait_{sid}_.png")}
    gate = score(tagger, photos)
    table(gate, "known-answer gate — the reader against the sheets it was written from")
    seen = [v for c in SCORED for v in gate["the photographs"][c]]
    mean = statistics.mean(seen)
    verdict = "PASS" if mean >= KNOWN_ANSWER_FLOOR else "FAIL"
    print(
        f"\nfloor {KNOWN_ANSWER_FLOOR:.2f}, stated before the run · "
        f"reader {mean:.2f} → {verdict}"
    )
    if verdict == "FAIL":
        raise SystemExit(
            "the reader cannot recover the sheets from the photographs, so its "
            "readings of the renders are not trusted and are not printed"
        )
    if args.known_answer:
        return

    rows = score(tagger, FLOWS)
    table(rows, "the two kept flows, on canonical sheets")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(
            {
                "threshold": THRESHOLD,
                "known_answer_floor": KNOWN_ANSWER_FLOOR,
                "known_answer_mean": mean,
                "scores": {
                    n: {c: statistics.mean(v) if v else None for c, v in r.items()}
                    for n, r in rows.items()
                },
            },
            indent=2,
        )
        + "\n"
    )
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
