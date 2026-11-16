# The surface — design

`Surface` holds what the routes share, and the vocabulary, tattoo library and place routes become classes registered from tables; behaviour, wire and tests are unchanged. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

`create_app` in `isekai/interface/ui/app.py` is one closure. Its routes read these shared closures — `folder`, `held`, `offered`, `rendering_slot`, `_rendering`, `rendered`, `baked`, `bake_image` — and the names `root`, `wired`, `flows`, `wire`, `jobs`, `billing`, `imports`, `broadcast`, `shared` and `limit`.

The tests patch these names of the module: `_DRAFT_UPDATE`, `FileResponse`, `_precondition`, `save_draft`, `approve`, `run` and `Jobs`. The ratchet `unread_patches` fails when the module stops reading a patched name, so no route that reads one moves here, and `Jobs(` stays built in `create_app`.

The routes this version moves read none of them. Their line ranges at `ab010b18`:

| group | handlers | lines of `app.py` |
|---|---|---|
| vocabulary | `read_tags`, `read_fields` | 1008-1044 |
| tattoo library | `read_tattoos`, `read_tattoo`, `delete_tattoo`, `read_tattoo_design`, `post_tattoo`, `post_cut`, `put_outline`, `get_stage1`, `put_stage1` | 491-599, `post_cut` among them |
| place | `post_ink`, `placed_on`, `post_preview`, `post_bake`, `post_propose` | 601-753 |

Between the grilling's read and this cut no line of `app.py`, of the server's tests or of `tests/record/` changed.

## Goals / Non-Goals

