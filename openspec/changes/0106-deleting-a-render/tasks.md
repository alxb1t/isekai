# Tasks — 0106 deleting a render

The function, then the verb, then the endpoint, then the page, then the record, per [design](design.md). Paths are
from the repository root.

## Progress

- [x] 1 — The function
- [x] 2 — The verb
- [x] 3 — The endpoint
- [x] 4 — The page
- [x] 5 — The record

## 1 — The function

- [x] 1.1 **HALT CHECK** — [D2](design.md#d2) reads a collection with `library.is_collection`.
  Verify: `grep -n 'def is_collection' isekai/interface/ui/library.py` prints one line.
- [x] 1.2 In `isekai/pipeline/generate.py`, after `render_groups`, add `discard_render(image: Path) -> list[Path]` per
  [D1](design.md#d1), importing `rendered_at` from `isekai/foundation/run.py`; its docstring says the order and why.
  Verify: `grep -n 'def discard_render(image: Path) -> list\[Path\]:' isekai/pipeline/generate.py` prints one line.
- [x] 1.3 In `tests/test_generate.py`, add `test_discarding_a_render_deletes_its_image_and_record_alone`
  (`image-generation:discard:the-image-and-its-record-are-deleted`,
  `image-generation:discard:the-approval-is-left-short`): an approval whose `renders.count` is 2, rendered at seeds 11
  and 22; 11 discarded; `shortfall` goes from 0 to 1; 22's render, the approval and the prompt kept.
  Verify: `uv run pytest tests/test_generate.py -k discarding_a_render_deletes` exits 0.
- [x] 1.4 In `tests/test_generate.py`, add `test_discarding_a_groups_last_render_removes_the_group`
  (`image-generation:discard:an-emptied-group-is-removed`): an approval rendered at one seed, discarded; the group's
  directory is gone, and the approval and its prompt are unchanged.
  Verify: `uv run pytest tests/test_generate.py -k groups_last_render` exits 0.
- [x] 1.5 In `tests/test_generate.py`, add `test_discarding_a_path_naming_no_render_is_refused`
  (`image-generation:discard:a-path-naming-no-render-is-refused`): a sidecar's and a prompt's path each raise `Refusal`
  matching `<seed>.png`, and a snapshot of the run is unchanged.
  Verify: `uv run pytest tests/test_generate.py -k path_naming_no_render` exits 0.
- [x] 1.6 In `isekai/interface/ui/library.py`, after `thumbnail`, add `drop_thumbnails(run, image)` per
  [D2](design.md#d2); in `isekai/interface/ui/__init__.py`, after `collection_runs`, add `drop_thumbnails(run, image)`
  calling it, its docstring naming the CLI as its caller.
  Verify: `git grep -n 'def drop_thumbnails' -- isekai/interface/ui` prints two lines.
- [x] 1.7 In `tests/test_ui_library.py`, add `test_dropping_a_renders_thumbnails_leaves_the_others`
  (`ui:delete-render:the-route-deletes-the-render-and-its-thumbnail`): in a `_collection` run, cache files written by
  hand for seeds 11 and 22; seed 11's are deleted and returned, 22's kept; a run under `.data/runs` returns `[]`.
  Verify: `uv run pytest tests/test_ui_library.py -k dropping_a_renders_thumbnails` exits 0.

## 2 — The verb

- [x] 2.1 In `isekai/interface/cli.py`, make the edits of [the verb](design.md#the-verb)'s table: the docstring line,
  the `VERBS` entry, the loop's tuple, the `discard` parser and the `dispatch` branch.
  Verify: `uv run python -m isekai discard --help` exits 0.
- [x] 2.2 In `isekai/interface/cli.py`, after `_draft`, add `_discard(image: Path, wired: Wiring) -> int` per
  [D3](design.md#d3), importing `drop_thumbnails` from `isekai.interface.ui` inside it, its docstring saying why.
  Verify: `grep -n 'def _discard(image: Path, wired: Wiring) -> int:' isekai/interface/cli.py` prints one line.
- [x] 2.3 In `tests/test_pipeline_cli.py`, add `"discard"` after `"draft"` in `EXPECTED_VERBS`, and
  `"discard": ["outputs/001/7.png"]` to `own` in `test_each_verb_is_reachable_as_a_subcommand`.
  Verify: `uv run pytest "tests/test_pipeline_cli.py::test_each_verb_is_reachable_as_a_subcommand[discard]"` exits 0.
- [x] 2.4 In `tests/test_pipeline_cli.py`, add `test_discard_deletes_the_render_and_its_thumbnail`
  (`cli:discard:the-render-and-its-thumbnail-are-deleted`): a run in `<tmp>/lib/<collection>/runs`, `sources/` beside
  it, its cache file by hand; the image given relative, after `monkeypatch.chdir(tmp_path)`; `dispatch` exits 0; the
  image, record and thumbnail gone, `wired.out` naming each.
  Verify: `uv run pytest tests/test_pipeline_cli.py -k discard_deletes_the_render` exits 0.
- [x] 2.5 In `tests/test_pipeline_cli.py`, add `test_discard_of_a_path_naming_no_render_is_refused`
  (`cli:discard:a-path-naming-no-render-is-refused`): a sidecar's path exits 1, `wired.err` naming it and
  `<run>/<flow>/outputs/<NNN>/<seed>.png`, and a snapshot of the run is unchanged.
  Verify: `uv run pytest tests/test_pipeline_cli.py -k discard_of_a_path` exits 0.

## 3 — The endpoint

- [x] 3.1 In `isekai/interface/ui/app.py`, add `delete_render` per [D4](design.md#d4), after `read_render_thumb`,
  importing `discard_render` beside `image_of`; the module docstring's route list gains, after the `…/compare/…` line,
  `DELETE /api/c/{collection}/renders/{digest}/{flow}/{version}/{seed}`.
  Verify: `grep -n '@app.delete("/api/c/{collection}/renders/{digest}/{flow}/{version}/{seed}")' isekai/interface/ui/app.py` prints one line.
- [x] 3.2 In `tests/test_ui_api.py`, add `test_deleting_a_render_deletes_its_files_and_thumbnail`
  (`ui:delete-render:the-route-deletes-the-render-and-its-thumbnail`): `_rendered_twice`, both `/thumb`s read, then
  `client.delete` on `v1/11` answers 200; 11's image, record and thumbnail are gone, v2's seed 22's kept.
  Verify: `uv run pytest tests/test_ui_api.py -k deleting_a_render_deletes` exits 0.
- [x] 3.3 In `tests/test_ui_api.py`, add `test_deleting_a_render_is_refused_while_a_render_runs`
  (`ui:delete-render:refused-while-a-render-runs`): `Jobs.slot` faked with `_rendering_slot`, as
  `test_an_approved_sheet_carries_why_it_cannot_be_cancelled` does; 409, `A render session is running.`, files kept.
  Verify: `uv run pytest tests/test_ui_api.py -k refused_while_a_render_runs` exits 0.

## 4 — The page

- [x] 4.1 In `ui/src/api.ts`, after `renderDetail`, add `deleteRender(place: RenderPlace): Promise<{ deleted: boolean
  }>`, `request(renderAt(place), { method: 'DELETE' })`, per [D5](design.md#d5).
  Verify: `grep -n 'export function deleteRender' ui/src/api.ts` prints one line.
- [x] 4.2 In `ui/src/stores/keys.ts`, add `Backspace: '⌫',` to `GLYPHS`; at the end of
  `ui:keys:hints-come-from-the-declarations` in `ui/src/stores/keys.test.ts`, declare a `screen` command `delete` on
  `{ code: 'Backspace', shift: true }` and expect `keys.hint('delete')` to be `'⇧⌫'`.
  Verify: `grep -n "toBe('⇧⌫')" ui/src/stores/keys.test.ts` prints one line.
- [x] 4.3 Write `ui/src/components/DeleteDialog.vue` per [the page](design.md#the-page), its head comment saying what
  it asks and that *No* comes first.
  Verify: `grep -n 'data-delete-dialog' ui/src/components/DeleteDialog.vue` prints one line.
- [x] 4.4 In `ui/src/views/RenderLarge.vue`, per [the page](design.md#the-page) and [D6](design.md#d6): `deleting`, the
  `delete` command after `compare`, the *Delete* group after *Compare with…*'s, the dialog after `DraftDialog`,
  `deleted()`; the head comment names `⇧⌫`.
  Verify: `grep -n "keys: \[shifted('Backspace')\]" ui/src/views/RenderLarge.vue` prints one line.
- [x] 4.5 In `ui/src/views/Hub.vue`'s `onMounted`, focus the spot `window.history.state?.cell` names before
  `kept(spots, named, store.focus.hub)`, per [D6](design.md#d6), with a comment saying who sends it.
  Verify: `grep -n 'history.state?.cell' ui/src/views/Hub.vue` prints one line.
- [x] 4.6 In `tests/e2e/conftest.py`, add `DELETED = "deleted"` after `CHOSEN`, commented as the collection a render is
  deleted from; `deleted: Run` in `Served` after `discarded`, seeded `_rendered_at_seven(lib / DELETED, "rae", (860,
  1000))` and passed to `Served`.
  Verify: `grep -n '^DELETED = "deleted"$' tests/e2e/conftest.py` prints one line.
- [x] 4.7 In `tests/e2e/test_render.py`, add `test_delete_asks_then_opens_the_hub_on_the_cell`
  (`ui:delete-render:the-dialog-opens-on-no`, `ui:delete-render:yes-opens-the-hub-on-the-cell`) on `DELETED`'s
  `v1/7` address: `⇧⌫`, `l`, `h`, `Esc`, then `⇧⌫`, `l`, `↵`; the Hub cell focused, `approved`, `group_of(…, 1)` gone.
  Verify: `uv run pytest tests/e2e/test_render.py --collect-only -q` prints `tests/e2e/test_render.py::test_delete_asks_then_opens_the_hub_on_the_cell`.

## 5 — The record

- [x] 5.1 In `docs/decisions.md`, amend D25 per [the record](design.md#the-record): the rule's clause, the *Why*
  sentence and `` `0106` `` in `Made by:`.
  Verify: `grep -n '⇧⌫' docs/decisions.md` prints one line.
- [x] 5.2 In `docs/principles.md`, add [the record](design.md#the-record)'s sentence to the *Known breaks* of *The run
  directory is the only channel between stages, and a run's only state*.
  Verify: `grep -n 'discard_render' docs/principles.md` prints one line.
- [x] 5.3 In `docs/data-flow.md`, add the `isekai discard` paragraph and edit the UI's writers, per
  [the record](design.md#the-record).
  Verify: `grep -n 'isekai discard <image.png>' docs/data-flow.md` prints one line.
- [x] 5.4 In `README.md`'s block holding `isekai draft --flow`, add [the record](design.md#the-record)'s `discard` line.
  Verify: `grep -n '# delete one render' README.md` prints one line.
- [x] 5.5 In `isekai/pipeline/README.md`, edit the verbs line and the `generate.py` row per
  [the record](design.md#the-record).
  Verify: `grep -n 'and discards one render' isekai/pipeline/README.md` prints one line.
- [x] 5.6 In `isekai/interface/README.md`'s file table, edit the `ui/app.py`, `cli.py` and `ui/__init__.py` rows per
  [the record](design.md#the-record), closing 0091·R3.
  Verify: `grep -n 'GET. and .DELETE …/{id}/files/{name}' isekai/interface/README.md` prints one line.
- [x] 5.7 In `isekai/interface/ui/README.md`, add [the record](design.md#the-record)'s *Delete* bullet after the
  *Render* bullet.
  Verify: `grep -n 'Delete\*\* on a large view' isekai/interface/ui/README.md` prints one line.
