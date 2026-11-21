---
bump: patch
---

# The contract covered

A test holds that every artifact kind in `VERSIONS` has a golden under `tests/golden/`, and a twin fails on a kind with none.

Reading map: [design](design.md) holds the reading of a golden's kind and the twin, [tasks](tasks.md) holds the one phase.

## Why

`tests/test_artifact_bytes.py` pins the bytes of each kind from a golden file. Every name in `VERSIONS` has one today, but nothing fails when a new kind is declared without one. The next kind would then reach the contract with no pinned bytes.

## What Changes

- `tests/test_artifact_bytes.py` gains `kinds_without_golden`, which reads each golden's `schema.name` and returns the names of `VERSIONS` that none holds.
- `test_every_artifact_kind_has_a_golden` asserts that set is empty over `VERSIONS` and `tests/golden/`.
- `test_the_check_catches_a_kind_with_no_golden` is its twin: a directory with a golden for one name and none for another returns the other.

No requirement changes: the change is tests alone, so it carries no spec delta.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None.

## Impact

Only `tests/test_artifact_bytes.py` changes, and the build writes the changelog entry. No product, browser, tool, evaluation or golden file changes, and no decision is added.

## Not in this change

- A golden for the tattoo library's `tattoo.json`, `outline.json` and stage record. They carry no kind today, and a schema block would change their bytes, which a patch may not. They leave for a minor of their own beside the placement work.
- A new golden, or a change to any golden's bytes.
- A change to `BYTE_WRITERS`, which keeps `isekai/pipeline/tattoos.py`.
