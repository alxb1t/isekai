---
bump: patch
version: 0.87.12
after: [0155-the-review-rules]
---

# The version limit

`next_version` refuses when the next number is one no artifact's name can spell, naming the directory and what to do.

Reading map: [design](design.md) holds the refusal, its message and the test cost, [tasks](tasks.md) holds the one phase.

## Why

An artifact's name holds three digits. After `999.json` the next version is 1000, and the write goes to `1000.json`.
No listing reads that name back, so `latest` stays 999 and every later write takes `1000.json` again and overwrites it.
[Artifacts are append-only and numbered, and re-running a command is a no-op](specs/run-directory/spec.md) says a written artifact is never overwritten.
`is_version` already says 1000 is a number no name can spell, and nothing asks it.

## What Changes

- `next_version` in `isekai/foundation/layout.py` raises a `Refusal` when `is_version` says the next number is not one. The callers in `isekai/pipeline/caption.py`, `tagging.py` and `review.py` take the refusal through that one place.
- A directory below 999 numbers as before.
- Requirement **Artifacts are append-only and numbered, and re-running a command is a no-op**: one scenario added, *a full directory refuses a new version*. Its text is unchanged.
- Tests in `tests/test_run_directory.py` bind the scenario.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `run-directory`: one scenario under *Artifacts are append-only and numbered, and re-running a command is a no-op*.

## Impact

- `isekai/foundation/layout.py`: `next_version` and its docstring.
- `tests/test_run_directory.py`: the tests that bind the scenario.
- The `run-directory` spec: the scenario, folded in at release.
- No format version moves, no flow digest moves, no image-frozen file changes, and no `.py` outside `isekai/foundation/layout.py` changes.

## Not in this change

- Wider numbers, and the artifact's name format.
- Any caller's own handling of the refusal.
- The callers' own lines, `is_version`, `latest` and `versions`.
