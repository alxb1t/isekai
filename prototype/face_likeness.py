#!/usr/bin/env python3
"""PROTOTYPE — N27: can a render be matched back to its own photograph.

**The question two rounds of scoreboards could not ask.** Round 1 measured
similarity-to-photograph, so the least-stylized render won by construction (F4,
F16). Round 2 measures adherence-to-description, so the flow that never reads the
photograph wins by construction -- F29 scores `D` above `A`, 0.77 to 0.73,
*because* it is blind to the thing that separates them. Nothing has ever measured
**is this the same person** in a way that survives stylization.

**The reframe, and it is the whole design.** Do not ask *how similar is this
render to its photograph* -- an absolute score that stylization poisons, whose
optimum is a render that did not stylize. Ask instead:

    given this render, which of the N photographs did it come from?

    render 00003  ─▶ rank all six photographs by cosine
                     1. 00003  ← correct, a top-1 hit
                     2. 00050
                     3. 00014 ...

Three properties follow, and none of them holds for a pairwise score:

- **Stylization is constant across the comparison.** Every candidate is equally
  anime, so a metric that merely punishes stylization cannot win here -- it would
  push every score down and leave the *ranking* untouched.
- **The answer is known**, so the instrument is falsifiable before it is trusted.
  F1 is this project's own record of building an evaluator before the thing it
  judged and getting a coin flip back.
- **It makes `A` vs `D` a measurement rather than an opinion.** If `D`'s renders
  cannot be matched above chance, that is what `D` trades away, in a number.

---

**The circularity, stated before any result, because it decides which cell of the
table can be believed.** `glintr100` is the recognizer InstantID injects identity
*with* -- `isekai/eval_backends.py` says so and says the axis may therefore only
falsify. That asymmetry is not uniform across this table:

- **Flow `D` never touches InstantID.** Nothing in `D` optimised against this
  encoder, so **a `D` score above chance is a clean, non-circular finding** -- the
  strongest thing this test can produce.
- **Flow `A` was optimised against exactly this loss.** A high `A` score is partly
  tautological, so the `A - D` gap is an **upper bound** on what InstantID buys,
  not an estimate of it.

Read `D` first. `A` is read against `D`, and never on its own.

    PYTHONPATH=. uv run --extra eval python prototype/face_likeness.py --stage
    PYTHONPATH=. uv run --extra eval python prototype/face_likeness.py --gate
    PYTHONPATH=. uv run --extra eval python prototype/face_likeness.py
"""

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from isekai.evaluate import cosine
from prototype.paths import resolve_render, utc_day

# The six subjects every arm below rendered. Six is what makes chance 1/6; it is
# not a sample chosen for this test, it is every subject the arms have in common.
SUBJECTS = ("00003", "00014", "00033", "00050", "00059", "00072")
PHOTOS = Path("inputs/synthetic")
PHOTO_NAME = "synthetic_portrait_{sid}_.png"

# Five arms, and the pairs that matter are stated rather than left to the reader:
# `a_*` against `d_*` is the identity question, and `*_no_hires` against its hires
# sibling is N28's question asked on identity rather than on style.
ARMS = {
    "a_no_hires": "prototype/renders/n18_position/3_wai/{sid}/0.png",
    "a_hires_035": "prototype/renders/n19_hires/2_hires_035/{sid}/0.png",
    "a_hires_050": "prototype/renders/n19_hires/3_hires_050/{sid}/0.png",
    "d_no_hires": "prototype/renders/n18_position/5_d_wai/{sid}/0.png",
    "d_hires_035": "prototype/renders/n19_hires/5_d_hires_035/{sid}/0.png",
}
FLOW_OF = {name: ("D" if name.startswith("d_") else "A") for name in ARMS}

# N29's held-out portraits, added 2026-09-10. **Chance is 1/10 here, not 1/6** --
# ten identities rather than six -- so the same hit count means something
# stronger, and the two runs' top-1 numbers are not directly comparable.
N29_SUBJECTS = (
    "02_00",
    "03_01",
    "05_01",
    "06_01",
    "08_00",
    "10_01",
    "14_00",
    "15_01",
    "16_01",
    "19_01",
)
N29_ARMS = {
    "a": "prototype/renders/n29_portfolio/1_a/{sid}/0.png",
    "d": "prototype/renders/n29_portfolio/2_d/{sid}/0.png",
}

