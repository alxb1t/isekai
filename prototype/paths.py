#!/usr/bin/env python3
"""PROTOTYPE — where a run's artifacts live, and how an old one is found again.

**Two output trees, split by what it costs to make one again.** Both are outputs
and both are gitignored, so the distinction is not *kind* -- it is price:

    prototype/renders/2026-09-08/n9_ablation/<sid>/0.png
      PAID. A pod session per run, and GPU nondeterminism is +-2/255 across pods,
      so a re-render is a different file. **Irreplaceable.**

    prototype/derived/2026-09-09/n24_real_photo_final_contact_sheet.html
      FREE. Thumbnails, contact sheets, scores -- every one of them rebuilt from
      `renders/` in a couple of minutes of CPU. **Disposable.**

They were `ladder/` and `out/` until 2026-09-10, which named the round-1 dial
ladder and "somewhere scripts write" -- neither said which one a stray `rm -rf`
would cost a pod session.

**Both are bucketed by UTC date**, because forty sibling run directories with
nothing in the name to say which session made them is not a record. A date rather
than a full timestamp, because the unit that means anything here is a *session's
day*: two runs an hour apart are read together and a run is never repeated within
one. UTC rather than local, so the bucket does not move when the operator does.

The three functions are deliberately asymmetric:

- **`render_dir` / `derived_dir`** are for *writing* -- they always mean today.
- **`resolve_render`** is for *reading* -- it takes the flat, undated path a
  contact sheet was written against and finds it under whichever date bucket it
  landed in. That is what keeps `contact_sheet.py`'s forty column templates from
  having to name a date they cannot know, and what stops a reorganisation from
  being a thing repeated in every script each time it happens.

The exempt paths under `derived/` -- `vlm_drafts/` and `reference_sheets/` -- are
**not** dated. They are named references read by other scripts, not artifacts of a
day, and dating them would pin those scripts to a date in the past.
"""

from datetime import UTC, datetime
from pathlib import Path

RENDERS = Path("prototype/renders")
DERIVED = Path("prototype/derived")

# Sheets are split by what they depict, not by who wrote them. `real/` is
# gitignored as a DIRECTORY -- see `.gitignore`, which carries the reason.
SHEETS = Path("prototype/sheets")
POOLS = ("synthetic", "real")


def utc_day() -> str:
    """Return today's UTC date, the bucket name every new artifact is written to."""
    return datetime.now(UTC).strftime("%Y-%m-%d")


def render_dir(name: str) -> Path:
    """Return `prototype/renders/<today>/<name>` -- where a new pod run writes."""
    return RENDERS / utc_day() / name


def derived_dir() -> Path:
    """Return `prototype/derived/<today>` -- where a new sheet or score file writes."""
    return DERIVED / utc_day()


def sheet_path(sid: str) -> Path:
    """Return a subject's criteria sheet, from whichever pool holds it.

    The pool is looked up rather than passed in because **a subject id already
    says which pool it is in** -- `00003` is synthetic, `real_photo_1` is not --
    and threading a pool argument through nine call sites would make every caller
    restate something the id already carries.

    A missing sheet returns the `real/` path rather than raising, so the caller's
    own error message is what the operator sees.
    """
    for pool in POOLS:
        candidate = SHEETS / pool / f"{sid}.md"
        if candidate.exists():
            return candidate
    return SHEETS / "real" / f"{sid}.md"


def resolve_render(path: str | Path) -> Path:
    """Return `path`, or the same run found under a date bucket.

    Takes an undated `prototype/renders/<run>/...` and returns it unchanged if it
    exists, otherwise searches `prototype/renders/*/<run>/...`. The *newest*
    matching bucket wins, so a run repeated on a later day supersedes its
    predecessor without any template being edited.

    Anything that is not under `prototype/renders/` is returned untouched, which
    is what lets a caller pass a photograph and a render through the same call.
    """
    path = Path(path)
    if path.exists():
        return path
    parts = path.parts
    if len(parts) <= 2 or parts[:2] != RENDERS.parts:
        return path
    hits = sorted(RENDERS.glob("/".join(("*", *parts[2:]))))
    return hits[-1] if hits else path
