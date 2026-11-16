# The render routes — design

The render and jobs routes and the events stream become resource classes over the `Surface`, each registered from a table; no route's path, body or answer changes. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

`create_app` in `isekai/interface/ui/app.py` declares the prepare route, a job's stop, the render's offer, quote and `POST`, the session reads, the billing check and the events stream. These closures serve them: `quoted`, `_held`, `short_of` and `bakes_in`. They read what `Surface` already holds: `root`, `flows`, `wired`, `wire`, `jobs`, `billing`, `imports`, `broadcast` and `folder`.

Module-level helpers serve them too: `cell_event`, `_quote`, `_quoted_row` and `_taken_out` are read by this group alone. `_strings`, `_whole`, `_hub` and `_cell_out` are read on both sides of the cut: `_strings` by assign and commit, `_whole` by `_numbered`, `_hub` by `read_hub`, `_cell_out` by `post_assign`.

The tests patch `Jobs`, `run`, `FileResponse`, `_precondition`, `save_draft`, `approve` and `_DRAFT_UPDATE` on `app.py`, and `tests/test_ui_jobs.py` imports `cell_event` from it and calls it. None of those names is read by these routes. `tests/record/routes.json` holds a status and a shape for some of the group, with no order; the prepare route, the render's `POST`, the session reads and the events stream are not in it, and stay out ([D5](#d5)).

## Goals / Non-Goals

Goals: the render and jobs routes and the events stream leave `create_app`; `app.py` keeps what a test patches; the gate's pins stay as they are.

