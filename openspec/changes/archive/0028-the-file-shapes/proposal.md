---
version: v0.22.6
---

# 0028 — the file shapes

Every run file's shape is declared once, in the run directory's contract, with a typed reader and writer
per kind and a version per kind. No byte on disk changes, and no behaviour does.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the shapes, the reader and writer, and every choice that settles how |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | empty — no requirement changes ([D14](design.md#d14)) |

## Why

**Each writer spells its file, and each reader re-spells it.** `caption`, `tagging`, `sheet`, `review` and
`generate` build their files as dict literals inside `envelope()` calls; `review`, `generate`, `sheet`, the
review UI and `scripts/derive_field_map.py` read them back by string key. Nothing declares what a file
holds, so a writer and its reader can disagree and every check still passes.

**That is how the router lost every multi-word tag.** WD14 stores Danbooru's spelling, `long_hair`; the
router's table is spelled `long hair`. The router and its test double agreed with each other and not with
WD14, and only a real batch showed it.

**One version covers every kind.** `SCHEMA_VERSION` stamps every kind, so a change to one kind's shape would
move the version of all of them. Sheets already shipped earlier shapes under that one number.

## What Changes

- **`isekai/foundation/artifacts.py`, the run directory's contract.** It declares each kind's shape and
  its producer's shape as a `TypedDict`, and each kind's name and version in an `Artifact[T]` descriptor.
  One typed `read` checks the kind's version; one typed `write` takes the whole file
  ([D1](design.md#d1)–[D4](design.md#d4)).
- **Every writer and reader goes through it** — the frame, the error record, the caption, both tag lists,
  the sheet, the review draft and approved sheet, the prompt and the render sidecar ([D5](design.md#d5)).
- **`DanbooruTag`** marks the tags in a WD14 file, and the router accepts only it, so a space-spelled
  stand-in for WD14's output is a type error ([D6](design.md#d6)).
- **`SCHEMA_VERSION`, `envelope` and `read_artifact` are retired** once nothing calls them; `CLAUDE.md`'s
  patch condition names the kinds' versions instead ([D7](design.md#d7)).
- **Guards first:** a golden file per kind proves no byte moves, and a tripwire keeps every other module
  from writing a run file by hand ([D8](design.md#d8), [D9](design.md#d9)).
- **Tests write valid files through the contract**, and the WD14 test helper uses production's spelling
  ([D10](design.md#d10)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The shapes are the ones the files already have, and every refusal keeps its text
([D14](design.md#d14)).

## Impact

- **Files:** `isekai/foundation/` (a new `artifacts.py`; `run.py`), the stages in `isekai/pipeline/`,
  `isekai/boundary/wd14.py`, `isekai/shared/field_map.py`, `isekai/interface/ui/app.py`,
  `isekai/interface/run_view.py`, `scripts/derive_field_map.py`, `tests/`, `docs/`, `CLAUDE.md`,
  `isekai/foundation/README.md`.
- **Behaviour:** none. Every file a run writes is byte-identical, every read accepts what it accepted, and
  every refusal keeps its text.
- **Patch conditions:** met — each kind's version stays `1` ([D14](design.md#d14)).
- **Dependencies:** none.

## Not in this change

- **Checking a file's kind name on read**, and the version check that `Run.frame` and `show` skip. Both are
  behaviour, and both wait for the defects patch.
- **Validating a file's shape at run time.** A `TypedDict` is a declaration for the type checker; a file
  that does not match it reads as it does today.
- **The defects found while surveying the run files** — a sidecar name that matches the artifact pattern,
  the sheet's retry budget, `detail` keys that can overwrite an error record's own, crash windows, corrupt
  JSON escaping as a traceback. They wait for the defects patch; the provenance gaps wait for *pin and record
  the build*.
- **A shape change of any kind.** Sheets keep today's shape, and older runs keep the earlier shapes they
  were written in, under the same version.
- **Types for the prompt's tag spelling.** `DanbooruTag` covers the path from a WD14 file to the router.