# N30's real photographs. **Chance is 1/17 = 5.9%**, the strongest floor this
# project has had -- and the first time the instrument is pointed at faces that
# were photographed rather than generated.
#
# `face_4` and `ful_height_1` are the SAME PERSON. The scorer has no way to know
# that, so a render of one ranking the other first reads as a miss when it is
# arguably a hit. Both are kept -- they are the only same-person-across-
# photographs case here -- and the pair is reported separately in the run's own
# report rather than silently inflating or deflating the headline.
N30_SUBJECTS = (
    "cowboy_shot_1", "cowboy_shot_2", "cowboy_shot_3", "cowboy_shot_4",
    "cowboy_shot_5", "face_1", "face_2", "face_3", "face_4", "face_5",
    "ful_height_1", "full_height_2", "full_height_3", "full_height_4",
    "male_cowboy_shot_1", "male_cowboy_shot_2", "male_full_height",
)
N30_ARMS = {
    "a": "prototype/renders/n30_real/1_a/{sid}/0.png",
    "d": "prototype/renders/n30_real/2_d/{sid}/0.png",
}

RUNS = {
    "t1": (SUBJECTS, PHOTOS, PHOTO_NAME, ARMS, "t1_face_likeness"),
    "n30": (
        N30_SUBJECTS,
        Path("prototype/inputs/real"),
        "{sid}",  # extension varies; resolved by `photo_for`
        N30_ARMS,
        "t3_real_likeness",
    ),
    "n29": (
        N29_SUBJECTS,
        Path("prototype/inputs/synthetic/portfolio"),
        "{sid}.png",
        N29_ARMS,
        "t2_portfolio_likeness",
    ),
}

# **Stated before any number is seen**, as F1 requires. Chance is 1/6 = 16.7%.
# The gate is not "better than chance" -- with six subjects and six renders per
# arm, one lucky hit is 16.7 points. It is that the instrument can find and embed
# a face in EVERY image, because an arm scored on four of six renders is not
# comparable to one scored on six.
DETECTION_FLOOR = 1.0  # every photograph and every render, or the run is void
CHANCE = 1.0 / len(SUBJECTS)


def flow_of(arm: str) -> str:
    """Return the flow an arm belongs to, from its name."""
    return "D" if arm.startswith("d") else "A"


