# The command builder — tasks

Add `command` with its cases and a mutation run, build the builders and the parser's `prog` from it, call it from each site that spelt the entry, guard the entry with a test and its twin, then amend the documents.

## Progress

- [x] 1 — Add `command` with its cases · moderate
- [x] 2 — Build the builders from `command` · moderate
- [x] 3 — Call `command` from the sites · moderate
- [x] 4 — Guard the entry with a test and its twin · moderate
- [x] 5 — Amend the documents and replay the standing mutants · moderate

## 1 — Add `command` with its cases

- [x] 1.1 **HALT CHECK** The premise of [D1](design.md#d1) stands: no name `command` or `ENTRY` is defined in the foundation yet.
  Verify: `git grep -n -e '^def command' -e '^ENTRY' -- isekai/foundation` prints nothing.

- [x] 1.2 Find the lines of `stage_command` and `migrate_command` in `isekai/foundation/run.py`: `stage_command` runs from its `def` to one line before `def migrate_command`, and `migrate_command` from its `def` to one line before `def unmigrated`.
  Verify: `git grep -n -e '^def stage_command' -e '^def migrate_command' -e '^def unmigrated' -- isekai/foundation/run.py` prints a line for each.

- [x] 1.3 Run the mutation over each builder of 1.2 before a line moves, per [D6](design.md#d6), one run a range: `uv run python -m tools.mutate isekai/foundation/run.py:<first>-<last> --tests tests/test_run_directory.py tests/test_review.py tests/test_resume.py tests/test_pipeline_cli.py`. Kill each survivor with a case in `tests/test_run_directory.py` named `test_stage_command_…` for a survivor in `stage_command` and `test_migrate_command_…` for one in `migrate_command`, bound to `cli:refusals:refusal-names-the-remedy`, holding the text whole; one no case can kill is named equivalent, with its reason, in the commit body.
  Verify: `uv run pytest tests/test_run_directory.py tests/test_review.py tests/test_resume.py tests/test_pipeline_cli.py` exits 0.

- [x] 1.4 In `tests/test_run_directory.py` add `test_command_joins_the_entry_the_verb_and_the_words` (`("render", "b/runs", "f=1")` gives `"python -m isekai render b/runs f=1"`), `test_command_with_no_words_ends_at_the_verb` (`("migrate",)` gives `"python -m isekai migrate"`) and `test_command_quotes_no_word` (`("tag", "my photo.jpg")` gives `"python -m isekai tag my photo.jpg"`), each bound to `cli:refusals:refusal-names-the-remedy`, per [D1](design.md#d1). Add `test_the_parser_prints_the_entry`, `build_parser().prog == ENTRY`, with `spec_exempt("structural: the parser names the entry the builder holds")`. Import `ENTRY` and `command` from `isekai.foundation.run`, which keeps the file red until 1.6.
  Verify: `git grep -n -F 'test_command_quotes_no_word' -- tests/test_run_directory.py` prints one line.

- [x] 1.5 Create `isekai/foundation/command.py` as [D1](design.md#d1) writes it: the docstring, `ENTRY = "python -m isekai"` with the comment above it, and `command(verb: str, *words: str) -> str` returning `" ".join((ENTRY, verb, *words))`, with a docstring and its examples. The module imports nothing.
  Verify: `git grep -n -e '^def command' -- isekai/foundation` prints one line.

- [x] 1.6 In `isekai/foundation/run.py` import `ENTRY` and `command` from `isekai.foundation.command` after the `atomic_write` import, list `ENTRY` after `EDIT_SUFFIXES` and `command` after `check_budget` in `__all__`, and name `command.py` in the docstring's paragraph on the siblings: it holds the words a command starts with and the join that builds one.
  Verify: `uv run pytest tests/test_run_directory.py` exits 0.

- [x] 1.7 In `isekai/foundation/README.md` add a *Files* row for `command.py` after `producers.py` — `ENTRY`, the words every printed command starts with, and `command(verb, *words)`, which builds the command a person is told to run; it imports nothing of `isekai` — and a row `| `command.py` | — | — |` to the end of *Imported by*, then run `uv run python -m tools.derive_imported_by`.
  Verify: `uv run pytest tests/test_docs.py` exits 0.

## 2 — Build the builders from `command`

- [x] 2.1 In `isekai/foundation/run.py` rewrite the bodies of `stage_command` and `migrate_command` as [D2](design.md#d2) writes them, the docstrings and the signatures as they are: the flags as `("--flow", flow)` pairs, `["--runs", shlex.quote(str(root))]` off the default root, and `command(verb, *flagged, *runs, *options, run.id)`; `command("migrate")` and `command("migrate", "--runs", shlex.quote(str(root)))`. The lines `return f"python -m isekai {verb}…` and `return "python -m isekai migrate"` go.
  Verify: `git grep -n -e 'return f"python -m isekai' -e 'return "python -m isekai' -- isekai/foundation/run.py` prints nothing.

- [x] 2.2 In `refusal_for` of `isekai/foundation/run.py` rename the local `command = …` to `pasted = …`, which the import would shadow; the strings that read it keep their text.
  Verify: `git grep -n -F 'command = ' -- isekai/foundation/run.py` prints nothing.

- [x] 2.3 In `_draft_command` of `isekai/pipeline/review.py` return `command("draft", "--flow", flow, shlex.quote(str(image)))` in place of `return f"python -m isekai draft …`, and import `command` from `isekai.foundation.run`; the docstring stays.
  Verify: `git grep -n -F 'return f"python -m isekai' -- isekai/pipeline/review.py` prints nothing.

- [x] 2.4 In `_named_a_flow` of `isekai/interface/cli.py` build `root` and `again` as tuples and return the command through `command(verb, *root, *again, photos)` in place of `python -m isekai {verb}{root}{again} {photos}`, as [D2](design.md#d2) writes it, and import `command` from `isekai.foundation.run`.
  Verify: `git grep -n -F 'python -m isekai {verb}' -- isekai/interface/cli.py` prints nothing.

- [x] 2.5 In `build_parser` of `isekai/interface/cli.py` replace `prog="python -m isekai"` with `prog=ENTRY`, and add `ENTRY` to the import from `isekai.foundation.run`.
  Verify: `git grep -n -F 'prog="python -m isekai"' -- isekai/interface/cli.py` prints nothing.

- [x] 2.6 Find the lines of `command` in `isekai/foundation/command.py` and of `stage_command` and `migrate_command` in `isekai/foundation/run.py` as in 1.2, and run the mutation over each, per [D6](design.md#d6), one run a range, with the tests of 1.3. Kill each survivor as in 1.3.
  Verify: `uv run pytest tests/test_run_directory.py tests/test_review.py tests/test_resume.py tests/test_pipeline_cli.py` exits 0.

## 3 — Call `command` from the sites

- [x] 3.1 In `_stale` of `isekai/pipeline/edit.py` build the discard with `command("discard", image)`, `image` the quoted path as it is, per [D3](design.md#d3), and import `command` from `isekai.foundation.run`.
  Verify: `git grep -n -F 'python -m isekai' -- isekai/pipeline/edit.py` prints nothing.

- [x] 3.2 In `_held_way` of `isekai/pipeline/review.py` bind `rendering` to `command("render", shlex.quote(str(run.path.parent)), f"{source}=1")` in place of `python -m isekai render …`; the sentence that reads it stays.
  Verify: `git grep -n -F 'python -m isekai render' -- isekai/pipeline/review.py` prints nothing.

- [x] 3.3 In `source_seeds` of `isekai/pipeline/generate.py` bind `pasted` to `command("render", _runs_root(run), f"{source}=1{_dependents(flows, source)}")` before the `raise`, and read it in the backticks of the refusal in place of `python -m isekai render …`; import `command` from `isekai.foundation.run`.
  Verify: `git grep -n -F 'python -m isekai' -- isekai/pipeline/generate.py` prints nothing.

- [x] 3.4 In `_reported` of `isekai/boundary/comfy/client.py` build the hint's command with `command("render", "<runs>", "<flow>=<count>")` inside an f-string in place of `python -m isekai render <runs> …`, the words around it as they are, and import `command` from `isekai.foundation.run` after the `flow` import.
  Verify: `git grep -n -F 'python -m isekai' -- isekai/boundary/comfy/client.py` prints nothing.

- [x] 3.5 In `_runs` of `isekai/interface/compare_view.py` bind `retag` to `command("tag", "--runs", shlex.quote(str(root)), f"{shlex.quote(str(collection / COLLECTION_PHOTOS))}/*")` before the `raise`, and read it in the backticks of the refusal in place of `python -m isekai tag …`; import `command` from `isekai.foundation.run`.
  Verify: `git grep -n -F 'python -m isekai' -- isekai/interface/compare_view.py` prints nothing.

- [x] 3.6 In `Surface.rendered` and `Surface.bake_image` of `isekai/interface/ui/surface.py` replace each `python -m isekai render <path>` with `command("render", str(<path>))`, the path unquoted as it was, and import `command` from `isekai.foundation.run`.
  Verify: `git grep -n -F 'python -m isekai' -- isekai/interface/ui/surface.py` prints nothing.

- [x] 3.7 In `sheet_cell` of `isekai/interface/verbs/prepare.py` build the command with `command("assign", "--flow", flow, "--runs", runs, run_id)`, and in `parse_cells` of `isekai/interface/verbs/common.py` with `command("assign", "--flow", flow, "--runs", runs, "<photo>")`; in place of each `python -m isekai assign …`; each file imports `command` from `isekai.foundation.run`.
  Verify: `git grep -n -F 'python -m isekai' -- isekai/interface/verbs/prepare.py isekai/interface/verbs/common.py` prints nothing.

- [x] 3.8 In `run_edit` of `isekai/interface/verbs/edits.py` build the request's hint with `command("edit", "<edit>", "<render>", "--composite", "<png>")` and the success line's with `command("render", shlex.quote(str(runs)))`, each inside the backticks it had, in place of each `python -m isekai …`, and import `command` from `isekai.foundation.run`.
  Verify: `git grep -n -F 'python -m isekai' -- isekai/interface/verbs/edits.py` prints nothing.

- [x] 3.9 In `again` of `isekai/interface/render.py` rename the local `command = [` to `argv = [`, which the import of 3.10 would shadow; the list and `shlex.join` stay.
  Verify: `git grep -n -F 'command = [' -- isekai/interface/render.py` prints nothing.

- [x] 3.10 In `_asked` of `isekai/interface/render.py` bind `asked` to `command("assign", " ".join(flows), "--runs", shlex.quote(str(runs)), f"{photos}/*")` before the `raise`, and read `uv run {asked}` in the refusal, per [D3](design.md#d3); import `command` from `isekai.foundation.run`.
  Verify: `git grep -n -F 'uv run python -m isekai' -- isekai/interface/render.py` prints nothing.

- [x] 3.11 In `RenderRoutes._held` of `isekai/interface/ui/routes/rendering.py` write ``f"…then start `uv run --env-file .env {command('ui')}` again."``, the words before it as they are, in place of `python -m isekai ui`, and import `command` from `isekai.foundation.run`.
  Verify: `git grep -n -F 'python -m isekai' -- isekai/interface/ui/routes/rendering.py` prints nothing.

- [x] 3.12 Run `uv run python -m tools.derive_imported_by`: the *Imported by* row of `run.py` gains `boundary/comfy/client.py`.
  Verify: `uv run pytest tests/test_docs.py tests/test_layers.py` exits 0.

## 4 — Guard the entry with a test and its twin

- [x] 4.1 In `tests/test_run_directory.py` import `ast` and `re`, add `ENTRY` and `REPOSITORY` to the import from `isekai.foundation.run`, and add `SPELT`, `BUILDER`, `_holds_doc` and `entry_spellings(root)` as [D5](design.md#d5) writes them, then `test_no_string_spells_the_entry_outside_the_builder`, asserting `entry_spellings(REPOSITORY) == []`, with `spec_exempt("structural: a command is built by command and spelt nowhere else")`.
  Verify: `uv run pytest tests/test_run_directory.py -k no_string_spells_the_entry` exits 0.

- [x] 4.2 In the same file add the twin `test_the_guard_finds_a_string_that_spells_the_entry`, with `spec_exempt("structural: twin of the guard on the repository")`: under `tmp_path`, one module with an f-string that spells the entry, a string behind `uv run` and a string in a nested function, and the result is exactly the `path:line` of those strings; a module with the entry in a docstring, in a comment, as `python -m isekai.boundary.provision`, and `isekai/foundation/command.py` spelling it, adds no line.
  Verify: `uv run pytest tests/test_run_directory.py -k guard_finds_a_string` exits 0.

## 5 — Amend the documents and replay the standing mutants

- [x] 5.1 In `docs/decisions.md` add D75 after D73, before `## Infrastructure`, as [D7](design.md#d7) writes it: the heading `### D75 · A command is built by command, in isekai/foundation/command.py`, the statement, *Why*, *Accepts* and *Made by*.
  Verify: `git grep -n -F '### D75' -- docs/decisions.md` prints one line.

- [x] 5.2 In `docs/decisions.md` amend D62's statement to list `command.py` among the siblings `run.py` re-exports, as [D7](design.md#d7) says, and add `0193` to its *Made by*.
  Verify: `git grep -n -e 'and .command.py. under' -- docs/decisions.md` prints one line.

- [x] 5.3 Replay the standing mutants. A find an edit of the builders or the sites moved stops the replay with an error: re-point that entry of `tests/mutants.json` to the edited line, with the same `why`.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0.
