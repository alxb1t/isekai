# The guards hold — tasks

Tests, goldens and config comments alone: the binding guard, the exemptions, then the guards that pass blind. Decisions are in [design](design.md).

## Progress

- [x] 1 — The binding guard · moderate
- [x] 2 — The exemptions · moderate
- [x] 3 — No guard passes blind · moderate

## 1 — The binding guard

- [x] 1.1 In `tests/test_spec_bindings.py`, add `scenarios(root)` and `scenario_faults(root)` per [D1](design.md#d1), the guard `test_every_scenario_names_its_key_and_its_layer` over `REPO_ROOT`, and its twin `test_a_scenario_without_its_key_or_layer_is_caught` over a `tmp_path` spec with one block missing each line and one with the layers value `both`.
  Verify: `uv run pytest tests/test_spec_bindings.py -k "names_its_key_and_its_layer or without_its_key_or_layer" -q` exits 0.

- [x] 1.2 **HALT CHECK** In `tests/test_spec_bindings.py`, add `layer_faults(root, tests)` per [D1](design.md#d1), the guard `test_every_key_has_a_test_on_its_layer` and its twin `test_a_key_whose_only_test_is_on_the_other_layer_is_caught`, whose tree binds an `e2e` key from outside `tests/e2e/` and a `unit` key from inside it. A guard red on the repository means the plan is wrong: stop.
  Verify: `uv run pytest tests/test_spec_bindings.py -k "has_a_test_on_its_layer or on_the_other_layer" -q` exits 0.

- [x] 1.3 **HALT CHECK** In `tests/test_run_directory.py`, add `test_containment_is_decided_by_identity_through_a_symlink`, bound to `run-directory:containment:containment-is-decided-by-identity`: per [D2](design.md#d2), link `tmp_path / "link"` to `REPO`, assert `_is_within(link / "x", REPO)` and `not _is_within(tmp_path / "x", REPO)`, importing `_is_within` from `isekai.interface.wiring`. A failure means the identity walk does not read as the plan says, and the product would have to move: edit nothing else, and stop.
  Verify: `uv run pytest tests/test_run_directory.py -k through_a_symlink -q` exits 0.

- [x] 1.4 In `tests/test_spec_bindings.py`, add `skipped(root)` and `rests_on_skips(keys, tests, skipped)` per [D2](design.md#d2), the guard `test_no_key_rests_only_on_skipped_tests` over the demanded keys and its twin `test_a_key_whose_every_test_is_skipped_is_caught`, whose tree binds one key by a `skipif` test alone and another by that test and a plain one.
  Verify: `uv run pytest tests/test_spec_bindings.py -k "rests_only_on_skipped or every_test_is_skipped" -q` exits 0.

- [x] 1.5 In `tests/test_spec_bindings.py`, make `unmarked` fail a `spec_exempt` whose reason is blank after `strip()` ([D3](design.md#d3)), and add `test_a_blank_exemption_reason_is_caught`, whose `tmp_path` source holds `@pytest.mark.spec_exempt("  ")` on a `def test_blank():` and expects `["tests/test_cap.py::test_blank"]` from `unmarked`.
  Verify: `uv run pytest tests/test_spec_bindings.py -k blank_exemption_reason -q` exits 0.

- [x] 1.6 In `tests/test_field_map.py`, rewrite `test_every_approved_tag_is_reachable_in_the_field_it_was_approved_in` over `FILED` per [the binding guard](design.md#the-binding-guard): build `filed` as `{tag: set(counts) for tag, counts in FILED.items()}`, drop the `APPROVED` glob, the `skip` and the imports they leave unused, and make its reason `structural: the committed table against the transcribed filings`. Keep `assert len(filed) == 113` and the reachability assertion.
  Verify: `git grep -c -F 'APPROVED' -- tests/test_field_map.py` prints nothing and exits 1.

- [x] 1.7 Run phase 1's test files together: edit nothing.
  Verify: `uv run pytest tests/test_spec_bindings.py tests/test_run_directory.py tests/test_field_map.py -q` exits 0.

## 2 — The exemptions

- [x] 2.1 **HALT CHECK** The scenario keys [D6](design.md#d6) rebinds exist in the living spec: a missing key means the plan is wrong, and the rebinds need a scenario a patch may not add. Edit nothing.
  Verify: `git grep -c -E -e 'Key:\*\* .(edit:refusals:a-composite-with-no-ink-is-refused|cli:refusals:refusal-names-the-remedy|cli:pipeline-surface:verbs-are-subcommands).' -- openspec/specs/edit/spec.md openspec/specs/cli/spec.md` prints `openspec/specs/cli/spec.md:2` and `openspec/specs/edit/spec.md:1`.

- [x] 2.2 Prefix `structural: ` to each unprefixed reason of the first table of [D5](design.md#d5): each `spec_exempt("the ` of `tests/test_ollama.py`, and the reason `"the one-path rule` on its own line in `tests/test_manifest.py`. Then run `uv run ruff format` over those files, which rewraps a decorator the prefix pushes past the width.
  Verify: `git grep -n -F -e 'spec_exempt("the ' -e '"the one-path rule' -- tests/test_ollama.py tests/test_manifest.py` prints nothing and exits 1.

- [x] 2.3 Reword the reasons of [D5](design.md#d5) that name a test, in `tests/test_ui_api.py`, `tests/test_resume.py`, `tests/test_infra.py` and `tests/test_ui.py`, each to `structural: twin of <the test the table names>`. Then run `uv run ruff format` over the files edited.
  Verify: `git grep -n -F 'twin of test_bake_names_no_module_of_the_surface_spells_an_edits_file_stem' -- tests/test_ui.py` prints the edited line.

- [x] 2.4 Reword each other reason of [D5](design.md#d5)'s tables to the rule form the table gives: `twin:` dropped, `twin of` dropped where it names no test, `the twin of` and `twin --` dropped, and `structural: ` before each. Then run `uv run ruff format` over the files edited.
  Verify: `git grep -n -E '"twin: |structural: (the twin|twin --)|structural: twin of (t[^e]|[^t"])' -- tests` prints nothing and exits 1.

- [x] 2.5 Bind the behaviour tests of [D6](design.md#d6) to their keys: replace `@pytest.mark.spec_exempt(...)` with `@pytest.mark.spec("<key>")` on the tests of `tests/test_edit.py`, `tests/test_render.py` and `tests/test_pipeline_cli.py` that the first table lists.
  Verify: `git grep -n -E 'structural: (a mask with nothing above the floor has no box|a refused request prints the refusal and writes nothing|the parser dispatches nothing yet)' -- tests/test_edit.py tests/test_pipeline_cli.py` prints nothing and exits 1.

- [x] 2.6 In `tests/test_spec_bindings.py`, add `reason_faults(tests)` per [D4](design.md#d4), the guard `test_every_exemption_reason_is_a_rule_or_a_twin_of_a_test` over the repository's tests, and its twin `test_a_reason_off_both_forms_or_naming_no_test_is_caught`, whose reasons are `x`, `twin of test_here`, `structural: twin of test_nowhere` and `structural: `. The twin's text holds none of the needles of tasks 2.2 to 2.5.
  Verify: `uv run pytest tests/test_spec_bindings.py -k "every_exemption_reason or off_both_forms" -q` exits 0.

- [x] 2.7 In `tests/test_spec_bindings.py`, add `BEHAVIOUR_EXEMPT` with the rows of [D6](design.md#d6)'s second table, `BEHAVIOUR_CEILING` as its length, `behaviour_faults(tests, table, ceiling)`, the guard `test_the_behaviour_exemptions_only_shrink` and its twin `test_a_stale_row_or_a_table_past_its_ceiling_is_caught`.
  Verify: `uv run pytest tests/test_spec_bindings.py -k "only_shrink or stale_row" -q` exits 0.

- [x] 2.8 Run phase 2's test files together: edit nothing.
  Verify: `uv run pytest tests/test_spec_bindings.py tests/test_spec_prose.py tests/test_edit.py tests/test_render.py tests/test_pipeline_cli.py tests/test_ollama.py -q` exits 0.

## 3 — No guard passes blind

- [x] 3.1 In `tests/test_spec_prose.py`, read change ids and versions as [D7](design.md#d7) says: `\b0\d{3}` in the change-id branch of `_HISTORY`, `\d{1,3}` in both parts of its version branch. Add `"see 0125-the-outline-gestures"` and `"since v0.100"` to `_CITED`: neither matches the old pattern.
  Verify: `git grep -n -F '0\d{3}' -- tests/test_spec_prose.py` prints the edited line.

- [x] 3.2 In `tests/test_spec_prose.py`, add `"pyproject.toml"` and `".github"` to `_COMMENT_TREES`, read a `.toml` and a `.yml` file by `_shell_prose` in `comment_history`, add `config.toml` and `workflow.yml` to the files of `test_history_in_a_comment_or_a_docstring_is_caught`, and add a `# pinned; v1.1.5 and v17.0` line to `test_a_third_partys_version_and_code_are_not_history`'s `Dockerfile`.
  Verify: `git grep -n -F '"pyproject.toml"' -- tests/test_spec_prose.py` prints the edited line.

- [x] 3.3 Reword the comments that cite history, so the guard of 3.2 goes green. In `pyproject.toml`: `empty until v0.22.3, held` to `empty once, held`; delete the line `# (design.md D3).` and end the line above with a full stop; `appears (design.md D4).` to `appears.`; `nothing. v0.22.3 made both required instead,` to `nothing. Both are required now,`; `same way (0033 design D1).` to `same way.`; `(deleted at v0.14)` to `(since deleted)`; `touched since v0.10.` to `touched for many releases.` In `.github/workflows/drift.yml`: `a deriver (0049 design D7).` to `a deriver.`
  Verify: `uv run pytest tests/test_spec_prose.py -q` exits 0.

- [x] 3.4 In `tests/test_principles.py`, add `PRINCIPLES`, the number of `### ` headings of `docs/principles.md` when written, the guard `test_every_principle_heading_is_one_the_parser_reads` per [D8](design.md#d8), and its twin `test_the_check_catches_a_principle_under_a_deeper_heading`, whose text moves one principle to `####` and another to `##`.
  Verify: `uv run pytest tests/test_principles.py -k "principle_heading or deeper_heading" -q` exits 0.

- [x] 3.5 In `tests/test_package_paths.py`, per [D9](design.md#d9): assert `anchor == REPO_ROOT.joinpath(*suffix)` in `_assert_anchors_the_repository_root`; add `ink.INK_CONFIG_PATH` with `("config", "ink.json")` and `pod_start.PROVISION` with `("isekai", "boundary", "provision.py")` to `ANCHORS`; add the guard `test_every_file_anchored_constant_is_listed`, its twin `test_the_check_catches_a_constant_missing_from_the_list` and `test_the_assertion_fails_when_a_segment_is_misnamed`, which asks the assertion of `REPO_ROOT / "data"` with `(".data",)`.
  Verify: `uv run pytest tests/test_package_paths.py -k "file_anchored or missing_from_the_list or misnamed or each_anchor" -q` exits 0.

- [x] 3.6 In `tests/test_artifact_bytes.py`, add `test_the_scan_reads_the_contract`, which asserts `CONTRACT in {name for name, _ in _modules(REPO_ROOT)}`, so an empty glob is red.
  Verify: `uv run pytest tests/test_artifact_bytes.py -k scan_reads_the_contract -q` exits 0.

- [x] 3.7 In `tests/test_artifact_bytes.py`, widen the tripwires per [D10](design.md#d10): `BYTE_WRITERS`, a mapping from each module the widened `json_writers` flags, matched by the called name `write_atomically`, to a phrase of what it writes; `TYPED_WRITERS` for `write`, `create` and `replace`, in place of `TYPED_WRITER`; and in `unannotated_writes`, an `ast.AnnAssign` whose target is `self.<name>` annotates `self.<name>` for every method of its class, so an artifact that is `self.<name>` counts as annotated. Add `test_the_check_catches_a_byte_writer_outside_its_table` and `test_the_check_learns_a_classs_annotated_attribute`, the second over a class with an annotated attribute, an unannotated one and a bare `replace(...)`.
  Verify: `uv run pytest tests/test_artifact_bytes.py -k "byte_writer_outside or classs_annotated or only_the_contract or annotated_artifact" -q` exits 0.

- [x] 3.8 In `tests/test_artifact_bytes.py`, add the kinds `edit`, `placement` and `session` to `KINDS` per [D13](design.md#d13), the producers `_edit`, `_placement` and `_session`, restating `tests/test_edit_placement.py`'s `_render`, `_png` and `_values` here, and write `tests/golden/edit.json`, `tests/golden/placement.json` and `tests/golden/session.json` from the production bytes. Read each golden before keeping it.
  Verify: `uv run pytest tests/test_artifact_bytes.py -k "each_kind and (edit or placement or session)" -q` exits 0.

- [x] 3.9 In `tests/test_ui.py`, rewrite `test_the_invariant_holds_no_module_of_the_surface_names_an_artifact` per [D12](design.md#d12), keeping its `spec` mark, and add `test_the_check_catches_a_module_importing_an_artifact_writer`, whose `tmp_path` modules import `write_json`, import it `as` another name, and import only `read`.
  Verify: `uv run pytest tests/test_ui.py -k "names_an_artifact or importing_an_artifact_writer" -q` exits 0.

- [x] 3.10 **HALT CHECK** In `tests/test_sheet_schema.py`, extend `test_no_second_ordering_is_defined_anywhere_else` per [D11](design.md#d11), keeping its `spec` mark and its `hair_silhouette` check, and add `test_the_ordering_check_catches_a_literal_of_field_names`, whose `tmp_path` tree holds a tuple and a dict at the threshold, a tuple under it, and the carve-out file `tools/derive_field_map.py`. A scan red on the repository beyond the carve-out means the plan is wrong: stop.
  Verify: `uv run pytest tests/test_sheet_schema.py -k "second_ordering or literal_of_field_names" -q` exits 0.

- [x] 3.11 In `tests/test_wd14.py`, add `test_every_module_that_opens_an_onnx_session_silences_telemetry` and `test_the_check_catches_a_module_that_opens_a_session_unsilenced` per [D14](design.md#d14), the second over a `tmp_path` module that calls `InferenceSession` and one that also calls `silence_onnxruntime`.
  Verify: `uv run pytest tests/test_wd14.py -k "opens_an_onnx_session or opens_a_session_unsilenced" -q` exits 0.

- [x] 3.12 Run phase 3's test files together: edit nothing.
  Verify: `uv run pytest tests/test_spec_prose.py tests/test_principles.py tests/test_package_paths.py tests/test_ui.py tests/test_artifact_bytes.py tests/test_sheet_schema.py tests/test_wd14.py -q` exits 0.