Non-Goals: a route's text, a test's assertion, a ratchet row, a record entry, the routes that read a patched name, `Jobs(` and `run`.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | one class, `RenderRoutes`, in `routes/rendering.py`, holds the render and jobs routes and their closures as methods | the group shares `quoted`, `_held`, `short_of` and `bakes_in`; the module is named for what it does, since `interface/render.py` and `ui/jobs.py` are modules of the layer already | `routes/render.py` and `routes/jobs.py`: a name modules of the layer hold reads as either; a class a route |
| [D2](#d2) | the events stream is its own resource, `StreamRoutes`, in `routes/stream.py`, mounted with the others | the stream reads no closure of the group and returns a `StreamingResponse`; `events.py` is a module of `ui/` already, so the name differs | `read_events` as a method of `RenderRoutes`: a second job for the class |
| [D3](#d3) | a method reads the surface as `self.surface.<name>`; its body keeps its text but for that prefix and for `self.` before a sibling method | a method's body sits where a nested handler's did, so each mutant's text holds, as it did in the surface's move | local aliases of the surface's names: they change a line's text |
| [D4](#d4) | `cell_event`, `_quote`, `_quoted_row` and `_taken_out` move into `routes/rendering.py`; `_strings`, `_whole`, `_hub` and `_cell_out` move into `routes/common.py`; `app.py` imports the second four back and binds `cell_event` | the first four are read by this group alone; the second four by both sides; a test imports `cell_event` from `app.py` | `cell_event` left in `app.py`: the class would import `app.py`, a cycle the layer's guard turns red |
| [D5](#d5) | `Jobs(`, `Billing(`, `Imports(`, `run`, the middleware, the lifespan and the draft lock stay in `app.py`; nothing under `tests/record/`, no ratchet row and no entry of `tests/mutants.json` changes | tests patch `Jobs` and `run`, and `unread_patches` fails when `app.py` stops reading a patched name; a move adds no record entry | moving `Jobs(` into the surface: it strands the patch |
| [D6](#d6) | `create_app` calls `render_mount` and `stream_mount` after `place_mount` and before `no_route`, and each table lists its routes in `app.py`'s order | the catch-alls and the assets' mount stay last; no resource route depends on another's order | mounting before the first route: it changes the order of every route after it |
| [D7](#d7) | each moving phase is proved by `tools.mutate` over the lines it moves, before and on their new home; a survivor is killed by a test or named in [Equivalent mutants](#equivalent-mutants) | `CONTRIBUTING.md`'s rule: a change that moves lines of `isekai/` runs the pre-flight over them, before and after | a proof by the suite alone: the suite does not hold every line |
| [D8](#d8) | no new decision: [D59](../../../docs/decisions.md#d59--a-resource-is-a-class-registered-from-a-table-over-one-surface)'s *Accepts* line and *Made by* are amended | the rule D59 sets is unchanged; its exception shrinks | a decision a version: a rule restated |

### D1

`RenderRoutes(surface)` holds `self.surface`. Its handlers are `post_prepare`, `post_stop`, `read_render_offer`, `post_quote`, `post_render`, `running_sessions`, `read_session` and `post_check`; its helpers are `quoted`, `_held`, `short_of` and `bakes_in`. A helper keeps its signature, `quoted(names, without=None)` included. `ROUTES` lists the handlers in `app.py`'s order:

```
POST /api/c/{collection}/prepare      post_prepare
POST /api/jobs/{kind}/stop            post_stop
GET  /api/c/{collection}/render       read_render_offer
POST /api/render/quote                post_quote
POST /api/render                      post_render
GET  /api/sessions/running            running_sessions
GET  /api/c/{collection}/sessions/{name}   read_session
POST /api/billing/check               post_check
```

### D2

`StreamRoutes(surface)` holds `read_events(collection=None, staging=None)`, whose nested `snapshot` reads `self`. Its table has one row, `GET /events`. The return annotation stays `StreamingResponse`.

### D3

What a body reads, and what it reads it as:

| today's name | becomes |
|---|---|
| `root`, `flows`, `wired`, `wire`, `jobs`, `billing`, `imports`, `broadcast` | `self.surface.root`, and so on |
| `folder(` | `self.surface.folder(` |
| `quoted(`, `_held(`, `short_of(`, `bakes_in(` | `self.quoted(`, and so on |

Every other name a body reads is an import of its module: `library`, `render`, `plan`, `KINDS`, `keyed`, `load_flow`, `tracked_flows`, `approved_versions`, `edit_at`, `edit_image_of`, `events`, `Refusal`, `Run`, `StreamingResponse`.

### D4

| name | home | read by |
|---|---|---|
| `cell_event`, `_quote`, `_quoted_row`, `_taken_out` | `routes/rendering.py` | the prepare route and the quote; `app.py` binds `cell_event` |
| `_strings`, `_whole`, `_hub`, `_cell_out` | `routes/common.py` | both sides: `app.py` imports them by name beside `_dimensions` |

`app.py` binds `cell_event` as `from isekai.interface.ui.routes.rendering import cell_event as cell_event`, and each `mount` as `mount as render_mount` and `mount as stream_mount`, never a module of `routes/` whose name another import of `app.py` binds.

### D5

`Jobs(` stays in `create_app`; `surface.jobs` is the object it builds. The routes read `self.surface.jobs`, so a test that patches `Jobs` on `app.py` still decides what the routes call.

### D6

```
create_app
  ├─ vocabulary_mount · tattoo_mount · place_mount     (today)
  ├─ render_mount · stream_mount                       (new)
  └─ no_route · assets · page                          (last)
```

### D7

Phase 1 opens with the run over its ranges in `app.py`. Phase 2 opens with the tests' baseline, since no range of `app.py` holds once phase 1 has shifted it; both phases close with the run on the new module, which covers the same mutants. `tools.mutate` copies tracked files only, so `git add -N` names each new module before its closing run. The opening run's ranges are the cut's base's, so its sub-task is checked at `HEAD` by the section below; a closing run over a whole module outlasts the plan check's 600 seconds, so phase 1's is split by line range, and no range holds both of `cell_event`'s timeout mutants, each of which waits out the 300-second default; the range from the end of `read_render_offer` through `post_render` timed out once under the load of other runs, so it is two ranges of the same lines, 141-165 and 166-210. Phase 1's closing runs leave out `test_without_the_lock_an_update_writes_after_the_approval` with pytest's `-k`: it races two threads on `app.py`'s draft lock, the draft and quote tests kill every mutant of these ranges without it, and under the load of the runs side by side it failed the unmutated baseline, so no mutant was tried. The gate still runs it.

### D8

D59's *Accepts* line loses the render, jobs and events routes and keeps the rest; its *Made by* line gains `0148`. The page [docs/decisions.md](../../../docs/decisions.md) holds it, so a task edits that page ([tasks](tasks.md) 3.1).

## Where things go

```
app.py ──▶ routes/rendering.py ──▶ routes/common.py ──▶ ui/library.py
       ├─▶ routes/stream.py    ──▶ routes/common.py
       └─▶ routes/common.py        routes/table.py · surface.py · ui/jobs.py · interface/render.py
```

No module of `routes/` imports `app.py` or a name `isekai.interface.ui` itself defines; each imports a sibling as a module. FastAPI is reached through `app.py` alone, so the entry point's `-S` guard holds.

## Equivalent mutants

A survivor the build cannot kill with a test is named here, one row each: `path:line · mutant · why no test can tell it`. None at the cut.

| survivor | why equivalent |
|---|---|

## Tests

The change adds a test only to kill a survivor, through a route that binds an existing scenario of the `ui` spec, at the lowest layer that can fail; it deletes and merges none, so no `I16` table is owed. It adds no end-to-end run: the routes are held at the lowest layer that can fail, the server's own tests. `tests/record/` and `tests/mutants.json` are read by the gate and the replay, and edited by no task.

| measure | now | command |
|---|---|---|
| tests the routes' files hold | `test_ui_api.py` 102, `test_ui_jobs.py` 40, `test_ui_billing.py` 6, `test_ui.py` 18, `test_ui_wire.py` 2, `test_record.py` 15 | `git grep -c -E "^(async )?def test_" -- tests/test_ui_api.py tests/test_ui_jobs.py tests/test_ui_billing.py tests/test_ui.py tests/test_ui_wire.py tests/test_record.py` |
| end-to-end runs added | none | none planned |

## Dependencies

None.

## Risks / Trade-offs

- A method that reads a name today's closure got from `create_app` by luck, not through the surface, fails on its first request: the server's tests reach each route, and `tests/record.py` builds the app.
- The derived *Imported by* rows list each new module under every package it imports; versions cut from one `main` that each add such a module edit one line. The next such version is cut after this one releases.
- A mutation run over a moved span takes minutes; it is out of the gate.

## Verdict

Ready to build. Each route keeps its text, so the suite and the mutation runs are the proof.