def digest(path: Path) -> str:
    """Return a file's sha256, so a staged copy is provably its source."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_dir(name: str) -> Path:
    """Return `prototype/evaluations/<today>/<name>` -- one run, self-contained."""
    return Path("prototype/evaluations") / utc_day() / name


def stage(
    dest: Path,
    subjects: tuple[str, ...],
    photos: Path,
    photo_name: str,
    arms: dict[str, str],
) -> dict:
    """Copy every input beside the results, and record what each copy came from.

    **Copies, not references.** An evaluation directory that points at
    `prototype/renders/...` stops being readable the moment those trees are
    reorganised -- which happened twice on 2026-09-10 alone. The cost is bulk;
    the benefit is that a finding can be re-read a year later without resolving a
    single path. The manifest carries the source path and sha256 of every copy, so
    "is this still the render F35 measured" stays answerable.
    """
    manifest: dict = {"subjects": list(subjects), "photos": {}, "arms": {}}

    (dest / "photos").mkdir(parents=True, exist_ok=True)
    for sid in subjects:
        src = photos / photo_name.format(sid=sid)
        if not src.exists():  # extension varies on real photographs
            from prototype.sheet import photo_for

            src = Path(photo_for(sid))
        if not src.exists():
            raise SystemExit(f"photograph missing: {src}")
        shutil.copy2(src, dest / "photos" / f"{sid}{src.suffix}")
        manifest["photos"][sid] = {"source": str(src), "sha256": digest(src)}

    for arm, template in arms.items():
        (dest / "renders" / arm).mkdir(parents=True, exist_ok=True)
        manifest["arms"][arm] = {
            "flow": flow_of(arm),
            "template": template,
            "renders": {},
        }
        for sid in subjects:
            src = resolve_render(template.format(sid=sid))
            if not src.exists():
                raise SystemExit(f"render missing: {src}")
            shutil.copy2(src, dest / "renders" / arm / f"{sid}.png")
            manifest["arms"][arm]["renders"][sid] = {
                "source": str(src),
                "sha256": digest(src),
            }
    return manifest


def embeddings(
    dest: Path, models: Path, subjects: tuple[str, ...], arms: dict[str, str]
) -> tuple[dict, dict]:
    """Return every image's face embedding, and a per-image detection record.

    **Each image is read at its own subject's canvas** (F35: both style axes are
    resolution-sensitive and reading at native size flipped linework's sign). An
    embedding must not depend on which photograph it is later compared against, so
    a render is embedded once, at the canvas it was rendered for.
    """
    from isekai.eval_backends import AnimeFaceDetector, ArcFaceEncoder
    from isekai.evaluate import canvas_for

    found: dict[str, dict] = {}
    vectors: dict[str, tuple[float, ...]] = {}

    def read(key: str, image: Path, sid: str) -> None:
        hits = sorted((dest / "photos").glob(f"{sid}.*"))
        canvas = canvas_for(str(hits[0]))
        detector = AnimeFaceDetector(models, canvas)
        encoder = ArcFaceEncoder(models, canvas)
        reading = detector.read_face(str(image))
        if reading.box is None:
            found[key] = {"face": False, "reason": "no box above confidence"}
            return
        vector = encoder.embed(str(image), reading.box)
        if vector is None:
            found[key] = {"face": False, "reason": "box too small to embed"}
            return
        found[key] = {"face": True, "box": [round(v, 1) for v in reading.box]}
        vectors[key] = vector

    for sid in subjects:
        read(f"photo/{sid}", sorted((dest / "photos").glob(f"{sid}.*"))[0], sid)
    for arm in arms:
        for sid in subjects:
            read(f"{arm}/{sid}", dest / "renders" / arm / f"{sid}.png", sid)
    return vectors, found


# **`isekai.evaluate.cosine`, not a local dot product.** `ArcFaceEncoder`'s
# docstring says it returns a "unit-normalised" embedding and it does not --
# glintr100's ONNX head emits the raw feature, measured here at an L2 norm of
# 16-18. A dot product of those ranks by magnitude as much as by direction, and
# the first run of this script did exactly that: it reported "cosine" margins of
# +-21, which is impossible for a cosine and is what caught it. The shipped
# `cosine` normalises both vectors itself, which is why it is the one to call.


def binomial_tail(hits: int, trials: int, chance: float) -> float:
    """Return P(at least `hits` correct | guessing), the exact one-sided p-value.

    **Six subjects is a small n and the headline number hides it.** 2 of 6 is
    "33.3%, twice chance" and is also what guessing produces a quarter of the
    time. Computed exactly rather than approximated -- the numbers are tiny, and a
    normal approximation at n=6 would be its own kind of overclaim.
    """
    from math import comb

    return sum(
        comb(trials, k) * chance**k * (1 - chance) ** (trials - k)
        for k in range(hits, trials + 1)
    )


def identify(
    vectors: dict,
    subjects: tuple[str, ...],
    arms: dict[str, str],
    chance: float,
) -> dict:
    """Rank every render against every photograph, and score the ranking.

    Two numbers per arm, and they answer different questions:

    - **top-1** -- how often the correct photograph ranks first. The headline, and
      the one with a stated chance floor of 1/6.
    - **margin** -- the correct photograph's cosine minus the best wrong one's,
      averaged. Positive means identity is *separable* even where the ranking
      fails; near zero on a passing arm means the win is fragile.
    """
    out: dict = {}
    for arm in arms:
        rows, hits, margins = [], 0, []
        for sid in subjects:
            key = f"{arm}/{sid}"
            if key not in vectors:
                rows.append({"subject": sid, "scored": False})
                continue
            scores = {
                other: cosine(vectors[key], vectors[f"photo/{other}"])
                for other in subjects
                if f"photo/{other}" in vectors
            }
            ranked = sorted(scores, key=lambda s: scores[s], reverse=True)
            correct = scores.get(sid)
            best_wrong = max((v for k, v in scores.items() if k != sid), default=None)
            hit = ranked[0] == sid
            hits += hit
            if correct is not None and best_wrong is not None:
                margins.append(correct - best_wrong)
            rows.append(
                {
                    "subject": sid,
                    "scored": True,
                    "hit": hit,
                    "rank_of_correct": ranked.index(sid) + 1,
                    "cosine_correct": round(correct, 4) if correct else None,
                    "cosine_best_wrong": round(best_wrong, 4) if best_wrong else None,
                    "ranking": ranked,
                }
            )
        scored = [r for r in rows if r.get("scored")]
        margin = sum(margins) / len(margins) if margins else None
        p_value = binomial_tail(hits, len(scored), chance) if scored else None
        out[arm] = {
            "flow": flow_of(arm),
            "scored": len(scored),
            "of": len(subjects),
            "hits": hits,
            "top1": round(hits / len(scored), 4) if scored else None,
            "mean_margin": round(margin, 4) if margin is not None else None,
            "p_value": round(p_value, 4) if p_value is not None else None,
            # Two independent signals, and the verdict needs both. top-1 can be
            # luck at n=6; a NEGATIVE mean margin says the wrong photograph out-
            # scores the right one on average, which no amount of top-1 rescues.
            "verdict": (
                "identity present"
                if p_value is not None and p_value < 0.05 and margin and margin > 0
                else "indistinguishable from guessing"
            ),
            "rows": rows,
        }
    return out


def main() -> None:
    """Stage a run, gate the instrument, then score every arm."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--run",
        choices=sorted(RUNS),
        default="t1",
        help="t1 = the tuned-on six (chance 1/6); n29 = the held-out ten (1/10)",
    )
    p.add_argument("--name", default=None)
    p.add_argument("--models", type=Path, default=Path("models"))
    p.add_argument("--stage", action="store_true", help="copy inputs and stop")
    p.add_argument("--gate", action="store_true", help="detection check only")
    args = p.parse_args()

    subjects, photos, photo_name, arms, default_name = RUNS[args.run]
    chance = 1.0 / len(subjects)

    dest = run_dir(args.name or default_name)
    dest.mkdir(parents=True, exist_ok=True)
    manifest = stage(dest, subjects, photos, photo_name, arms)
    (dest / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    total = len(subjects) * (len(arms) + 1)
    print(f"staged {total} images into {dest}")
    if args.stage:
        return

    vectors, found = embeddings(dest, args.models, subjects, arms)
    (dest / "detection.json").write_text(json.dumps(found, indent=2) + "\n")
    missing = [k for k, v in found.items() if not v["face"]]
    rate = 1 - len(missing) / len(found)
    hits = len(found) - len(missing)
    print(f"\n=== gate: face found in {hits}/{len(found)} images ===")
    for key in missing:
        print(f"  MISS  {key}  ({found[key]['reason']})")
    if rate < DETECTION_FLOOR:
        print(
            f"\nDetection {rate:.0%} is below the {DETECTION_FLOOR:.0%} floor stated "
            "before the run. Arms scored on different numbers of renders are not\n"
            "comparable, so no identification number is reported."
        )
        if args.gate:
            return
        return
    print("  every image yielded a face — the arms are comparable")
    if args.gate:
        return

    results = identify(vectors, subjects, arms, chance)
    results = {"chance": round(chance, 4), "arms": results}
    (dest / "results.json").write_text(json.dumps(results, indent=2) + "\n")

    print(f"\n=== {len(subjects)}-way identification · chance {chance:.1%} ===")
    head = f"{'arm':14s}{'flow':>5s}{'top-1':>10s}{'margin':>10s}{'p':>9s}  verdict"
    print(head)
    for arm, row in results["arms"].items():
        top1 = "—" if row["top1"] is None else f"{row['hits']}/{row['scored']}"
        margin = "—" if row["mean_margin"] is None else f"{row['mean_margin']:+.4f}"
        pval = "—" if row["p_value"] is None else f"{row['p_value']:.4f}"
        print(
            f"{arm:14s}{row['flow']:>5s}{top1:>10s}{margin:>10s}{pval:>9s}"
            f"  {row['verdict']}"
        )
    print(f"\nwrote {dest / 'results.json'}")


if __name__ == "__main__":
    main()
