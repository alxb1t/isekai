# The terminal guards — tasks

The rule for a run's runs root changes, the cancel asks it, the owner unlinks a thumbnail that came back, and the documents say so.

## Progress

- [x] 1 — The root's guard · moderate
- [x] 2 — The cancel's guard · moderate
- [x] 3 — The second drop · moderate
- [x] 4 — The documents · moderate

## 1 — The root's guard

- [x] 1.1 **HALT CHECK** `render_running` stands in `isekai/foundation/library.py` with the collection test [D1](design.md#d1) removes.
  Verify: `git grep -n -e "^def render_running" -e "runs.name == RUNS" -- isekai/foundation/library.py` prints a `def` line at `126` and the `if not` line at `134`.
- [x] 1.2 In `tests/test_pipeline_cli.py`, after `test_discard_deletes_the_render_and_its_thumbnail`, add `test_discard_is_refused_beside_a_session_under_a_plain_runs_root` marked `cli:discard:a-session-beside-a-plain-runs-root-refuses-it`, per [D5](design.md#d5). The run sits under `tmp_path / "runs"`, its session record in `tmp_path / SESSIONS`; it asserts exit `1`, the sentence on standard error, the image still a file and an unchanged `tree(tmp_path)`.
  Verify: `uv run pytest tests/test_pipeline_cli.py -k discard_is_refused_beside` exits 1, on the unrefused discard.
- [x] 1.3 In `tests/test_edit_session.py`, after `test_edit_discard_a_running_session_refuses_an_edits_path`, add `test_edit_discard_a_session_under_a_plain_runs_root_refuses_an_edits_path` marked `edit:discard:a-session-beside-a-plain-runs-root-refuses-it`. It is that case without its `(tmp_path / "b" / "sources").mkdir()` line.
  Verify: `uv run pytest tests/test_edit_session.py -k a_session_under_a_plain` exits 1, on the unrefused discard.
- [x] 1.4 In `tests/test_ui_library.py`, import `render_running` from `isekai.foundation.library` and add `test_a_run_is_held_by_a_session_beside_its_runs_root` after `test_a_collection_is_held_by_a_live_session_lock`, marked `@pytest.mark.spec_exempt("structural: a run is held by a live session beside its runs root")`, per [D5](design.md#d5). It holds the plain root, a collection's root, a free lock, another root unheld, and a run named `Path("id")` whose root is the working directory, set by `monkeypatch.chdir`, held by a record in the folder above that root.
  Verify: `uv run pytest tests/test_ui_library.py -k beside_its_runs_root` exits 1, on the plain root.
- [x] 1.5 In `isekai/foundation/library.py`, replace `render_running` exactly as [D1](design.md#d1) gives it, its `is_collection(runs.parent)` test gone.
  Verify: `git grep -n -F "is_collection(runs.parent)" -- isekai/foundation/library.py` prints nothing.
- [x] 1.6 In `isekai/interface/verbs/drafts.py`, in `run_discard`'s docstring change `holds the collection, as the` to `holds the run's runs root, as the`; in `isekai/interface/ui/__init__.py` change the docstring of `render_running` to ``Return whether a render holds `run`'s runs root, for the `discard` verb.``
  Verify: `git grep -n -F -e "holds the run's runs root" -e "runs root, for the" -- isekai/interface/verbs/drafts.py isekai/interface/ui/__init__.py` prints a line in each file.
- [x] 1.7 Run the cases of the rule and of the verbs over the new function.
  Verify: `uv run pytest tests/test_ui_library.py tests/test_pipeline_cli.py tests/test_edit_session.py` exits 0.
- [x] 1.8 Run `tools.mutate` over the function's one body line; a survivor is killed by a further assertion in the cases of 1.2 to 1.4 ([D7](design.md#d7)).
  Verify: `uv run python -m tools.mutate isekai/foundation/library.py:134 --tests tests/test_ui_library.py tests/test_pipeline_cli.py tests/test_edit_session.py` exits 0.

## 2 — The cancel's guard

- [x] 2.1 **HALT CHECK** the approve builder's cancel branch stands in `isekai/interface/verbs/runner.py` where [D2](design.md#d2) edits it.
  Verify: `git grep -n -F "if item.args.cancel:" -- isekai/interface/verbs/runner.py` prints `240:        if item.args.cancel:`.
- [x] 2.2 In `tests/test_pipeline_cli.py`, after `test_approve_cancel_answers_each_run_on_its_own`, add `test_approve_cancel_is_refused_under_a_runs_root_a_session_holds` marked `cli:approve-cancel:a-running-render-refuses-it`, per [D5](design.md#d5). An approved run under `tmp_path / "held" / "runs"`, its record's lock held, and one under `tmp_path / "free" / "runs"`, each named by its absolute path; it asserts exit `1`, the held run's `001.approved.json` on disk, the free run's `001.draft.json`, and the sentence naming the held run.
  Verify: `uv run pytest tests/test_pipeline_cli.py -k a_session_holds` exits 1, on the cancel that was not refused.
- [x] 2.3 In `isekai/interface/verbs/runner.py`, import `render_running` from `isekai.foundation.library` between the imports of `flow` and `refusal`, and put the guard in the cancel branch exactly as [D2](design.md#d2) gives it.
  Verify: `uv run pytest tests/test_pipeline_cli.py tests/test_review.py tests/test_ui_api.py` exits 0.
- [x] 2.4 Derive the *Imported by* tables with `uv run python -m tools.derive_imported_by`, here and not in phase 4: 2.3's import makes `interface/verbs/runner.py` a reader of `library.py`, and the docs check is red until the `library.py` row of `isekai/foundation/README.md` names it.
  Verify: `uv run pytest tests/test_docs.py tests/test_layers.py` exits 0.
- [x] 2.5 Run no `tools.mutate` over the guard's lines: the tool mutates only a node that starts and ends on one line, and the guard, from `if render_running(run):` to the `)` that closes `Refusal(`, is an `if` over a call and a `raise` over four lines, so it holds no site and the tool exits 2. The guard's one mutant, the cancel not refused, is killed by the case of 2.2, which failed on it before 2.3; hold the case green.
  Verify: `uv run pytest tests/test_pipeline_cli.py -k a_session_holds` exits 0.
- [x] 2.6 Replay the standing mutants over the edited files.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0 with no survivor.

## 3 — The second drop

- [x] 3.1 **HALT CHECK** the library's and the owner's functions stand where [D3](design.md#d3) edits them, `library.py` as phase 1 left it.
  Verify: `git grep -n -e "^def thumbnail_of" -e "^def drop_" -e "^class Deleted" -e "^def delete_" -- isekai/foundation/library.py isekai/foundation/discard.py` prints, in `discard.py`, `class Deleted` at `176`, `delete_render` at `183` and `delete_edit` at `201`, and, in `library.py`, `thumbnail_of` at `175` and the drop at `188`.
- [x] 3.2 In `tests/test_edit_session.py`, after `test_edit_discard_the_owner_takes_a_render_its_edits_and_their_thumbnails`, add `test_edit_discard_the_owner_unlinks_a_thumbnail_rebuilt_in_the_gap`, `@pytest.mark.spec_exempt("structural: the owner unlinks a thumbnail a request rebuilt")`, parametrized by the image `"42.png"` and `"42.edit-1.png"`, per [D5](design.md#d5). It wraps `Path.unlink` so unlinking that image rewrites its thumbnail, calls `delete_render` for the render's image and `delete_edit` for the edit's, and asserts the thumbnail gone and listed once in `deleted.thumbnails`.
  Verify: `uv run pytest tests/test_edit_session.py -k unlinks_a_thumbnail_rebuilt` exits 1, on the thumbnail left.
- [x] 3.3 In `isekai/foundation/library.py`, add `named_thumbnail` after `thumbnail_of` and end `drop_thumbnails` on it, exactly as [D3](design.md#d3) gives them.
  Verify: `uv run pytest tests/test_ui_library.py tests/test_pipeline_cli.py` exits 0.
- [x] 3.4 In `isekai/foundation/discard.py`, import `Callable` and `Iterable` from `collections.abc` and `named_thumbnail` in place of `drop_thumbnails`, add `_edit_images`, `_named`, `_unlinked` and `_deleted` after `Deleted`, replace `delete_render` and `delete_edit`, and rewrite the module docstring's first paragraph, exactly as [D3](design.md#d3) gives them.
  Verify: `git grep -n -F "drop_thumbnails" -- isekai/foundation/discard.py` prints nothing.
- [x] 3.5 Run the cases of the owner, the verb, the route and the review stage over the new owner.
  Verify: `uv run pytest tests/test_edit_session.py tests/test_pipeline_cli.py tests/test_review.py tests/test_ui_api.py` exits 0.
- [x] 3.6 Run `tools.mutate` over `named_thumbnail` and `drop_thumbnails`, from the first `def` line to the last line; a survivor is killed by a further assertion in the cases of `tests/test_ui_library.py`.
  Verify: `uv run python -m tools.mutate isekai/foundation/library.py:188-214 --tests tests/test_ui_library.py tests/test_edit_session.py tests/test_pipeline_cli.py` exits 0.
- [x] 3.7 Run `tools.mutate` over the owner's helpers and both owners, from `_edit_images` to the last line of `delete_edit`; a survivor is killed by a further assertion in the case of 3.2 and in the owner's cases of `tests/test_edit_session.py`.
  Verify: `uv run python -m tools.mutate isekai/foundation/discard.py:184-252 --tests tests/test_edit_session.py tests/test_pipeline_cli.py tests/test_review.py` exits 0.
- [x] 3.8 Replay the standing mutants over the edited files.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0 with no survivor.

## 4 — The documents

- [x] 4.1 In `docs/decisions.md`, add D74 after D73 and before `## Infrastructure`, as [D6](design.md#d6) gives it, with a blank line before the heading.
  Verify: `git grep -n -F "### D74 · A terminal delete or cancel refuses beside a live render" -- docs/decisions.md` prints the heading, one line.
- [x] 4.2 In `docs/decisions.md`, amend D72 as [D6](design.md#d6) says: its bold paragraph, its *Why* ending, its *Accepts* line and its *Made by*, which gains `0190`. The heading stays.
  Verify: `git grep -n -F "then unlink any named thumbnail that came back" -- docs/decisions.md` prints D72's paragraph.
- [x] 4.3 In `docs/decisions.md`, amend D68 as [D6](design.md#d6) says: its bold paragraph names `named_thumbnail` between `thumbnail_of` and `drop_thumbnails`, and its *Made by* gains `0190`. The heading stays.
  Verify: `git grep -n -F "named_thumbnail" -- docs/decisions.md` prints D68's paragraph, one line.
- [x] 4.4 In `isekai/foundation/README.md`, in the `library.py` row of *Files* change `` `thumbnail_of` and `drop_thumbnails` `` to `` `thumbnail_of`, `named_thumbnail` and `drop_thumbnails` ``, and in the `discard.py` row change `which drop each thumbnail, then the files, then the approval` to `which name each thumbnail, drop them, delete the files and the approval, then unlink any that came back`.
  Verify: `git grep -n -F "named_thumbnail" -- isekai/foundation/README.md` prints the `library.py` row of *Files*.
- [x] 4.5 In `isekai/interface/README.md`, in the `verbs/runner.py` row append `; the approve builder refuses a cancel beside a render session`, and in the `verbs/drafts.py` row change `` `discard` deletes a render or an edit and each image's thumbnail`` to `` `discard` deletes a render or an edit and each image's thumbnail, refusing beside a render session``.
  Verify: `git grep -n -F "beside a render session" -- isekai/interface/README.md` prints the `verbs/runner.py` and `verbs/drafts.py` rows.
- [x] 4.6 In `README.md`, in the `--cancel` bullet, change `not combinable with `--from`.` to `a run is refused while a render session holds its runs root; not combinable with `--from`.`; in `docs/edit-tattoo.md` change `Both refuse while a render session holds the collection.` to `Both refuse while a render session holds its runs root.`
  Verify: `git grep -n -F "while a render session holds its runs root" -- README.md docs/edit-tattoo.md` prints one line in each file.
- [x] 4.7 Check the documents' tests hold with the new decision and the rows.
  Verify: `uv run pytest tests/test_docs.py tests/test_layers.py tests/test_spec_bindings.py tests/test_spec_prose.py` exits 0.
