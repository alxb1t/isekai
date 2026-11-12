# The guards hold — design

Guards that pass blind are made to read what they hold, each with a twin that goes red without it: edits to tests, goldens for an edit, a placement and a session record, and the comments of `pyproject.toml` and the drift workflow. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

An audit of the suite found guards that stay green while the thing they hold is gone. The refactor that follows reads the gate as its proof, so each guard must be able to fail.

```
phase 1  the binding guard      scenario key and layer · layer side · skipped keys · blank reason · symlink case · FILED
phase 2  the exemptions         two reason forms · reasons reworded · four rebinds · shrink-only table
phase 3  no guard passes blind  history · principles · anchors · artifact scan · writers · goldens · surface · order · ONNX
```

The change is built after `0127-green-main` releases. The two share `tests/test_infra.py`, `tests/test_ui.py` and `CHANGELOG.md`, on disjoint lines.

## Goals / Non-Goals

Goals:

- Each guard named in a phase reads the whole of what it claims to hold, and a twin shows it red without that.
- A reason a test is exempt from a scenario has a form a test can check, and a behaviour test that hides behind one is listed.

Non-Goals:

- No product file moves: no `.py` under `isekai/` or `evaluation/` changes, and the image-frozen `Dockerfile` stays.
- No requirement, scenario or decision of `docs/decisions.md` is added or amended.
- No test is deleted or merged.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | The binding guard reads each scenario's key and layer, and holds a key to a test on its own layer | nothing reads `#### Scenario:` or `- **Layers:**`, so a dropped key or a flipped layer passes | the strict rule, every binder on the layer: some `unit` keys also have a browser binder, a spec-audit matter |
| [D2](#d2) | A key whose every test a decorator skips is red; the containment key gets a symlink test that runs everywhere | a skipped binder counts as a binder today | an allow-list of runtime skips, which a decorator scan cannot see |
| [D3](#d3) | A blank `spec_exempt` reason is red | `""` is a string, so it reads as a reason | — |
| [D4](#d4) | A reason is `structural: <rule>` or `structural: twin of <test>`, each test named existing | many reasons sit off both, and one twin names no test | a free-text reason |
| [D5](#d5) | Each off-form reason is reworded by one rule: a twin of a test names it, anything else is a rule | the form check then holds all of them | a per-reason judgement at the build |
| [D6](#d6) | The behaviour tests that fit a scenario that exists are bound to it; the others are listed in a table that may only shrink | a patch may add a scenario only for a defect, so the missing scenarios wait for the *spec audit* | adding the scenarios here |
| [D7](#d7) | The history pattern reads change ids as `0\d{3}` and versions as `v0\.\d{1,3}`, and its reach takes `pyproject.toml` and the workflows | change ids are `01xx`, and the config files held history the guard never read | `v\d+\.\d+`, which hits third-party versions in the `Dockerfile`, `tests/test_manifest.py` and `tools/derive_manifest.py` |
| [D8](#d8) | The principles parse asserts a floor of principles and no heading deeper than `###` | a heading moved one level drops its principle from every check | — |
| [D9](#d9) | Each anchor is compared with the repository root joined to its suffix, and every constant anchored on `__file__` is listed | segments are counted and names never compared; one constant is unlisted | — |
| [D10](#d10) | The writer tripwires also read `write_atomically`, `create` and `replace`, and learn a class's annotated attributes | each reads one writer of the run files | an allow-list of call sites, which a moved line breaks |
| [D11](#d11) | *No second ordering* reads `isekai/`, `evaluation/` and `tools/` for a literal of three schema names; `tools/derive_field_map.py` is the one carve-out | a scan of `isekai/` alone misses the deriver, which holds the names as criteria | a bare-name scan: `pose`, `gaze` and `count` are everywhere |
| [D12](#d12) | The surface check parses imports and asserts it read modules | `import write_json as x` walks past a text search, and an empty glob passes | — |
| [D13](#d13) | Goldens pin the whole bytes of an edit, a placement and a session record | the bytes of every other kind are pinned | — |
| [D14](#d14) | A scan derives the modules that open an ONNX session and asks each to silence telemetry | the opener list names two of four | — |
| [D15](#d15) | The change is `0128-the-guards-hold`, a patch, built on Sonnet 5.5 high and converged on Codex checkers | small tests to place; the house's converge | — |

### D1

`scenarios(root)` reads each `#### Scenario:` block of the effective spec with its `- **Key:**` and `- **Layers:**` values; a block without either, or with a value that is not `unit` or `e2e`, is a fault. A demanded `e2e` key needs a binder under `tests/e2e/`, and a `unit` key one outside it. A vitest binder is outside.

### D2

`skipped(root)` lists each collected test with a `pytest.mark.skip` or `pytest.mark.skipif` decorator. A demanded key all of whose binders are in it is a fault, and the guard keeps no allow-list. A new test in `tests/test_run_directory.py`, bound to the containment key, makes a symlink to the repository and asks `_is_within` of `isekai/interface/wiring.py` whether a path under it is inside, so the key has a binder on Linux.

### D3

`unmarked` fails a `spec_exempt` whose reason is blank after `strip()`, beside the cases it already fails.

### D4

The form check reads each reason through the markers `marked_tests` returns.

```
structural: <rule>                      the rule is text that does not begin with `twin` or `the twin`
structural: twin of <test> [and <test>]  each <test> a test collected under tests/
```

A name resolves against the tests of every module, because a twin may stand in another file from the test it twins.

### D5

Every reason the form check flags is one of the groups below, and one rule rewords it: a target that is a test is named, any other `twin of` is dropped, and an unprefixed reason takes `structural: `. The tables are the evidence, read at the base with the command in [Tests](#tests); a reason the check flags and the tables miss follows the same rule.

Unprefixed reasons, which take `structural: ` and nothing else:

| file | reason |
|---|---|
| `tests/test_ollama.py` | `the endpoint and the ceiling are constants, not behaviour` |
| `tests/test_ollama.py` | `the reachability scenarios are bound at the adapters` |
| `tests/test_ollama.py` | `the failure-kind scenarios are bound at the adapters` |
| `tests/test_manifest.py` | `the one-path rule, not a provisioning scenario: D8 admits one base` |

Reasons that begin `twin:`:

| file | old reason | new reason |
|---|---|---|
| `tests/test_ui_api.py` | `twin: the overlap test fails once the lock is gone` | `structural: twin of test_overlapping_draft_updates_cannot_both_commit` |
| `tests/test_ui_api.py` | `twin: the approval test fails once approval takes no lock` | `structural: twin of test_an_update_overlapping_an_approval_is_refused` |
| `tests/test_resume.py` | `twin: the guard above catches a command naming no run` | `structural: twin of test_every_command_a_refusal_prints_is_one_this_build_accepts` |
| `tests/test_caption.py` | `twin: a build-only remedy does not name the files first` | `structural: a build-only remedy does not name the files first` |
| `tests/test_generate.py` | `twin: every named flow approved leaves nothing refused` | `structural: every named flow approved leaves nothing refused` |
| `tests/test_pipeline_cli.py` | `twin: the named-first flow runs whatever the per-flow guard` | `structural: the named-first flow runs whatever the per-flow guard` |
| `tests/test_run_view.py` | `twin: a readable frame prints its photograph, not a refusal` | `structural: a readable frame prints its photograph, not a refusal` |
| `tests/test_sheet_stage.py` | `twin: the same run, tagged, reads the trapped list` | `structural: the same run, tagged, reads the trapped list` |
| `tests/test_tagging.py` | `twin: a root holding an untagged flow still tags the photograph` | `structural: a root holding an untagged flow still tags the photograph` |
| `tests/test_tagging.py` | ``twin: `tag` named with flows refuses, naming no other verb`` | ``structural: `tag` named with flows refuses, naming no other verb`` |
| `tests/test_vocabulary_manifest.py` | `twin: why the refusal is the callers', not provision.py's` | `structural: why the refusal is the callers', not provision.py's` |

Reasons that say `twin of` and name no test:

| file | old reason | new reason |
|---|---|---|
| `tests/test_infra.py` | `structural: twin of the test that reads the Makefile's placement route` | `structural: twin of test_infra_placement_route_is_in_setup_and_drift_and_not_the_gate` |
| `tests/test_infra.py` | `structural: twin of test_the_pod_is_created_from_the_pinned_digest`, which does not exist | `structural: twin of test_the_session_boots_the_digest_the_image_config_pins` |
| `tests/test_ui.py` | `structural: twin of the surface's edit-stem check` | `structural: twin of test_bake_names_no_module_of_the_surface_spells_an_edits_file_stem` |
| `tests/test_layers.py` | `structural: twin of the scope every scan reads` | `structural: the scope every scan reads` |
| `tests/test_metric_scripts.py` | `structural: twin of the collected count` and `structural: twin of the reading set's count` | `structural: the collected count` and `structural: the reading set's count` |
| `tests/test_spec_bindings.py` | `structural: twin of the active deltas' keys`, at each site | `structural: the active deltas' keys` |
| `tests/test_test_ui.py` | `structural: twin of the browser tests' refusals` | `structural: the browser tests' refusals` |
| `tests/test_typecheck_ui.py` | `structural: twin of the browser check's refusals` | `structural: the browser check's refusals` |
| `tests/test_vocabulary.py` | `structural: twin of require_vocabulary's failure` and `structural: twin of require_vocabulary's skip` | `structural: require_vocabulary's failure` and `structural: require_vocabulary's skip` |

Reasons off the form in another way:

| file | old reason | new reason |
|---|---|---|
| `tests/test_docs.py` | `structural: the twin of the pins guide's path check` | `structural: the pins guide's path check` |
| `tests/test_ink.py` | `structural: the twin of the dark image's refusal` | `structural: the dark image's refusal` |
| `tests/test_pipeline_cli.py` | `structural: twin -- ISEKAI_WIRING without a factory refuses` | `structural: ISEKAI_WIRING without a factory refuses` |
| `tests/test_ui_api.py` | `structural: twin -- this page's own requests are answered` | `structural: this page's own requests are answered` |

### D6

The behaviour tests below prove a scenario that exists, and each takes `spec` in place of `spec_exempt`.

| test | scenario key |
|---|---|
| `test_edit_crop_a_mask_with_no_tattoo_is_refused` in `tests/test_edit.py` | `edit:refusals:a-composite-with-no-ink-is-refused` |
| `test_edit_verb_a_refused_request_exits_one_and_writes_nothing` in `tests/test_edit.py` | `edit:refusals:a-composite-with-no-ink-is-refused` |
| `test_a_refusal_naming_a_bare_gpunit_command_ends_on_one_that_loads_the_key` in `tests/test_render.py` | `cli:refusals:refusal-names-the-remedy` |
| `test_parsing_a_verb_succeeds` in `tests/test_pipeline_cli.py` | `cli:pipeline-surface:verbs-are-subcommands` |

The other behaviour tests exempt as structural go in `BEHAVIOUR_EXEMPT` of `tests/test_spec_bindings.py`, a mapping from `<file>::<test>` to where its scenario belongs, for the *spec audit*. The table may only shrink: a row whose test is bound or gone is a fault, and the table's length may not pass `BEHAVIOUR_CEILING`, its length when written.

| test, all in the file named | where its scenario belongs |
|---|---|
| `tests/test_edit.py::test_edit_derive_the_ink_is_the_composite_divided_by_the_render` | `edit` · An edit request is made from a render and its composite |
| `tests/test_edit.py::test_edit_derive_darkness_follows_the_darkest_channel` | `edit` · An edit request is made from a render and its composite |
| `tests/test_edit.py::test_edit_derive_the_mask_covers_the_ink_and_reaches_past_its_edge` | `edit` · An edit request is made from a render and its composite |
| `tests/test_edit.py::test_edit_derive_a_feather_of_nothing_leaves_a_hard_edge` | `edit` · An edit request is made from a render and its composite |
| `tests/test_edit.py::test_edit_derive_the_control_is_darkness_times_the_gain_clipped` | `edit` · An edit request is made from a render and its composite |
| `tests/test_edit.py::test_edit_derive_a_png_decodes_to_the_pixels_it_holds` | no requirement fits |
| `tests/test_edit.py::test_edit_refuse_a_composite_that_does_not_decode_names_the_export` | `edit` · A request the composite cannot support is refused |
| `tests/test_edit.py::test_edit_crop_the_sampling_size_is_a_multiple_of_eight_on_its_long_side` | `edit` · The crop is the tattoo's own, widened and grown by two guards |
| `tests/test_edit.py::test_edit_request_a_composite_that_is_missing_is_refused_and_writes_nothing` | `edit` · A request the composite cannot support is refused |
| `tests/test_edit.py::test_edit_request_a_source_that_is_no_render_is_refused` | `edit` · An edit request is made from a render and its composite |
| `tests/test_edit.py::test_edit_verb_an_untracked_edit_is_refused_naming_the_tracked_ones` | `edit` · An edit is one flat directory, pinned by its digest |
| `tests/test_edit.py::test_edit_sample_pending_lists_the_requests_with_no_image_in_chain_order` | `edit` · A render session runs every pending edit |
| `tests/test_edit.py::test_edit_stitch_an_answer_that_is_no_image_is_refused` | `edit` · A render session runs every pending edit |
| `tests/test_edit.py::test_edit_pending_progress_json_prints_a_line_per_sampled_edit` | no requirement fits |
| `tests/test_edit_placement.py::test_placement_request_writes_in_the_order_a_request_is_read` | `tattoo` · A bake writes the edit request and its placement record |
| `tests/test_edit_session.py::test_edit_group_a_group_holding_an_edits_file_is_no_group_of_failure_records` | `edit` · A discard takes edits |
| `tests/test_render.py::test_a_dependent_before_its_source_is_refused_naming_both` | `cli` · A render session's limit is estimated from its work |
| `tests/test_render.py::test_a_request_of_another_shape_is_refused_into_the_log` | no requirement fits |
| `tests/test_render.py::test_a_port_that_already_answers_is_refused_before_the_session` | no requirement fits |
| `tests/test_render.py::test_a_lost_create_exits_3_and_a_failed_teardown_names_gpunit_down` | `cli` · A render session writes its record into the collection, from its start to its end |
| `tests/test_render.py::test_a_failed_body_is_named_beside_a_failed_teardown` | `cli` · A render session writes its record into the collection, from its start to its end |
| `tests/test_render.py::test_bake_quote_every_root_asked_has_its_edits_and_the_bakes_add_up` | `edit` · An edit's time is estimated from its work |

### D7

`_HISTORY` reads `\b0\d{3}` in its change-id branch and `\d{1,3}` in its version branch. `_COMMENT_TREES` gains `pyproject.toml` and `.github`, and `comment_history` reads a `.toml` or a `.yml` file by its `#` lines, as it reads a `Dockerfile`. The comments of `pyproject.toml` and `.github/workflows/drift.yml` that cite a version, a change id or a design are reworded in the same phase, the guard being red until they are.

### D8

`docs/principles.md` holds its principles as `### ` headings, and `_principles` reads those alone. A principle moved to `####`, or lifted to `##`, leaves the parse with fewer and every check green. The new guard asserts `_principles` reads at least `PRINCIPLES` of them, the number written when the guard is, and that no heading in the file is deeper than `###`.

### D9

`_assert_anchors_the_repository_root` also asserts `anchor == REPO_ROOT.joinpath(*suffix)`, which compares each segment's name where the pyproject check counts them. A scan reads each module of `isekai/` and `evaluation/` for a module-level assignment whose value uses `__file__`, and asks that each be an id of `ANCHORS`. `ink.INK_CONFIG_PATH` and `pod_start.PROVISION` are not listed today, and both join the list.

### D10

The twins of [Tests](#tests) show each widening red. The edits:

- `json_writers` also flags a call to `write_atomically` in a module outside `CONTRACT` and outside `BYTE_WRITERS`, a mapping from module to what it writes, each a byte or a library file and no run file.
- `unannotated_writes` reads `write`, `create` and `replace`.
- It learns a class's annotated attributes: `self._body: SessionRecord = {...}` in a method makes `self._body` annotated for every method of that class, so `create(path, SESSION_FILE, self._body)` in `isekai/interface/render.py` passes.

### D11

The scan reads each tuple, list, set and dict literal of `isekai/`, `evaluation/` and `tools/` and counts its string constants that are a name of the summon schema. Three or more is a fault, outside `tools/derive_field_map.py`, whose literals are field-map criteria. The old check for `hair_silhouette` in `isekai/` stays.

### D12

`test_the_invariant_holds_no_module_of_the_surface_names_an_artifact` parses each module under `isekai/interface/ui/` and refuses an import of `write_json`, `write`, `create` or `replace` from `isekai.foundation.artifacts`, or of `artifact_name` from `isekai.foundation.run`, under any alias. It asserts it read at least five modules. `library.py` imports `write_atomically` for thumbnails, which stays allowed.

### D13

Each golden is the bytes the production writer makes from fixed inputs, read once and kept. The edit and placement records come from `request_placed` of `isekai/pipeline/edit.py`, with a flat render, a composite multiplied under its tattoo's square, `seed=5` and `random.Random(1)`. The session record comes from `Record` of `isekai/interface/render.py`, opened with a fixed id and start, one step and one image, and not ended: `end` reads the clock.

### D14

A scan reads each module of `isekai/` and `evaluation/` for a call to `InferenceSession`, and asks that the module also call `silence_onnxruntime`. The openers the runtime test drives stay as they are.

### D15

The phases rate `moderate`: guard logic in small functions, each with its twin, and reasons to place. The build runs on Sonnet 5.5 high whole, and each phase ends on a green `make check`.

## The binding guard

What phase 1 adds to `tests/test_spec_bindings.py`, beside the guards it keeps.

```
scenario block ──▶ key + layers present      scenarios(root)          D1
key + layers   ──▶ a binder on its layer     layer_faults(...)        D1
every binder   ──▶ not a decorator skip      skipped(root)            D2
spec_exempt("")──▶ red                       unmarked(tests)          D3
```

`FILED` in `tools/derive_field_map.py` is the committed transcription of the operator's approved sheets. The reachability test of `tests/test_field_map.py` reads it, so it no longer waits on the gitignored runs; where the vocabulary is absent it still skips. Its neighbour that compares `FILED` with the runs stays: it holds the transcription against the operator's own disk, and `--refresh` prints the same diff.

## The blind guards

What phase 3 reads that each guard missed, with the files it edits.

| guard | file | what it missed |
|---|---|---|
| history | `tests/test_spec_prose.py` | change ids `01xx`; `pyproject.toml` and the workflows |
| principles | `tests/test_principles.py` | a principle under a moved heading |
| anchors | `tests/test_package_paths.py` | segment names; `ink.INK_CONFIG_PATH` and `pod_start.PROVISION` unlisted |
| artifact scan | `tests/test_artifact_bytes.py` | an empty glob; `write_atomically`, `create`, `replace`; a class's attributes |
| surface | `tests/test_ui.py` | an aliased import; an empty glob |
| order | `tests/test_sheet_schema.py` | `tools/` |
| ONNX | `tests/test_wd14.py` | the sessions of the pose finder and the segmenter |

## Tests

Counts are those of `uv run pytest --collect-only -qq --ignore=tests/e2e` over the files below, at the base, and the same command prints them after.

| file | tests before | tests added |
|---|---|---|
| `tests/test_spec_bindings.py` | 15 | 11 |
| `tests/test_run_directory.py` | 92 | 1 |
| `tests/test_field_map.py` | 18 | 0 |
| `tests/test_spec_prose.py` | 16 | 0 |
| `tests/test_principles.py` | 4 | 2 |
| `tests/test_package_paths.py` | 16 | 5 |
| `tests/test_artifact_bytes.py` | 16 | 6 |
| `tests/test_ui.py` | 20 | 1 |
| `tests/test_sheet_schema.py` | 15 | 1 |
| `tests/test_wd14.py` | 22 | 2 |

The tests added are the ones the tasks name: each guard with its twin, and the cases of `tests/test_package_paths.py` for the anchors above and `tests/test_artifact_bytes.py` for the new kinds, each case counted as a test.

Edited with no test added: the exemption reasons of `tests/test_ollama.py`, `tests/test_manifest.py`, `tests/test_ui_api.py`, `tests/test_resume.py`, `tests/test_infra.py`, `tests/test_edit.py`, `tests/test_render.py` and `tests/test_pipeline_cli.py`, and the goldens `tests/golden/edit.json`, `tests/golden/placement.json` and `tests/golden/session.json`. `tests/test_cap.py::test_blank` is a test inside the source a twin of `tests/test_spec_bindings.py` writes to a `tmp_path`, `tests/e2e/` is read, for the layer rule of [D1](#d1), and `tests/test_edit_placement.py` for the inputs of the goldens, neither edited.

| layer | added | removed | command |
|---|---|---|---|
| unit and integration | the sum of the column above | 0 | the command above |
| end-to-end | 0 | 0 | `uv run pytest --collect-only -qq tests/e2e` |

No end-to-end test is added (`T1`): each guard is a unit test of a function over a tree, and each twin runs it over a `tmp_path` tree. No test is deleted or merged, so there is no table of what carries each one's assertions (`T5`). The twin of each new guard is a unit test of the guard, never a browser test (`T6`).

## Dependencies

None.

## Risks / Trade-offs

- A golden of an edit or a placement holds the digests of PNG bytes Pillow encodes, as `tests/golden/run.json` holds a JPEG's. A different encoder on Linux turns CI red, and a patch fixes it at once.
- The layer rule of [D1](#d1) reads a vitest binder as a unit one. A `unit` key bound by a vitest test alone passes, which is right: that test is not a browser test.
- The shrink-only table of [D6](#d6) guards a count, not the reason a row is there. The *spec audit* removes rows as it adds their scenarios.
- A rewording of [D5](#d5) that names the wrong test passes the check, which reads that the name exists. The reviewer reads each twin against the test it names.

## Verdict

Ready to build, in the phases of [tasks](tasks.md). No decision of `docs/decisions.md` is added or amended, and no requirement is touched.
