# Design — 0106 deleting a render

One pipeline function deletes a render's files, one library function its thumbnails; the verb and the route call
both, and the large view asks before the route runs. **Verdict: feasible.**

## Context

A render is its files in `runs/<id>/<flow>/outputs/<NNN>/`: the image `<seed><suffix>` and `<seed>.render.json`
(`isekai/pipeline/generate.py:663-690`, the record written first). No index holds them: every reader lists the
directory (`generate.py:312-375`). `rendered_at(image)` (`isekai/foundation/run.py:527-556`) already reads the run,
flow, approval and seed from an image's path, and refuses one that names no render.

The thumbnail is `<library>/.cache/<run digest>/<flow>/outputs/<NNN>/<seed>.<image digest>.jpg`, made by
`library.thumbnail` (`isekai/interface/ui/library.py:459-472`) and never swept. A collection's runs root is
`<library>/<collection>/runs` (`library.py:3-13`).

The layer rules shape where the code goes (`tests/test_layers.py`): imports point down (`:18-19`), so
`pipeline/generate.py` cannot reach `interface/ui/library.py`; and a sub-package is reached through its front door
(`:182-195`), so `interface/cli.py` reaches `ui/library.py` only through `ui/__init__.py`, as `_migrate` reaches
`collection_runs` (`cli.py:484-507`).

The route's neighbours: `post_cancel` refuses under `_DRAFT_UPDATE` while `_rendering(collection)` answers
(`isekai/interface/ui/app.py:840-865`); `rendered()` resolves a render's address to its run, image and approval
(`app.py:983-998`). The large view is `ui/src/views/RenderLarge.vue`; its keys are `:101-124`, its buttons `:162-188`,
its dialogs `:196-210`. `ThemeDialog.vue` is the yes-or-no modal pattern: `useHeldFocus`, `showModal()`, an
`overlay` key layer. The Hub restores its focus from `store.focus.hub` in `onMounted` (`ui/src/views/Hub.vue:424-437`).

## Goals / Non-Goals

**Goals:**
- One function owns each deletion: the render stage its run files, the library its cache (D4 in force).
- The verb and the page delete the same files, in the same order.

