# Design system — Nocturne, as applied here

`styles.css` in this folder is the system's single stylesheet: the `:root` token sheet (colour roles
with 100–900 OKLCH ramps, type, spacing, radii, shadows) plus a component layer. Link it once from
the Vue app and take **every** colour, font, space, radius and shadow from its variables. Do not
hard-code a hex, a font name, or a px value the tokens already carry.

## Tokens actually used

| Token | Value | Used for |
| --- | --- | --- |
| `--color-bg` | #161826 | app ground |
| `--color-surface` | #232532 | autocomplete dropdown, refusal panel, flow nodes |
| `--color-text` | #e9e9ed | primary text, token totals |
| `--color-accent` | #9184d9 | the one accent: outlines, marks, carets, focus ring |
| `--color-neutral-200/300` | #e4e7f5 / #cfd3e5 | caption body, chip text |
| `--color-neutral-400` | #b2b6ca | field keys, secondary text |
| `--color-neutral-500` | #9397ab | **all small functional text** (see contrast below) |
| `--color-neutral-600` | #75798c | non-informational chrome only — hollow ring borders, chip × |
| `--color-neutral-800/900` | #3f424d / #292b31 | borders, row rules, skeleton bars, tinted fills |
| `--color-accent-300` | #d2cefd | accent-coloured text at body size |
| `--color-accent-600/700/900` | #796cbf / #5d5294 / #2b2741 | chip ×, badge borders, selected row fill |
| `--radius-sm / md` | 4px / 8px | chips / cards, dropdown, buttons |
| `--shadow-md / lg` | see sheet | dropdown / photo overlay |

Type is **Inter** throughout (`--font-heading` / `--font-body`, heading weight 500, never bolder).
Numbers, field keys, file paths, keystrokes and post counts are set in a **monospace** stack
(`ui-monospace, SFMono-Regular, Menlo, monospace`) with `font-variant-numeric: tabular-nums` wherever
digits are compared. This is load-bearing for the autocomplete: the post count is read by digit
count, which only works if digits align.

Spacing comes from `--space-1..8` (density 0.70×). This interface is dense on purpose.

## Two rules that are easy to get wrong

**1. The accent is a line and a mark, never a flood.** Primary buttons are a 1px accent border on
transparent — never filled. Tinted fills come from the dark ramp steps (`--color-accent-900` for a
selected row, `color-mix(… 6–8%)` for a highlighted one). If a large area ends up saturated, it is
wrong.

**2. Status is shape-coded, not colour-coded.** There is one accent and no error colour. Every status
in this design is carried by a **shape** so it survives a mono palette:

| Mark | Meaning | Where |
| --- | --- | --- |
| 7px filled circle, `neutral-800` | field decided / filled | sheet gutter |
| 7px hollow circle, 1px `neutral-600` | empty, not yet claimed | sheet gutter |
| 7px dashed circle, `neutral-700` | not read yet | sheet gutter while loading |
| **7px square**, `--color-accent` | refusal on this field | sheet gutter |
| 8px filled circle, `--color-accent` | approved | batch rail |
| 8px half-filled circle, `accent-500` | edited, not approved | batch rail |
| 8px hollow circle, `neutral-600` | read, untouched | batch rail |
| 8px dashed circle | files not read yet | batch rail while loading |
| 4×14px accent bar | this field falls past the 77-token budget | sheet token column |

Do not substitute colour for any of these, and do not add a red.

## Contrast floor

Functional text must clear **4.5:1** against the ground it sits on. `--color-neutral-600` on
`--color-bg` is 4.08:1, so it is **not** available for text — only for hairline borders and the chip
×. Small informational text (token numbers, file paths, kickers, load states, rail labels) uses
`--color-neutral-500` at 6.19:1. The 22px token total may use `neutral-600` because it is
headline-scale.

Never stack a wrapper `opacity` on already-muted text — recolour down a ramp step instead. Dimming
`neutral-500` to 40% is how the photo overlay's header first became illegible.

## Photographs

Every content photograph goes through the system's `.lighten` wrapper (`mix-blend-mode: lighten`), so
dark values fall away into the page. **One exception:** the expanded photo overlay does not blend —
there the photograph must be seen as it is, because that is where colour is judged. The overlay's
ground is one shade below the app's, mixed from the token (`color-mix(in srgb, var(--color-bg) 72%,
black)`), never an invented hex.

## Interaction states

Themed, never browser defaults. Hover and pressed states come from the accent ramp; keyboard focus is
`:focus-visible { outline: 2px solid var(--color-accent); outline-offset: 2px }`. Disabled controls
drop to 45% opacity. All of this is already in `styles.css` — do not restyle per component.

Since this interface is keyboard-first, the focus ring is not decoration: it is how the operator
knows which field they are in. Never suppress it.

## Icons

Phosphor icons where icons are needed. This design uses almost none — the only glyphs are the chip ×
and arrow characters in keystroke hints.
