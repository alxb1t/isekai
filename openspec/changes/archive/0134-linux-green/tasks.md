# Linux green — tasks

The phases, each green on its own: the sampler's edge, the PNG digests, the pinned interpreter. Decisions are in [design](design.md).

## Progress

- [x] 1 — The edge · moderate
- [x] 2 — The digests · moderate
- [x] 3 — The interpreter · moderate

## 1 — The edge

- [x] 1.1 In `isekai/shared/chain.py`, add `EDGE = 1e-9` after `CHUNK`, its comment saying it is the pixels past an edge that still count as on it. Read it in `_sample`'s `inside`, and say so in the docstring, per [D1](design.md#d1).
  Verify: `grep -n -F "x >= -EDGE" isekai/shared/chain.py` prints the line.
- [x] 1.2 In `tests/test_chain.py`, add `test_chain_lookup_takes_a_point_a_hair_past_the_edge_as_on_it`, marked `spec("tattoo:chain:a-point-a-hair-past-the-edge-is-on-it")`, on the bilinear test's ink: `lookup(ink, [_shift(dx, dy)], (1, 1))` for `(dx, dy)` of `(-e, 1)`, `(1, -e)`, `(3 + e, 1)` and `(1, 3 + e)` has `layer[0, 0, 3]` approx 1.0 for `e = 1e-12`, and `layer[0, 0].tolist()` approx `[1, 1, 1, 0]` for `e = 1e-6`.
  Verify: `uv run pytest tests/test_chain.py -k hair` exits 0.

## 2 — The digests

- [x] 2.1 In `tests/test_artifact_bytes.py`, add `def held(record)`: it checks `source_sha256` against the sha256 of the file `source` names and `composite_sha256` against the record's sibling `.composite.png`, and returns the record's bytes with each digest replaced by `<sha256 of NAME>`, per [D2](design.md#d2) and [D3](design.md#d3). `written` returns `held(path)` for the `edit` kind and the file's bytes for each other kind.
  Verify: `grep -n -F "def held" tests/test_artifact_bytes.py` prints the line.
- [x] 2.2 In `tests/golden/edit.json`, hold `<sha256 of 42.png>` for `source_sha256` and `<sha256 of 42.edit-1.composite.png>` for `composite_sha256`, the names `held` writes.
  Verify: `grep -c -F "<sha256 of" tests/golden/edit.json` prints `2`.
- [x] 2.3 In `tests/test_artifact_bytes.py`, give `_png` and `_placed` an optional `level`, the `compress_level` of the source PNG, and add `test_an_edit_record_holds_whatever_level_its_png_was_deflated_at`, marked `spec_exempt("structural: twin of test_each_kind_is_written_byte_for_byte")`: each in a run directory of its own, the source saved at level 1 and at level 9 gives records that differ as written and equal the golden as held.
  Verify: `uv run pytest tests/test_artifact_bytes.py -k deflated` exits 0.
- [x] 2.4 In `tests/record.py`, make `normalised` replace each string equal to the sha256 of a PNG under `root` by `<sha256 of a PNG>`, per [D2](design.md#d2) and [D3](design.md#d3). Its signature stays; a helper under it recurses with the digests, which `entry`'s call reads once.
  Verify: `grep -n -F "<sha256 of a PNG>" tests/record.py` prints the line.
- [x] 2.5 In `tests/test_record.py`, add `test_a_png_digest_in_a_json_file_is_a_placeholder`, marked `spec_exempt("structural: twin of test_each_record_file_is_what_the_writer_derives")`: the digest of a PNG saved at level 0 and at level 9 normalises to one placeholder, and a digest of no PNG stays.
  Verify: `uv run pytest tests/test_record.py -k placeholder` exits 0.
- [x] 2.6 Run `uv run python -m tests.record` to write the record again. Only `tests/record/run.json` moves, its PNG digests becoming `<sha256 of a PNG>`.
  Verify: `grep -c -F "<sha256 of a PNG>" tests/record/run.json` prints `2`.

## 3 — The interpreter

- [x] 3.1 **HALT CHECK** The record is written again on the Python the pin names, so the build runs on it.
  Verify: `uv run python --version` prints `Python 3.12.14`.
- [x] 3.2 Write `3.12.14` and a newline alone into `.python-version`, per [D4](design.md#d4).
  Verify: `grep -x -F "3.12.14" .python-version` prints `3.12.14`.
- [x] 3.3 In `tests/record.py`, make `_argument`'s `"action"` the action's kind, per [D5](design.md#d5): the table of argparse's classes, `type(action).__name__` for a class whose `__module__` is not `argparse`, and a `ValueError` naming an argparse class the table lacks.
  Verify: `grep -n -F "boolean_optional" tests/record.py` prints the line.
- [x] 3.4 In `tests/test_record.py`, make `_argument` default `action="store"` and the append case `"append"`. Have `test_the_walk_reads_each_flag_of_a_parser` walk a `store_true` flag and a class of its own, add them and `help` as `"help"` to its expected options, and expect `action="count"` to raise `ValueError` naming `_CountAction`.
  Verify: `uv run pytest tests/test_record.py -k walk` exits 0.
- [x] 3.5 In `tests/test_record.py`, add `test_the_interpreter_is_pinned_to_a_patch`, marked `spec_exempt("structural: the interpreter is pinned to a patch")`: `REPO_ROOT / ".python-version"` holds `3.12.N` with N from 7 on.
  Verify: `uv run pytest tests/test_record.py -k pinned` exits 0.
- [x] 3.6 Run `uv run python -m tests.record` to write the record again. Only `tests/record/verbs.json` moves, at its action names.
  Verify: `git diff --name-only -- tests/record` prints `tests/record/verbs.json` alone.
