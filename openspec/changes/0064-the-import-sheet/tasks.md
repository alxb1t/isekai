# Tasks — 0064 the import sheet

The read after the answer, the sheet, Home, then the cards, per [design](design.md). Every new pytest test carries
`@pytest.mark.spec` with the key its task names.

## Progress

- [ ] 1 — The read
- [ ] 2 — The sheet
- [ ] 3 — Home
- [ ] 4 — The cards

## 1 — The read

- [ ] 1.1 **HALT CHECK** — the upload reads in its own request.
  Verify: `grep -c 'importing.receive, name, body, folder, limit' isekai/interface/ui/app.py` prints `1`.
- [ ] 1.2 Make `put_file` in `isekai/interface/ui/app.py` answer `202` once the bytes land, and read staged files one at a time on a reader per staging folder, publishing on `/events?staging=<id>`, per [D1](design.md#d1).
  Verify: `grep -c 'status_code=202' isekai/interface/ui/app.py` prints a number of at least `1`.
- [ ] 1.3 Add `GET /api/staging/{id}/files/{name}/thumb` per [D3](design.md#d3), and bind `ui:sheet:an-upload-is-answered-before-reading` in `tests/test_ui_api.py`.
  Verify: `grep -c '/files/{name}/thumb' isekai/interface/ui/app.py` prints `1`, and `uv run pytest -q tests/test_ui_api.py` exits 0.

## 2 — The sheet

- [ ] 2.1 In `ui/src/components/ImportSheet.vue`, show each tile's states and its preview from the staging stream, and Import's disabled reasons, per [D2](design.md#d2).
  Verify: `grep -c -E 'EventSource|/thumb' ui/src/components/ImportSheet.vue` prints a number of at least `2`, and `uv run python -m tools.typecheck_ui` exits 0.
- [ ] 2.2 Extend the test bound to `ui:sheet:each-file-shows-its-progress` in `tests/e2e/test_import.py` with steps binding `ui:sheet:a-conversion-shows-on-its-tile` and `ui:sheet:a-ready-tile-shows-its-preview`, through the HEIC fixture.
  Verify: `uv run pytest -q tests/e2e/test_import.py` exits 0, and `grep -c -E 'ui:sheet:a-conversion-shows-on-its-tile|ui:sheet:a-ready-tile-shows-its-preview' tests/e2e/test_import.py` prints `2`.

## 3 — Home

- [ ] 3.1 Order Home's first start in `ui/src/views/Home.vue` as [D4](design.md#d4) says, and add a step to the first test in `tests/e2e/test_import.py` that sees *New batch* below the privacy line on an empty library.
  Verify: `uv run pytest -q tests/e2e/test_import.py` exits 0.

## 4 — The cards

- [ ] 4.1 Move the approval's step out of the test bound to `ui:draft-update:a-stale-precondition-is-refused` into a test bound to `ui:draft-update:a-stale-approval-is-refused` in `tests/test_ui_api.py`, per [D5](design.md#d5).
  Verify: `grep -c 'ui:draft-update:a-stale-approval-is-refused' tests/test_ui_api.py` prints `1`, and `uv run pytest -q tests/test_ui_api.py` exits 0.
- [ ] 4.2 Rewrite the docstring of `tests/test_ui_api.py` to name what it proves and the gate's pytest command, per [D5](design.md#d5).
  Verify: `grep -c -E 'four .ui. scenarios|gate command five' tests/test_ui_api.py` prints `0`.
