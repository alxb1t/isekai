# The front door — design

The images', library's, staging's and sources' routes become resource classes over the surface, moved whole with the helpers only they read, and `create_app` falls under the function ceiling. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

`create_app` declares the images', library's, staging's and sources' routes as closures. Since the seams moved, each reads the file response from the `Surface`, and none reads a name a test patches on `app.py`. [D59](../../../docs/decisions.md#d59--a-resource-is-a-class-registered-from-a-table-over-one-surface) says a resource is a class registered from a table.

```
before                                     after
app.py  create_app                         app.py  create_app
          closures: library, staging,                mounts: hub, staging, images,
          images, sources                            sources, vocabulary, tattoos,
          mounts: vocabulary, tattoos,               place, render, stream, review
          place, render, stream, review              the guard · the refusal handler
          the guard · the refusal handler            _bundle: the catch-alls
          the catch-alls                    routes/images.py   ImageRoutes + its helpers
        module helpers (images')            routes/hub.py      HubRoutes
                                            routes/staging.py  StagingRoutes
                                            routes/sources.py  SourceRoutes
```

```
app.py ──▶ routes/images.py ──▶ routes/common.py ──▶ ui/library.py
       ├─▶ routes/hub.py     ──┤                 └─▶ routes/table.py · surface.py
       ├─▶ routes/staging.py ──┘
       └─▶ routes/sources.py
```

No module of `routes/` imports `app.py` or a name `isekai.interface.ui` itself defines. FastAPI is reached through `app.py` alone.

## Goals / Non-Goals

- Goal: the images', library's, staging's and sources' routes and the helpers only they read leave `app.py`; every URL, status, body and message stays.
- Goal: `create_app` is no row of the ratchet, and `read_compare` takes no positional parameter past the ceiling.
- Goal: `app.py` still binds each name a test imports or patches: `Held`, `RARE_BELOW`, `authorities`, `cell_event`, `create_app`, `_precondition`, `run`, `Server` and the `*_KEYS` tuples.
- Non-goal: a record entry; an assertion; the wire's declarations; `run`'s patch row; any route's behaviour.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | a class a resource, each in a module of `routes/`: `ImageRoutes` in `routes/images.py`, `HubRoutes` in `routes/hub.py`, `StagingRoutes` in `routes/staging.py`, `SourceRoutes` in `routes/sources.py` | a resource is a class ([D59](../../../docs/decisions.md#d59--a-resource-is-a-class-registered-from-a-table-over-one-surface)); the library's routes are named for the hub, since `ui/library.py` and `verbs/library.py` are modules of the layer already | `routes/library.py`: a name the layer holds twice; one class for the library, staging and sources: they share no helper of their own |
| [D2](#d2) | the images move first, the other three second, the front door third, the documents last | the images are the largest group and the only one that changes a signature; a halt costs one of them | one phase for every route: a halt costs the whole |
| [D3](#d3) | `_side`, `_filled` and `_images_out` move into `routes/images.py`; no helper moves into `routes/common.py` | only the images' routes read them; what the other resources read is in `common.py` already | a copy in each module: a second spelling that drifts |
| [D4](#d4) | each handler keeps its text, but a closure name it read becomes a read of `self.surface` | the surface already holds `folder`, `offered`, `rendered`, `baked`, `bake_image`, `rendering`, `flows`, `root`, `wired`, `imports`, `limit`, `file_response` and `draft_lock` | locals bound in `__init__`: a second set of names |
| [D5](#d5) | `read_compare`'s path parameters are keyword-only: `def read_compare(self, *, collection: str, …)` | FastAPI calls a handler by keyword, so behaviour holds, and the ratchet counts no keyword-only parameter | a row for the method: a row is never added |
| [D6](#d6) | `Route` gains `status: int \| None = None` and `register` passes it as `status_code` | the staging upload answers `202`, a test and the record pin it, and the table had no place for a status | a `JSONResponse` in the handler: a change of its text; a decorator on the method: FastAPI reads none |
| [D7](#d7) | the middleware is a module-level factory `_addressed_here(allowed, origins)` with its body unchanged; the catch-alls and the assets' mount are `_bundle(app, bundle)`; the resources are mounted by a loop over `MOUNTS`, in today's registration order | the middleware alone leaves `create_app` a line over the ceiling, and the catch-alls with a mount line a resource are the rest | the catch-alls in a class of `routes/`: a resource with no table row; the lifespan as a factory: it alone does not reach the ceiling |
| [D8](#d8) | the pre-flight of every moving phase runs once, in phase 1, over the base's ranges; each moving phase closes with `tools.mutate` on the new module in runs of about a hundred lines, the lock's race test left out | a move shifts `app.py`, so a later phase's base ranges hold other lines; one run over a whole module times out | a range of the base in a later phase |
| [D9](#d9) | `UA-7` takes the new path in phase 1; `UA-1a`, `UA-1b` and `UA-2` keep their text; the rows of `create_app` and `read_compare` and their counts go in the phase that removes the offender | an entry is addressed by path and exact text, and a path is an address, not an assertion; the ratchet reads a row whose offender no longer offends as red | re-anchoring in the last phase: phase 1 would leave an entry whose text is in no file |

### D1

Each class holds `self.surface` and the handlers of its routes, listed in `ROUTES` in `app.py`'s order, with `mount(app, surface)` as the other resources have it. A handler keeps its parameters, its annotations, its docstring and its comments.

| class | handlers |
|---|---|
| `ImageRoutes` | `read_render`, `read_compare`, `read_compare_photo`, `read_render_image`, `read_render_thumb`, `read_bake`, `read_bake_image`, `read_bake_thumb`, `delete_render` |
| `HubRoutes` | `read_library`, `read_hub`, `post_assign` |
| `StagingRoutes` | `post_staging`, `put_file`, `read_staged`, `delete_staged`, `read_staged_thumb`, `delete_staging`, `post_commit` |
| `SourceRoutes` | `read_source`, `read_source_thumb` |

### D2

Phase 1 holds the images' routes, `read_compare`'s signature and `UA-7`; phase 2 the other classes and the table's `status`; phase 3 the factory, `_bundle`, `MOUNTS` and the `create_app` row. Each phase ends with the app built from the tables and the closures it left, so every test of the server proves the join.

### D3

| helper | home | read by |
|---|---|---|
| `_side`, `_filled`, `_images_out` | `routes/images.py`, phase 1 | `read_render`, `read_compare`, `read_compare_photo` |
| `_approved`, `_decimal`, `_renders_out`, `_saved`, `_photograph`, `_hub`, `_strings`, `_cell_out` | `routes/common.py`, as they stand | the new classes import each one they read |
| `_version`, `_DECIMAL`, `Held` | `surface.py`, as they stand | the images' and the sources' handlers |
| `REFUSED`, `_saved` | `routes/common.py`, as they stand | `app.py` keeps importing them: `_refused` and `_precondition` read them |

`app.py` stops importing `_approved`, `_cell_out`, `_decimal`, `_hub`, `_photograph`, `_renders_out`, `_strings` and `_version` once their last closure leaves, and prunes every other import it no longer reads.

### D4

A closure name becomes a read of the surface: `folder` → `self.surface.folder`, `offered` → `self.surface.offered`, `rendered` → `self.surface.rendered`, `baked` → `self.surface.baked`, `bake_image` → `self.surface.bake_image`, `_rendering` → `self.surface.rendering`, `imports` → `self.surface.imports`, `limit` → `self.surface.limit`, `root` → `self.surface.root`, `flows` → `self.surface.flows`, `wired` → `self.surface.wired` and `surface.x` → `self.surface.x`. Nothing else in a body changes.

### D5

`read_compare` takes `self`, then `*`, then its parameters as they are. The ratchet counts no leading `self` and no keyword-only parameter, so its row is red until removed ([D9](#d9)). The record pins the route's shape, so a wrong signature fails when the app is built or in `tests/test_record.py`.

### D6

```
Route("PUT", "/api/staging/{staged}/files/{name}", "put_file", 202)
```

`register` calls `app.add_api_route(route.path, handler, methods=[route.method], status_code=route.status)`; `None` is FastAPI's default, so the other rows are served as before. The upload's `202` is asserted by `tests/test_ui_api.py` and held by `tests/record/routes.json`, so a row without it fails there.

### D7

```
_addressed_here(allowed, origins)   the middleware's body at the indent it has now
_bundle(app, bundle)                no_route, the assets' mount, page
MOUNTS = (hub, staging, images, sources, vocabulary, tattoos, place, render, stream, review)
create_app: … surface → app.middleware("http")(_addressed_here(allowed, origins))
            → the refusal handler → for mount in MOUNTS: mount(app, surface) → _bundle(app, bundle)
```

`MOUNTS` lists the resources in the order `create_app` registers them today: the library's, staging's, images' and sources' routes, then the six mounted already. A path a parameter could swallow belongs to a route registered after the one that should answer it, and no resource's literal segments overlap another's, so the order holds as it was. The catch-alls and the assets' mount come last, as they do now.

`allowed` and `origins` stay bound in `create_app`, so `UA-2`'s anchor stands. The factory's inner function holds the body at the same indent as the closure does now, so `UA-1a`'s and `UA-1b`'s anchors stand.

### D8

The opening runs are these, each over about a hundred lines of the base, on the tests that reach the moving routes. They leave out `test_without_the_lock_an_update_writes_after_the_approval`: that test is a race that fails beside other runs and passes alone, and the gate still runs it.

```
A  uv run python -m tools.mutate isekai/interface/ui/app.py:289-315 isekai/interface/ui/app.py:322-370 --tests T
B  uv run python -m tools.mutate isekai/interface/ui/app.py:372-439 isekai/interface/ui/app.py:616-632 --tests T
C  uv run python -m tools.mutate isekai/interface/ui/app.py:441-540 --tests T
D  uv run python -m tools.mutate isekai/interface/ui/app.py:541-614 isekai/interface/ui/app.py:662-689 --tests T

T = tests/test_ui_api.py tests/test_record.py tests/test_ui_wire.py "-k not test_without_the_lock_an_update_writes_after_the_approval"
```

A holds the middleware and the library's routes, B staging's and the sources', C and D the images' routes and helpers; the ranges are the lines of the cut's base, which the first move shifts. The closing runs are one per range of each new module, and for `app.py` ranges over the factory and `_bundle` as they stand; the ranges are written against the layout the moves give, and a rescue re-fits one that falls off its module. A survivor is killed by a case added to an existing test through a route that binds a scenario, and named below only when no such case can tell it from the code, with the reason. `routes/table.py` is the exception: `tools.mutate` mutates a statement that starts and ends on one line, and `register`'s one call spans several, so no range of the module holds a mutant and the tool refuses it; its one mutant, `status_code=route.status,` → `status_code=None,`, is a recorded edit in `tests/mutants.json`, which the last phase replays.

### D9

`UA-7` anchors on the artifacts import of the images' module, written over several lines with the tail `    renders_of,` and `)`; only its `path` changes, since phase 1 moves the last reader of `renders_of` out of `app.py`. After phase 3, `create_app` holds fewer lines than `LONG_FUNCTIONS`'s ceiling, so its row and the table's count go there; `read_compare`'s row and `WIDE_ROWS`'s count go in phase 1. A table's row and its count are the test's data, not an assertion.

## Tests

The change adds no test and removes none: `git diff --name-only main -- tests` lists `tests/mutants.json` and `tests/test_ratchets.py` alone, unless a pre-flight survivor needs one case, added to an existing test that reaches the same state and carrying the scenario it already binds. No end-to-end run is added: `git diff --name-only main -- tests/e2e` prints nothing. The proof is the suite as it stands: `tests/test_ui_api.py` builds the app and calls each route, `tests/test_record.py` pins the recorded routes' shapes and statuses, `tests/test_ui_wire.py` the key tuples, `tests/test_ratchets.py` the sizes and patches, `tests/test_layers.py` the imports, `tests/test_docs.py` the derived tables, `tests/test_pipeline_cli.py` the entry point's imports and `tests/test_ui.py` the surface's tripwire and its shutdown.

### Equivalent mutants

Pre-flight at the base: run.

- `_side`'s `fields.setdefault(name, [])` → `pass`: `token_budget` and `assemble` read each field with `.get(name, ())`, and `_side` returns nothing of `fields` but that total, so no case can tell it from the code. `tools.mutate` has no way to accept a named equivalent, so the closing run over `images.py` steps over its line: its first range is `35-100`, since lines 1-33 hold no mutant and the tool refuses a range that holds none.

Closing runs: not run.

## Dependencies

None.

## Risks / Trade-offs

- A handler's text is meant to move unchanged, so a missed `self.surface.` read is a `NameError` that every route test of the server raises at once.
- The import pruning can drop a name a test imports from `app.py`; the names the goals list stay bound, and the tests of the server fail on import otherwise.
- The race test is left out of the mutation runs, so a mutant only it kills is named below; the gate still runs it.
- `MOUNTS` registers the resources by a loop, so a resource added later is one more name in the tuple and one more import, and a route added to `create_app` itself would sit beside the guard, which no longer reads as a place for one.
- A closing range of `app.py` is an estimate of the layout the moves give, and falls off the module if the estimate is wrong.

## Verdict

The move changes no behaviour and no requirement, and each phase ends on the suite as it stands. Ready to build.
