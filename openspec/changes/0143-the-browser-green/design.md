# The browser green — design

The browser suite goes green again: the import test's fake, the render tests' refusals and the Hub after a delete. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

The guard in `tests/e2e/guard.py` fails a browser test on a page error, a console error that is not a failed load, any 5xx and any 4xx the test did not declare. It also fails a declared refusal no response answered. `tests/e2e/conftest.py` wires it on the browser context, and a test declares a refusal by appending a `Refused(status, path-prefix)` to the `refusals` fixture.

CI run `43448367157` named each test the guard failed. Each fault is read from the code at `HEAD`:

| test | what the guard saw | the cause |
|---|---|---|
| the import test's second step | a page error | `CONVERTING` in `tests/e2e/test_import.py` sends `files` alone; `ui/src/stores/live.ts` sets `jobs` from every snapshot and `ui/src/App.vue` reads `jobs.value.prepare` unguarded |
| the render dialog test and the drawer test | an undeclared 409 under `/api/c/<collection>/sessions/` | `isekai/interface/ui/jobs.py` publishes the session id when the job is taken; the render child opens the record later in `isekai/interface/render.py`; the drawer in `ui/src/stores/drawer.ts` reads once when shown; `isekai/interface/ui/library.py` refuses an id no record holds |
| the conjure test | an undeclared 409 under the deleted render's `/thumb` | `ui/src/views/RenderLarge.vue` pushes the Hub at once; `ui/src/stores/collection.ts` still holds the hub read before the delete; `ui/src/views/Hub.vue` draws it, then reloads |

```
before   Yes ──▶ delete ──▶ push Hub ──▶ Hub draws the old hub ──▶ GET thumb of the deleted render ──▶ 409 ──▶ reload
after    Yes ──▶ delete ──▶ reload the hub ──▶ push Hub ──▶ Hub draws the new hub
```

## Goals / Non-Goals

Goals:

- The import test, the render tests and the conjure test pass in CI with the guard unchanged.
- After *Yes*, the Hub is drawn from a hub read after the delete.

Non-Goals:

- No change to the guard, to `ui/src/stores/live.ts` or to `isekai/interface/ui/`.
- No requirement changes: one scenario is added under an existing requirement, as a patch may.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | the red run after the page-in-a-browser version is fixed by its own patch, `the-browser-green`, before the refactor's first version | a red run gets a patch at once; "hardened" needs CI green with the browser tests run | folding it into the refactor's first version |
| [D2](#d2) | the import test's faked snapshot is completed with `jobs` and `billing`; the page gains no default | the server's scenario says every snapshot carries both slots, so the fake was the fault | a default in `ui/src/stores/live.ts` or a guard in `ui/src/App.vue` |
| [D3](#d3) | the session record's refusals are declared in the render dialog test and the drawer test, one `sessions/` prefix per rendered collection | the refusal is its scenario's; the drawer draws from the slot until the record is written; no requirement demands the read be skipped | making the drawer skip the read; making the server publish the id after the record opens |
| [D4](#d4) | after *Yes* the large view reloads the hub, then opens it; a reload that fails opens it all the same; one scenario under the delete requirement says the Hub opens without the deleted render | the cell is where the delete shows, by the requirement; a declared 409 would fail whenever the reload answers first | declaring the 409 in the conjure test |
| [D5](#d5) | CI proves the change after the merge, as the version before it was proven; in the run, the collection and the bindings test | a build cannot start Chromium | a Chromium step before the merge |

### D1

The change is a patch: tests and one view, no format version, no verb or flag, no new requirement. It is cut with no `after`, and it is queued beside the tattoo fixes version, whose rework of the delete dialog meets this change in `ui/src/views/RenderLarge.vue`; integrate merges that one shared view.

### D2

`CONVERTING` in `tests/e2e/test_import.py` becomes a snapshot with both slots a server sends: `"jobs": {"prepare": null, "render": null}` and `"billing": {"pod": false, "volume": null}`. Those are the shapes `isekai/interface/ui/jobs.py` and `isekai/interface/ui/billing.py` give an idle server. `files` stays as it is.

### D3

`test_the_render_dialog_opens_on_its_first_photograph` renders `RENDER`, and `test_the_drawer_holds_the_render` renders `DRAWN` and then `WIDE`. Each takes the `refusals` fixture and appends `Refused(409, "/api/c/<collection>/sessions/")` for each collection it renders. The path is a prefix, so the session id stays out of the test.

### D4

`ui/src/views/RenderLarge.vue` takes the collection store, `useCollectionStore` from `ui/src/stores/collection.ts`, which `ui/src/App.vue` already opens on the route's collection. `deleted` becomes async: it awaits `store.reloadHub()`, ignores a refusal, and then pushes `hubCell`. `Hub.vue` reloads again as it mounts, which stays.

The scenario is `ui:delete-render:the-hub-opens-without-the-deleted-render`, `Layers: e2e`. The conjure test binds it and asserts that no request for the deleted render's thumbnail was sent after *Yes*. The guard holds the rest: an undeclared 4xx fails the test.

### D5

The sandbox has no Chromium. The build's checks are the collection of the browser suite and `tests/test_spec_bindings.py`. A red run after the merge is fixed by a patch at once.

## Tests

This change adds no test and removes none. It edits existing browser tests and adds a scenario key to the conjure test; the browser tests run on one engine, Chromium, as before.

| test file | what changes | layer | tests added | tests removed |
|---|---|---|---|---|
| `tests/e2e/test_import.py` | the faked snapshot carries `jobs` and `billing` | browser | none | none |
| `tests/e2e/test_render.py` | the render dialog test and the drawer test declare their refusals; the conjure test binds the new key and asserts on the requests it saw | browser | none | none |

The browser suite collects `22 tests`, the same before and after: `uv run pytest tests/e2e --collect-only -q`. The bindings test holds the new key: `uv run pytest tests/test_spec_bindings.py`.

The new end-to-end step extends `test_conjure_from_this_opens_review`, which already reaches the large view and its delete, so no new end-to-end test is added and no reason is owed. No test is deleted or merged, so there is no table of removed tests.

## Dependencies

None.

## Risks / Trade-offs

- **A declared refusal no response answered fails the test.** The drawer reads the session record once when shown, before the render child opens it. A machine fast enough for the record to exist first would fail the guard's *declared refusal never answered*. The read happens on the click that starts the job, and the child starts after it; the brief accepted this ([D3](#d3)). A red run after the merge names it, and a patch fixes it at once.
- **The browser tests are first run by CI.** A step written here is proven after the merge ([D5](#d5)).
- **`RenderLarge.vue` is shared with the tattoo fixes version.** The change is one function and one import, so the merge is small.
- **The reload waits for the server.** *Yes* opens the Hub after one more read of the hub; a slow read delays the Hub, and a failed one does not.
- **The dialog stays open while the hub is read.** `ui/src/components/DeleteDialog.vue` emits `deleted` and does not await its handler, so *Yes* can be pressed again before the Hub opens; the second delete is refused and the dialog shows it. The window is one read of the hub, accepted, and `DeleteDialog.vue` is not edited.

## Verdict

Ready to build, in the phases of [tasks](tasks.md): the fake and the refusals first, the Hub after a delete second.
