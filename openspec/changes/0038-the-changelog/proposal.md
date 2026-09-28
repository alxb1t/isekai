---
version: v0.26.1
---

# 0038 — the changelog

`CHANGELOG.md` rewritten whole, terse, and held that way: Keep a Changelog sections, one short bullet per change
ending with its design id, and the change id in each heading. No behaviour changes.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the bullet and heading rules, what goes, what stays, and the tests |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | none — no requirement changes ([D9](design.md#d9)) |

## Why

**The changelog is too long to read.** It holds every version since 0.1 at up to several hundred lines each —
figures, caveats, acceptance tables and design reasoning that the archived changes already hold. A person skims
past it, and an agent that loads it spends its context on history.

**Nothing holds it short.** mf-build appends an entry per phase, and nothing checks the length, the sections or
the headings, so the file grew by paragraphs from v0.8 on.

## What Changes

- **Every version rewritten** to Keep a Changelog sections and one bullet per change an operator notices: 1–3 short
  lines, what changed and why, ending with its design id ([D1](design.md#d1)).
- **Every heading from 0.7 names its change**: `## [0.25.0] - 2026-09-27 · 0035-the-flow-skills`
  ([D2](design.md#d2)).
- **Gone:** figures, pod ids, old digests, sections outside Keep a Changelog, the `0.5.0` heading and the link
  references; the current `conjure` and `summon` digests stay ([D3](design.md#d3), [D4](design.md#d4)).
- **The preamble holds the rules only** ([D5](design.md#d5)).
- **`CLAUDE.md` states the rules**, and no code, doc or README cites the changelog ([D6](design.md#d6),
  [D7](design.md#d7)).
- **A format test and a no-citation test hold them** ([D8](design.md#d8)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None — `skip_specs` ([D9](design.md#d9)).

## Impact

- **Files:** `CHANGELOG.md`, `CLAUDE.md`, `evaluation/baseline/README.md`, `evaluation/baseline/build_subjects.py`
  (a comment), and a new `tests/test_changelog.py`.
- **Behaviour:** none.
- **Patch conditions** ([D9](design.md#d9)): no format version moves, no behaviour fix, nothing deprecated, the
  product unchanged.
- **Dependencies:** none.

## Not in this change

- **MinionsFactory's skills** — isekai's rules follow what they write; the release agent adds the heading's change
  id and keeps a patch's `vX.Y.Z`.
- **The re-pin record's home** — it stays in the changelog, which `tests/test_flow.py` reads.
- **The archived changes' citations of old changelog lines** — the archive stays frozen.
- **Any change to behaviour, output or format versions.**
