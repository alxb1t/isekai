#!/usr/bin/env python3
"""PROTOTYPE — the criteria sheet as an editable, checkable artifact.

The sheets have been the ground truth since `notes/CRITERIA.md` §1, but nothing has
owned them: every runner parsed the assembled prompt, and the prompt itself was
rebuilt by whichever throwaway script last touched the table. **Edit a sheet's
table by hand and the prompt does not change**, which makes the sheet look
editable and quietly is not.

This is the missing half. One command turns a sheet's table into its prompt, and
checks every tag on the way:

    sheet.py check <id>...   report unknown and rare tags; change nothing
    sheet.py build <id>...   rewrite the prompt block from the table, after checking
    sheet.py adopt <id>...   write a draft's tags into the sheet's table, then build
    sheet.py find <words>    search the vocabulary; the answer to "is there a tag for X"

So the loop is: **edit the table -> `sheet.py build` -> render.** Add a tag, drop
one, change one, and see what it does.

`adopt` is the front of the same loop. A reader writes a draft to
`prototype/derived/vlm_drafts/<pool>/<id>.json` (see `vlm_reader.py`), `adopt`
turns it into a sheet, and the operator edits from there rather than from a blank page:

    photo -> reader -> draft -> adopt -> **review and edit** -> build -> render

**`adopt` never touches anything but the table.** A sheet's prose, its source
note and its verdict block are the operator's; a draft only proposes field
values, and overwriting a human's notes with a model's output would be the
opposite of a review step.

### The vocabulary check is F28 enforced instead of remembered

F28 found, without a single exception across two rounds, that **canonical Danbooru
tags work and invented ones do not**. It was a reading of results; here it is a
gate. The authority is `models/wd14/selected_tags.csv`, which ships with the
tagger and lists **8,106 general tags with their Danbooru post counts** -- so it
answers both halves of the question `notes/ILLUSTRIOUS.md` §1 raised:

    is this a real tag?              -> is it in the file
    is it common enough to be learnt -> is its post count above a floor

`hand on own knee` at 9,589 posts worked. A tag at 50 posts is in the vocabulary
and almost certainly was never learnt. **Rare is a warning, not an error** --
`nose piercing` has only 2,691 posts and rendered clearly on `real_photo_2`.

### What it deliberately does not check

That the tag is *true of the photograph*, or that it is the *right* canonical tag.
`pale skin` is canonical, common, and was wrong twice (F36) because it means
"bleached". **No vocabulary file catches that.** Only a person or a known-answer
test does.

    PYTHONPATH=. uv run python prototype/sheet.py check real_photo_1 00003
    PYTHONPATH=. uv run python prototype/sheet.py build real_photo_1
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

from prototype.paths import DRAFTS, draft_path, new_sheet_path, sheet_path

VOCABULARY = Path("models/wd14/selected_tags.csv")

# WAI's published quality string, which F34 measured as worth +0.013 when it
# leads the prompt rather than trailing it. Not Danbooru vocabulary, so it is
# exempt from the check below.
QUALITY = ("masterpiece", "best quality", "amazing quality", "newest")
# Danbooru always front-loads a count tag; `notes/CRITERIA.md` records why `1girl`
# is back in the prototype and why that is not a proposal for `main`.
#
# **It is a SHEET FIELD, not a constant, since 2026-09-10.** It was hardcoded for
# as long as every subject was a woman -- which is a property of the round 2 set,
# not of the product. The pose set contains men, and `1girl` on a male subject
# fights the face embedding that flow `A` gets its gender from, putting an
# unmeasured confound in the middle of a pose experiment. Flow `D` has no
# embedding at all, so for `D` the tag is the *only* thing asserting gender.
#
# `COUNT_DEFAULT` is what a sheet gets when its draft does not say; the sheet's
# own value always wins. Same pattern as the negative prompt, which `00059`
# overrides per sheet so the change is visible rather than global.
COUNT_DEFAULT = "1girl, solo"
# Style tags inherited from the shipped graph's committed prompt. `anime
# screencap` is canonical; the other two are not, and are exempt rather than
# fixed because changing them is a deliberate test edit, not a cleanup.
TRAILER = ("anime screencap", "detailed eyes", "soft lighting")
EXEMPT = {*QUALITY, "1girl", "1boy", "solo", *TRAILER}

# The order fields are emitted in: subject, then appearance, then action, then
# frame. One definition, here, rather than a copy in every runner.
ORDER = (
    "count",
    "age band",
    "skin / ancestry",
    "hair colour",
    "hair silhouette",
    "eye colour",
    "eyebrows",
    "marks",
    "clothes",
    "accessories",
    "expression",
    "gaze",
    "pose",
    "framing",
    "body shape",
    "background",
)
RARE_BELOW = 5000  # a floor to warn at, not a rule; `nose piercing` is 2,691

_ROW = re.compile(
    r"^\|\s*\d+ · (?P<name>[^|✓]+?)\s*✓?\s*\|\s*(?P<value>.*?)\s*\|$", re.M
)
_PROMPT = re.compile(
    r"(### The positive prompt, assembled\s*\n\s*```\n)(.+?)(\n```)", re.DOTALL
)
_PROMPT_NO_POSE = re.compile(
    r"(### The positive prompt — pose tags dropped\n.*?```\n)(.+?)(\n```)",
    re.DOTALL,
)


def vocabulary() -> dict[str, int]:
    """Return every general Danbooru tag the tagger knows, with its post count."""
    if not VOCABULARY.exists():
        raise SystemExit(
            f"{VOCABULARY} is missing; it is pinned in "
            "prototype/styles/wd14_models.json with its source"
        )
    with VOCABULARY.open() as handle:
        return {
            row["name"].replace("_", " "): int(row["count"])
            for row in csv.DictReader(handle)
            if row["category"] == "0"
        }


def fields_of(sid: str) -> dict[str, str]:
    """Return a sheet's fields, keyed by name, with absences as empty strings."""
    path = sheet_path(sid)
    if not path.exists():
        raise SystemExit(f"{path} does not exist")
    found = {
        m["name"]: ("" if m["value"] == "*(none)*" else m["value"])
        for m in _ROW.finditer(path.read_text())
    }
    missing = [f for f in ORDER if f not in found]
    if missing:
        raise SystemExit(f"{sid}: sheet is missing fields {missing}")
    return found


