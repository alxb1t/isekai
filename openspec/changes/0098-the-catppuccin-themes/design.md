# Design — 0098 the Catppuccin themes

How Latte, Frappé, Macchiato and Mocha become token blocks, how `⇧T` chooses one and the browser keeps it, and what holds each.
**Verdict: feasible.**

## Context

The app's colours are CSS custom properties on `:root` in `ui/src/styles.css`, read everywhere by `var(--…)`:

```
ui/index.html ─▶ main.ts ─▶ styles.css  :48-125   Nocturne, vendored byte for byte (:1-14)
                         │              :340-366  the app's tokens, ui/design/spec.md §2
                         ├─▶ themes.css           new: a block per flavour
                         └─▶ app.css              reads both sets; its header says it invents no hex
```

At `22291a5f`, these colours in `ui/src/app.css` escape the tokens: `#0f1018` at `:182` (`.band`) and `:189`
(`.band__resolve`); `:396`'s gradient, a copy of `--placeholder`; `.drawer::backdrop` at `:522-524`, a wash of
`--ground`; and `.overlay` at `:1539`, `--color-bg` mixed with `black`. Nothing in `ui/` reads
`prefers-color-scheme`, `color-scheme`, `data-theme` or `localStorage`. The vitest suite runs in node, with no DOM
(`ui/vitest.config.ts`), and serves a CSS import as an empty string unless `css`
is on. The palette is `catppuccin/palette` v1.8.0.

## Goals / Non-Goals

**Goals:** every colour a theme can reach is a token; each Catppuccin flavour sets every token, as hex; a theme dialog on
`⇧T`; the choice kept and painted first; each flavour's contrast held by a test.

