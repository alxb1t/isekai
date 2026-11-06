# Tasks — 0109 the paydown

The browser steps first, then the remedy, the accent and the record, per [design](design.md). No spec delta, per
[D5](design.md#d5).

## Progress

- [ ] 1 — The tests
- [ ] 2 — The remedy
- [ ] 3 — The accent
- [ ] 4 — The record

## 1 — The tests

- [ ] 1.1 In `tests/e2e/test_import.py`'s `test_importing_a_new_collection_opens_its_hub_with_every_source_unassigned`,
  per [D1](design.md#d1): after `page.locator(".import__tile").first.focus()`, add `chosen: list[FileChooser] = []`,
  `page.on("filechooser", chosen.append)` and `page.keyboard.press("Shift+A")`; before `commit.continue_()`, add
  `assert not chosen`. Import `FileChooser` from `playwright.sync_api`.
  Verify: `grep -n -e 'page.on("filechooser", chosen.append)' -e 'assert not chosen' tests/e2e/test_import.py` prints a line for each.
- [ ] 1.2 In `tests/e2e/test_routes.py`, add `@pytest.mark.spec("ui:batch-folder:an-edge-row-shows-the-head")` to
  `test_a_reload_lands_on_the_same_hub_and_the_same_review`, per [D1](design.md#d1).
  Verify: `grep -n 'ui:batch-folder:an-edge-row-shows-the-head' tests/e2e/test_routes.py` prints a line.
- [ ] 1.3 After that test's first `to_be_focused()`, with `rows = page.locator(".library__row[data-collection]")` and
  `new = page.get_by_role("button", name="New collection")`: a `1280`×`300` viewport; `j` `rows.count() - 1` times,
  `rows.last` focused, `new` `not_to_be_in_viewport()`; `k` as often, `rows.first` focused, `new` `to_be_in_viewport()`;
  then a `1280`×`720` viewport, per [D1](design.md#d1).
  Verify: `grep -n -e 'set_viewport_size' -e 'not_to_be_in_viewport' -e 'name="New collection"' tests/e2e/test_routes.py` prints a line for each.

## 2 — The remedy

- [ ] 2.1 **HALT CHECK** `review` writes no draft for a flow holding a version unless `--new-version` asks, the premise
  of [D2](design.md#d2).
  Verify: `grep -n 'if versions(review_directory) and not new_version:' isekai/pipeline/review.py` prints a line.
- [ ] 2.2 In `tests/test_review.py`'s `test_a_copy_carries_the_sources_fields_and_the_targets_schema_validates_them`,
  `stage_command(run, "review", CONTROL) in str(refused.value)` → `stage_command(run, "review", CONTROL,
  options=NEW_VERSION) in str(refused.value)`.
  Verify: `grep -n 'stage_command(run, "review", CONTROL, options=NEW_VERSION)' tests/test_review.py` prints a line.
- [ ] 2.3 In `isekai/pipeline/review.py`'s `schema_remedy`, ``f"`{stage_command(run, STAGE, flow)}`, edit the draft, then "``
  → `f"{_again(run, flow)}, edit the draft, then "`, per [D2](design.md#d2).
  Verify: `uv run pytest tests/test_review.py -k targets_schema_validates_them` exits 0.

## 3 — The accent

- [ ] 3.1 In `ui/src/themes.test.ts`'s `PAIRS`, after `[['--color-text'], ['--color-bg', '--color-surface'], 4.5],`
  add `[['--color-accent'], ['--color-bg', '--color-surface'], 4.5],`, per [D3](design.md#d3).
  Verify: `grep -n -F "[['--color-accent'], ['--color-bg', '--color-surface'], 4.5]," ui/src/themes.test.ts` prints a line.
- [ ] 3.2 In `ui/src/themes.css`, Latte's `--color-accent: #8839ef;` → `--color-accent: #7c3dd4;` and Frappé's
  `--color-accent: #ca9ee6;` → `--color-accent: #c9a8e9;`, per [D3](design.md#d3).
  Verify: `uv run python -m tools.test_ui` exits 0.
- [ ] 3.3 At the end of `ui/src/themes.css`, delete the comment `/* Latte's accent is under 4.5:1 as link text; its
  links take the accent ink. */`, the rule `:where([data-theme="latte"]) a { color: var(--accent-ink); }` and the blank
  line above them, per [D3](design.md#d3).
  Verify: `grep -n -F ':where(' ui/src/themes.css` prints nothing.

## 4 — The record

- [ ] 4.1 In `ui/design/spec.md`'s state table, per [D4](design.md#d4): `| Renders | a missing image |` → `| Renders |
  a missing image, its record kept |`, and after that row add `| Renders | a deleted render | \`no render is here, its
  record and its image are gone\` |`.
  Verify: `grep -n -e 'a missing image, its record kept' -e 'no render is here, its record and its image are gone' ui/design/spec.md` prints a line for each.
- [ ] 4.2 In `docs/decisions.md`'s D48 lead, the two lines ending "nothing else but Latte's" and "keeps the choice in
  `localStorage` under" become the two below, per [D4](design.md#d4); D48's **Made by:** `` `0098`. `` → `` `0098`,
  `0109`. ``.
  ```markdown
  **A theme sets every colour token the app and the sheet declare, in `ui/src/themes.css`, and nothing else; Nocturne,
  the vendored sheet's own, is the default. `⇧T` chooses one, and the browser keeps the choice in `localStorage` under
  ```
  Verify: `grep -n -e 'nothing else but' -e "Latte's link" docs/decisions.md` prints nothing.