# Fields flow `A` can omit because a mechanism in the graph already carries them.
# **`pose` is a hypothesis, not a settled fact** -- N25 is the experiment that
# decides whether OpenPose's skeleton makes the tags redundant, and until it has
# rendered, the ablation prompt is a candidate rather than the default.
POSE_FIELDS = ("pose",)


def assemble(fields: dict[str, str], drop: tuple[str, ...] = ()) -> str:
    """Return the positive prompt: quality string, the fields, the trailer.

    The count tag is no longer spliced in here -- it is `ORDER`'s first field, so
    a sheet declaring `1boy, solo` emits that and nothing overrides it.

    `drop` omits fields from the PROMPT and never from the sheet. The sheet is the
    evaluator's ground truth: delete `pose` from the table and the scoreboard no
    longer knows what the pose was, so *did the skeleton carry it* becomes
    unanswerable at the moment it is asked.
    """
    body = [fields[name] for name in ORDER if fields[name] and name not in drop]
    return ", ".join([*QUALITY, *body, *TRAILER])


def find(words: list[str], known: dict[str, int]) -> None:
    """Print every tag containing all the given words, commonest first.

    The question this answers is "is there a tag for X", and the useful answer is
    usually "no, but here are the neighbours" -- `white corset` does not exist
    while `black corset` and `brown corset` do, which is not something anyone
    would guess. When a colour+garment compound is missing, **compose two tags
    that each exist** rather than inventing the one that does not.
    """
    hits = sorted(
        (
            (count, tag)
            for tag, count in known.items()
            if all(w.lower() in tag for w in words)
        ),
        reverse=True,
    )
    if not hits:
        print(f"no tag contains all of {words}")
        return
    print(f"{len(hits)} tag(s) containing {words}, commonest first:")
    for count, tag in hits[:25]:
        flag = "  (rare)" if count < RARE_BELOW else ""
        print(f"  {tag:40s} {count:>9,}{flag}")
    if len(hits) > 25:
        print(f"  ... and {len(hits) - 25} more")


