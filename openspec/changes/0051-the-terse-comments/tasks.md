# Tasks — 0051 the terse comments

One tree per phase, then the rule and the guard, per [design](design.md). Each phase rewrites the comments,
docstrings and `spec_exempt` reasons of its tree per [D1](design.md#d1) and [D2](design.md#d2); code does not move.

## Progress

- [x] 1 — foundation and shared
- [ ] 2 — boundary
- [ ] 3 — pipeline
- [ ] 4 — interface
- [ ] 5 — tools, infra, start.sh and the Dockerfile
- [ ] 6 — tests
- [ ] 7 — The rule, the guard and the README rows

Line numbers are `9f8a479`'s. The pattern every phase's check greps for, **`HISTORY`**, is
`design\.md.?,? *D[0-9]|\b00[0-9]{2}.? +(design|proposal|tasks|D[0-9])|\bv0\.[0-9]`.

## 1 — foundation and shared

- [x] 1.1 **HALT CHECK** — the history is where the design counts it, and `CLAUDE.md` has no comment rule.
  Verify: `grep -rlE 'design\.md.?,? *D[0-9]|\b00[0-9]{2}.? +(design|proposal|tasks|D[0-9])|\bv0\.[0-9]' isekai --include='*.py' | wc -l` prints `24`, and `grep -c 'A comment says what and why' CLAUDE.md` prints `0`.
- [x] 1.2 Rewrite the history in `isekai/foundation/` and `isekai/shared/`.
  Verify: `grep -rlE 'design\.md.?,? *D[0-9]|\b00[0-9]{2}.? +(design|proposal|tasks|D[0-9])|\bv0\.[0-9]' isekai/foundation isekai/shared --include='*.py'` prints nothing.

## 2 — boundary

- [ ] 2.1 Rewrite the history in `isekai/boundary/`, the refusal in `isekai/boundary/wd14.py:211-216` included.
  Verify: `grep -rlE 'design\.md.?,? *D[0-9]|\b00[0-9]{2}.? +(design|proposal|tasks|D[0-9])|\bv0\.[0-9]' isekai/boundary --include='*.py'` prints nothing.

## 3 — pipeline

- [ ] 3.1 Rewrite the history in `isekai/pipeline/`.
  Verify: `grep -rlE 'design\.md.?,? *D[0-9]|\b00[0-9]{2}.? +(design|proposal|tasks|D[0-9])|\bv0\.[0-9]' isekai/pipeline --include='*.py'` prints nothing.

## 4 — interface

- [ ] 4.1 Rewrite the history in `isekai/interface/` and `isekai/__main__.py`.
  Verify: `grep -rlE 'design\.md.?,? *D[0-9]|\b00[0-9]{2}.? +(design|proposal|tasks|D[0-9])|\bv0\.[0-9]' isekai --include='*.py'` prints nothing.

## 5 — tools, infra, start.sh and the Dockerfile

- [ ] 5.1 Rewrite the history in `tools/`, `infra/`, `start.sh` and the `Dockerfile`.
  Verify: `grep -rlE 'design\.md.?,? *D[0-9]|\b00[0-9]{2}.? +(design|proposal|tasks|D[0-9])|\bv0\.[0-9]' tools infra start.sh Dockerfile | sort` prints `tools/derive_field_map.py` and `tools/derive_manifest.py` alone, each for its data, and `bash -n start.sh infra/*.sh tools/*.sh && echo ok` prints `ok`.

## 6 — tests

- [ ] 6.1 Rewrite the history in `tests/`, its `spec_exempt` reasons included.
  Verify: `grep -rlE 'design\.md.?,? *D[0-9]|\b00[0-9]{2}.? +(design|proposal|tasks|D[0-9])|\bv0\.[0-9]' tests | sort` prints `tests/test_evaluate.py`, `tests/test_field_map.py`, `tests/test_infra.py` and `tests/test_spec_prose.py` alone, each for its data.

## 7 — The rule, the guard and the README rows

- [ ] 7.1 Add the rule to `CLAUDE.md`'s *Engineering conventions*, per [D3](design.md#d3).
  Verify: `grep -c 'A comment says what and why' CLAUDE.md` prints `1`.
- [ ] 7.2 In `tests/test_spec_prose.py`, widen `_HISTORY` and add `test_no_comment_names_a_version_change_or_design` with its twin, per [D4](design.md#d4).
  Verify: `grep -c '^def test_no_comment_names_a_version_change_or_design(' tests/test_spec_prose.py` prints `1`, and `grep -c 'design.md' tests/test_spec_prose.py` prints a number above `0`.
- [ ] 7.3 Complete the importer rows of `isekai/foundation/README.md`, `isekai/shared/README.md` and `isekai/boundary/README.md`, per [D5](design.md#d5).
  Verify: `grep '^| .run\.py. ' isekai/foundation/README.md | grep -c 'interface/compare_view.py'` prints `1`, and `grep '^| .comfy/. ' isekai/boundary/README.md | grep -c 'tests/stages.py'` prints `1`.
