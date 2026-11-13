# The paydown — tasks

Phases of tools, tests and prose: the runner's copy, its replay mode, the audit's mutants as a file, the findings left without a test, the patch scanner's scope, and the prose cards.

## Progress

- [x] 1 — The runner holds · moderate
- [x] 2 — The replay · hard
- [x] 3 — The audit's mutants · moderate
- [x] 4 — The two left · moderate
- [x] 5 — The scanner · hard
- [x] 6 — The prose · moderate

## 1 — The runner holds

- [x] 1.1 **HALT CHECK** The runner links `models`, `ui/node_modules` and `ui/dist` today, as [D1](design.md#d1) says; if `LINKED` already differs, the plan is wrong.
  Verify: `git grep -c -F 'LINKED = ("models", "ui/node_modules", "ui/dist")' tools/mutate.py` prints `1`.
- [x] 1.2 In `tools/mutate.py` set `LINKED = ("models",)`, and rewrite the `copy_tree` docstring to say it copies each tracked file that exists, makes the copy a git repository, then links `models`, so a test that writes under `models/` writes through the link and is a test to isolate.
  Verify: `git grep -c -F 'LINKED = ("models",)' tools/mutate.py` prints `tools/mutate.py:1`.
- [x] 1.3 In `copy_tree`, after the copy loop and before the links, run `["git", "-C", str(into), "init", "-q"]` and `["git", "-C", str(into), "add", "-A", "-f"]` each with `subprocess.run(..., capture_output=True, check=True)`. A `CalledProcessError` raises `Refused` naming the copy, as [D1](design.md#d1) says.
  Verify: `git grep -c -F -e '"init"' tools/mutate.py` prints `tools/mutate.py:1`.
- [x] 1.4 In `tests/test_mutate.py` extend `test_the_copy_holds_the_tracked_files_and_links_the_ignored_ones`, keeping its name. Write untracked `ui/dist/app.js` and `ui/node_modules/m.js` into the repository first. After `copy_tree` assert `not (copy / "ui").exists()` and that `git -C <copy> ls-files` lists the repository's test file and no `models` path. Change its exemption reason to `structural: a copy is a repository of the tracked files that exist and links models alone`.
  Verify: `uv run pytest tests/test_mutate.py::test_the_copy_holds_the_tracked_files_and_links_the_ignored_ones` passes.
- [x] 1.5 In `tests/test_mutate.py` add `test_a_survivor_that_outlasts_the_timeout_is_a_survivor`: `main` over `small_repo` with `calc.py:{LABEL_LINE}`, `--tests tests/test_calc.py` and `--timeout 0.1`, which pytest's own start outlasts. Assert exit 1, `survived calc.py:6 const: ...` among the printed lines, and no printed line beginning `timeout`. It carries `@pytest.mark.spec_exempt("structural: a survivor that outlasts --timeout is reported as one")`; it fails with the `timeout = mutant_timeout(...)` line of `run_mutants` removed, as [D2](design.md#d2) says.
  Verify: `uv run pytest tests/test_mutate.py::test_a_survivor_that_outlasts_the_timeout_is_a_survivor` passes.
- [x] 1.6 In `CONTRIBUTING.md`, in the paragraph on the pre-flight, add the sentence: "The run works in a copy that is a git repository of the tracked files and links `models/` alone, so a test that writes under `models/` writes through to the checkout: isolate it." Wrap the paragraph at its width and keep the words `links `models/` alone` on one line.
  Verify: `git grep -c -E 'models/. alone' CONTRIBUTING.md` prints `CONTRIBUTING.md:1`.

## 2 — The replay

- [x] 2.1 **HALT CHECK** `main` refuses a run with both or neither of `--tests` and `--all`, as [D3](design.md#d3) says; if the check lives elsewhere, the plan is wrong.
  Verify: `git grep -c -F 'give one of --tests and --all' tools/mutate.py` prints `1`.
- [x] 2.2 In `tools/mutate.py` make `targets` `nargs="*"` and add `--edits <path>` to `parse_args`; rewrite the module docstring's usage to show both forms. `main` takes the `--edits` branch before the existing check of `--tests` and `--all`: it refuses `--edits takes no target, --tests or --all` when `--edits` comes with any of them, and `give a target or --edits` when it has neither a target nor `--edits`. A run with a target keeps its checks and sentences as they are.
  Verify: `git grep -c -F 'give a target or --edits' tools/mutate.py` prints `tools/mutate.py:1`.
- [x] 2.3 In `tools/mutate.py` add a frozen dataclass `Edit` (`finding`, `path`, `find`, `replace`, `tests`, `line`, `equivalent`) and `def load_edits(root, path)`, which reads the JSON array and applies every refusal of the `D3` table: a missing key, an unknown key, empty `tests`, an untracked `path`, a `find` that occurs none or more than once. Each `Refused` names the finding. `line` is the 1-based line where `find` starts. `path` is read as given, relative to the working directory; `root` is the repository whose tracked files an entry names. A refusal names an entry by its `finding`, and by `entry <n>`, `<n>` its 1-based position, when `finding` is missing.
  Verify: `git grep -c -F 'def load_edits' tools/mutate.py` prints `tools/mutate.py:1`.
- [x] 2.4 In `tools/mutate.py` add `def run_edits(root, edits, timeout)`: one copy, a baseline for each distinct `tests` list (red is `Refused`, as in `run_mutants`), each mutant's limit `mutant_timeout` of its list's own baseline, the file written edited and restored after each run, a `.py` file parsed after the edit (`invalid` when it does not). Every baseline runs before any line prints. An edit goes through `verdict_line` and `report` as a `Mutant` whose `operator` is the `finding` and whose `old` and `new` are the first lines of `find` and `replace`, so a verdict line and a `survivor <path>:<line> <finding>` line have the form of a run on lines. An entry with `equivalent` is not run and prints `equivalent <path>:<line> <finding>: <reason>`. `main` calls it for `--edits` and ends with `report` and the exit codes it has.
  Verify: `git grep -c -F 'def run_edits' tools/mutate.py` prints `tools/mutate.py:1`.
- [x] 2.5 In `tests/test_mutate.py` add `test_an_edit_replays_in_any_file_and_a_survivor_exits_one`: a repository whose tracked `notes.txt` holds `limit = 10` and whose test file reads it, and an edits file with an entry the test notices and one it does not. Assert the verdict lines in the `D3` form, the summary `mutate: 1 killed, 1 survived, 0 invalid, 0 timeout`, the survivor line and exit 1. It carries `@pytest.mark.spec_exempt("structural: an edit is replayed in any tracked file, with its own tests")`.
  Verify: `uv run pytest tests/test_mutate.py::test_an_edit_replays_in_any_file_and_a_survivor_exits_one` passes.
- [x] 2.6 In `tests/test_mutate.py` add `test_an_entry_out_of_shape_or_whose_find_is_not_once_is_refused`, parametrized over a `find` that occurs twice, a `find` that occurs nowhere, an untracked `path`, a missing key, an unknown key, empty `tests`, and `--edits` beside a target. Each asserts exit 2, nothing printed to stdout, and the finding named in the refusal, save the last, which runs `calc.py:2 --edits <file>`, the target first, and asserts `--edits takes no target, --tests or --all`. It carries `@pytest.mark.spec_exempt("structural: an entry that cannot be replayed is refused before any mutant runs")`.
  Verify: `uv run pytest tests/test_mutate.py::test_an_entry_out_of_shape_or_whose_find_is_not_once_is_refused` passes.
- [x] 2.7 In `tests/test_mutate.py` add `test_an_equivalent_entry_is_printed_and_not_run` and `test_an_edit_that_breaks_python_is_invalid`. The first holds an entry that would survive, carrying `equivalent`, and asserts its printed line, no survivor and exit 0. The second edits `calc.py` into text that does not parse and asserts verdict `invalid` and exit 0. Each carries a `structural:` exemption naming its rule.
  Verify: `uv run pytest tests/test_mutate.py::test_an_equivalent_entry_is_printed_and_not_run tests/test_mutate.py::test_an_edit_that_breaks_python_is_invalid` passes.
- [x] 2.8 In `tests/test_mutate.py` add `test_a_red_baseline_of_one_entrys_tests_refuses_the_run`: entries with different `tests` lists, the later naming a test that fails unmutated. Assert exit 2, nothing printed, and `do not pass unmutated` in the refusal. It carries a `structural:` exemption.
  Verify: `uv run pytest tests/test_mutate.py::test_a_red_baseline_of_one_entrys_tests_refuses_the_run` passes.

## 3 — The audit's mutants

- [x] 3.1 **HALT CHECK** The guards reworded MT-2's decorator, so its `find` is the form of [D4](design.md#d4); if the decorator reads otherwise, the plan is wrong.
  Verify: `git grep -c -E "structural: the pins guide's path check" tests/test_docs.py` prints `1`.
- [x] 3.2 Write `tests/mutants.json`: each entry of [mutants.json](mutants.json) but `PB-14` and `UB-14`, keys and order unchanged, indented as the source is. Those two enter in phase 4 ([D4](design.md#d4)).
  Verify: `uv run python -m json.tool tests/mutants.json` exits `0`.
- [x] 3.3 In `Makefile` add the `mutants` target after `derive`, and list it in `.PHONY`; `gate` is unchanged and does not run it. Add each of these lines, the recipe indented with a tab:
  ```diff
  - .PHONY: gate e2e setup browsers drift derive
  + .PHONY: gate e2e setup browsers drift derive mutants
  + # Replay the audit's mutants, each against the tests it names, and fail on a
  + # survivor. Not part of the gate, because a replay takes minutes.
  + mutants:
  + uv run python -m tools.mutate --edits tests/mutants.json
  ```
  Verify: `make -n mutants` prints `uv run python -m tools.mutate --edits tests/mutants.json`.
- [x] 3.4 In `CONTRIBUTING.md`, after the sentence of 1.6, add: "A mutant of a finding a version closed lives in `tests/mutants.json`, and `make mutants` replays them outside the gate; a refactor version's pre-flight adds its own entries." Keep `make mutants` on one line.
  Verify: `git grep -c -F 'make mutants' CONTRIBUTING.md` prints `CONTRIBUTING.md:1`.
- [x] 3.5 Run the replay over `tests/mutants.json`. It takes minutes. A line that names a survivor goes to 3.6.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits `0`.
- [x] 3.6 Apply the rule of [D5](design.md#d5) to each `survivor` line 3.5 printed. Where 3.5 printed none, this task holds.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits `0`.

## 4 — The two left

- [x] 4.1 **HALT CHECK** `discard` deletes the draft's own source copy by its number, as [D6](design.md#d6) says; if it does not, the plan is wrong.
  Verify: `git grep -c -F 'copy = source_copy(run, flow, int(draft.name[:3]))' isekai/pipeline/review.py` prints `1`.
- [x] 4.2 In `tests/test_review.py` add `test_a_discard_leaves_the_source_copy_of_another_draft` beside `test_a_drafted_draft_goes_alone_and_the_flow_stays`, arranged as it is. Before `discard`, write `other = source_copy(run, CONJURE, 2)` with the bytes of the draft's own copy. Afterwards assert the draft's copy is gone, `other.is_file()` and its bytes are unchanged. It carries `review:discard:a-drafted-draft-goes-alone`.
  Verify: `uv run pytest tests/test_review.py::test_a_discard_leaves_the_source_copy_of_another_draft` passes.
- [x] 4.3 In `tests/test_ui_library.py` extend `test_an_unreadable_run_file_marks_its_cell_alone`, keeping its name and key. Add sources `cy.jpg`, `dee.jpg` and `eve.jpg` to its collection: `cy` holds a sheet made with `sheet`, `dee` a tag list written with `write_wd14` and its flow directory made with `directory(SUMMON).mkdir()`, as the tagged-cell test does, since `stage` reads no file where that directory is absent, `eve` an approval made as `_approved` makes one. Set each file's `schema.version` to 99 as `ada`'s draft is set, and assert each cell is `unreadable`, its refusal names its file and `version 99`, and `bea`'s cell is as before.
  Verify: `uv run pytest tests/test_ui_library.py::test_an_unreadable_run_file_marks_its_cell_alone` passes.
- [x] 4.4 Append the `PB-14` and `UB-14` entries of [mutants.json](mutants.json) to `tests/mutants.json`, keys unchanged; each entry opens with `"finding":`.
  Verify: `grep -c -F '"finding":' tests/mutants.json` prints `22`.
- [x] 4.5 Run the replay: every entry dies, and `PB-14` and `UB-14` die by the tests of 4.2 and 4.3.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits `0`.

## 5 — The scanner

- [x] 5.1 **HALT CHECK** `resolved_patches` builds one alias map for a whole test file, as [D7](design.md#d7) says; if it does not, the plan is wrong.
  Verify: `git grep -c -F 'bound = _bound_modules(root, tree, packages)' tests/test_ratchets.py` prints `1`.
- [x] 5.2 In `tests/test_ratchets.py` make `resolved_patches` and `_patches` bind each `setattr` target by its lexical scope as [D7](design.md#d7) says: the imports a function makes extend those of its enclosing scope, and reach no sibling function and not the module. `_bound_modules` stays, for `names_read`.
  Verify: `uv run pytest tests/test_ratchets.py` passes.
- [x] 5.3 In `tests/test_ratchets.py` add `test_a_reused_local_alias_hides_no_patched_module`, its twin: the modules `isekai.shared.fields`, binding `validate`, and `isekai.shared.ink`, binding `extract_ink`, are written under `tmp_path`. One test file imports `fields` at module level, and has a function that imports `fields as subject` and patches `subject.validate`, one that imports `ink as subject` and patches `subject.extract_ink`, one that patches `fields.validate` through the module-level import, and one that imports `ink as fields` and patches `fields.extract_ink`. Assert `patched_modules(tmp_path) == {"isekai.shared.fields": 2, "isekai.shared.ink": 2}`; the file-wide map reports `isekai.shared.ink` alone. It carries `@pytest.mark.spec_exempt("structural: twin of test_no_patched_module_is_unlisted")`.
  Verify: `uv run pytest tests/test_ratchets.py::test_a_reused_local_alias_hides_no_patched_module` passes.
- [x] 5.4 **HALT CHECK** The scope reads no patch the file-wide map hid in the repository's own tests: `PATCHED_MODULES` gains no row. If this test names an unlisted module, the plan is wrong.
  Verify: `uv run pytest tests/test_ratchets.py::test_no_patched_module_is_unlisted` passes.

## 6 — The prose

- [x] 6.1 **HALT CHECK** `0119·R4` is fixed already: the quote's comment names a queued bake, as [D8](design.md#d8) says; if it does not, the plan is wrong.
  Verify: `git grep -c -F 'holds a queued bake' isekai/interface/render.py` prints `1`.
- [x] 6.2 **HALT CHECK** `0119·S4` is fixed already: the quote keeps a collection that holds a queued bake; if its filter reads otherwise, the plan is wrong.
  Verify: `git grep -c -F 'one.lines or one.refused or held[runs].count' isekai/interface/render.py` prints `1`.
- [x] 6.3 **HALT CHECK** `0121·S3` is fixed already: `ink_view` reads the skin point once, through `extract_ink_grey`; if it calls `extract_ink` and `white_grey` again, the plan is wrong.
  Verify: `git grep -c -F 'extract_ink_grey(' isekai/pipeline/tattoos.py` prints `1`.
- [x] 6.4 **HALT CHECK** `0126·R4` sits in an archived design, which is a record; if the note is no longer there, the plan is wrong.
  Verify: `git grep -c -F 'the later rename fails' openspec/changes/archive/0126-cuts-per-photograph/design.md` prints `1`.
- [x] 6.5 **HALT CHECK** `0133·R1` sits in an archived design, which is a record; if the row is no longer there, the plan is wrong.
  Verify: `git grep -c -E 'pinned as .running' openspec/changes/archive/0133-the-base/design.md` prints `1`.
- [x] 6.6 In `isekai/interface/ui/app.py` replace the comment above `_BAKE_DIGITS`: before `# The most digits a bake number is read from: `int` refuses a longer spelling.`, after `# The most digits a bake number is read from: a longer spelling is refused unread.`
  Verify: `git grep -c -F 'a longer spelling is refused unread.' isekai/interface/ui/app.py` prints `isekai/interface/ui/app.py:1`.
- [x] 6.7 In `ui/design/spec.md` change the bullet **A bake's view**: its first sentence after `*baked*.` reads `It offers no write — no *Draft from this*, *Compare with…*, *Place a tattoo* (⇧P) or *Delete*, and none of their keys — since a delete there would take the render and every bake;`. Re-wrap the bullet's lines, none past 120 characters, and keep that clause `*Compare with…*, *Place a tattoo* (⇧P) or *Delete*` on one line.
  Verify: `git grep -c -F '*Compare with…*, *Place a tattoo* (⇧P) or *Delete*' ui/design/spec.md` prints `ui/design/spec.md:1`.