def check(sid: str, known: dict[str, int]) -> int:
    """Report unknown and rare tags in one sheet. Returns the unknown count."""
    fields = fields_of(sid)
    unknown: list[tuple[str, str]] = []
    rare: list[tuple[str, str, int]] = []
    for name in ORDER:
        for tag in (t.strip() for t in fields[name].split(",") if t.strip()):
            if tag in EXEMPT:
                continue
            count = known.get(tag)
            if count is None:
                unknown.append((name, tag))
            elif count < RARE_BELOW:
                rare.append((name, tag, count))

    print(f"\n=== {sid} ===")
    for field, tag in unknown:
        print(f"  UNKNOWN  {tag:40s} ({field}) — not a Danbooru tag (F28)")
    for field, tag, count in rare:
        print(f"  rare     {tag:40s} ({field}) — {count:,} posts, may be unlearnt")
    if not unknown and not rare:
        print("  every tag is canonical and common")
    return len(unknown)


TEMPLATE = """# `{sid}` — criteria sheet

Drafted by a reader from `{photo}`, {date}. **Not reviewed.** ✓ marks a scored
criterion. Edit the table, then run `sheet.py build {sid}` to regenerate the prompt.

| field | value |
|---|---|
{table}

### The positive prompt, assembled

```
{prompt}
```

### The positive prompt — pose tags dropped

**Flow `A`'s ablation arm (N25).** The same table with field 13 omitted, on the
hypothesis that OpenPose's skeleton already carries the geometry. Flow `D` never
uses this block: it has no skeleton, so for `D` the tags are the only thing
placing the body.

```
{prompt_no_pose}
```

### The negative prompt

```
bad quality, worst quality, sketch, censor, nsfw, lens flare, light particles, dust
```

### Verdict — filled in after the render, by eye

| scored criterion | survived? | note |
|---|:-:|---|
| pose *(mandatory)* | | |
| gaze | | |
| hair silhouette *(mandatory)* | | |
| hair colour | | |
| eye colour | | |
| clothes | | |
| marks | | |

**Bar: 6 of 7, and both mandatory ones.**
"""

SCORED = {
    "pose",
    "gaze",
    "hair silhouette",
    "hair colour",
    "eye colour",
    "clothes",
    "marks",
}


def render_table(fields: dict[str, str]) -> str:
    """Return the sheet's field table, numbered and ticked."""
    rows = []
    for i, name in enumerate(ORDER, 1):
        tick = " ✓" if name in SCORED else ""
        rows.append(f"| {i} · {name}{tick} | {fields[name] or '*(none)*'} |")
    return "\n".join(rows)


# Where a subject's photograph lives. Round 2's portraits are the exception, not
# the rule: they carry a `synthetic_portrait_<id>_.png` filename from the
# generator that made them, while every later set is named for what it depicts.
PHOTO_ROOTS = (
    Path("prototype/inputs/synthetic/pose"),
    Path("prototype/inputs/synthetic/portfolio"),
    Path("prototype/inputs/synthetic"),
    Path("prototype/inputs/real"),
    Path("inputs/synthetic"),
)


# Real photographs arrive as JPEG and generated ones as PNG, so the extension is
# searched rather than assumed -- a reader that only looked for `.png` silently
# reported "no photograph" for an entire real subject set on 2026-09-11.
PHOTO_SUFFIXES = (".png", ".jpeg", ".jpg", ".webp")


def photo_for(sid: str) -> str:
    """Return the photograph a subject id names, searched across the input roots."""
    for root in PHOTO_ROOTS:
        for suffix in PHOTO_SUFFIXES:
            for name in (f"{sid}{suffix}", f"synthetic_portrait_{sid}_{suffix}"):
                if (root / name).exists():
                    return str(root / name)
    return f"inputs/synthetic/synthetic_portrait_{sid}_.png"


REVIEWED = re.compile(r"\*\*Reviewed by the operator", re.I)


