# Design — 0083 the multi-batch render

How one session renders many collections, and how the app quotes, starts and shows it. **Verdict: feasible** — each
`generate` line already carries its own `--runs`, and `_rendered` already runs every line on one pod; what changes is
who gathers the lines, where the records and the log go, and the app around them.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut, `main` at `f35f347` (`v0.55.0`):

- **The session:** `run_session` takes one `args.runs` (`isekai/interface/render.py:396`) and tees its log to
  `runs.parent / "log.txt"` (`:421–425`); `_session` (`:707`) builds the lines — each a `Line` (`:442`) carrying its
  `where` with `--runs` — estimates the limit (`_estimated`, `:540`) and opens one `Record` at `runs.parent / SESSIONS`
  (`:775`; `Record`, `:225–262`); `_rendered` runs every line on one pod, *one flow failing does not cost the next its
  render* (`:830`, `:863`). `short` and `quote` read one runs root (`:624`, `:671`).
- **The verb:** `render`'s positional `runs` and `requests` (`isekai/interface/cli.py:336–348`).
- **The record:** `SessionRecord` (`isekai/foundation/artifacts.py:371`), no field naming other collections.
- **The app:** `quoted(collection)` (`isekai/interface/ui/app.py:454`), `_held` (`:462`), the offer
  `read_render_offer` (`:476`), `post_quote` (`:491`), `post_render` (`:499–539`); `jobs.render` starts one collection's
  render (`isekai/interface/ui/jobs.py:270–300`) through `render_command(limit, runs, session)` (`:95`); the running
  scan reads every collection's records (`running_sessions`, `app.py:549`).
- **The page:** `RunningSession {collection, id, started}` (`ui/src/types.ts:251–255`); the drawer's store and grid
  (`ui/src/stores/drawer.ts`, `ui/src/sessions.ts:51–78`, `ui/src/components/SessionDrawer.vue`); the bar and the
  dialog (`ui/src/components/RenderBar.vue`, `ui/src/components/RenderDialog.vue`).
- **D36** accepts *ComfyUI's history and node cache hold the batch's photograph until the teardown. Reopen when a pod
  serves more than one batch* (`docs/decisions.md:483–484`).

| measured at the cut | value | command |
|---|---|---|
| tests in `tests/test_render.py` | 39 | `grep -c "def test_" tests/test_render.py` |
| tests in `tests/test_ui_api.py` | 76 | `grep -c "def test_" tests/test_ui_api.py` |
| tests in `tests/test_ui_jobs.py` | 25 | `grep -c "def test_" tests/test_ui_jobs.py` |
| vitest tests | 43 | `cat ui/src/*.test.ts ui/src/*/*.test.ts \| grep -cE "^(spec\|test\|it)\("` |
| e2e tests | 32 | `cat tests/e2e/test_*.py \| grep -c "def test_"` |

## Goals / Non-Goals

**Goals:** every collection short of images rendered on one pod, one quote. **Non-Goals:** explicit requests across
collections; a change to gpunit or a flow.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | **the verb:** `render`'s positionals are one list, each a directory or a `<flow>=<count\|source>` request; several directories are rendered in one session in the order named, shortfall mode alone; a request beside a second directory is refused before anything is rented; `_session` gathers each collection's `short` lines, collection after collection | the app's mode is the shortfall; one boot serves all | a `--collection` flag |
| [D2](#d2) | **the limit:** one boot and one teardown plus every collection's images, each priced from its own collection's recent durations (`recent`) | as the estimate is, summed | a boot per collection |
| [D3](#d3) | **the records:** `Records` opens a `Record` per collection, all with the session's id, each with its own `asked`, `planned` and `images`, the shared `steps` and outcome written to all; `SessionRecord` gains optional `collections` naming the others and `collection_order` naming the complete traversal, including the record's own collection; a line's images go to its collection's record; the tee writes to every collection's `log.txt` | a record stays its collection's file beside its log; the running scan finds every one; D32 | one library-level record |
| [D4](#d4) | **the quote:** `render.quote(runs_roots, wired)`; the API's `POST /api/render/quote {collections}` and `POST /api/render {collections, limit_s, images, keep_open}` replace the per-collection quote and start; `GET /api/c/{collection}/render` gains `others`, the images other collections lack; `jobs.render` takes the collections, `render_command(limit, runs_roots, session)` | one quote over what is ticked | a quote per collection |
| [D5](#d5) | **the dialog:** a row per collection short of images, the Library's order, each ticked; unticking quotes the rest again; an estimate past `gpunit.toml`'s ceiling disables the confirmation — *the estimate passes the ceiling; untick a collection*; the bar reads its count and `+n in other collections`, shown while any collection is short | the operator agrees to one price for all | a part render |
| [D6](#d6) | **the drawer:** the live store groups running records by id, using `collection_order` for the grids and retaining scan order for older records without it; the drawer's `shown` is `{id, collections}` and reads each record; `sessions.ts` gains `stacked(grids)` and its move — `j` `↓` from a grid's last row to the next grid's first row, `k` `↑` back, the column kept, held at a shorter row's end; each grid headed by its collection; `⇧I` the focused image's collection's Renders | the operator walks one batch | a drawer per collection |
| [D7](#d7) | **D36:** its *Accepts* line becomes *ComfyUI's history and node cache hold every photograph the session renders, from every collection, until the teardown*, its *Reopen* clause deleted; *Made by* gains `0083` | one self-hosted operator; D35 bounds the pod's memory for every collection alike | clearing history between collections |

`collection_order` includes the record's own collection because a list of the others cannot locate its own
position. It is optional under D32, leaving the meaning of `collections` and older records intact; the running
API carries the metadata from disk to the live store without depending on a job slot.

## Tests

| layer | added | edited | where |
|---|---|---|---|
| unit · pytest | `cli:render-short:many-collections-render-in-one-session`; `cli:render-limit:one-boot-for-many-collections`; `cli:render-session:each-collection-holds-its-record`; `ui:render:the-dialog-quotes-every-collection`; `ui:render:past-the-ceiling-disables-render` | the quote and start tests to `/api/render/quote` and `/api/render`; the jobs tests to `jobs.render`'s collections; the terminal-session test checks complete traversal metadata through disk and the record test checks it in every file | `tests/test_render.py`, `tests/test_ui_api.py`, `tests/test_ui_jobs.py` |
| unit · vitest | `ui:sessions:the-grids-stack-by-collection` | the drawer's and the live store's tests to `shown`'s collections; the terminal-session test proves reverse-name traversal in the live store | `ui/src/sessions.test.ts`, `ui/src/stores/drawer.test.ts`, `ui/src/stores/live.test.ts` |
| e2e | none | the dialog's row for its collection in `test_confirming_the_dialog_opens_the_session` and `test_the_drawer_holds_the_render` | `tests/e2e/test_render.py` |

**End-to-end runs added:** none — the stacking is a move between grids, a unit's (T1); the e2e batches stay one
collection each.

**Removed or merged:** none.

## Dependencies

None.

## Risks / Trade-offs

- **[Risk]** two quotes of the same collections reading different shortfalls → the start takes the quote again and
  refuses a longer limit or another image total, as today.
- **[Trade-off]** a failed collection does not stop the next → the outcome reads `failed`, naming it, as a failed flow
  does.

## Verdict

**Feasible.** The lines already carry their runs root; the session gathers more of them.
