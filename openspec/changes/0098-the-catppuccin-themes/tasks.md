# Tasks — 0098 the Catppuccin themes

The tokens, then the dialog, then the record, per [design](design.md).

## Progress

- [ ] 1 — The tokens
- [ ] 2 — The dialog
- [ ] 3 — The record

## 1 — The tokens

- [ ] 1.1 **HALT CHECK** The band's literal sits in `ui/src/app.css` at `:182` and `:189`, as [D1](design.md#d1) names.
  Verify: `grep -c '#0f1018' ui/src/app.css` prints `2`.
- [ ] 1.2 Add `--band`, `--scrim-drawer` and `--overlay` to the app block of `ui/src/styles.css`, after `--shadow-bar`,
  per [D1](design.md#d1). Nocturne's block, `:48-125`, stays byte for byte.
  Verify: `grep -c -F -e '--band: #0f1018;' -e '--scrim-drawer: color-mix(in srgb, var(--ground) 80%, transparent);' -e '--overlay: color-mix(in srgb, var(--color-bg) 72%, black);' ui/src/styles.css` prints `3`.
- [ ] 1.3 In `ui/src/app.css`, point `.band` (`:182`), `.band__resolve` (`:189`) and the tile at `:396` at
  `var(--band)` and `var(--placeholder)`, per [D1](design.md#d1).
  Verify: `grep -L -e '#0f1018' -e '#1f2030' ui/src/app.css` prints `ui/src/app.css`.
- [ ] 1.4 In `ui/src/app.css`, point `.drawer::backdrop` (`:523`) at `var(--scrim-drawer)`, and `.overlay` (`:1539`)
  at `var(--overlay)` with `:1538`'s new comment, per [D1](design.md#d1).
  Verify: `grep -c -F -e 'var(--scrim-drawer)' -e 'var(--overlay)' ui/src/app.css` prints `2`.
- [ ] 1.5 Write `ui/src/themes.css`: [the header](design.md#the-header), the Latte, Frappé, Macchiato and Mocha blocks from
  [the hex table](design.md#the-hex-table), and Latte's link rule, per [D2](design.md#d2).
  Verify: `grep -c '^\[data-theme="[a-z]*"\] {$' ui/src/themes.css` prints `4`.
- [ ] 1.6 Import `./themes.css` in `ui/src/main.ts`, between `./styles.css` and `./app.css`, per [D2](design.md#d2).
  Verify: `grep -n "import './themes.css'" ui/src/main.ts` prints `6:import './themes.css'`.
- [ ] 1.7 Set `css: true` in `ui/vitest.config.ts`'s `test`, with its comment, which does not repeat `css: true`, per
  [D7](design.md#d7).
  Verify: `grep -c 'css: true' ui/vitest.config.ts` prints `1`.
- [ ] 1.8 Write `ui/src/themes.test.ts` with `ui:themes:each-catppuccin-theme-meets-aa` and
  `ui:themes:a-theme-sets-every-colour-token`, per [D7](design.md#d7) and [the pairs](design.md#the-pairs).
  Verify: `npm --prefix ui run test -- src/themes.test.ts` exits 0.

## 2 — The dialog

- [ ] 2.1 Write `ui/src/themes.ts` per [D5](design.md#d5).
  Verify: `grep -c "export const KEPT = 'isekai.theme'" ui/src/themes.ts` prints `1`.
- [ ] 2.2 Write `ui/src/components/ThemeDialog.vue` per [D4](design.md#d4).
  Verify: `grep -c 'useHeldFocus(dialog, restore)' ui/src/components/ThemeDialog.vue` prints `1`.
- [ ] 2.3 Declare `⇧T` and mount the dialog in `ui/src/App.vue`, per [D4](design.md#d4).
  Verify: `grep -c '<ThemeDialog v-if="theming"' ui/src/App.vue` prints `1`.
- [ ] 2.4 In `ui/src/styles.css`, the app block's `:root {` (`:340`) becomes `:root,` and `[data-theme="nocturne"] {`
  on two lines, `:root` kept; add [the row rule](design.md#the-row-rule) to `ui/src/app.css`; per [D4](design.md#d4).
  Verify: `grep -c -e '^:root,$' -e '^\[data-theme="nocturne"\] {$' -e '^\.theme-dialog__row {$' ui/src/styles.css ui/src/app.css` prints `ui/src/styles.css:2` and `ui/src/app.css:1`.
- [ ] 2.5 Add [the head script](design.md#the-head-script) to `ui/index.html`'s `<head>`, after `<title>`, per
  [D6](design.md#d6).
  Verify: `grep -c "localStorage.getItem('isekai.theme')" ui/index.html` prints `1`.
- [ ] 2.6 Add `ui:themes:the-dialog-previews-keeps-and-restores` and `ui:themes:the-first-paint-shows-the-kept-theme`
  to `ui/src/themes.test.ts`, per [Tests](design.md#tests).
  Verify: `grep -c -F -e "spec('ui:themes:the-dialog-previews-keeps-and-restores'" -e "spec('ui:themes:the-first-paint-shows-the-kept-theme'" ui/src/themes.test.ts` prints `2`.
- [ ] 2.7 Add the theme step at the end of `test_a_reload_lands_on_the_same_hub_and_the_same_review` in
  `tests/e2e/test_routes.py`, and a `@pytest.mark.spec("ui:themes:a-chosen-theme-survives-a-reload")` decorator above
  it with the others (`:9-11`), per [Tests](design.md#tests). It runs by `make e2e` in CI, not in the build.
  Verify: `grep -c 'ui:themes:a-chosen-theme-survives-a-reload' tests/e2e/test_routes.py` prints `1`.

## 3 — The record

- [ ] 3.1 Add [D48](design.md#the-decision) to `docs/decisions.md` after D47, per [D8](design.md#d8).
  Verify: `grep -c '^### D48 · A theme is a token set, chosen in the browser$' docs/decisions.md` prints `1`.
- [ ] 3.2 Add the `--band`, `--scrim-drawer` and `--overlay` rows and the **Themes.** paragraph to `ui/design/spec.md` §2, and `⇧T` to §7's
  everywhere row, per [the design spec](design.md#the-design-spec).
  Verify: `grep -c -F -e 'scrim-drawer' -e '**Themes.**' -e '⇧T the theme dialog' ui/design/spec.md` prints `3`.