**Non-Goals:**
- A seed check or a refusal for what was made from the image ([D7](#d7)).
- Removing an emptied `.cache/` directory: the cache is rebuildable, and an empty folder holds no likeness.
- Refusing the verb while a session renders: the terminal's operator sees the session; the page's does not.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | `discard_render(image: Path) -> list[Path]` in `generate.py`, after `render_groups`: `rendered_at(image)` refuses a path naming no render; then, on `image.absolute()`, it unlinks the image, then `<seed>.render.json` when there, then `rmdir`s the group when `not any(group.iterdir())`; it returns the deleted paths, absolute, in that order | Q1: no trash. The image first: a discard cut short leaves a record alone, which reads as unrendered (`generate.py:663-665`). An empty group is listed as derived (`isekai/pipeline/review.py:674-679`); the approval's prompt is too, so *Cancel approve* stays refused after the last render goes, as Q3 leaves what was made alone. Absolute paths, because `rendered_at` reads `run.path` from `image.absolute()` (`run.py:533-536`) | a trash folder: a folder in a run reads as a flow (`run.py:311-325`); the name `discard`: `cli.py:43` and `app.py` import review's |
| <a id="d2"></a>**D2** | `drop_thumbnails(run: Run, image: Path) -> list[Path]` in `library.py`: when `run.path.parent.name == RUNS` and `is_collection(run.path.parent.parent)`, it unlinks each `<seed>.*.jpg` in `run.path.parents[2] / CACHE / run.digest / image.absolute().parent.relative_to(run.path.absolute())`, sorted, and returns them; else `[]`. `ui/__init__.py` gains `drop_thumbnails(run, image)`, calling it, for the CLI | Q1. A glob on the seed finds every thumbnail of the image's place after the image is gone. The library is read from the run's own path, so the verb and the route find one cache. The layers forbid `generate.py` the cache | the thumbnail in `discard_render`: an upward import; `ISEKAI_LIBRARY` in the verb: a run in another library would keep its thumbnail |
| <a id="d3"></a>**D3** | The `discard` verb, per [the verb](#the-verb): one positional `image`; `_discard(image, wired)` prints `refused: <image>: <reason>` and returns 1 on a refusal; else it calls `discard_render`, then `drop_thumbnails` imported inside the function, and prints `discard deleted <path>` per path — a run's file relative to `run.path.parent`, a thumbnail relative to `run.path.parents[2]` — and returns 0 | Q5, D3 in force. One image is what the button deletes. The import inside the function keeps `ui/` off `python -m isekai`'s graph (`tests/test_pipeline_cli.py:211-219`) | many images, as `draft`: nobody asked for a batch delete |
| <a id="d4"></a>**D4** | `@app.delete("/api/c/{collection}/renders/{digest}/{flow}/{version}/{seed}")`, `delete_render`: `rendered()` first; under `_DRAFT_UPDATE`, `_rendering(collection)` refuses with `f"{rendering} Wait for it to end, then delete the render again."`; then `discard_render(image)` and `library.drop_thumbnails(run, image)`; it answers `{"deleted": True}`. `app.py`'s route list gains its line | Q4, Q5. The render's own address, so the page names no file; the lock and refusal are `post_cancel`'s, so a delete and a cancel cannot cross. A `Refusal` answers 409, as every route's does | `POST …/discard`: the address already names the one render |
| <a id="d5"></a>**D5** | The page, per [the page](#the-page): `deleteRender(place)` in `api.ts`; `Backspace: '⌫'` in `GLYPHS`; `DeleteDialog.vue`, new; in `RenderLarge.vue` a `delete` command on `[shifted('Backspace')]` and a *Delete* button after *Compare with…*, before the way back | Q4. `⇧⌫` keeps D25's "a command takes ⇧"; the glyph makes the hint read `⇧⌫`, and ImportSheet's `remove-file` hint `⌫`, as `ui/spec.md` names it | a plain `⌫`: one key alone would delete; the inline ask of `ApproveBar.vue:72-76`: no keys, and Q4 settled a modal |
| <a id="d6"></a>**D6** | Yes pushes `{ name: 'hub', params: { collection }, state: { cell: { digest, flow } } }`. `Hub.vue`'s `onMounted` focuses the spot whose source's `digest` and flow match `window.history.state?.cell`, else `kept(spots, named, store.focus.hub)` | Q4: the Hub on the cell from either screen. The view knows the digest, not the source's name `store.focus.hub` keys on | `store.focus.hub`: from Renders it names another cell, or none |
| <a id="d7"></a>**D7** | No seed logic and no refusal for a draft or approval made from the image | Q2, Q3, the person: "keep it simple — just delete this render". A short approval is offered again by the next quote; Review shows a missing image as any lost file (`app.py:1264`, `:1300-1301`) | refusing a listed seed: the person declined it; a refusal for what derives: the same |
| <a id="d8"></a>**D8** | The record, per [the record](#the-record): D25 amended in `docs/decisions.md`, its `Made by:` gaining `` `0106` ``; principles' *Known breaks* names `discard_render`; `docs/data-flow.md`, `README.md`, `isekai/pipeline/README.md`, `isekai/interface/README.md` (with 0091·R3) and `isekai/interface/ui/README.md` | A7: a decision in force is edited where it lives. A README states what holds once the code does, so the docs close the change | each doc in its code's phase: phases 1–4 would each touch five docs |

### The verb

```
isekai discard <image>
  │ rendered_at(image) ── refuses ──▶ refused: <image>: is not an image a render wrote; …   exit 1
  ▼
discard_render(image)   ─▶ discard deleted <run>/<flow>/outputs/001/42.png
                          discard deleted <run>/<flow>/outputs/001/42.render.json
drop_thumbnails(run, image) ─▶ discard deleted .cache/<digest>/<flow>/outputs/001/42.<sha>.jpg   exit 0
```

`cli.py` edits, beside `draft`'s:

| place | before → after |
|---|---|
| module docstring, after the `draft` line | + `    discard   (4) a render's image, its record and its thumbnails deleted` |
| `VERBS`, after `("draft", …)` | + `("discard", "delete a render: its image, its record and its thumbnails"),` |
| the loop adding `photos` and `--runs` (`cli.py:230-234`) | `("compare", "draft", "import", …)` → `("compare", "discard", "draft", "import", …)` |
| after `made["draft"].set_defaults(…)` | `made["discard"].add_argument("image", type=Path, help="the render, <run>/<flow>/outputs/<NNN>/<seed>.png")`, then `made["discard"].set_defaults(photos=[], runs=RUNS_ROOT)` |
| `dispatch`, after the `draft` branch | `if verb == "discard": return _discard(args.image, wired)` |

### The page

`DeleteDialog.vue` takes `place: RenderPlace` and emits `close` and `deleted`, built on `ThemeDialog.vue`'s pattern:

- `<dialog ref="dialog" class="render-dialog" aria-label="Delete this render?" data-delete-dialog @cancel.prevent>`,
  its head `<h2 class="render-dialog__title">Delete this render?</h2>`.
- A refusal line `<p v-if="refusal" class="renders__refusal" data-delete-refusal>` under the head.
- In `render-dialog__actions`: `No<KeyHint command="cancel" />` (`data-delete-no`), then `Yes` (`data-delete-yes`),
  both `btn btn-secondary` and `data-delete-choice`.
- `useHeldFocus(dialog, () => emit('close'))`; `onMounted` calls `showModal()` and focuses *No*.
- `useKeys('overlay', …)`: `cancel` on `Escape` closes; `previous` on `KeyH`, `ArrowLeft` focuses *No*; `next` on
  `KeyL`, `ArrowRight` focuses *Yes*; `press` on `Enter` clicks the focused choice, `when` one has the focus.
- *Yes* awaits `deleteRender(place)`, then emits `deleted`; a refusal fills the line and focuses *No*.

`RenderLarge.vue`: `const deleting = ref(false)`; the command `{ id: 'delete', keys: [shifted('Backspace')], label:
'delete this render', run: () => (deleting.value = true), when: () => detail.value !== null }`; a `large__group`
holding `<button class="btn btn-secondary" type="button" data-delete @click="deleting = true">Delete<KeyHint
command="delete" /></button>`; `<DeleteDialog v-if="deleting" :place="place" @close="deleting = false"
@deleted="deleted" />`, `deleted()` pushing the Hub per [D6](#d6).

### The record

| file | before → after |
|---|---|
| `docs/decisions.md` D25 | "a command is `⇧` + a letter," → "a command is `⇧` + a letter, or `⇧⌫`, the large view's Delete, which asks first,"; a *Why* sentence: "`⌫` is the key a delete is pressed on, and the dialog's *No* first keeps it two keys and a choice."; `Made by:` + `` `0106` `` |
| `docs/principles.md` *Known breaks* | + "`pipeline/generate.py`'s `discard_render` deletes a render's image and record, and the outputs group it empties, when the operator discards that render: a render is a likeness, so it leaves the run rather than being hidden." |
| `docs/data-flow.md`, after the paragraph on `isekai draft --flow` | + "**`isekai discard <image.png>`** deletes one render: its image, its record, its group when emptied, and its thumbnails in the library's cache. The newest approval it leaves short renders what it lacks at the next session." |
| `docs/data-flow.md`, the UI's writers | "review's for a draft, its edits and an approval," → "review's for a draft, its edits and an approval, the render stage's and the library's for a deleted render," |
| `README.md`, the `draft` block | + `python -m isekai discard .data/runs/<run>/summon-anime-wai/outputs/001/1840266731.png   # delete one render` |
| `isekai/pipeline/README.md` | the verbs line gains `` · `discard` `` after `` `draft` ``; the `generate.py` row: "then renders each against an endpoint" → "then renders each against an endpoint, and discards one render" |
| `isekai/interface/README.md` `ui/app.py` row | "`…/renders/{digest}/{flow}/{version}/{seed}` and its" → "`…/renders/{digest}/{flow}/{version}/{seed}`, its `DELETE`, and its"; "`PUT …/{id}/files/{name}` and its `/thumb`" → "`PUT`, `GET` and `DELETE …/{id}/files/{name}` and its `/thumb`" (0091·R3) |
| `isekai/interface/README.md`, the `cli.py` row of the file table | + "; `discard` deletes a render and its thumbnails" |
| `isekai/interface/README.md`, the `ui/__init__.py` row of the file table | + ", and `drop_thumbnails` for the `discard` verb" |
| `isekai/interface/ui/README.md` | + a bullet: "**Delete** on a large view, `⇧⌫`, asks first; Yes is `DELETE …/renders/{digest}/{flow}/{version}/{seed}`, refused while a render runs for the collection, then the Hub opens on the cell." |

## Tests

Every new test is a unit test but the one end-to-end test the page needs (`T1`). The vitest suite gains a step, not a
test.

| layer | adds | removes |
|---|---|---|
| unit | `tests/test_generate.py`: the `image-generation:discard:*` keys, a test each but the short approval, held beside the delete; `tests/test_ui_library.py`: `drop_thumbnails`; `tests/test_pipeline_cli.py`: the `cli:discard:*` keys, and a `[discard]` row of `test_each_verb_is_reachable_as_a_subcommand`; `tests/test_ui_api.py`: the route's unit keys; `ui/src/stores/keys.test.ts`: a `⇧⌫` step in `ui:keys:hints-come-from-the-declarations` | none |
| end-to-end | `tests/e2e/test_render.py`: `test_delete_asks_then_opens_the_hub_on_the_cell`, the `ui:delete-render` e2e keys, on Chromium alone | none |

The new end-to-end test is new because it deletes: a step in `test_a_rendered_cell_opens_its_newest_image` would empty
`SHOWN`, which the routes test needs rendered (`T2`). It gets its own collection, `DELETED`, as `DISCARDED` is the
discard's. Its keys run in one flow, the dialog then the delete (`T3`). Client behaviour, so it runs on every
engine the suite has: Chromium (`T4`).

Counted with `uv run pytest <file> --collect-only -q | tail -1` at `a4bbbaa3`, and as planned:

| file | at `a4bbbaa3` | planned |
|---|---|---|
| `tests/test_generate.py` | 106 | 109 |
| `tests/test_ui_library.py` | 24 | 25 |
| `tests/test_pipeline_cli.py` | 61 | 64 |
| `tests/test_ui_api.py` | 95 | 97 |
| the suite, `uv run pytest --ignore=tests/e2e --collect-only -q` | 1487 | 1496 |
| `tests/e2e`, `uv run pytest tests/e2e --collect-only -q` | 19 | 20 |

No test is deleted or merged (`I16`). `EXPECTED_VERBS` (`tests/test_pipeline_cli.py:59-74`) gains `"discard"` after
`"draft"`, as `VERBS` does.

## Dependencies

None.

## Risks / Trade-offs

- [A discard while the verb's own session renders that seed] → the terminal's operator started the session; the page,
  which cannot see a terminal, is refused ([D4](#d4)).
- [*Cancel approve* stays refused once an approval's last render goes: its prompt is derived too (`review.py:674-679`)]
  → Q3 leaves what was made alone; the approval is rendered again, or stays approved.
- [A seed listed in `renders.seeds` renders the same graph again] → Q2 accepted it: the graph, not the pixels, is what a
  seed reproduces (D13), so the re-render may differ.
- [`DELETED`'s approval is short after its test] → the e2e fixture is per session; no other test reads `DELETED`, and a
  quote names the collections it covers.
- [A glob on `<seed>.*.jpg` in a run's cache folder] → the folder is one approval's group of one run, so it holds that
  group's thumbnails alone, and a seed's stem is digits, so `42.*` never matches `420.…`.

## Moved since the brief

The brief cites `2c379d2a`; the plan reads `a4bbbaa3`, after `0105` was released. These moved, and the plan carries
the value at `a4bbbaa3`:

- `openspec/specs/ui/spec.md`: *Every command has one key…* is `:1273-1399`, *A dialog holds the focus…* `:1400-1426`;
  their text is unchanged.
- `tests/e2e/test_render.py`: `test_a_rendered_cell_opens_its_newest_image` is `:241-285`.
- `ui/src/components/ImportSheet.vue`: the `remove-file` command's `plain('Backspace')` is `:398`.

## Verdict

**Feasible.** Every premise behind Q1–Q6 holds at `a4bbbaa3`. The brief's phase 1 put the thumbnail in `generate.py`;
the layers put it in `library.py` beside it ([D2](#d2)), which leaves Q1 and Q5 as settled.
