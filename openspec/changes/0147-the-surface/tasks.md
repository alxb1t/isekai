# The surface — tasks

Each phase is a move with behaviour unchanged: the surface, vocabulary and the tattoo library, place, the documents. Shape and names are in [design](design.md).

## Progress

- [ ] 1 — The surface · hard
- [ ] 2 — Vocabulary and the tattoo library · hard
- [ ] 3 — Place · moderate
- [ ] 4 — The documents and the replay · moderate

## 1 — The surface

- [ ] 1.1 Pre-flight: run `tools.mutate` over the lines this phase moves, at `ab010b18`: `Held` 258-275, the closures 363-372, 778-781, 940-945, 1229-1240, 1325-1349 and 1469-1502, `_Shared` 1596-1635, `_version` 1827-1838 and `_flow` 2117-2125, all in `isekai/interface/ui/app.py`, on the test files [D7](design.md#d7) lists. Kill a survivor as [D7](design.md#d7) says.
  Verify: `uv run python -m tools.mutate isekai/interface/ui/app.py:258-275 isekai/interface/ui/app.py:363-372 isekai/interface/ui/app.py:778-781 isekai/interface/ui/app.py:940-945 isekai/interface/ui/app.py:1229-1240 isekai/interface/ui/app.py:1325-1349 isekai/interface/ui/app.py:1469-1502 isekai/interface/ui/app.py:1596-1635 isekai/interface/ui/app.py:1827-1838 isekai/interface/ui/app.py:2117-2125 --tests tests/test_ui.py tests/test_ui_api.py tests/test_ui_jobs.py tests/test_ui_library.py tests/test_ui_wire.py tests/test_ui_tattoo.py tests/test_ui_placement.py tests/test_ui_propose.py tests/test_ui_billing.py` exits 0.
- [ ] 1.2 Write `isekai/interface/ui/surface.py`: a docstring, then `Held`, `_Shared`, `_DECIMAL`, `_BAKE_DIGITS`, `_version` and `_flow` moved from `app.py` with their text and comments unchanged. It imports no `fastapi`, `starlette` or `uvicorn`.
  Verify: `grep -nE '^(class Held|class _Shared|def _version|def _flow|_DECIMAL =|_BAKE_DIGITS =)' isekai/interface/ui/surface.py` prints a line for each of the six names.
- [ ] 1.3 Add `class Surface` to `surface.py` as [D1](design.md#d1) and [D2](design.md#d2) draw it: `__init__(self, root, wired, *, flows, wire, jobs, billing, imports, broadcast, limit)`, `self.shared = _Shared(wired)`, and the methods `folder`, `held`, `rendering_slot`, `rendering`, `rendered`, `baked` and `bake_image`, each the closure's body of `app.py` with each shared name read as `self.<name>`.
  Verify: `grep -nE '    def (folder|held|rendering_slot|rendering|rendered|baked|bake_image)\(' isekai/interface/ui/surface.py` prints a line for each of the seven names.
- [ ] 1.4 In `Surface.__init__` bind `self.offered = cache(self._load)`, with `_load(self, flow)` returning `_flow(self.wired, flow)`, and import `cache` from `functools`.
  Verify: `grep -n 'self.offered = cache(self._load)' isekai/interface/ui/surface.py` prints the line.
- [ ] 1.5 Edit `app.py`: delete the moved definitions; build the surface and bind the names after `imports = importing.Imports(...)` as [D1](design.md#d1) shows, deleting `shared = _Shared(wired)` and the `offered` closure; import `Held`, `Surface` and each other moved name `app.py` still reads from `isekai.interface.ui.surface`. Delete `class Held`, prune the imports `app.py` no longer reads, and leave the block ending `renders_of,` `require,` `)` as it is.
  Verify: `grep -L 'class Held' isekai/interface/ui/app.py` prints the path.
- [ ] 1.6 Run `uv run ruff format isekai/interface/ui/app.py isekai/interface/ui/surface.py`, then run the server's tests, which assert nothing new.
  Verify: `uv run pytest tests/test_ui.py tests/test_ui_api.py tests/test_ui_jobs.py tests/test_ui_library.py tests/test_ui_wire.py tests/test_ui_tattoo.py tests/test_ui_placement.py tests/test_ui_propose.py tests/test_ui_billing.py` passes.
- [ ] 1.7 Run `git add -N isekai/interface/ui/surface.py`, since `tools.mutate` copies tracked files only. Close with the same run on the new home: `tools.mutate` over `isekai/interface/ui/surface.py:1-2000` on the same test files. Handle a survivor as [D7](design.md#d7) says.
  Verify: `uv run python -m tools.mutate isekai/interface/ui/surface.py:1-2000 --tests tests/test_ui.py tests/test_ui_api.py tests/test_ui_jobs.py tests/test_ui_library.py tests/test_ui_wire.py tests/test_ui_tattoo.py tests/test_ui_placement.py tests/test_ui_propose.py tests/test_ui_billing.py` exits 0.
- [ ] 1.8 Re-derive the *Imported by* tables with `uv run python -m tools.derive_imported_by`, and hold the guards: the routes of `tests/record/routes.json` answer as before.
  Verify: `uv run pytest tests/test_record.py tests/test_ratchets.py tests/test_layers.py tests/test_docs.py tests/test_pipeline_cli.py tests/test_ui_wire.py` passes.

## 2 — Vocabulary and the tattoo library

- [ ] 2.1 Pre-flight: the tests' baseline, the test files [D7](design.md#d7) lists green on the tree phase 1 left, before a line moves.
  Verify: `uv run pytest tests/test_ui.py tests/test_ui_api.py tests/test_ui_jobs.py tests/test_ui_library.py tests/test_ui_wire.py tests/test_ui_tattoo.py tests/test_ui_placement.py tests/test_ui_propose.py tests/test_ui_billing.py` passes.
- [ ] 2.2 Write `isekai/interface/ui/routes/__init__.py` holding a docstring alone, and `routes/table.py` holding `Route` (a named tuple of `method`, `path`, `handler`) and `register(router, resource, table)` as [D3](design.md#d3) draws it.
  Verify: `grep -nE '^(class Route|def register)' isekai/interface/ui/routes/table.py` prints a line for each of the two names.
- [ ] 2.3 Write `routes/keys.py` holding `OUTLINE_KEYS` and `STAGE1_KEYS` and `routes/common.py` holding `_needs` and `_dimensions`, each moved from `app.py` with its comment and text unchanged.
  Verify: `grep -nE '^(OUTLINE_KEYS|STAGE1_KEYS|def _needs|def _dimensions)' isekai/interface/ui/routes/keys.py isekai/interface/ui/routes/common.py` prints a line for each of the four names.
- [ ] 2.4 Write the new `isekai/interface/ui/routes/vocabulary.py` holding `RARE_BELOW` and `DEFAULT_LIMIT` with their comments, `class VocabularyRoutes` with `read_tags` and `read_fields` as [D3](design.md#d3) says, a `ROUTES` table and `router(surface)`. `read_fields` reads `_flow` from `isekai.interface.ui.surface`.
  Verify: `grep -nE '^(RARE_BELOW|DEFAULT_LIMIT|class VocabularyRoutes|ROUTES|def router)' isekai/interface/ui/routes/vocabulary.py` prints a line for each of the five names.
- [ ] 2.5 Write `isekai/interface/ui/routes/tattoos.py`: `class TattooRoutes` with `read_tattoos`, `read_tattoo`, `delete_tattoo`, `read_tattoo_design`, `post_tattoo`, `post_cut`, `put_outline`, `get_stage1` and `put_stage1`; `_digest_asked` and `_tattoo_limits` as module functions; a `ROUTES` table in `app.py`'s order and `router(surface)`.
  Verify: `grep -nE '^(class TattooRoutes|def _digest_asked|def _tattoo_limits|ROUTES|def router)' isekai/interface/ui/routes/tattoos.py` prints a line for each of the five names.
- [ ] 2.6 Edit `app.py`: delete the moved handlers, constants and helpers; bind `RARE_BELOW`, `OUTLINE_KEYS` and `STAGE1_KEYS` by the alias `NAME as NAME` ([D5](design.md#d5)); import `_dimensions` and `_needs` from `routes/common.py`; import `router as vocabulary_router` and `router as tattoo_router` by name from `routes/vocabulary.py` and `routes/tattoos.py`, never the module `tattoos`, which `app.py` still reads from `isekai.pipeline`; include both routers right before `no_route`, and delete `read_tattoos` with the rest. Prune the imports no longer read, and keep each name a test patches.
  Verify: `grep -L 'read_tattoos' isekai/interface/ui/app.py` prints the path.
- [ ] 2.7 Run `uv run ruff format isekai/interface/ui`, then the server's tests.
  Verify: `uv run pytest tests/test_ui.py tests/test_ui_api.py tests/test_ui_jobs.py tests/test_ui_library.py tests/test_ui_wire.py tests/test_ui_tattoo.py tests/test_ui_placement.py tests/test_ui_propose.py tests/test_ui_billing.py` passes.
- [ ] 2.8 Run `git add -N isekai/interface/ui/routes`, since `tools.mutate` copies tracked files only. Close with `tools.mutate` over the new modules on the same test files: `routes/vocabulary.py`, `routes/tattoos.py`, `routes/common.py` and `routes/table.py`, lines 1-2000 each.
  Verify: `uv run python -m tools.mutate isekai/interface/ui/routes/vocabulary.py:1-2000 isekai/interface/ui/routes/tattoos.py:1-2000 isekai/interface/ui/routes/common.py:1-2000 isekai/interface/ui/routes/table.py:1-2000 --tests tests/test_ui.py tests/test_ui_api.py tests/test_ui_jobs.py tests/test_ui_library.py tests/test_ui_wire.py tests/test_ui_tattoo.py tests/test_ui_placement.py tests/test_ui_propose.py tests/test_ui_billing.py` exits 0.
- [ ] 2.9 Re-derive the *Imported by* tables with `uv run python -m tools.derive_imported_by`.
  Verify: `uv run pytest tests/test_record.py tests/test_ratchets.py tests/test_layers.py tests/test_docs.py tests/test_pipeline_cli.py tests/test_ui_wire.py` passes.

## 3 — Place

- [ ] 3.1 Pre-flight: the tests' baseline on the tree phase 2 left, the test files [D7](design.md#d7) lists green before a line moves.
  Verify: `uv run pytest tests/test_ui.py tests/test_ui_api.py tests/test_ui_jobs.py tests/test_ui_library.py tests/test_ui_wire.py tests/test_ui_tattoo.py tests/test_ui_placement.py tests/test_ui_propose.py tests/test_ui_billing.py` passes.
- [ ] 3.2 Add `INK_KEYS`, `PREVIEW_KEYS`, `PROPOSE_KEYS` and `BAKE_KEYS` to `routes/keys.py`, moved from `app.py` with their comments unchanged.
  Verify: `grep -nE '^(INK_KEYS|PREVIEW_KEYS|PROPOSE_KEYS|BAKE_KEYS)' isekai/interface/ui/routes/keys.py` prints a line for each of the four names.
- [ ] 3.3 Write the new `isekai/interface/ui/routes/place.py` holding `BAKE_EDIT`; `class PlaceRoutes` with `post_ink`, `placed_on`, `post_preview`, `post_bake` and `post_propose`, where `post_preview`, `post_bake` and `post_propose` each call `self.placed_on`; `_is_point`, `_points_of` and `_upright_of` as module functions; a `ROUTES` table and `router(surface)`.
  Verify: `grep -nE '^(BAKE_EDIT|class PlaceRoutes|def _is_point|def _points_of|def _upright_of|ROUTES|def router)' isekai/interface/ui/routes/place.py` prints a line for each of the seven names.
- [ ] 3.4 Edit `app.py`: delete the moved handlers, `placed_on`, constants and helpers; bind the tuples by `NAME as NAME`; import `router as place_router` by name from `routes/place.py` and include it before `no_route`; delete `post_propose` with the rest; drop the `_needs` import if `app.py` no longer reads it. Prune the imports no longer read, and keep each name a test patches.
  Verify: `grep -L 'post_propose' isekai/interface/ui/app.py` prints the path.
- [ ] 3.5 Run `uv run ruff format isekai/interface/ui`, then the server's tests.
  Verify: `uv run pytest tests/test_ui.py tests/test_ui_api.py tests/test_ui_jobs.py tests/test_ui_library.py tests/test_ui_wire.py tests/test_ui_tattoo.py tests/test_ui_placement.py tests/test_ui_propose.py tests/test_ui_billing.py` passes.
- [ ] 3.6 Run `git add -N isekai/interface/ui/routes`, since `tools.mutate` copies tracked files only. Close with `tools.mutate` over `routes/place.py`, lines 1-2000, on the same test files; `routes/keys.py` holds only tuples and no mutant.
  Verify: `uv run python -m tools.mutate isekai/interface/ui/routes/place.py:1-2000 --tests tests/test_ui.py tests/test_ui_api.py tests/test_ui_jobs.py tests/test_ui_library.py tests/test_ui_wire.py tests/test_ui_tattoo.py tests/test_ui_placement.py tests/test_ui_propose.py tests/test_ui_billing.py` exits 0.
- [ ] 3.7 Re-derive the *Imported by* tables with `uv run python -m tools.derive_imported_by`.
  Verify: `uv run pytest tests/test_record.py tests/test_ratchets.py tests/test_layers.py tests/test_docs.py tests/test_pipeline_cli.py tests/test_ui_wire.py` passes.

## 4 — The documents and the replay

- [ ] 4.1 Add `### D59 · A resource is a class, registered from a table, over one surface` to `docs/decisions.md` after D58, as [D8](design.md#d8) says: with its `Why`, its `Accepts` and `Made by` naming this change.
  Verify: `grep -n '^### D59' docs/decisions.md` prints the heading.
- [ ] 4.2 Amend the docstring of `isekai/interface/ui/app.py`: delete "Kept to one file deliberately" and the claim that this is the only module of the package importing a web framework; say that `surface.py` imports none, and that the routers of `routes/` import FastAPI and are reached through this module alone.
  Verify: `grep -L 'Kept to one file' isekai/interface/ui/app.py` prints the path.
- [ ] 4.3 Amend `isekai/interface/README.md`: the `ui/app.py` row no longer says it is the only importer of FastAPI; add rows for `ui/surface.py` and `ui/routes/`.
  Verify: `grep -n 'ui/surface.py' isekai/interface/README.md` prints a row.
- [ ] 4.4 Amend `docs/modules.md`: the tattoo routes and the proposer's call are in `interface/ui/routes/tattoos.py` and `interface/ui/routes/place.py`, not in `app.py`; the wheel-reaching paragraph says the routers import `fastapi` too, reached through `app.py` alone.
  Verify: `grep -n 'routes/place.py' docs/modules.md` prints a line.
- [ ] 4.5 Amend `ARCHITECTURE.md`'s `interface` line: the UI's routes live in `interface/ui/routes/`, a class a resource over one `Surface`.
  Verify: `grep -n 'ui/routes' ARCHITECTURE.md` prints the line.
- [ ] 4.6 **HALT CHECK** Replay the mutants of `tests/mutants.json`, none re-anchored: an entry of `app.py` that no longer finds its text once is a plan fault, so stop and say so.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0 with no survivor.
- [ ] 4.7 Re-derive the *Imported by* tables with `uv run python -m tools.derive_imported_by`.
  Verify: `uv run pytest tests/test_record.py tests/test_ratchets.py tests/test_layers.py tests/test_docs.py tests/test_pipeline_cli.py tests/test_ui_wire.py` passes.
- [ ] 4.8 Hold the series' conditions: nothing under `tests/record/`, no mutant entry, no ratchet table and no image-frozen file changed.
  Verify: `git diff --stat ab010b18 -- tests/record tests/mutants.json tests/test_ratchets.py Dockerfile config/models.json isekai/boundary/provision.py isekai/boundary/pod_start.py` prints nothing.