def adopt(
    sid: str, drafts: Path, known: dict[str, int], force: bool = False
) -> None:
    """Write a draft's field values into the sheet's table, creating it if absent.

    Only the table is written. Everything else in an existing sheet -- its source
    note, its prose, its verdict block -- belongs to the operator and survives.

    **It REFUSES a sheet marked reviewed, unless forced.** A draft is what a
    reader guessed; a reviewed table is what a human corrected, and the whole
    architecture exists for that correction. Adopting over it silently replaces
    the corrections with the guesses that were already rejected -- which is not
    hypothetical: it happened to `00003` on 2026-09-10 and took `green eyes` back
    to the reader's `blue eyes`, undoing a fix F26 had measured. The sheet was
    tracked, so `git checkout` recovered it; an untracked one would be gone.

    This is the sibling of the `build` trap already recorded: `build` regenerates
    the prompt from the table, `adopt` regenerates the table from the draft. In
    both cases the operator's edit is the thing at risk.
    """
    import datetime

    # `drafts` is honoured when the caller names a directory explicitly; the
    # default resolves through the pool tree, which mirrors the sheet tree.
    src = (drafts / f"{sid}.json") if drafts != DRAFTS else draft_path(sid)
    if not src.exists():
        raise SystemExit(f"{src} does not exist")
    draft = json.loads(src.read_text())
    # `count` defaults rather than being required: every draft written before
    # 2026-09-10 predates the field, and failing them all would make the reader's
    # ten existing drafts unusable to prove a point about a tag they all agree on.
    draft.setdefault("count", COUNT_DEFAULT)
    missing = [f for f in ORDER if f not in draft]
    if missing:
        raise SystemExit(f"{src}: missing fields {missing}")
    fields = {name: draft[name].strip() for name in ORDER}

    photo = photo_for(sid)
    path = sheet_path(sid)
    if not path.exists():
        path = new_sheet_path(sid, photo)
        path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        text = path.read_text()
        if REVIEWED.search(text) and not force:
            raise SystemExit(
                f"{path} is marked reviewed by the operator; adopting would "
                f"replace those corrections with the reader's draft.\n"
                f"  Pass --force if that is genuinely what you want."
            )
        rows = list(_ROW.finditer(text))
        if not rows:
            raise SystemExit(f"{sid}: existing sheet has no field table to replace")
        text = text[: rows[0].start()] + render_table(fields) + text[rows[-1].end() :]
        path.write_text(text)
        print(f"\n=== {sid} ===\n  table replaced from {src}")
    else:
        path.write_text(
            TEMPLATE.format(
                sid=sid,
                photo=photo,
                date=datetime.date.today().isoformat(),
                table=render_table(fields),
                prompt=assemble(fields),
                prompt_no_pose=assemble(fields, drop=POSE_FIELDS),
            )
        )
        print(f"\n=== {sid} ===\n  sheet created from {src}")
    build(sid, known)


def build(sid: str, known: dict[str, int]) -> None:
    """Rewrite a sheet's prompt blocks from its table, after checking it.

    **Both blocks come from one table**, which is the point. Two sheets per
    subject would mean fifteen fields transcribed twice, and a correction applied
    to one of them -- the sheet is the single source of truth precisely so that a
    fix lands everywhere it is used.

    A sheet with no ablation block is left with one, so nothing written before
    2026-09-10 has to be regenerated to stay readable.
    """
    check(sid, known)
    path = sheet_path(sid)
    text = path.read_text()
    fields = fields_of(sid)

    wrote = []
    for pattern, prompt, label in (
        (_PROMPT, assemble(fields), "full"),
        (_PROMPT_NO_POSE, assemble(fields, drop=POSE_FIELDS), "no-pose"),
    ):
        match = pattern.search(text)
        if match is None:
            if pattern is _PROMPT:
                raise SystemExit(f"{sid}: no assembled-prompt block to rewrite")
            continue
        if match.group(2) == prompt:
            continue
        text = text[: match.start(2)] + prompt + text[match.end(2) :]
        wrote.append(f"{label} ({len(prompt.split(','))} tags)")

    if not wrote:
        print("  prompts already match the table")
        return
    path.write_text(text)
    print(f"  rewritten: {', '.join(wrote)}")


def main() -> None:
    """Check or rebuild one or more sheets."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("check", "build", "adopt", "find"))
    parser.add_argument(
        "sheets", nargs="+", help="sheet ids, or search words when action is `find`"
    )
    parser.add_argument(
        "--drafts",
        type=Path,
        default=DRAFTS,
        help="where `adopt` reads a reader's draft JSON from",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="let `adopt` overwrite a table the operator has marked reviewed",
    )
    args = parser.parse_args()

    known = vocabulary()
    if args.action == "find":
        find(args.sheets, known)
        return
    unknown = 0
    for sid in args.sheets:
        if args.action == "check":
            unknown += check(sid, known)
        elif args.action == "build":
            build(sid, known)
        else:
            adopt(sid, args.drafts, known, args.force)
    if args.action == "check" and unknown:
        # A non-zero exit so this can gate a run, but the report is always
        # printed first -- an unknown tag is a warning to a human, not a crash.
        print(f"\n{unknown} unknown tag(s)")
        sys.exit(1)


if __name__ == "__main__":
    main()
