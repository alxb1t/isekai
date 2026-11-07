# Tasks — 0114 the delete's leftovers

The failure records, then the flow's own description, then the record, per [design](design.md). Paths are from the
repository root.

## Progress

- [ ] 1 — The failure records
- [ ] 2 — The own description
- [ ] 3 — The record

## 1 — The failure records

- [ ] 1.1 **HALT CHECK** — [D1](design.md#d1) replaces the one test that removes a render group only when empty.
  Verify: `grep -n 'if not any(group.iterdir()):' isekai/pipeline/generate.py` prints one line.
- [ ] 1.2 In `isekai/foundation/run.py`, add `failures_alone` after `failure_named`, per [the code](design.md#the-code).
  Verify: `grep -n 'def failures_alone(directory: Path) -> list\[Path\] | None:' isekai/foundation/run.py` prints one line.
- [ ] 1.3 In `isekai/pipeline/generate.py`, make `discard_render` delete a group holding failure records alone, with
  them, its docstring edited, per [the code](design.md#the-code).
  Verify: `grep -n 'records = failures_alone(group)' isekai/pipeline/generate.py` prints one line.
- [ ] 1.4 In `isekai/pipeline/review.py`, add `_holds_render` before `withdraw`, and make `withdraw` read it and delete
  each going approval's group records and group, per [phase 1's `withdraw`](design.md#the-code), not phase 2's.
  Verify: `grep -n 'def _holds_render(run: Run, flow: str, version: int) -> bool:' isekai/pipeline/review.py` prints one line.
- [ ] 1.5 In `tests/test_generate.py`, add `test_a_groups_failure_records_go_with_its_last_render`, per
  [Tests](design.md#tests).
  Verify: `uv run pytest tests/test_generate.py -k groups_failure_records_go_with_its_last_render` exits 0.
- [ ] 1.6 In `tests/test_review.py`, add `test_an_older_approval_whose_group_holds_failure_records_alone_goes`, per
  [Tests](design.md#tests).
  Verify: `uv run pytest tests/test_review.py -k whose_group_holds_failure_records_alone` exits 0.

## 2 — The own description

- [ ] 2.1 **HALT CHECK** — [D2](design.md#d2) extends the one loop that clears a flow with no approval left.
  Verify: `grep -n 'for name in (SHEETS, REVIEW, PROMPTS, SOURCES):' isekai/pipeline/review.py` prints one line.
- [ ] 2.2 In `isekai/pipeline/review.py`, make `withdraw`'s no-approval loop also clear each kind of `DESCRIPTION`
  that `photo/` holds, after `SOURCES`, per [phase 2's `withdraw`](design.md#the-code).
  Verify: `grep -n 'shared = \[kind for kind in DESCRIPTION if versions(run.directory(PHOTO, kind))\]' isekai/pipeline/review.py` prints one line.
- [ ] 2.3 In `tests/test_review.py`, add `test_a_flows_own_description_goes_where_photo_holds_it`, per
  [Tests](design.md#tests).
  Verify: `uv run pytest tests/test_review.py -k own_description_goes_where_photo_holds_it` exits 0.

## 3 — The record

Each edit keeps its grepped phrase on one line, rewrapping around it.

- [ ] 3.1 In `docs/decisions.md`, edit D4 and D50, per [the record](design.md#the-record).
  Verify: `grep -n 'failure records alone is none' docs/decisions.md` prints one line.
- [ ] 3.2 In `docs/principles.md`, edit *Known breaks*, per [the record](design.md#the-record).
  Verify: `grep -n 'render groups of failure' docs/principles.md` prints one line.
- [ ] 3.3 In `docs/data-flow.md`, edit the discard paragraph and the migrate paragraph, per
  [the record](design.md#the-record).
  Verify: `grep -n 'leaves the flow no approval (D50)' docs/data-flow.md` prints one line.
- [ ] 3.4 In `THREAT_MODEL.md`, edit *Out of scope*'s delete line, per [the record](design.md#the-record).
  Verify: `grep -n 'its failure records with it' THREAT_MODEL.md` prints one line.
- [ ] 3.5 In `isekai/foundation/migrate.py`, edit the module docstring, per [the record](design.md#the-record).
  Verify: `grep -n 'leaves the flow no approval (D50)' isekai/foundation/migrate.py` prints one line.
- [ ] 3.6 In `isekai/interface/ui/app.py`, edit the module docstring's D4 sentence, per
  [the record](design.md#the-record).
  Verify: `grep -n 'own copies of the photograph' isekai/interface/ui/app.py` prints one line.
