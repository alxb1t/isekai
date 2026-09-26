# Tasks — 0028 the file shapes

Guards first, then the contract, then each kind's writers and readers, then the old names retire and the
docs follow. Each phase converts only what it names ([D13](design.md#d13)).

## Progress

- [x] 1 — Guards: golden bytes and the tripwire
- [x] 2 — The contract: `foundation/artifacts.py`
- [x] 3 — Run files: the frame and the error record
- [x] 4 — Readings: the caption and both tag lists
- [x] 5 — Sheets: the sheet, the draft and the approved sheet
- [x] 6 — Renders: the prompt and the render sidecar
- [x] 7 — Readers, and the old names retire
- [ ] 8 — The docs name the contract

Line numbers are `a3d0ca3`'s; find each site by the text it names.

## 1 — Guards: golden bytes and the tripwire

- [x] 1.1 **HALT CHECK** — today's writers of run JSON in `isekai/` are exactly [D9](design.md#d9)'s allowlist.
  Verify: `git grep -l -e 'write_json(' -e 'envelope(' -- isekai | sort | tr '\n' ' '` prints `isekai/foundation/run.py isekai/pipeline/caption.py isekai/pipeline/generate.py isekai/pipeline/review.py isekai/pipeline/sheet.py isekai/pipeline/tagging.py `.
- [x] 1.2 Write `tests/test_artifact_bytes.py`'s golden test and capture `tests/golden/`, one file per kind, from today's production writers, per [D8](design.md#d8).
  Verify: `ls tests/golden | tr '\n' ' '` prints `approved.json caption.json draft.json error.json prompt.json render.json run.json sheet.json tags.json wd14.json `, and `grep -c '^def test_each_kind_is_written_byte_for_byte(' tests/test_artifact_bytes.py` prints `1`.
- [x] 1.3 Add the tripwire, its exact allowlist and its twin to `tests/test_artifact_bytes.py`, per [D9](design.md#d9).
  Verify: `grep -c -e '^def test_only_the_contract_writes_a_run_file(' -e '^def test_the_allowlist_names_only_modules_that_still_write(' -e '^def test_the_check_catches_a_module_writing_json(' tests/test_artifact_bytes.py` prints `3`.

## 2 — The contract: `foundation/artifacts.py`

- [x] 2.1 Write `isekai/foundation/artifacts.py`: [D2](design.md#d2)'s shapes, [D3](design.md#d3)'s descriptors, [D4](design.md#d4)'s `read` and `write`, `DanbooruTag` and `Failure`.
  Verify: `grep -c -e '^class Artifact' -e '^def read(' -e '^def write(' -e '^DanbooruTag = NewType' isekai/foundation/artifacts.py` prints `4`, and `grep -c '_FILE: Artifact\[' isekai/foundation/artifacts.py` prints `10`.
- [x] 2.2 Move `write_json` from `isekai/foundation/run.py` into `isekai/foundation/artifacts.py`, and point every importer [D1](design.md#d1) lists at it.
  Verify: `grep -c '^def write_json' isekai/foundation/artifacts.py isekai/foundation/run.py | paste -sd' ' -` prints `isekai/foundation/artifacts.py:1 isekai/foundation/run.py:0`.
- [x] 2.3 Type `instructions_record` and `constant_record` in `isekai/foundation/run.py` with the record shapes, per [D1](design.md#d1).
  Verify: `grep -c -e '-> InstructionsRecord' -e '-> DigestRecord' isekai/foundation/run.py` prints `2`.
- [x] 2.4 Add `test_a_typed_read_refuses_an_unknown_version` to `tests/test_run_directory.py`, bound to `run-directory:schema:unknown-version-is-refused`: `read(path, CAPTION_FILE)` refuses version `2` with [D4](design.md#d4)'s text.
  Verify: `grep -c '^def test_a_typed_read_refuses_an_unknown_version(' tests/test_run_directory.py` prints `1`.

## 3 — Run files: the frame and the error record

- [x] 3.1 Write the frame in `open_run` with `write(path, RUN_FILE, …)`, and type `Run.frame` as `Frame`, unchecked, per [D4](design.md#d4).
  Verify: `grep -c '"schema": {"name": "run"' isekai/foundation/run.py` prints `0`, and `grep -c 'RUN_FILE' isekai/foundation/run.py` prints a number above `0`.
- [x] 3.2 Make `record_failure` take a `Failure` and write with `write(path, ERROR_FILE, …)`; pass a `stage` and a `detail` at every test call [D11](design.md#d11) lists, and in the golden test.
  Verify: `grep -c 'write_json(' isekai/foundation/run.py` prints `0`, and `git grep -n 'record_failure(.*, {})' -- tests` prints nothing.
- [x] 3.3 Delete `isekai/foundation/run.py` from the tripwire's allowlist.
  Verify: `grep -c '"isekai/foundation/run.py"' tests/test_artifact_bytes.py` prints `0`.

## 4 — Readings: the caption and both tag lists

- [x] 4.1 Write the caption at `isekai/pipeline/caption.py:249-261` with `write(path, CAPTION_FILE, …)`.
  Verify: `grep -c -e 'envelope(' -e 'write_json(' isekai/pipeline/caption.py` prints `0`.
- [x] 4.2 Write the WD14 file (`isekai/pipeline/tagging.py:284-297`) and the hosted list (`:350-363`) with `write`; type `Scored.tag` (`isekai/boundary/wd14.py:123-127`) as `DanbooruTag`, and `tests/test_wd14.py:91`, `:99`, per [D6](design.md#d6).
  Verify: `grep -c -e 'envelope(' -e 'write_json(' isekai/pipeline/tagging.py` prints `0`, and `grep -c 'tag: DanbooruTag' isekai/boundary/wd14.py` prints `1`.
- [x] 4.3 Delete `isekai/pipeline/caption.py` and `isekai/pipeline/tagging.py` from the tripwire's allowlist.
  Verify: `grep -c -e '"isekai/pipeline/caption.py"' -e '"isekai/pipeline/tagging.py"' tests/test_artifact_bytes.py` prints `0`.

## 5 — Sheets: the sheet, the draft and the approved sheet

- [x] 5.1 In `isekai/pipeline/sheet.py`, read the WD14 file with `read(…, WD14_FILE)` and write the sheet with `write(…, SHEET_FILE, …)`; `route` (`isekai/shared/field_map.py`) takes `Iterable[DanbooruTag]`. [D5](design.md#d5), [D6](design.md#d6).
  Verify: `grep -c -e 'envelope(' -e 'write_json(' -e 'read_artifact(' isekai/pipeline/sheet.py` prints `0`, and `grep -A3 '^def route(' isekai/shared/field_map.py | grep -c DanbooruTag` prints a number above `0`.
- [x] 5.2 Convert every writer and reader in `isekai/pipeline/review.py` that [D5](design.md#d5) lists, with [D5a](design.md#d5a)'s typed read per branch.
  Verify: `grep -c -e 'envelope(' -e 'write_json(' -e 'read_artifact(' -e 'carried.get(' isekai/pipeline/review.py` prints `0`.
- [x] 5.3 Delete `isekai/pipeline/sheet.py` and `isekai/pipeline/review.py` from the tripwire's allowlist.
  Verify: `grep -c -e '"isekai/pipeline/sheet.py"' -e '"isekai/pipeline/review.py"' tests/test_artifact_bytes.py` prints `0`.

## 6 — Renders: the prompt and the render sidecar

- [x] 6.1 In `isekai/pipeline/generate.py`, read the approved sheet (`:173`) and the prompt (`:410`) with `read`, and write the prompt (`:191-203`) and the sidecar (`:454-469`) with `write`. [D5](design.md#d5).
  Verify: `grep -c -e 'envelope(' -e 'write_json(' -e 'read_artifact(' isekai/pipeline/generate.py` prints `0`.
- [x] 6.2 Delete `isekai/pipeline/generate.py` from the tripwire's allowlist, leaving it empty.
  Verify: `grep -c '"isekai/pipeline/generate.py"' tests/test_artifact_bytes.py` prints `0`.

## 7 — Readers, and the old names retire

- [x] 7.1 Read with `read(path, KIND)` at `isekai/interface/ui/app.py:250`, `:261`, `:376`, `:411` and `scripts/derive_field_map.py:465`, per [D5](design.md#d5).
  Verify: `git grep -n 'read_artifact' -- isekai/interface scripts` prints nothing.
- [x] 7.2 Delete `SCHEMA_VERSION`, `envelope` and `read_artifact` from `isekai/foundation/run.py`, per [D7](design.md#d7).
  Verify: `grep -c -e SCHEMA_VERSION -e '^def envelope' -e '^def read_artifact' isekai/foundation/run.py` prints `0`.
- [x] 7.3 Convert the tests [D7](design.md#d7) lists: `read(path, KIND)` for a read, `write` for a valid file, `write_json` for a broken one.
  Verify: `git grep -n -e read_artifact -e 'envelope(' -e SCHEMA_VERSION -- tests ':!tests/test_ui.py' ':!tests/stages.py'` prints nothing.
- [x] 7.4 Set `tests/test_ui.py:281`'s forbidden strings to `("artifact_name(", "write_json(", "write(")`, per [D9](design.md#d9).
  Verify: `grep -c 'forbidden = ("artifact_name(", "write_json(", "write(")' tests/test_ui.py` prints `1`.
- [x] 7.5 Write `tests/stages.py`'s WD14 file with `write(…, WD14_FILE, …)`, its default tags in production spelling, and the WD14 literals in `tests/test_sheet_stage.py` likewise, per [D10](design.md#d10).
  Verify: `grep -c '"long_hair", "brown_hair", "smile", "shirt"' tests/stages.py` prints `1`, and `grep -c -E 'tags=\[.*"[a-z]+ [a-z]+"' tests/test_sheet_stage.py` prints `0`.
- [x] 7.6 Reword `CLAUDE.md:123` and `:136`, per [D7](design.md#d7).
  Verify: `grep -c -e SCHEMA_VERSION -e 'gate array' CLAUDE.md` prints `0`.

## 8 — The docs name the contract

- [ ] 8.1 In `docs/principles.md`'s *The run directory is the only channel*, replace the *not yet, for the shapes* sub-bullet with the golden test and the tripwire, per [D12](design.md#d12).
  Verify: `grep -c 'for the shapes' docs/principles.md` prints `0`, and `grep -c 'tests/test_artifact_bytes.py::' docs/principles.md` prints `2`.
- [ ] 8.2 Name `artifacts.py` in `docs/modules.md`, `docs/data-flow.md` and `isekai/foundation/README.md`, per [D12](design.md#d12).
  Verify: `grep -L 'artifacts.py' docs/modules.md docs/data-flow.md isekai/foundation/README.md` prints nothing.
- [ ] 8.3 Correct the docstrings at `isekai/interface/cli.py:9-12` and `isekai/interface/ui/app.py:435-443`, per [D12](design.md#d12).
  Verify: `grep -c -e 'Only schema version 1' -e 'read_artifact' isekai/interface/cli.py isekai/interface/ui/app.py | paste -sd' ' -` prints `isekai/interface/cli.py:0 isekai/interface/ui/app.py:0`.
- [ ] 8.4 Delete the empty allowlist and `test_the_allowlist_names_only_modules_that_still_write` from `tests/test_artifact_bytes.py`.
  Verify: `grep -c -i allowlist tests/test_artifact_bytes.py` prints `0`.
- [ ] 8.5 No live file names a retired name.
  Verify: `git grep -n -e SCHEMA_VERSION -e read_artifact -e 'envelope(' -- ':!CHANGELOG.md' ':!openspec/changes'` prints nothing.
