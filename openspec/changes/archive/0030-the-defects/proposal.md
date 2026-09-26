---
version: v0.22.8
---

# 0030 — the defects

Behaviour fixes, each one demanded by a requirement the living spec already holds: no traceback ends a batch,
every remedy is a command that works, failures are recorded as the kind they were, and an approved input stays
approved.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | each fix, the requirement that demands it, and every choice that settles how |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | a scenario per fix, under the requirement that demands it |

## Why

**The code breaks requirements it already has.** The architecture review and the recent converges found
defects the living spec forbids: a hand-edited file ends a whole batch with a traceback; a refusal names a
command that does nothing, or one the next run refuses; a rejected graph is told to bring a pod up; an approved
input serves an abandoned draft, and `approve` re-approves it.

**Each fix here is demanded by an existing requirement.** A defect no requirement covers stays out, and a
scenario is added only under a requirement whose SHALL already states the behaviour.

## What Changes

- **No traceback ends a batch.** An unreadable file, a missing key, a malformed answer from the endpoint and a
  non-string tag each become a refusal naming its cause, site by site ([D1](design.md#d1)).
- **Every remedy works.** A printed stage command carries its run id; a refusal after a permanent or
  budget-filling record names the record and says to delete it; a budget refusal names `<flow>/<stage>/`
  ([D2](design.md#d2)).
- **Records are right.** The attempt number never collides; a failed upload is recorded; an HTTP client error
  is recorded permanent and a server error transient, each naming its status ([D3](design.md#d3)).
- **One definition of a draft**, so an approved input stays approved and `approve` on it writes nothing; a
  lock stops overlapping draft updates from both committing ([D4](design.md#d4)).
- **Reads check the version**, the run's frame included; `show` marks a file it cannot read rather than
  parsing it ([D5](design.md#d5)).
- **The render's sidecar is written before its image**, so an image always has its provenance
  ([D6](design.md#d6)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

Each requirement keeps its SHALL and gains a scenario ([D8](design.md#d8)).

- `ui` · *An approved input is read-only on the surface until it is re-opened* — a stale lower draft does not
  re-open it.
- `ui` · *A draft update states the version of the draft it replaces* — overlapping updates cannot both commit.
- `run-directory` · *Artifacts are append-only and numbered, and re-running a command is a no-op* — approving
  an approved flow writes nothing.
- `run-directory` · *An unknown schema version is refused, naming the fix* — an unreadable artifact is refused
  by name.
- `image-generation` · *A failure is recorded as the kind it was, and one flow's failure is its own* — a
  rejected graph is permanent, a server error transient, a failed upload recorded.

## Impact

- **Files:** `isekai/foundation/` (`artifacts.py`, `run.py`), `isekai/pipeline/` (`review.py`,
  `generate.py`, `sheet.py`), `isekai/boundary/comfy/`, `isekai/interface/` (`cli.py`, `run_view.py`,
  `ui/app.py`, `ui/batch.py`), `tests/`, `docs/principles.md`, `isekai/boundary/README.md`.
- **Behaviour:** refusal texts; failure records' kinds for HTTP statuses; a record for a failed upload;
  refusals where tracebacks were; `approve` on an approved flow writes nothing; the later of overlapping
  draft updates answers 409; `show` marks an unreadable file. The product is unchanged.
- **Patch conditions:** met ([D9](design.md#d9)).
- **Dependencies:** none.

## Not in this change

- **Defects no requirement covers**: a reader checking a file's kind name, the frame's `id` after a rename,
  the render sidecar's name, `entry_for`'s message, the sheet stage's unused retry budget. They wait for a
  requirement that demands them.
- **A timeout on the transport.** Settled on 2026-09-20: the campaign runs attended.
- **A catch-all for exceptions.** A traceback is a defect, fixed where it happens.
- **The browser-only defects** of the review surface, which wait for a browser test runner.
