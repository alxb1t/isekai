# Tasks — 0062 run flow

The copy, import, `assign`, progress, the job and its stream, the sheet, the hub, then the docs, per
[design](design.md). Every new pytest test carries `@pytest.mark.spec` with the key its task names.

## Progress

- [x] 1 — The copy
- [x] 2 — Import
- [x] 3 — Assign and the offered flows
- [x] 4 — Progress
- [x] 5 — The job and its stream
- [x] 6 — The sheet
- [x] 7 — The hub
- [ ] 8 — The docs

## 1 — The copy

- [x] 1.1 **HALT CHECK** — the refusals end in *"then run this command again"*.
  Verify: `grep -rn 'then run this command again' isekai | wc -l | tr -d ' '` prints `5`.
- [x] 1.2 End each of those refusals in `isekai/boundary/ollama.py` and `isekai/shared/vocabulary.py` with *"then try again"*, per [D11](design.md#d11).
  Verify: `grep -rn 'then run this command again' isekai` prints nothing, and `uv run pytest -q tests/test_ollama.py` exits 0.
- [x] 1.3 Add **D42 · A new draft starts from the last approval** to `docs/decisions.md`, per [D11](design.md#d11).
  Verify: `grep -c '^### D42 · A new draft starts from the last approval' docs/decisions.md` prints `1`.

## 2 — Import

- [x] 2.1 Add `pi-heif` per [Dependencies](design.md#dependencies): `uv add pi-heif==1.4.0`.
  Verify: `grep -c 'pi-heif==1.4.0' pyproject.toml` prints `1`.
- [x] 2.2 Add `tests/fixtures/sources/plain.heic`: `sips -s format heic` on a 64×64 solid-colour PNG Pillow writes.
  Verify: `file tests/fixtures/sources/plain.heic` names a HEIF image.
- [x] 2.3 **HALT CHECK** — `pi-heif` decodes the fixture.
  Verify: `uv run python -c "import pi_heif; from PIL import Image; pi_heif.register_heif_opener(); print(Image.open('tests/fixtures/sources/plain.heic').size)"` prints `(64, 64)`.
- [x] 2.4 Add `config/ui.json` with `upload_limit_mb` 200, and `isekai/pipeline/importing.py` — `read`, `verify`, `commit`, `cancel`, `sweep` — per [D1](design.md#d1), [D2](design.md#d2) and [D3](design.md#d3).
  Verify: `grep -c '"upload_limit_mb": 200' config/ui.json` prints `1`, and `uv run python -c "import isekai.pipeline.importing"` exits 0.
- [x] 2.5 Add the `import` verb to `isekai/interface/cli.py` per [D1](design.md#d1).
  Verify: `uv run python -m isekai import --help` exits 0.
- [x] 2.6 Add `tests/test_importing.py` binding every key of [the import delta](specs/import/spec.md).
  Verify: `uv run pytest -q tests/test_importing.py` exits 0, and `grep -c 'import:stage:leftover-staging-is-swept' tests/test_importing.py` prints `1`.

## 3 — Assign and the offered flows

- [x] 3.1 Add the `assign` verb to `isekai/interface/cli.py` per [D4](design.md#d4), and `tests/test_assign.py` binding every `cli:assign:*` key.
  Verify: `uv run pytest -q tests/test_assign.py` exits 0, and `grep -c 'cli:assign:removing-a-prepared-flow-is-refused' tests/test_assign.py` prints `1`.
- [x] 3.2 Add `flows` to `config/ui.json`, and make `_suffixes` in `isekai/interface/ui/library.py` take the offered flows, per [D5](design.md#d5).
  Verify: `grep -c '"summon-anime-wai", "conjure-anime-wai"' config/ui.json` prints `1`, and `grep -c 'tracked_flows(flows_dir)' isekai/interface/ui/library.py` prints `0`.
- [x] 3.3 Add `POST /api/b/{batch}/assign` to `isekai/interface/ui/app.py`, and the `not cleaned` mark to `library.py`'s source, per [D4](design.md#d4) and [D10](design.md#d10).
  Verify: `grep -c '/api/b/{batch}/assign' isekai/interface/ui/app.py` prints `1`.
- [x] 3.4 In `tests/test_ui_library.py` and `tests/test_ui_api.py`, bind `ui:batch-folder:an-unoffered-flow-has-no-count`, `ui:hub:a-prepared-tick-stays` and `ui:hub:an-uncleaned-source-is-marked`, and move the `ui:hub:an-untracked-flow-is-ignored` test onto a flow the configuration does not offer.
  Verify: `uv run pytest -q tests/test_ui_library.py tests/test_ui_api.py` exits 0, and `grep -c 'ui:hub:an-uncleaned-source-is-marked' tests/test_ui_library.py` prints `1`.

## 4 — Progress

- [x] 4.1 Add `--progress json` to `tag`, `caption` and `sheet` in `isekai/interface/cli.py`, through one reporter behind `_say`, per [D6](design.md#d6).
  Verify: `uv run python -m isekai tag --help` prints `--progress`.
- [x] 4.2 Add `tests/test_progress.py` binding every `cli:progress:*` key.
  Verify: `uv run pytest -q tests/test_progress.py` exits 0, and `grep -c 'cli:progress:' tests/test_progress.py` prints `3`.

## 5 — The job and its stream

- [x] 5.1 Add `probe` to `isekai/boundary/ollama.py` and a `probe` field to `Wiring` in `isekai/interface/wiring.py`, with an answering double in `tests/e2e/wiring.py`, per [D7](design.md#d7).
  Verify: `grep -c 'def probe' isekai/boundary/ollama.py` prints `1`, and `grep -c 'probe=' tests/e2e/wiring.py` prints a number of at least `1`.
- [x] 5.2 Add `isekai/interface/ui/jobs.py` — one slot, Prepare's children, Stop, SIGINT on server stop — and its routes in `app.py`, per [D7](design.md#d7); `serve` in `isekai/interface/ui/__init__.py` calls `importing.sweep` before binding.
  Verify: `uv run python -c "import isekai.interface.ui.jobs"` exits 0, and `grep -c 'sweep(' isekai/interface/ui/__init__.py` prints `1`.
- [x] 5.3 Add `GET /events` to `isekai/interface/ui/app.py` per [D8](design.md#d8).
  Verify: `grep -c '"/events"' isekai/interface/ui/app.py` prints `1`.
- [x] 5.4 Add `tests/test_ui_jobs.py` binding `ui:prepare:one-job-at-a-time`, `ui:prepare:refused-when-ollama-does-not-answer`, `ui:prepare:stop-interrupts-the-job`, `ui:events:a-connection-starts-with-a-snapshot` and `ui:events:a-stages-report-reaches-the-stream`.
  Verify: `uv run pytest -q tests/test_ui_jobs.py` exits 0, and `grep -c 'ui:events:' tests/test_ui_jobs.py` prints `2`.

## 6 — The sheet

- [x] 6.1 Add the staging routes of [D9](design.md#d9) to `isekai/interface/ui/app.py`.
  Verify: `grep -c '/api/staging' isekai/interface/ui/app.py` prints a number of at least `4`.
- [x] 6.2 Add `ui/src/components/ImportSheet.vue` per [D9](design.md#d9) and the design spec's J1 and J7, opened by New batch in `ui/src/views/Home.vue` and Add sources in `ui/src/views/Hub.vue`.
  Verify: `grep -c 'XMLHttpRequest' ui/src/components/ImportSheet.vue` prints a number of at least `1`, and `uv run python -m tools.typecheck_ui` exits 0.
- [x] 6.3 Add `tests/e2e/test_import.py` binding every `ui:sheet:*` key.
  Verify: `uv run pytest -q tests/e2e/test_import.py` exits 0, and `grep -c 'ui:sheet:' tests/e2e/test_import.py` prints `3`.

## 7 — The hub

- [x] 7.1 In `ui/src/views/Hub.vue`, add ticking, multi-select, the Prepare bar and live cells from `/events`, per [D10](design.md#d10) and the design spec's J2 and J8a.
  Verify: `grep -c 'EventSource' ui/src/views/Hub.vue` prints a number of at least `1`, and `uv run python -m tools.typecheck_ui` exits 0.
- [x] 7.2 Add `tests/e2e/test_prepare.py` binding `ui:hub:a-tick-assigns-the-flow`, and extend it with a step binding `ui:prepare:prepare-runs-the-assigned-cells`.
  Verify: `uv run pytest -q tests/e2e/test_prepare.py` exits 0, and `grep -c -E 'ui:hub:a-tick-assigns-the-flow|ui:prepare:prepare-runs-the-assigned-cells' tests/e2e/test_prepare.py` prints `2`.

## 8 — The docs

- [ ] 8.1 Rewrite D4 and add **D43 · A source holds pixels and orientation only** in `docs/decisions.md`, per [D11](design.md#d11).
  Verify: `grep -c '^### D43 · A source holds pixels and orientation only' docs/decisions.md` prints `1`, and `grep -c 'No upload, no captioning, no render button' docs/decisions.md` prints `0`.
- [ ] 8.2 Describe `import`, `assign`, `--progress json`, Prepare and `/events` in `README.md`, `docs/data-flow.md`, `docs/modules.md` and `isekai/interface/ui/README.md`.
  Verify: `grep -c 'isekai assign' README.md docs/data-flow.md` prints a number of at least `1` for each file, and `uv run pytest -q tests/test_docs.py tests/test_spec_prose.py` exits 0.
