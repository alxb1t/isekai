# The review routes — design

The review's routes become one resource class over the surface, moved whole with the helpers only they read. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

`create_app` declares the review's routes as closures. Since the seams moved, each reads the draft lock, `save_draft`, `approve`, the precondition and the file response from the `Surface`, and none reads a name a test patches on `app.py`. [D59](../../../docs/decisions.md#d59--a-resource-is-a-class-registered-from-a-table-over-one-surface) says a resource is a class registered from a table.

```
before                                    after
app.py  create_app                        app.py  create_app
          closures: library, staging,                closures: library, staging,
          review, images, sources                    images, sources
          mount: vocabulary, tattoos,                mount: vocabulary, tattoos,
          place, render, stream                      place, render, stream, review
        module helpers (review's, shared) routes/reviewing.py  ReviewRoutes + its helpers
                                          routes/common.py     + what two sides read
```

```
app.py ──▶ routes/reviewing.py ──▶ routes/common.py ──▶ ui/library.py
       │                          └─▶ routes/table.py · surface.py · interface/drafting.py
       └─▶ routes/common.py  (what the closures left in app.py still read)
```

No module of `routes/` imports `app.py` or a name `isekai.interface.ui` itself defines. FastAPI is reached through `app.py` alone.

## Goals / Non-Goals

