---
bump: minor
version: 0.66
---

# 0098 — the Catppuccin themes

The app gains Catppuccin's four flavours — Latte, Frappé, Macchiato and Mocha — beside Nocturne, which stays the
default. `⇧T` opens a theme dialog that previews as it moves, and the browser keeps the choice.

| read | for |
|---|---|
| this file | why, and what changes |
| [the delta](specs/ui/spec.md) | the requirement and its scenarios |
| [design](design.md) | the tokens, every flavour's hex, the dialog, the tests |
| [tasks](tasks.md) | the phases, in build order |

```
1 the tokens   the band, the tile, the drawer and the cheatsheet read tokens; themes.css; the contrast vitest
2 the dialog   themes.ts; ThemeDialog.vue; ⇧T; the first-paint script; the choice's vitest; the browser step
3 the record   docs D48; ui/design/spec.md §2 and §7
```

## Why

**The app has one look, dark, and no way to change it.** A person who works in it for hours wants their own
palette. Catppuccin's flavours are the ones asked for, and Zed's ports show the look to match.

## What Changes

- **The colours that escape the tokens become tokens**: `--band`, `--scrim-drawer` and `--overlay`, and
  `var(--placeholder)` where `app.css` repeats it ([D1](design.md#d1)).
- **`ui/src/themes.css`** holds a block per flavour, every value hex, under Catppuccin's MIT notice
  ([D2](design.md#d2), [D3](design.md#d3)).
- **`⇧T` opens a theme dialog** listing the five themes, each in its own colours; a move previews, `↵` keeps and
  `Esc` restores ([D4](design.md#d4), [D5](design.md#d5)).
- **The choice is kept** in `localStorage` and applied before the first paint ([D6](design.md#d6)).
- **A vitest holds WCAG AA** for each flavour ([D7](design.md#d7)).
- **Docs D48** records that a theme is a token set, chosen in the browser ([D8](design.md#d8)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui`: ADDED *The app offers five themes, and the choice is kept* — the theme dialog and its keys, the kept choice
  and its first paint, the contrast each Catppuccin flavour meets, and every colour token a theme sets.

## Impact

- New: `ui/src/themes.css`, `ui/src/themes.ts`, `ui/src/themes.test.ts`, `ui/src/components/ThemeDialog.vue`.
- Changed: `ui/src/styles.css` (the app's tokens only), `ui/src/app.css`, `ui/src/main.ts`, `ui/src/App.vue`,
  `ui/index.html`, `ui/vitest.config.ts`, `tests/e2e/test_routes.py`, `docs/decisions.md`, `ui/design/spec.md`.
- Nocturne's vendored block in `styles.css` is untouched. No dependency.

## Not in this change

- `prefers-color-scheme`: the choice is the person's, not the system's.
- A settings screen, or a preference kept on the server.
- `@catppuccin/palette` from npm: the values are copied by hand.
- A `color-scheme` declaration: native controls stay light on every theme.
- The accent as text on `--raised`, at 4.45:1 on Latte and 4.30:1 on Frappé: only Latte's links are re-routed
  ([D2](design.md#d2)).
