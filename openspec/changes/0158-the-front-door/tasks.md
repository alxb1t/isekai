# The front door — tasks

The phases are the images, the library, staging and sources, the front door and the documents. Each moves lines and no behaviour, and the suite as it stands is the proof.

## Progress

- [ ] 1 — The images · moderate
- [ ] 2 — The library, staging and sources · moderate
- [ ] 3 — The front door · moderate
- [ ] 4 — The documents · moderate

## 1 — The images

- [x] 1.1 **HALT CHECK** No test patches a name of `isekai/interface/ui/app.py` that the moving routes or their helpers read: the one patch the module keeps is `run`'s, which `serve` reads.
  Verify: `git grep -n "setattr(app_module" -- tests` prints one line.
- [x] 1.2 Before any line moves, run each pre-flight run [D8](design.md#d8) lists over the lines of `isekai/interface/ui/app.py` that the moving resources and the middleware hold, one command at a time. Kill each survivor with a case added to an existing test; name it in [Equivalent mutants](design.md#equivalent-mutants) only when no case can tell it from the code, then set that section's first line to `Pre-flight at the base: run.`
  Verify: `grep -n "Pre-flight at the base: run" openspec/changes/0158-the-front-door/design.md` prints a line.
- [x] 1.3 Write the new `isekai/interface/ui/routes/images.py`: `class ImageRoutes` with `read_render`, `read_compare`, `read_compare_photo`, `read_render_image`, `read_render_thumb`, `read_bake`, `read_bake_image`, `read_bake_thumb` and `delete_render` as [D1](design.md#d1) and [D4](design.md#d4) say, `_side`, `_filled` and `_images_out` as module functions ([D3](design.md#d3)), a `ROUTES` table in that order and `mount(app, surface)`. Import `renders_of` from `isekai.foundation.artifacts` over several lines, ending `    renders_of,` and `)`.
  Verify: `grep -nE "^(class ImageRoutes|ROUTES|def mount|def _side|def _filled|def _images_out)" isekai/interface/ui/routes/images.py` prints a line for each of those names.
- [x] 1.4 In `ImageRoutes.read_compare`, write `self` then a lone `*` before the path parameters, which keep their names, order and annotations ([D5](design.md#d5)).
  Verify: `grep -c "^        \*,$" isekai/interface/ui/routes/images.py` prints `1`.
- [x] 1.5 In `isekai/interface/ui/app.py`, delete the closures `read_render`, `read_compare`, `read_compare_photo`, `read_render_image`, `read_render_thumb`, `read_bake`, `read_bake_image`, `read_bake_thumb` and `delete_render` from `create_app`, and the functions `_side`, `_filled` and `_images_out`. Call `images_mount(app, surface)` where the closures stood, so the registration order is today's, and delete the bindings `_rendering` and `rendered, baked, bake_image` that only they read.
  Verify: `git grep -nE "def (read_render|read_compare|read_compare_photo|read_render_image|read_render_thumb|read_bake|read_bake_image|read_bake_thumb|delete_render)\(" -- isekai/interface/ui/app.py` prints nothing.
- [x] 1.6 In `isekai/interface/ui/app.py`, prune the imports nothing reads now and keep each name a test reads ([D3](design.md#d3)): `renders_of`, `Flow`, `asdict`, `edit_files`, `edit_numbers`, `discard_render`, `token_budget`, `withdraw`, `_approved`, `_decimal`, `_renders_out` and `_version` go, unless a remaining line reads one.
  Verify: `git grep -n "renders_of" -- isekai/interface/ui/app.py` prints nothing.
- [x] 1.7 In `tests/test_ratchets.py`, remove the row ``"isekai/interface/ui/app.py::create_app.read_compare": 8`` from `WIDE_FUNCTIONS`, since the method takes no positional parameter ([D9](design.md#d9)).
  Verify: `git grep -nF "create_app.read_compare" -- tests/test_ratchets.py` prints nothing.
- [x] 1.8 In `tests/test_ratchets.py`, lower `WIDE_ROWS` to ``WIDE_ROWS = 13``, the count of the rows `WIDE_FUNCTIONS` now holds.
  Verify: `git grep -n "^WIDE_ROWS = 13" -- tests/test_ratchets.py` prints a line.
- [x] 1.9 In `tests/mutants.json`, change `UA-7`'s `path` to `isekai/interface/ui/routes/images.py`, its `find` and `replace` unchanged ([D9](design.md#d9)).
  Verify: `git grep -n "routes/images.py" -- tests/mutants.json` prints a line.
- [x] 1.10 Re-derive the *Imported by* tables with `uv run python -m tools.derive_imported_by`: the new module and the pruned imports change them.
  Verify: `uv run pytest tests/test_docs.py` exits 0.
- [x] 1.11 Prove the move against the record, the ratchets, the layers, the entry point's imports, the wire and the server's own tests.
  Verify: `uv run pytest tests/test_record.py tests/test_ratchets.py tests/test_layers.py tests/test_docs.py tests/test_pipeline_cli.py tests/test_ui_wire.py tests/test_ui_api.py tests/test_ui.py` exits 0.
- [x] 1.12 Run `git add -N isekai/interface/ui/routes/images.py`, since `tools.mutate` copies tracked files only, then close with `tools.mutate` on the module's first range ([D8](design.md#d8)). Kill each survivor with a case added to an existing test; name it in [Equivalent mutants](design.md#equivalent-mutants) only when no case can tell it from the code. A range run cannot accept a named equivalent, so the Verify below steps over its line: `_side`'s `fields.setdefault(name, [])` is line 34, the one named there. Lines 1-33 hold no mutant, and `tools.mutate` refuses a range that holds none, so the range starts at 35.
  Verify: `uv run python -m tools.mutate isekai/interface/ui/routes/images.py:35-100 --tests tests/test_ui_api.py tests/test_record.py tests/test_ui_wire.py "-k not test_without_the_lock_an_update_writes_after_the_approval"` exits 0.
- [x] 1.13 Close with the next range of `isekai/interface/ui/routes/images.py`, each survivor handled as 1.12 says.
  Verify: `uv run python -m tools.mutate isekai/interface/ui/routes/images.py:101-200 --tests tests/test_ui_api.py tests/test_record.py tests/test_ui_wire.py "-k not test_without_the_lock_an_update_writes_after_the_approval"` exits 0.
- [x] 1.14 Close with the rest of `isekai/interface/ui/routes/images.py`, each survivor handled as 1.12 says.
  Verify: `uv run python -m tools.mutate isekai/interface/ui/routes/images.py:201-2000 --tests tests/test_ui_api.py tests/test_record.py tests/test_ui_wire.py "-k not test_without_the_lock_an_update_writes_after_the_approval"` exits 0.

## 2 — The library, staging and sources

- [ ] 2.1 In `isekai/interface/ui/routes/table.py`, give `Route` a fourth field ``status: int | None = None`` and have `register` pass ``status_code=route.status`` to `app.add_api_route` ([D6](design.md#d6)).
  Verify: `git grep -n "status_code=route.status" -- isekai/interface/ui/routes/table.py` prints a line.
- [ ] 2.2 Write the new `isekai/interface/ui/routes/hub.py`: `class HubRoutes` with `read_library`, `read_hub` and `post_assign` as [D1](design.md#d1) and [D4](design.md#d4) say, a `ROUTES` table in that order and `mount(app, surface)`.
  Verify: `grep -nE "^(class HubRoutes|ROUTES|def mount)" isekai/interface/ui/routes/hub.py` prints a line for each of those names.
- [ ] 2.3 Write the new `isekai/interface/ui/routes/staging.py`: `class StagingRoutes` with `post_staging`, `put_file`, `read_staged`, `delete_staged`, `read_staged_thumb`, `delete_staging` and `post_commit`, a `ROUTES` table in that order, the upload's row ending ``, 202)``, and `mount(app, surface)`. `put_file` stays `async` and keeps its `request: Request` parameter.
  Verify: `grep -nE "^(class StagingRoutes|ROUTES|def mount)|, 202\)" isekai/interface/ui/routes/staging.py` prints a line for each of those names and one for the status.
- [ ] 2.4 Write the new `isekai/interface/ui/routes/sources.py`: `class SourceRoutes` with `read_source` and `read_source_thumb`, a `ROUTES` table in that order and `mount(app, surface)`.
  Verify: `grep -nE "^(class SourceRoutes|ROUTES|def mount)" isekai/interface/ui/routes/sources.py` prints a line for each of those names.
- [ ] 2.5 In `isekai/interface/ui/app.py`, delete the closures `read_library`, `read_hub`, `post_assign`, `post_staging`, `put_file`, `read_staged`, `delete_staged`, `read_staged_thumb`, `delete_staging`, `post_commit`, `read_source` and `read_source_thumb` from `create_app`, and the binding `folder, offered = surface.folder, surface.offered`. Replace phase 1's lone `images_mount(app, surface)` call with the calls of `hub_mount`, `staging_mount`, `images_mount` and `sources_mount`, in that order, before `vocabulary_mount`, so the registration order is today's and no resource is mounted twice.
  Verify: `git grep -c -E "^    @app\.(get|put|post|delete)\(" -- isekai/interface/ui/app.py` prints `isekai/interface/ui/app.py:2`.
- [ ] 2.6 In `isekai/interface/ui/app.py`, prune the imports nothing reads now and keep each name a test reads ([D3](design.md#d3)): `run_in_threadpool`, `asdict`, `assign`, `find_run`, `open_run`, `library`, `_cell_out`, `_hub`, `_photograph` and `_strings` go, unless a remaining line reads one.
  Verify: `git grep -n "run_in_threadpool" -- isekai/interface/ui/app.py` prints nothing.
- [ ] 2.7 Re-derive the *Imported by* tables with `uv run python -m tools.derive_imported_by`: the new modules and the pruned imports change them.
  Verify: `uv run pytest tests/test_docs.py` exits 0.
- [ ] 2.8 Prove the move against the record, the ratchets, the layers, the entry point's imports, the wire and the server's own tests.
  Verify: `uv run pytest tests/test_record.py tests/test_ratchets.py tests/test_layers.py tests/test_docs.py tests/test_pipeline_cli.py tests/test_ui_wire.py tests/test_ui_api.py tests/test_ui.py` exits 0.
- [ ] 2.9 Run `git add -N isekai/interface/ui/routes/hub.py isekai/interface/ui/routes/staging.py isekai/interface/ui/routes/sources.py`, then close with `tools.mutate` on `hub.py` ([D8](design.md#d8)). Kill each survivor with a case added to an existing test; name it in [Equivalent mutants](design.md#equivalent-mutants) only when no case can tell it from the code.
  Verify: `uv run python -m tools.mutate isekai/interface/ui/routes/hub.py:1-2000 --tests tests/test_ui_api.py tests/test_record.py tests/test_ui_wire.py "-k not test_without_the_lock_an_update_writes_after_the_approval"` exits 0.
- [ ] 2.10 Close with `tools.mutate` on `staging.py`, each survivor handled as 2.9 says.
  Verify: `uv run python -m tools.mutate isekai/interface/ui/routes/staging.py:1-2000 --tests tests/test_ui_api.py tests/test_record.py tests/test_ui_wire.py "-k not test_without_the_lock_an_update_writes_after_the_approval"` exits 0.
- [ ] 2.11 Close with `tools.mutate` on `sources.py`, each survivor handled as 2.9 says.
  Verify: `uv run python -m tools.mutate isekai/interface/ui/routes/sources.py:1-2000 --tests tests/test_ui_api.py tests/test_record.py tests/test_ui_wire.py "-k not test_without_the_lock_an_update_writes_after_the_approval"` exits 0.
- [ ] 2.12 Close with `tools.mutate` on `table.py`, each survivor handled as 2.9 says.
  Verify: `uv run python -m tools.mutate isekai/interface/ui/routes/table.py:1-2000 --tests tests/test_ui_api.py tests/test_record.py tests/test_ui_wire.py "-k not test_without_the_lock_an_update_writes_after_the_approval"` exits 0.

## 3 — The front door

- [ ] 3.1 In `isekai/interface/ui/app.py`, replace the closure `_addressed_here` with the module-level factory ``def _addressed_here(allowed: frozenset[str], origins: frozenset[str])`` above `create_app` and below `_precondition`. It returns an inner `async def` holding the docstring and the body unchanged at their indent, and `create_app` registers it with ``app.middleware("http")(_addressed_here(allowed, origins))`` ([D7](design.md#d7)).
  Verify: `git grep -nE "^def _addressed_here" -- isekai/interface/ui/app.py` prints a line.
- [ ] 3.2 In `isekai/interface/ui/app.py`, move the catch-all `no_route`, the assets' mount and the catch-all `page` out of `create_app` into ``def _bundle(app: FastAPI, bundle: Path) -> None`` below `_addressed_here`, their text unchanged, and call ``_bundle(app, bundle)`` as the last statement before `return app` ([D7](design.md#d7)).
  Verify: `git grep -nE "^def _bundle" -- isekai/interface/ui/app.py` prints a line.
- [ ] 3.3 In `isekai/interface/ui/app.py`, add the module-level tuple `MOUNTS` of `hub_mount`, `staging_mount`, `images_mount`, `sources_mount`, `vocabulary_mount`, `tattoo_mount`, `place_mount`, `render_mount`, `stream_mount` and `review_mount`, in that order and annotated ``tuple[Callable[[FastAPI, Surface], None], ...]``, above `_addressed_here`, and replace the calls of `create_app` with ``for mount in MOUNTS:`` and ``mount(app, surface)`` ([D7](design.md#d7)).
  Verify: `git grep -n "^MOUNTS" -- isekai/interface/ui/app.py` prints a line.
- [ ] 3.4 In `tests/test_ratchets.py`, remove the row ``"isekai/interface/ui/app.py::create_app": 1315`` from `LONG_FUNCTIONS`, since `create_app` now holds fewer lines than the ceiling ([D9](design.md#d9)).
  Verify: `git grep -nE "^    \"isekai/interface/ui/app.py" -- tests/test_ratchets.py` prints nothing.
- [ ] 3.5 In `tests/test_ratchets.py`, lower `FUNCTION_ROWS` to ``FUNCTION_ROWS = 8``, the count of the rows `LONG_FUNCTIONS` now holds.
  Verify: `git grep -n "^FUNCTION_ROWS = 8" -- tests/test_ratchets.py` prints a line.
- [ ] 3.6 Re-derive the *Imported by* tables with `uv run python -m tools.derive_imported_by`: the pruned imports of `app.py` change them.
  Verify: `uv run pytest tests/test_docs.py` exits 0.
- [ ] 3.7 Prove the move against the ratchets, which read `create_app` as no offender, and against the record, the layers, the entry point's imports, the wire and the server's own tests.
  Verify: `uv run pytest tests/test_record.py tests/test_ratchets.py tests/test_layers.py tests/test_docs.py tests/test_pipeline_cli.py tests/test_ui_wire.py tests/test_ui_api.py tests/test_ui.py` exits 0.
- [ ] 3.8 Close with `tools.mutate` on the first range of `isekai/interface/ui/app.py` as it now stands, which holds the mounts' tuple, the factory and the start of `_bundle` ([D8](design.md#d8)). Kill each survivor with a case added to an existing test; name it in [Equivalent mutants](design.md#equivalent-mutants) only when no case can tell it from the code.
  Verify: `uv run python -m tools.mutate isekai/interface/ui/app.py:150-250 --tests tests/test_ui_api.py tests/test_record.py tests/test_ui_wire.py "-k not test_without_the_lock_an_update_writes_after_the_approval"` exits 0.
- [ ] 3.9 Close with the next range of `isekai/interface/ui/app.py`, which holds the rest of `_bundle` and `create_app`, each survivor handled as 3.8 says.
  Verify: `uv run python -m tools.mutate isekai/interface/ui/app.py:251-350 --tests tests/test_ui_api.py tests/test_record.py tests/test_ui_wire.py "-k not test_without_the_lock_an_update_writes_after_the_approval"` exits 0.

## 4 — The documents

- [ ] 4.1 In `docs/decisions.md`, change D59's *Accepts* line to ``the middleware, the refusal handler and the catch-alls stay in `app.py`, which also keeps `make_jobs` and `run`; none is a resource. Reopen when a route of a resource is declared in `create_app` again.`` ([D59](../../../docs/decisions.md#d59--a-resource-is-a-class-registered-from-a-table-over-one-surface)).
  Verify: `git grep -n "none is a resource" -- docs/decisions.md` prints a line.
- [ ] 4.2 In D59's statement, change ``a `ROUTES` table of `Route(method, path, handler)`.`` to say each row may add a `status`: ``a `ROUTES` table of `Route(method, path, handler)` rows, each with a `status` where the route answers other than `200`.``
  Verify: `git grep -n "where the route answers other than" -- docs/decisions.md` prints a line.
- [ ] 4.3 In D59's *Made by* line, add `0158` after `0154`.
  Verify: `git grep -nE "0154.{4}0158" -- docs/decisions.md` prints a line.
- [ ] 4.4 In the docstring of `isekai/interface/ui/app.py`, change ``They hold the vocabulary, tattoo library and place routes, `RenderRoutes`, `StreamRoutes` and `ReviewRoutes`; `create_app` takes what a test replaces and declares the routes that read it, and the rest.`` to name `HubRoutes`, `StagingRoutes`, `ImageRoutes` and `SourceRoutes` beside them, and to say `create_app` takes what a test replaces, builds the surface and mounts each, while the guard, the refusal handler and the catch-alls are this module's own.
  Verify: `git grep -n "StagingRoutes" -- isekai/interface/ui/app.py` prints a line.
- [ ] 4.5 In the same docstring, change ``It owns HTTP routing and status codes, serving photograph bytes and the built bundle,`` to ``It owns the guard on every request, the mounting of each resource and the built bundle,``.
  Verify: `git grep -n "serving photograph bytes" -- isekai/interface/ui/app.py` prints nothing.
- [ ] 4.6 In `isekai/interface/README.md`, change the `ui/routes/` row's ``the vocabulary, tattoo library, place, render and jobs, review, and events routes`` to ``the hub, staging, images, sources, vocabulary, tattoo library, place, render and jobs, review, and events routes``.
  Verify: `git grep -n "the hub, staging, images, sources, vocabulary" -- isekai/interface/README.md` prints a line.
- [ ] 4.7 In the same README, change the `ui/app.py` row's ``the library, staging, images and sources endpoints `create_app` still declares, the catch-alls`` to ``the guard on every request, the refusal handler, the catch-alls``.
  Verify: `git grep -n "the library, staging, images and sources endpoints" -- isekai/interface/README.md` prints nothing.
- [ ] 4.8 In `docs/modules.md`, replace the words "the surface's staging routes" with "`StagingRoutes` of `interface/ui/routes/staging.py`", and "the hub's route both call it" with "`HubRoutes` of `interface/ui/routes/hub.py` both call it".
  Verify: `git grep -n "HubRoutes" -- docs/modules.md` prints a line.
- [ ] 4.9 In `docs/modules.md`, after the words "review's `withdraw`" add ", which `ImageRoutes` of `interface/ui/routes/images.py` calls", keeping the semicolon that follows.
  Verify: `git grep -n "ImageRoutes" -- docs/modules.md` prints a line.
- [ ] 4.10 In `docs/principles.md`, replace "`interface/ui/app.py`'s `delete_render`" with "`interface/ui/routes/images.py`'s `delete_render`".
  Verify: `git grep -n "routes/images.py" -- docs/principles.md` prints a line.
- [ ] 4.11 In `ARCHITECTURE.md`, after "a class a resource over one `Surface`" add "; `ui/app.py` keeps the guard on every request, the refusal handler and the catch-alls".
  Verify: `git grep -n "keeps the guard on every request" -- ARCHITECTURE.md` prints a line.
- [ ] 4.12 Replay the recorded mutants: every entry's `find` must occur once in its file and each must die.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits 0 with no survivor.
- [ ] 4.13 Prove the documents against the record, the ratchets, the layers, the entry point's imports, the wire and the server's own tests.
  Verify: `uv run pytest tests/test_record.py tests/test_ratchets.py tests/test_layers.py tests/test_docs.py tests/test_pipeline_cli.py tests/test_ui_wire.py tests/test_ui_api.py tests/test_ui.py` exits 0.