**Non-Goals:** retuning Nocturne; the sheet's component classes in `styles.css`; a theme per screen.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | **The escapes become tokens.** In `ui/src/styles.css`'s app block, after `--shadow-bar`, add `--band: #0f1018;`, `--scrim-drawer: color-mix(in srgb, var(--ground) 80%, transparent);` and `--overlay: color-mix(in srgb, var(--color-bg) 72%, black);`. In `ui/src/app.css`: `:182` and `:189` `color: #0f1018;` → `color: var(--band);`; `:396`'s `background: repeating-linear-gradient(…);` → `background: var(--placeholder);`; `:523` → `background: var(--scrim-drawer);`; `:1538`'s comment → `/* The cheatsheet's ground, a token each theme sets. */` and `:1539` → `background: var(--overlay);`. Nocturne draws the same | no theme rewrites a rule; `app.css`'s header (`:1-3`) holds again | a literal per theme in `app.css` |
| <a id="d2"></a>**D2** | **`ui/src/themes.css`** opens with the [header](#the-header), then `[data-theme="latte"]`, `[data-theme="frappe"]`, `[data-theme="macchiato"]` and `[data-theme="mocha"]` blocks, in that order. Each declares every token in the [hex table](#the-hex-table), in its order, one `  --token: value;` line each, copied from its column. No `color-mix()`, `var()` or `rgba()` appears in a block; Latte's link rule is not a block. After the blocks: `:where([data-theme="latte"]) a { color: var(--accent-ink); }`, under the comment `/* Latte's accent is under 4.5:1 as link text; its links take the accent ink. */`. `ui/src/main.ts` imports `./themes.css` between `./styles.css` and `./app.css` | `[data-theme]` weighs what `:root` weighs, so the later file wins; `:where()` keeps app.css's class rules above Latte's link rule | `@catppuccin/palette`, a dependency; `:root[data-theme]`, which no dialog row could match ([D4](#d4)) |
| <a id="d3"></a>**D3** | **The map is by Catppuccin's role**, the [hex table](#the-hex-table) its values. Grounds: `--ground`, `-deep`, `-media` base, mantle, crust; `--raised` mantle on Latte, else surface0; `--raised-2` surface1. Lines: `--line`, `-soft`, `-disabled`, `--chip-line` surface1; `--line-control`, `--tick-locked` surface2. Inks on Macchiato and Mocha: text, subtext1, subtext0, overlay1, overlay2, overlay0 for `--ink`, `-1b`, `-2`, `-3`, `-muted`, `-disabled`; on Frappé and Latte, `--ink-2` subtext1, `--ink-3` overlay2 and `--ink-muted` subtext0. `--accent` and `--color-accent` mauve; `--color-accent-2` blue; `--accent-dim` mauve 50% over base; `--accent-ink` mauve 80% over text. `--focus` lavender, on Latte lavender 80% over text. `--band` crust, on Latte base. `--overlay` crust. The **shade** is crust, on Latte text: `--scrim` the shade at 40%; `--shadow-sheet` and `-bar` at 50% and 55%, on Latte 20% and 22%; `--scrim-drawer` base at 80%, on Latte text at 60%. The sheet: `--color-bg` base, `-surface` as `--raised`, `-text` text, `-divider` text at 16%; `--color-neutral-100…900` text at 100, 88, 76, 64, 52, 40, 28, 18 and 10% over base; each accent ramp's `100…400` its role at 20, 40, 60 and 80% over text, `500` the role, `600…900` the role at 80, 60, 40 and 20% over base; `--color-section`, `-glow`, `-ghost` surface0, 1, 2; `--shadow-sm/md/lg` Nocturne's shapes on `neutral-800`, `-700`, `-500`, the shade at 55% and 65%, on Latte 20% and 25%. `--placeholder` Nocturne's gradient on surface0, then surface1. A mix is sRGB, each channel rounded half to even; an alpha is `#rrggbbaa` | Catppuccin's own roles; the ramps run from ink to ground on every flavour, so each `var(--…)` keeps its meaning on Latte; the Frappé and Latte inks pass AA where Q3's did not | lightness-matched ramps, which flip on Latte; `color-mix()` in the blocks, which the contrast test cannot read |
| <a id="d4"></a>**D4** | **`ui/src/components/ThemeDialog.vue`** follows `DraftDialog.vue`: a `<dialog class="render-dialog" aria-label="Theme" data-theme-dialog @cancel.prevent>`, its head `<h2 class="render-dialog__title">Theme</h2>`, a `render-dialog__targets` div of a `<button class="theme-dialog__row" type="button" :data-theme="theme.id" data-theme-row @click="keep(theme.id)">` per `THEMES` entry showing its `name`, and a footer Close button with `<KeyHint command="cancel" />` that runs `restore`. `onMounted` runs `showModal()` and focuses the row of `choice.opened`; `useHeldFocus(dialog, restore)`. `useKeys('overlay', …)`: `cancel` `Escape` → `restore`; `down` `KeyJ` `ArrowDown` and `up` `KeyK` `ArrowUp` → focus the row `clamp`ed from the focused one by ±1, then `choice.preview` its theme; `keep` `Enter`, when a row is focused, → `keep` its theme. `keep` and `restore` call the chooser's, then emit `close`. `ui/src/App.vue` adds `{ id: 'theme', keys: [shifted('KeyT')], label: 'theme', run: () => (theming.value = true) }` after `renders`, a `theming` ref, and `<ThemeDialog v-if="theming" @close="theming = false" />` after `<KeyList …/>`. `ui/src/app.css` adds the [row rule](#the-row-rule). `styles.css`'s app block selector `:root {` → `:root,\n[data-theme="nocturne"] {` | a row's `data-theme` gives it its own theme's tokens, so each name is drawn in its own colours; ⇧T is free and D25's shape | a swatch map of hex per theme in TypeScript, a second copy of the values |
| <a id="d5"></a>**D5** | **`ui/src/themes.ts`** exports `THEMES`, `[{ id: 'nocturne', name: 'Nocturne' }, { id: 'latte', name: 'Latte' }, { id: 'frappe', name: 'Frappé' }, { id: 'macchiato', name: 'Macchiato' }, { id: 'mocha', name: 'Mocha' }] as const`; `type Theme`, its ids; `KEPT = 'isekai.theme'`; `interface Root { dataset: DOMStringMap }`; `interface Kept { setItem(key: string, value: string): void }`; `shown(root: Root): Theme`, the root's `data-theme` when a `THEMES` id, else `'nocturne'`; and `chooser(root: Root, kept: Kept)`, returning `{ opened, preview, keep, restore }`: `opened` is `shown(root)`; `preview(theme)` sets `root.dataset.theme`; `keep(theme)` previews it, then `kept.setItem(KEPT, theme)`; `restore()` previews `opened`. The dialog passes `document.documentElement` and `localStorage` | the choice is testable in node with a fake root and a fake store | a Pinia store: nothing else reads the theme |
| <a id="d6"></a>**D6** | **The first paint.** `ui/index.html`'s `<head>` gains, after `<title>`, the [head script](#the-head-script), a classic inline script. Nocturne is the absence of a kept name, and an unknown name is ignored | no flash; no CSP is sent (`isekai/interface/ui/app.py`), so an inline script runs | a module script, which runs after the first paint |
| <a id="d7"></a>**D7** | **`ui/src/themes.test.ts`** reads `./themes.css`, `./styles.css` and `../index.html` with `?raw`. A sheet's blocks are its comment-free `selector { … }` runs and their `--name: value;` declarations; Nocturne's tokens are those of each `styles.css` block whose comma-split selector list holds `:root`, but `--font-*`, `--space-*` and `--radius-*`. `ratio` is WCAG 2.x's, from each hex's relative luminance. Its [pairs](#the-pairs) are Q6's, Q17's and Q18's. *Each to a hex value* means: in each Catppuccin block, every value holds at least one colour, each `#rrggbb` or `#rrggbbaa`, and no `color-mix(`, `var(` or `rgba(`; a shadow or the gradient holds several. `ui/vitest.config.ts` sets `css: true`, under a comment that a test reads a sheet as text, which vitest serves empty without it | the contrast is the one way a theme breaks the app; a test that reads the shipped file cannot drift from it | a Playwright screenshot per theme; a copy of the hex in the test |
| <a id="d8"></a>**D8** | **The record.** `docs/decisions.md` gains [D48](#the-decision) after D47, before `## Infrastructure`. `ui/design/spec.md` §2 gains the `--band`, `--scrim-drawer` and `--overlay` rows after `scrim` and a **Themes.** paragraph after the table; §7's everywhere row gains `⇧T the theme dialog` after `⇧I Renders` ([the design spec](#the-design-spec)). D25 is unchanged: ⇧T is one more `⇧` command | the first state the app keeps in a browser is a decision in force | editing D25 |

### The header

`ui/src/themes.css` opens with this comment, verbatim:

```css
/* Catppuccin's four flavours as the app's and the sheet's colour tokens (D48).
   The palette is copied by hand from catppuccin/palette v1.8.0,
   https://github.com/catppuccin/palette, and mapped by role; the ramps and
   mixes are computed once and written as hex. Nocturne, the default, is
   styles.css's own.

   MIT License

   Copyright (c) 2021 Catppuccin

   Permission is hereby granted, free of charge, to any person obtaining a copy
   of this software and associated documentation files (the "Software"), to deal
   in the Software without restriction, including without limitation the rights
   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   copies of the Software, and to permit persons to whom the Software is
   furnished to do so, subject to the following conditions:

   The above copyright notice and this permission notice shall be included in all
   copies or substantial portions of the Software.

   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
   SOFTWARE. */
```

### The hex table

Every value each block declares, per [D3](#d3), computed from `catppuccin/palette` v1.8.0. Copy a column into its
block, row for row; derive nothing.

| token | Latte | Frappé | Macchiato | Mocha |
|---|---|---|---|---|
| `--color-bg` | `#eff1f5` | `#303446` | `#24273a` | `#1e1e2e` |
| `--color-surface` | `#e6e9ef` | `#414559` | `#363a4f` | `#313244` |
| `--color-text` | `#4c4f69` | `#c6d0f5` | `#cad3f5` | `#cdd6f4` |
| `--color-accent` | `#8839ef` | `#ca9ee6` | `#c6a0f6` | `#cba6f7` |
| `--color-accent-2` | `#1e66f5` | `#8caaee` | `#8aadf4` | `#89b4fa` |
| `--color-divider` | `#4c4f6929` | `#c6d0f529` | `#cad3f529` | `#cdd6f429` |
| `--color-neutral-100` | `#4c4f69` | `#c6d0f5` | `#cad3f5` | `#cdd6f4` |
| `--color-neutral-200` | `#60627a` | `#b4bde0` | `#b6bedf` | `#b8c0dc` |
| `--color-neutral-300` | `#73768b` | `#a2abcb` | `#a2aac8` | `#a3aac4` |
| `--color-neutral-400` | `#87899b` | `#9098b6` | `#8e95b2` | `#8e94ad` |
| `--color-neutral-500` | `#9a9dac` | `#7e85a1` | `#7a809b` | `#797e95` |
| `--color-neutral-600` | `#aeb0bd` | `#6c728c` | `#666c85` | `#64687d` |
| `--color-neutral-700` | `#c1c4ce` | `#5a6077` | `#52576e` | `#4f5265` |
| `--color-neutral-800` | `#d2d4dc` | `#4b5066` | `#42465c` | `#3e3f52` |
| `--color-neutral-900` | `#dfe1e7` | `#3f4458` | `#35384d` | `#303042` |
| `--color-accent-100` | `#584b84` | `#c7c6f2` | `#c9c9f5` | `#cdccf5` |
| `--color-accent-200` | `#64469f` | `#c8bcef` | `#c8bff5` | `#ccc3f5` |
| `--color-accent-300` | `#7042b9` | `#c8b2ec` | `#c8b4f6` | `#ccb9f6` |
| `--color-accent-400` | `#7c3dd4` | `#c9a8e9` | `#c7aaf6` | `#cbb0f6` |
| `--color-accent-500` | `#8839ef` | `#ca9ee6` | `#c6a0f6` | `#cba6f7` |
| `--color-accent-600` | `#9d5ef0` | `#ab89c6` | `#a688d0` | `#a88bcf` |
| `--color-accent-700` | `#b183f1` | `#8c74a6` | `#8570ab` | `#8670a7` |
| `--color-accent-800` | `#c6a7f3` | `#6e5e86` | `#655785` | `#63547e` |
| `--color-accent-900` | `#daccf4` | `#4f4966` | `#443f60` | `#413956` |
| `--color-accent-2-100` | `#435485` | `#bac8f4` | `#bdcbf5` | `#bfcff5` |
| `--color-accent-2-200` | `#3a58a1` | `#afc1f2` | `#b0c4f5` | `#b2c8f6` |
| `--color-accent-2-300` | `#305dbd` | `#a3b9f1` | `#a4bcf4` | `#a4c2f8` |
| `--color-accent-2-400` | `#2761d9` | `#98b2ef` | `#97b5f4` | `#97bbf9` |
| `--color-accent-2-500` | `#1e66f5` | `#8caaee` | `#8aadf4` | `#89b4fa` |
| `--color-accent-2-600` | `#4882f5` | `#7a92cc` | `#7692cf` | `#7496d1` |
| `--color-accent-2-700` | `#729ef5` | `#677bab` | `#6177aa` | `#5e78a8` |
| `--color-accent-2-800` | `#9bb9f5` | `#556389` | `#4d5d84` | `#495a80` |
| `--color-accent-2-900` | `#c5d5f5` | `#424c68` | `#38425f` | `#333c57` |
| `--color-section` | `#ccd0da` | `#414559` | `#363a4f` | `#313244` |
| `--color-section-glow` | `#bcc0cc` | `#51576d` | `#494d64` | `#45475a` |
| `--color-section-ghost` | `#acb0be` | `#626880` | `#5b6078` | `#585b70` |
| `--shadow-sm` | `0 0 0 1px #d2d4dc` | `0 0 0 1px #4b5066` | `0 0 0 1px #42465c` | `0 0 0 1px #3e3f52` |
| `--shadow-md` | `0 0 0 1px #c1c4ce, 0 6px 18px #4c4f6933` | `0 0 0 1px #5a6077, 0 6px 18px #2326348c` | `0 0 0 1px #52576e, 0 6px 18px #1819268c` | `0 0 0 1px #4f5265, 0 6px 18px #11111b8c` |
| `--shadow-lg` | `0 0 0 1px #9a9dac, 0 16px 40px #4c4f6940` | `0 0 0 1px #7e85a1, 0 16px 40px #232634a6` | `0 0 0 1px #7a809b, 0 16px 40px #181926a6` | `0 0 0 1px #797e95, 0 16px 40px #11111ba6` |
| `--ground` | `#eff1f5` | `#303446` | `#24273a` | `#1e1e2e` |
| `--ground-deep` | `#e6e9ef` | `#292c3c` | `#1e2030` | `#181825` |
| `--ground-media` | `#dce0e8` | `#232634` | `#181926` | `#11111b` |
| `--raised` | `#e6e9ef` | `#414559` | `#363a4f` | `#313244` |
| `--raised-2` | `#bcc0cc` | `#51576d` | `#494d64` | `#45475a` |
| `--line` | `#bcc0cc` | `#51576d` | `#494d64` | `#45475a` |
| `--line-soft` | `#bcc0cc` | `#51576d` | `#494d64` | `#45475a` |
| `--line-control` | `#acb0be` | `#626880` | `#5b6078` | `#585b70` |
| `--line-disabled` | `#bcc0cc` | `#51576d` | `#494d64` | `#45475a` |
| `--focus` | `#6a7cdf` | `#babbf1` | `#b7bdf8` | `#b4befe` |
| `--ink` | `#4c4f69` | `#c6d0f5` | `#cad3f5` | `#cdd6f4` |
| `--ink-1b` | `#5c5f77` | `#b5bfe2` | `#b8c0e0` | `#bac2de` |
| `--ink-2` | `#5c5f77` | `#b5bfe2` | `#a5adcb` | `#a6adc8` |
| `--ink-3` | `#7c7f93` | `#949cbb` | `#8087a2` | `#7f849c` |
| `--ink-muted` | `#6c6f85` | `#a5adce` | `#939ab7` | `#9399b2` |
| `--ink-disabled` | `#9ca0b0` | `#737994` | `#6e738d` | `#6c7086` |
| `--accent` | `#8839ef` | `#ca9ee6` | `#c6a0f6` | `#cba6f7` |
| `--accent-dim` | `#bc95f2` | `#7d6996` | `#756498` | `#746292` |
| `--accent-ink` | `#7c3dd4` | `#c9a8e9` | `#c7aaf6` | `#cbb0f6` |
| `--tick-locked` | `#acb0be` | `#626880` | `#5b6078` | `#585b70` |
| `--chip-line` | `#bcc0cc` | `#51576d` | `#494d64` | `#45475a` |
| `--placeholder` | `repeating-linear-gradient(135deg, #ccd0da 0 5px, #bcc0cc 5px 10px)` | `repeating-linear-gradient(135deg, #414559 0 5px, #51576d 5px 10px)` | `repeating-linear-gradient(135deg, #363a4f 0 5px, #494d64 5px 10px)` | `repeating-linear-gradient(135deg, #313244 0 5px, #45475a 5px 10px)` |
| `--scrim` | `#4c4f6966` | `#23263466` | `#18192666` | `#11111b66` |
| `--shadow-sheet` | `0 30px 80px #4c4f6933` | `0 30px 80px #23263480` | `0 30px 80px #18192680` | `0 30px 80px #11111b80` |
| `--shadow-bar` | `0 20px 50px #4c4f6938` | `0 20px 50px #2326348c` | `0 20px 50px #1819268c` | `0 20px 50px #11111b8c` |
| `--band` | `#eff1f5` | `#232634` | `#181926` | `#11111b` |
| `--scrim-drawer` | `#4c4f6999` | `#303446cc` | `#24273acc` | `#1e1e2ecc` |
| `--overlay` | `#dce0e8` | `#232634` | `#181926` | `#11111b` |

### The row rule

`ui/src/app.css` gains, beside the `render-dialog` rules:

```css
/* The theme dialog's rows, each drawn in its own theme's tokens (D48). */
.theme-dialog__row {
  padding: 8px 14px;
  border: 1px solid var(--line-control);
  border-radius: 4px;
  background: var(--ground);
  color: var(--ink);
  font: inherit;
  text-align: left;
}

.theme-dialog__row:focus {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}
```

### The head script

```html
    <script>
      try {
        const kept = localStorage.getItem('isekai.theme')
        if (['nocturne', 'latte', 'frappe', 'macchiato', 'mocha'].includes(kept))
          document.documentElement.dataset.theme = kept
      } catch {}
    </script>
```

### The pairs

Each Catppuccin flavour fails the test below its ratio; Nocturne's ratios are printed with `console.info` for each
pair whose values are both hex, and fail nothing.

| text | on | at least | from |
|---|---|---|---|
| `--ink`, `--ink-2` | `--ground`, `--raised` | 4.5 | Q6 |
| `--ink-3`, `--ink-muted` | `--ground`, `--raised` | 3 | Q6 |
| `--focus` | `--ground`, `--raised` | 3 | Q18 |
| `--accent-ink` | `--ground`, `--raised` | 4.5 | Q18 |
| `--band` | `--accent` | 4.5 | Q18 |
| `--color-text` | `--color-bg`, `--color-surface` | 4.5 | Q18 |
| `--color-text` | `--overlay` | 4.5 | Q17 |

The ratios at the cut, from `python3 -I fullmap_q19.py palette.json` over the [hex table](#the-hex-table) (the cut's
script, outside the repository): every pair passes. The worst per flavour:

| flavour | worst | pair |
|---|---|---|
| Latte | 3.10 | `--focus` on `--raised` |
| Frappé | 3.48 | `--ink-3` on `--raised` |
| Macchiato | 3.15 | `--ink-3` on `--raised` |
| Mocha | 3.40 | `--ink-3` on `--raised` |

### The decision

`docs/decisions.md`, after D47's `- **Made by:** \`0092\`.`:

```markdown
### D48 · A theme is a token set, chosen in the browser

**A theme sets every colour token the app and the sheet declare, in `ui/src/themes.css`, and nothing else; Nocturne,
the vendored sheet's own, is the default. `⇧T` chooses one, and the browser keeps the choice in `localStorage` under
`isekai.theme`, applied by `ui/index.html`'s head script before the first paint.**

- **Why:** a look is the person's, not the library's, so no API or file holds it. A token set means no screen carries a
  rule of its own for a theme, and a test reads every value.
- **Accepts:** the choice is per browser and per origin, so the UI served on another `--port` opens on Nocturne. Reopen
  when the UI is served from more than one origin.
- **Made by:** `0098`.
```

### The design spec

`ui/design/spec.md` §2, after the `scrim` row:

```markdown
| `--band` | `#0f1018` | text on the billing band |
| `--scrim-drawer` | `color-mix(in srgb, var(--ground) 80%, transparent)` | behind the session drawer |
| `--overlay` | `color-mix(in srgb, var(--color-bg) 72%, black)` | the tag cheatsheet's ground |
```

and after the table, before **Type.**:

```markdown
**Themes.** These are Nocturne's values, the default. Catppuccin's Latte, Frappé, Macchiato and Mocha set every token
in `ui/src/themes.css`, mapped by role, and `⇧T` chooses one
([D48](../../docs/decisions.md#d48--a-theme-is-a-token-set-chosen-in-the-browser)).
```

§7's everywhere row: `⇧I Renders · ⌃;` → `⇧I Renders · ⇧T the theme dialog · ⌃;`.

## Tests

| layer | adds | removes |
|---|---|---|
| unit | `ui/src/themes.test.ts`: `ui:themes:each-catppuccin-theme-meets-aa`, `ui:themes:a-theme-sets-every-colour-token` (phase 1); `ui:themes:the-dialog-previews-keeps-and-restores`, over `chooser` with a fake root and store; `ui:themes:the-first-paint-shows-the-kept-theme`, running the head script from `index.html` with `new Function` under `vi.stubGlobal`'d `localStorage` and `document`, once per `THEMES` id, an unknown name and none, and checking it stands before the module script (phase 2) | none |
| end-to-end | a step at the end of `test_a_reload_lands_on_the_same_hub_and_the_same_review` in `tests/e2e/test_routes.py`, `ui:themes:a-chosen-theme-survives-a-reload`: `Shift+T`, the Nocturne row focused, `ArrowDown` sets `html`'s `data-theme` to `latte`, `Enter` closes the dialog, `body`'s `background-color` is `rgb(239, 241, 245)`, and after `page.reload()` both still hold | none |

At the base, `npm --prefix ui run test` passes 19 files and 58 tests, and `uv run pytest tests/e2e --collect-only -q`
collects 19 tests. This change adds one vitest file and no end-to-end test: one step on Chromium alone. That test
already reloads a screen and checks it is the same (T2); the step runs last, so it leans on no earlier step (T3);
the first paint is client behaviour, but `make e2e` runs one engine. It deletes and merges no test. The browser step
runs by `make e2e` in CI after the push, not in the build: Chromium does not start in an unattended run's sandbox
(`CONTRIBUTING.md`, *The evidence a change carries*).

## Dependencies

None.

## Risks / Trade-offs

- **The accent as text is under 4.5:1 on `--raised` on Latte (4.45) and Frappé (4.30)** — links, `.btn-primary`,
  `.btn-ghost`, `.card-kicker` and the other rules that colour text with `--accent` or `--color-accent`; Macchiato
  (5.21) and Mocha (6.19) pass → only Latte's links are re-routed ([D2](#d2)), as settled; no pair holds the accent
  as text.
- **Native controls draw light on every theme** → no `color-scheme` is set, so Nocturne is unchanged; a dark
  flavour's checkbox is light.
- **The hex is a hand copy** → the vitest reads the shipped file, so a mistyped value that breaks contrast fails it; a
  mistyped value that keeps contrast is a wrong shade only.
- **A non-default `--port` opens on Nocturne** → accepted in [D48](#the-decision).

## Verdict

**feasible.** Every file and line named exists at `22291a5f`, or is new. No dependency, no format version, no
change to the product's images.