- **Goals:** the shape of `Surface` and of a resource class, proved on routes with no patch and no lock; every name a test reads still bound in `app.py`; the documents the move makes false amended in the diff.
- **Non-Goals:** the routes in [Not in this change](proposal.md#not-in-this-change); a new test; a ratchet row added, removed or lowered; a change to a route's path, method, status or body.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `Surface` is a class in `surface.py` with no web framework; `create_app` builds it and binds its methods under today's names | no route's line changes, and `Jobs(`, `Billing(` and `Imports(` stay built in `create_app`, where a test patches `Jobs` | a dataclass of fields: the closures are methods; building the jobs inside `Surface`: it moves a patched name |
| [D2](#d2) | `offered` is cached per surface by `functools.cache` over a private method, bound in `__init__` | a flow is pinned while served, as today; the cache dies with the surface, as it does with the app | `cache` on the method: it keeps `self` alive in a module-level table |
| [D3](#d3) | a resource is a class: `__init__(self, surface)`, today's handlers as methods, a `ROUTES` table of `Route(method, path, handler)` and `mount(app, surface)`, which registers each row on the app itself | the ratchets list no new row, a method is no wider than its handler, a body keeps its text but for the surface's prefix, and each route stays one `APIRoute` of `app.routes`, where the server's tests and `tests/record.py` read its `path` and `methods` | a function holding the handlers as closures: over the function ceiling at once; an `APIRouter` the app includes: FastAPI 0.141.1 leaves one `_IncludedRouter` in `app.routes`, with no `path` or `methods` there |
| [D4](#d4) | the resource modules live in `routes/`, entered by `app.py` alone; none imports `app.py` or a name of `isekai.interface.ui` that is no module | a cycle inside the layer is red, lazy imports included; the entry point imports with site-packages off, so FastAPI is reached through `app.py` alone | a resource module of `app.py`'s own: it is the cycle |
| [D5](#d5) | a moved name keeps its spelling; `app.py` keeps binding `Held`, `RARE_BELOW` and the `*_KEYS` tuples | `tests/test_ui_api.py` imports `RARE_BELOW` and `Held`, and `tests/test_ui_wire.py` reads the tuples from `vars(app_module)` | repointing the tests: a later version's work |
| [D6](#d6) | the shared helpers go to the lowest module that holds all their readers | `_version`, `_DECIMAL` and `_flow` are read by the surface and by `app.py`; `_dimensions` and `_needs` by the resource modules and `app.py` | one helper module for all: it is a grab bag |
| [D7](#d7) | phase 1 opens with `tools.mutate` over its ranges in `app.py`; phases 2 and 3 open with the tests' baseline; each closes with `tools.mutate` on its new modules | phase 1 shifts every later line of `app.py`, so no range of it holds for phase 2; the closing run covers the same mutants | a range-based opening for every phase: stale after phase 1 |
| [D8](#d8) | a new decision, `D59`, states the shape; `app.py`'s docstring, the interface's README, `docs/modules.md` and `ARCHITECTURE.md` are amended | the documents this move makes false are amended in its diff, and a rule gets a decision | amending later: a stale claim ships |

### D1

`surface.py` imports no `fastapi`, `starlette` or `uvicorn`, so the layer's entry point and its tests read it with no server installed.

```
Surface(root, wired, *, flows, wire, jobs, billing, imports, broadcast, limit)
  .root .wired .flows .wire .jobs .billing .imports .broadcast .limit   as given
  .shared                       _Shared(wired)
  .folder(collection)           .held(collection, digest, flow)
  .offered(flow)                .rendering_slot()      .rendering(collection)
  .rendered(collection, digest, flow, version, seed)
  .baked(collection, digest, flow, version, seed, k)
  .bake_image(collection, digest, flow, version, seed, k)
```

`create_app` builds the surface after `imports` and binds, so the routes still written in it read what they read today:

```python
surface = Surface(
    root,
    wired,
    flows=flows,
    wire=wire,
    jobs=jobs,
    billing=billing,
    imports=imports,
    broadcast=broadcast,
    limit=limit,
)
shared = surface.shared
folder, held, offered = surface.folder, surface.held, surface.offered
rendering_slot, _rendering = surface.rendering_slot, surface.rendering
rendered, baked, bake_image = surface.rendered, surface.baked, surface.bake_image
```

Only `root` and `wired` are positional, so no constructor is wider than the positional ceiling. `rendering` is `_rendering` without its underscore, as a public method.

### D2

```python
self.offered = cache(self._load)  # _load(flow) -> _flow(self.wired, flow)
```

### D3

A handler's body is its text today with `self.surface.` in front of each name the surface now holds: `root`, `wired`, `held`, `folder`, `rendered`, `imports`, `shared`. Nothing else in a body changes. A decorator becomes a row:

```
@app.get("/api/tags")  def read_tags(...)   ──▶   Route("GET", "/api/tags", "read_tags")
                                                  ROUTES = (Route(...), ...)
mount(app, surface) = register(app, VocabularyRoutes(surface), ROUTES)
```

`routes/table.py` holds `Route` and `register`; `register(app, resource, table)` calls `app.add_api_route(path, getattr(resource, handler), methods=[method])` on the app itself, and no module builds an `APIRouter`: an included router is one `_IncludedRouter` in `app.routes`, and a route registered on the app is one `APIRoute` there, as `@app.get` left it. A row that names no method fails when the app is built, in every test of the server.

### D4

```
app.py ──▶ routes/{vocabulary,tattoos,place}.py ──▶ routes/{keys,common,table}.py
   │                          │
   └──────────────▶ surface.py ◀┘      surface.py ──▶ library, jobs, billing, events
```

`routes/__init__.py` holds a docstring. `app.py` imports each `mount` by name, as `mount as <group>_mount`, never a module of `routes/` whose name another import of `app.py` already binds. It calls each with the app and the surface right before `no_route`, so the catch-alls and the assets' mount stay last. Their imports of siblings are `from isekai.interface.ui import library`, a module, never a name `ui/__init__.py` defines.

### D5

`app.py` binds each by the redundant alias `NAME as NAME`, which ruff reads as a re-export. `Held` is read by the review's helpers in `app.py` itself.

### D6

| name | goes to | read by |
|---|---|---|
| `Held`, `_Shared`, `_version`, `_flow`, `_DECIMAL`, `_BAKE_DIGITS` | `surface.py` | the surface; `app.py` binds `Held`, `_version`, `_DECIMAL`; `routes/vocabulary.py` reads `_flow` |
| `_dimensions`, `_needs` | `routes/common.py` | the tattoo library, place and the review's `read_input` |
| `OUTLINE_KEYS`, `STAGE1_KEYS` (phase 2), `INK_KEYS`, `PREVIEW_KEYS`, `PROPOSE_KEYS`, `BAKE_KEYS` (phase 3) | `routes/keys.py` | their resource modules; `app.py` binds each |
| `RARE_BELOW`, `DEFAULT_LIMIT` | `routes/vocabulary.py` | `read_tags`; `app.py` binds `RARE_BELOW` |
| `_digest_asked`, `_tattoo_limits` | `routes/tattoos.py` | the tattoo library alone |
| `BAKE_EDIT`, `_is_point`, `_points_of`, `_upright_of` | `routes/place.py` | place alone |

### D7

The test files that reach the moved lines through the routes are these: `tests/test_ui.py`, `tests/test_ui_api.py`, `tests/test_ui_jobs.py`, `tests/test_ui_library.py`, `tests/test_ui_wire.py`, `tests/test_ui_tattoo.py`, `tests/test_ui_placement.py`, `tests/test_ui_propose.py` and `tests/test_ui_billing.py`. A survivor is killed by a test through a route that binds an existing scenario, or is named in [the equivalent mutants](#equivalent-mutants) with its reason.

### D8

`D59 · A resource is a class, registered from a table, over one surface`, made by `0147`, accepting that the render, jobs and events routes and the routes reading a patched name stay closures of `create_app` until their versions.

## Equivalent mutants

A survivor of a pre-flight or closing run that no test through a route can kill is a row here, with the reason it changes no behaviour. None at the cut.

| mutant | phase | why it is equivalent |
|---|---|---|

## Tests

This change adds no test and removes none, and changes no assertion. A survivor may add one test, through a route, bound to an existing scenario.

| layer | added | removed | end-to-end runs added |
|---|---|---|---|
| unit and integration | none | none | none |

The count is `git diff --stat ab010b18 -- tests`, which prints nothing but a survivor's test. No test is deleted or merged, so the table of `I16` is empty.

Held by the suite as it stands: `tests/record/routes.json` holds the status and shape of the routes, `tests/test_ratchets.py` the rows, `tests/test_layers.py` the imports, `tests/test_ui_wire.py` the key tuples, `tests/test_docs.py` the *Imported by* tables, and the replay of `tests/mutants.json` the entries that name `app.py`.

## Dependencies

None.

## Risks / Trade-offs

- A moved handler read a closure name the surface does not hold: the route fails on its first request. Held by `tests/test_record.py` and the server's tests, which request each moved route.
- A pruned import was a patched name: `tests/test_ratchets.py`'s `unread_patches` goes red. Keep `FileResponse`, `save_draft`, `approve`, `run` and `Jobs` read.
- The import block ending `renders_of,` `require,` `)` is the address of the mutant `UA-7`. Phase 4 replays it, and a miss is a halt: nothing is re-anchored here.
- `app.py` stays a listed offender, and its row may grow until the version that removes it.

## Verdict

Ready to build, in the phases of [tasks](tasks.md): the surface; vocabulary and the tattoo library; place; the documents.