- Goal: the review's routes and the helpers only they read leave `app.py`; every URL, status, body and message stays.
- Goal: `app.py` still binds each name a test imports or patches: `Held`, `RARE_BELOW`, `authorities`, `cell_event`, `create_app`, `_precondition` and `run`.
- Non-goal: a route of the images, library, staging or sources; a ratchet row but the file's own ([D9](#d9)); an assertion; a record entry.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | a class, `ReviewRoutes`, in `routes/reviewing.py`, holds the review's routes as methods | the routes share their helpers and their URL prefix; `app.py` binds `review` and `state as review_state` from the pipeline, so the module is named for what it does, as `rendering.py` is | `routes/review.py`: a name the pipeline's `review.py` already holds; a class for reads and one for writes |
| [D2](#d2) | the reads move first, the writes second, the documents last | the reads share their helpers with the images' routes and read one seam; the writes hold the lock and `post_draft`, the largest closure; a halt costs one of them | one phase for every route: a halt costs the whole |
| [D3](#d3) | a helper only the review reads moves into `reviewing.py`; a helper a closure left in `app.py` also reads, and `REFUSED`, move into `routes/common.py`; `app.py` imports each back by name | a router imports no `app.py`, so what both sides read cannot stay there; the closures and `_precondition` keep their names | a copy in each module: a second spelling that drifts |
| [D4](#d4) | each handler keeps its text, but a closure name it read becomes a read of `self.surface` | the surface already holds `held`, `folder`, `offered`, `shared`, `flows`, the seams and `rendering`; the text of `PB-2c`'s anchor then holds | locals bound in `__init__`: a second set of names |
| [D5](#d5) | `post_draft` is annotated `-> object` and no row carries a response model | `register` adds a route with no `response_model`, and FastAPI refuses a return annotation that unions a dict with a response class; `-> Any` fails ruff's `ANN401` | a response model on `Route`: an edit of the table, not a move |
| [D6](#d6) | `ReviewRoutes` is mounted by `review_mount(app, surface)` after `stream_mount`, its table in `app.py`'s order, before the catch-alls | no resource's routes depend on another's order; the catch-alls and the assets' mount come last | mounting before the vocabulary: a move of the others' order |
| [D7](#d7) | the pre-flight of both moving phases runs once, in phase 1, over the base's ranges; each moving phase closes with `tools.mutate` on the new module in runs of about a hundred lines, the lock's race test left out | a move shifts `app.py`, so the writes' base ranges hold only before the reads move; one run over a whole module times out | a range of the base in a later phase: it holds other lines |
| [D8](#d8) | `PB-2c` takes the new path with its text unchanged, `UA-7` is re-anchored on the import block as it ends, and the replay proves each dies | an entry is addressed by path and exact text, and a path is an address, not an assertion | a new entry: no finding is closed here |
| [D9](#d9) | the file's ratchet row of `app.py` and the table's count go in the writes' phase | `app.py` falls under its ceiling there, and the ratchet reads a row whose offender no longer offends as red | the documents' phase: the writes' phase would end red |

### D1

`ReviewRoutes(surface)` holds `self.surface`. Its handlers are `read_input`, `read_photo`, `read_source_copy`, `put_draft`, `post_approve`, `post_cancel`, `post_discard` and `post_draft`, listed in `ROUTES` in `app.py`'s order, with `mount(app, surface)` as the other resources have it. A handler keeps its parameters, its annotations but for [D5](#d5), its docstring and its comments.

### D2

Phase 1 holds `read_input`, `read_photo` and `read_source_copy` and every helper they call. Phase 2 holds `put_draft`, `post_approve`, `post_cancel`, `post_discard`, `post_draft` and the helpers only they call. Each phase ends with the app built from the table and the closures it left, so every test of the server proves the join.

### D3

| helper | home | read by |
|---|---|---|
| `_revision`, `_drafted`, `_prose`, `_wd14`, `_tags`, `_command`, `_remedy`, `_flow_of`, `_budget` | `routes/reviewing.py`, phase 1 | `read_input`; `put_draft` reads `_command` and `_budget` |
| `_update`, `_renders_in`, `_images`, `_image_out`, `_numbered` | `routes/reviewing.py`, phase 2 | `put_draft` and `post_draft` |
| `_approved`, `_fields`, `_untagged`, `_decimal`, `_renders_out`, `_saved`, `_photograph` | `routes/common.py`, phase 1 | `read_render`, `_side`, `read_staged`, `read_source` and `_precondition` of `app.py`, and the review |
| `REFUSED` | `routes/common.py`, phase 2 | `_refused` of `app.py` and `post_draft` |

`app.py` imports `_approved`, `_decimal`, `_photograph`, `_renders_out`, `_saved` and `_untagged` back in phase 1, and `_budget` and `_command` from `reviewing.py`, until phase 2 moves their last readers, `_update` and `put_draft`; phase 2 adds `REFUSED` to the names it imports back and drops `_untagged`, `_budget` and `_command`. `_images_out`, `_filled` and `_side` stay in `app.py`: only the images' routes read them.

### D4

A closure name becomes a read of the surface: `held` → `self.surface.held`, `folder` → `self.surface.folder`, `offered` → `self.surface.offered`, `shared` → `self.surface.shared`, `flows` → `self.surface.flows`, `_rendering` → `self.surface.rendering`, and `surface.x` → `self.surface.x`. `post_draft` keeps its loop variable `held`, which shadows nothing in a method. Nothing else in a body changes, so `PB-2c`'s anchor, `                definition=one.flow,`, stands at the same indent.

### D5

`app.add_api_route` runs FastAPI's return-annotation check, and a union of `dict[str, Any]` and `JSONResponse` is no response field: the route was declared with `response_model=None` for that. A method annotated `-> object` is served as the dict or the response it returns, as before, and a probe of FastAPI with the repository's pins showed the union refused and `object` answering both. A wrong row or annotation fails when the app is built, in every test of the server.

### D6

The table is `Route` rows in the order `app.py` declares the routes today. `register` reads each handler off the instance, as for the render routes. The review's paths share no segment with a route declared after them that a path parameter could swallow.

### D7

The opening runs are these, each over about a hundred lines of the base, on the tests that reach the review routes. They leave out `test_without_the_lock_an_update_writes_after_the_approval`: that test is a race that fails beside other runs and passes alone, and the gate still runs it.

```
A  uv run python -m tools.mutate isekai/interface/ui/app.py:484-582 --tests T
B  uv run python -m tools.mutate isekai/interface/ui/app.py:972-1031 isekai/interface/ui/app.py:1099-1101 isekai/interface/ui/app.py:1112-1134 --tests T
C  uv run python -m tools.mutate isekai/interface/ui/app.py:1137-1235 --tests T
D  uv run python -m tools.mutate isekai/interface/ui/app.py:1238-1263 isekai/interface/ui/app.py:1266-1291 --tests T
E  uv run python -m tools.mutate isekai/interface/ui/app.py:584-668 --tests T
F  uv run python -m tools.mutate isekai/interface/ui/app.py:669-750 isekai/interface/ui/app.py:1056-1088 isekai/interface/ui/app.py:1104-1109 --tests T

T = tests/test_ui_api.py tests/test_record.py tests/test_ui_wire.py "-k not test_without_the_lock_an_update_writes_after_the_approval"
```

A, B, C and D hold the reads' lines and the helpers they call, E and F the writes' lines and theirs; the ranges are the lines of the cut's base, which the first move shifts. The closing runs are one per range of the new module, each holding at most one mutant that times out. A survivor is killed by a case added to an existing test through a route that binds a scenario, and named below only when no such case can tell it from the code, with the reason.

### D8

`PB-2c` anchors on the approve route's `definition=one.flow,` and changes only its `path` to `isekai/interface/ui/routes/reviewing.py`. `UA-7` anchors on the tail of the artifacts import block of `app.py`, which the pruned imports rewrite to the one name `renders_of`; its `find` and `replace` are written against the import as it ends, and the replay shows it killed by `tests/test_ui.py`.

### D9

After the writes move, `app.py` holds fewer lines than `LONG_FILES`'s ceiling, so its row in `tests/test_ratchets.py` is red until removed, and `FILE_ROWS` is lowered with it. `create_app`'s row, `read_compare`'s row and the patch row of `app.py` stay: the closures of the front door still hold them. A table's row and its count are the test's data, not an assertion.

## Tests

The change adds no test and removes none: `git diff --name-only main -- tests` lists `tests/mutants.json` and `tests/test_ratchets.py` alone, unless a pre-flight survivor needs one case, added to an existing test that reaches the same state and carrying the scenario it already binds. No end-to-end run is added: `git diff --name-only main -- tests/e2e` prints nothing. The proof is the suite as it stands: `tests/test_ui_api.py` builds the app and calls each review route, `tests/test_record.py` pins the recorded routes' shapes, `tests/test_ui_wire.py` the key tuples, `tests/test_ratchets.py` the sizes and patches, `tests/test_layers.py` the imports, `tests/test_docs.py` the derived tables, `tests/test_pipeline_cli.py` the entry point's imports and `tests/test_ui.py` the surface's tripwire.

### Equivalent mutants

Pre-flight at the base: not run.

Closing runs: not run.

## Dependencies

None.

## Risks / Trade-offs

- A handler's text is meant to move unchanged, so a missed `self.surface.` read is a `NameError` that every route test of the server raises at once.
- The import pruning can drop a name a test imports from `app.py`; `Held`, `RARE_BELOW`, `authorities`, `cell_event`, `create_app` and `_precondition` stay bound, and the tests of the server fail on import otherwise.
- The race test is left out of the mutation runs, so a mutant only it kills is named below; the gate still runs it.
- `read_photo` and `read_source_copy` call `_photograph` from `routes/common.py`, which imports `Response` from FastAPI: the module is reached through `app.py` alone, as the other routers are.

## Verdict

The move changes no behaviour and no requirement, and each phase ends on the suite as it stands. Ready to build.
