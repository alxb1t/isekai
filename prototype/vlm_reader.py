#!/usr/bin/env python3
"""PROTOTYPE — N22: compare a model-written criteria sheet against the hand-written one.

`CRITERIA.md` §1 made the sheet the ground truth and left a human writing it.
F36 measured what that costs: three transcription defects on the first real
photographs, each producing a visible render failure, and every one of them a
rule that had already been written down and not applied. **So: does a model read
a photograph into a sheet better, or at least as well?**

F29 already disqualified the obvious candidate. WD14 is trained on drawings and
scored **0.47 on the photographs** against 0.73 on the renders, with `pose` at
0.08 and `marks` at 0.00. A vision model is trained on photographs.

### The reader is a seam, and this file is not the reader

**Drafts are JSON files on disk. Nothing here calls an API.** One JSON object per
subject, keyed by the fifteen field names, values comma-separated tag strings:

    prototype/derived/vlm_drafts/00003.json
    {"age band": "", "skin / ancestry": "tan", "hair colour": "blonde hair", ...}

Anything can fill that directory — an agent session reading the images, a
subscription client, a scripted API call later. The comparison does not care,
which is the point: swapping the reader must not mean rewriting the measurement.
`--schema` prints the exact instructions a reader should be given.

### The gate, stated before any number is seen

`CRITERIA.md` §5's rule for any new reader: **agreement floor 0.60 mean, and no
scored field below 0.40.**

### The contamination this cannot escape on its own

**The references are hand-written sheets, and F36 proved three of them wrong.**
Where a draft disagrees, the *sheet* may be at fault — `pale skin` was in every
reference and was the defect. So a disagreement is **a difference, not an
error**, and the disagreement list is the output that matters. The mean is the
weaker number.

Worse, if the same session that wrote the references also writes the drafts, it
is grading its own memory and the agreement is inflated. **A reader that has
never seen the sheets is the only version of this test that measures anything**,
and `--schema` exists so one can be briefed without them.

### Only synthetic subjects

The ten portraits depict people who do not exist. The `real_photo_*` sheets describe a
real person; they are excluded here, and adding them means handing a real
person's photograph to whatever reader is used.

    PYTHONPATH=. uv run python prototype/vlm_reader.py --schema
    PYTHONPATH=. uv run python prototype/vlm_reader.py
"""

import argparse
import json
import statistics
from pathlib import Path

from prototype.sheet import ORDER, fields_of, vocabulary

PHOTOS = Path("inputs/synthetic")
SUBJECTS = (
    "00003",
    "00004",
    "00014",
    "00022",
    "00033",
    "00035",
    "00050",
    "00059",
    "00060",
    "00072",
)
SCORED = (
    "pose",
    "gaze",
    "hair silhouette",
    "hair colour",
    "eye colour",
    "clothes",
    "marks",
)
FLOOR_MEAN = 0.60
FLOOR_FIELD = 0.40

INSTRUCTIONS = """Transcribe each photograph into a criteria sheet.

Write ONE JSON file per photograph, named <id>.json, into the drafts directory.
Each is a JSON object mapping every field name below to a comma-separated string
of Danbooru tags. Use an empty string for a field the photograph does not show.

Fields, exactly these keys:
{fields}

Rules:
- Every tag MUST be a real Danbooru tag, lowercase, spaces not underscores. A tag
  that does not exist on Danbooru does nothing at all in the generator.
- Describe THIS photograph, not the person in general.
- Prefer the common tag over the precise-sounding one.
- `pale skin` means bleached, not fair. Most light-skinned subjects need NO skin
  tag at all: Danbooru's default is the usual Eurasian tone, and every skin tag
  is a deviation from it.
- Do not include quality tags, `1girl`, `solo`, or style tags. Only the fields.

Photographs: {photos}

**Do not read prototype/sheets/ .** Those are the references this is measured
against; a reader that has seen them is grading its own memory."""


