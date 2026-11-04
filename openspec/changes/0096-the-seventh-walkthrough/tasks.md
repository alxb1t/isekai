# Tasks — 0096 the seventh walkthrough

The hub, the viewer, the chain, then the discard, per [design](design.md). Each new test carries the `spec` key its task
names.

## Progress

- [x] 1 — The hub
- [ ] 2 — The viewer
- [ ] 3 — The chain
- [ ] 4 — The discard

## 1 — The hub

- [x] 1.1 `ui/src/views/Hub.vue` and `ui/src/app.css` per [D1](design.md#d1); `ui/design/spec.md`'s hub lines say so.
  Verify: `grep -c 'the tick stays' ui/src/views/Hub.vue` prints `0`, and `uv run python -m tools.test_ui` exits 0.
- [x] 1.2 The library row's chips go from `ui/src/views/Home.vue` and `ui/src/app.css` per [D2](design.md#d2), the API's
  `flows` kept; `ui/design/spec.md`'s library lines say so.
  Verify: `grep -c 'class="library__chip"' ui/src/views/Home.vue` prints `0`, and `uv run pytest tests/test_ui_library.py tests/test_ui_api.py -k "flow or count"` exits 0.

## 2 — The viewer

- [ ] 2.1 `.viewer__frame`, `.viewer__title` and the pick in `ui/src/app.css`, and the hub's and the drawer's titles, per
  [D3](design.md#d3) and [D4](design.md#d4); `ui/design/spec.md`'s viewer and pick lines say so.
  Verify: `grep -c 'seed \${' ui/src/views/Hub.vue` prints `0`, `sed -n '/^\.viewer__title {/,/}/p' ui/src/app.css | grep -c 'contain: inline-size'` prints `1`, and `uv run python -m tools.typecheck_ui` exits 0.

## 3 — The chain

- [ ] 3.1 Add `tagger_of` and read it in `_from_source`, per [D5](design.md#d5); tests bound to
  `sheet:tags-from:a-source-without-a-list-leads-on`.
  Verify: `uv run pytest tests/test_sheet_stage.py -k leads_on` exits 0.
- [ ] 3.2 `_caption`, `_wd14` and `_tags` in `isekai/interface/ui/app.py` read the tagger's when the flow holds none, per
  [D5](design.md#d5); tests in `tests/test_ui_api.py` bound to `ui:source:a-two-hop-sheet-shows-the-taggers-caption` and
  `ui:source:a-borrowed-sheet-shows-the-taggers-lists`.
  Verify: `uv run pytest tests/test_ui_api.py -k taggers` exits 0.

## 4 — The discard

- [ ] 4.1 `discard` in `isekai/pipeline/review.py` per [D6](design.md#d6); a test in `tests/test_review.py` bound to
  `review:discard:a-drafted-draft-is-undone-whole`.
  Verify: `uv run pytest tests/test_review.py -k undone_whole` exits 0.
- [ ] 4.2 Rewrite the plain design cites per [D7](design.md#d7) in `ui/src/app.css`, `Hub.vue`, `Review.vue`,
  `composables/useViewer.ts`, `components/RendersBlock.vue`, `composables/useCentred.ts`, `slots.ts`, `staging.ts`,
  `components/ImportSheet.vue` and `cells.ts`.
  Verify: `git grep -nE '\(D[0-9]+\)' -- 'ui/src/*.ts' 'ui/src/*.vue' 'ui/src/*.css'` prints nothing.