def tags(value: str) -> set[str]:
    """Return a field's tags as a set."""
    return {t.strip() for t in value.split(",") if t.strip()}


def agreement(reference: str, draft: str) -> float | None:
    """Return the share of the reference's tags the draft also has, or None.

    Recall against the hand-written sheet, matching how `criteria_eval.py` scores
    a render. None is a refusal and never a zero: a field the reference leaves
    empty has nothing to agree about.
    """
    want = tags(reference)
    if not want:
        return None
    return len(want & tags(draft)) / len(want)


def main() -> None:
    """Compare every draft on disk against its hand-written sheet."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subjects", nargs="*", default=list(SUBJECTS))
    parser.add_argument(
        "--drafts", type=Path, default=Path("prototype/derived/vlm_drafts")
    )
    parser.add_argument(
        "--schema", action="store_true", help="print the reader's instructions and exit"
    )
    args = parser.parse_args()

    if args.schema:
        photos = ", ".join(
            str(PHOTOS / f"synthetic_portrait_{s}_.png") for s in args.subjects
        )
        print(
            INSTRUCTIONS.format(
                fields="\n".join(f"- {f}" for f in ORDER), photos=photos
            )
        )
        print(f"\nWrite them to: {args.drafts}")
        print(f"Floor: mean >= {FLOOR_MEAN}, no scored field < {FLOOR_FIELD}")
        return

    known = vocabulary()
    scores: dict[str, list[float]] = {f: [] for f in ORDER}
    invented: list[tuple[str, str, str]] = []
    disagreements: list[tuple[str, str, str, str]] = []
    seen = 0

    for sid in args.subjects:
        path = args.drafts / f"{sid}.json"
        if not path.exists():
            print(f"  {sid}: no draft at {path} — skipped")
            continue
        seen += 1
        draft = json.loads(path.read_text())
        reference = fields_of(sid)
        missing = [f for f in ORDER if f not in draft]
        if missing:
            raise SystemExit(f"{path}: missing fields {missing}")
        for field in ORDER:
            for tag in tags(draft[field]):
                if tag not in known:
                    invented.append((sid, field, tag))
            value = agreement(reference[field], draft[field])
            if value is None:
                continue
            scores[field].append(value)
            if value < 1.0 and field in SCORED:
                disagreements.append((sid, field, reference[field], draft[field]))

    if not seen:
        raise SystemExit(
            f"no drafts found in {args.drafts}\n"
            "run with --schema to get the instructions a reader needs"
        )

    print(f"\n=== agreement with the hand-written sheets ({seen} subjects) ===")
    means: dict[str, float] = {}
    for field in ORDER:
        if scores[field]:
            means[field] = statistics.mean(scores[field])
            mark = " *" if field in SCORED else "  "
            print(f"  {field:20s}{mark} {means[field]:.2f}  (n={len(scores[field])})")

    scored = [means[f] for f in SCORED if f in means]
    overall = statistics.mean(scored) if scored else 0.0
    low = [f for f in SCORED if f in means and means[f] < FLOOR_FIELD]
    verdict = "PASS" if overall >= FLOOR_MEAN and not low else "FAIL"
    print(f"\nscored mean {overall:.2f} against a floor of {FLOOR_MEAN} → {verdict}")
    if low:
        print(f"  fields below {FLOOR_FIELD}: {low}")

    print(f"\n=== invented tags ({len(invented)}) — F28's failure mode ===")
    for sid, field, tag in invented[:20]:
        print(f"  {sid} {field:20s} {tag}")
    if not invented:
        print("  none — every tag produced is real Danbooru vocabulary")

    print(f"\n=== {len(disagreements)} disagreements on scored fields ===")
    print("Read these; do not average them. The references are hand-written and")
    print("F36 proved three of them wrong — a disagreement may be the sheet's fault.")
    for sid, field, ref, vlm in disagreements[:15]:
        print(f"\n  {sid} · {field}\n    sheet: {ref}\n    draft: {vlm}")


if __name__ == "__main__":
    main()
