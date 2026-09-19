# States

One section per state. Frame ids refer to `screens/isekai-review-design.html`; the PNGs are listed
with each. **Copy strings in backticks are exact** — reproduce them verbatim, including the middle
dots and the lowercase file paths.

## Shared chrome

Present in every review state.

**App header** (41px tall, bottom border `--color-neutral-900`):

- left: `isekai review` (14px, weight 500) then the run line in mono 11.5px `neutral-400`:
  `run 2026-09-17 · 3 inputs · 0 approved`
- right: the ② draft toggle — a 26×14px pill and the label `Show ② draft`, off by default — then the
  receipts in mono 11.5px.

**Receipts.** Always the draft; the approved line appears once the input has been approved.

```
runs/2026-09-17/sheets/00003.draft.json · saved 14:02:11        neutral-500
00003.sheet.json · approved 14:12:40                            accent-300
```

**Batch rail** (132px, right border): kicker `batch`, one 5px-padded card per input with a thumbnail
at its true aspect ratio, the filename in mono 10.5px, and an 8px status mark. A legend at the foot
lists `approved` / `edited` / `untouched`. A `run` entry sits below it showing `3 of 3 approved`,
clickable at any time — that is the only route to the manifest mid-batch.

**Source column** (492px portrait / 620px landscape, right border, 16px padding): kicker
`① photograph` with `00003.png · 832×1216 · click to fill window` on the right; the photo in the
`.lighten` wrapper; kicker `② caption` with the word count; all caption paragraphs expanded, 13px,
line-height 1.62. Phrases a field mapped from are tinted `accent` at 22%; text no field claimed is
underlined dashed with the note `dashed = no field claimed this text`.

**Form column** (flex, fills the rest):

- header: kicker `③ sheet — …`, a line like `16 fields, schema order. 10 filled · 6 empty, none
  marked intentional.`, and the token budget block on the right.
- rows: `grid-template-columns: 12px 148px 1fr 30px`, `gap: 10px`, `min-height: 34px`,
  `padding: 4px 18px`, bottom rule `neutral-900` at 60%. Gutter mark · schema key in mono 12px
  `neutral-400` · chips · per-row token count in mono 11px `neutral-500`, right-aligned.
- chips: the system's `.tag .tag-outline` at 12px, `padding: 1px 5px 1px 8px`, `gap: 5px`, with a ×
  in `accent-600`.
- footer: the empties action on the left, the Approve control on the right.

**Token budget block:** the total in mono 22px, `/ 77 tokens` in mono 12px `neutral-500`, a 190×3px
bar, and `heaviest: clothes 8 · background 7 · expression 4` in mono 10.5px.

---

## 1a · Draft loaded

`screens/01-review-draft-loaded.png`

The sorter's output, untouched. This is what the operator lands on.

- Header: `run 2026-09-17 · 3 inputs · 0 approved`. Draft receipt only.
- Rail: current input hollow (read, untouched); the other two hollow.
- Sheet header: `③ sheet — draft from the sorter` / `16 fields, schema order. 10 filled · 6 empty,
  none marked intentional.` / **30** of 77 tokens.
- Empty rows show the italic word `empty` in `neutral-500` and a **hollow** gutter ring.
- Footer left: `Mark 6 empty fields intentional` (secondary button) with
  `Approve refuses an unmarked empty field.` beneath.
- Footer right: `Saving happens on its own.` and `Approve sheet ⌘↩` — accent outline, live.

## 2a · Editing

`screens/02-editing-autocomplete.png`

Mid-correction, autocomplete open on `hair_silhouette` for the fragment `wav`.

- Header: `0 approved`; draft receipt now `saved 14:06:33`.
- Rail: current input **half-filled** (edited).
- Sheet header: `③ sheet — 7 fields corrected` / **36** of 77 /
  `heaviest: clothes 7 · background 7 · framing 6`.
- The focused field shows its committed chips, then the fragment as **bare mono text with a 1px
  accent caret** — never a chip.
- The caption's mapped phrase brightens to 30% with a 1px `accent-600` outline while its field is
  focused; the note beside the caption reads `focused field is lighting its phrase`.
- **Autocomplete**: 430px wide, `--color-surface`, `--radius-md`, `--shadow-md`, positioned
  `top: 30px` under the field and **overlaying** the rows below — it must never displace them.
  Rows are `padding: 6px 11px`; the first row is filled `accent-900`. Tag name left, post count
  right in mono tabular. Footer: `↑↓ move · ⏎ commit · esc close` and `5 of 8,106`.

Rows as drawn, for the fragment `wav`:

| Tag | Count shown |
| --- | --- |
| wavy hair | `143,201` |
| wavy mouth | `11,438` |
| wavy bangs | `2,104` |
| wavy hair strand | `903 · rare` |
| wavy eyes | `461 · rare` |

The `· rare` suffix is `accent-300`; it appears under roughly 2,000 posts. Everything above it is a
plain count in a neutral ramp step, dimming as the count falls.

## 2b · Autocomplete, detail

`screens/03-autocomplete-blonde-detail.png`

The same dropdown on `hair_colour` for `blonde`: `1,204,331` / `38,742` / `2,431` /
`1,988 · rare`, footer `4 of 8,106`. Demonstrates fragment-matches-any-word (`blonde` reaching
`platinum blonde hair`) and that a seven-digit count needs no label — the absence of `rare` is
itself information.

## 3a · Photo expanded

`screens/04-photo-overlay.png`

Clicking the photograph. A lens over the review screen; nothing here can change the sheet.

- Ground: `color-mix(in srgb, var(--color-bg) 72%, black)`. **No `.lighten` blend.**
- App header stays, recoloured to `neutral-400` — never dimmed with `opacity`.
- Photo fit to height (`872px` from a 1216px original) with `--shadow-lg`; meta beneath:
  `00003.png` and `832 × 1216 · fit to height (72%)`. The percentage is stated because a judgement
  made at 72% is not the same judgement.
- Right column: `Fit` (primary) / `1:1 pixels` (secondary), `esc · click anywhere` and an × button;
  kicker `② caption`; all paragraphs at 13.5px.
- Footer note: `Editing is suspended while the photo is open — the sheet is behind this, untouched.`
  and `← → move through the batch without closing`.

## 4a · Landscape input

`screens/05-landscape-input.png`

The same screen for a wide photograph. **Only the column widths change**: source 492 → 620px, form
column absorbs the difference. The photo fills the column width; the caption gets the vertical space
the shorter photo frees.

Its draft also demonstrates the sorter's typical failure: `brown` and `grey` sitting in `clothes` —
real vocabulary tags, wrong field, no colour bound to a garment.

Header `3 inputs · 0 approved`, receipt `16_01.draft.json · saved 14:11:02`, `9 filled · 7 empty`,
**28** of 77 tokens, footer button `Mark 7 empty fields intentional`.

## 4b · Over the token budget

`screens/06-over-token-budget.png`

Real sheets run 80–122 against a 77 budget, so **over is the normal case** and is styled as
information: no red, no icon, no shake.

- Total in `--color-accent`: **104** `/ 77 tokens`, plus a `.tag .tag-outline` chip reading
  `27 over`.
- The bar is split, not clipped: 74% `accent-700`, a 1px `neutral-300` hairline at the 77 mark, then
  26% `--color-accent`. Caption beneath, `accent-300`:
  `everything past the mark is dropped by the renderer`.
- The four fields the budget reaches carry a 4×14px accent bar beside their token number. Because
  schema order is fixed, the budget always bites the bottom of the sheet.
- Footer states where it runs out and what to cut:
  `The budget runs out inside pose. Past it: framing, body_shape, background.` and
  `Cutting clothes (14) or background (11) buys the most room.`
- **Approve stays live.** The budget is soft.

## 5a · Refused

`screens/07-refused.png`

⌘↩ on a sheet with problems. All four refusal kinds plus the unmarked-empty rule.

- Sheet header: `③ sheet — refused` / `6 refusals. Nothing was written; the draft on disk is
  unchanged.` / total **41**, with `refused tags are excluded from the count` beneath.
- Refused rows: **square** accent gutter mark. The offending tag renders as an invalid chip — 1px
  **dashed** `--color-accent` border, `accent-900` fill, `accent-100` text, `--radius-sm`.
- File-shape problems render as rows rather than chips: an unknown field (`mood`) appears as a row
  that should not exist; a missing field (`body_shape`) shows `field absent from file` in
  `accent-300`. An unclaimed empty shows italic `empty, unclaimed`.
- **Refusal queue**, a `--color-surface` panel across the footer:
  - kicker `6 refusals · ⌃↓ walks them`, right side `click a suggestion to replace it · ⌥⏎ takes both`
  - one line per refusal: field key in mono `accent-300`, the reason, and for recoverable ones
    `replace with` + the canonical tag as a **primary-outline button**
  - closing line: `Editing is unaffected — the draft keeps saving. Only the approved artifact was
    refused.`

Refusals as drawn:

| Field | Reason | Suggestion |
| --- | --- | --- |
| `count` | `empty, not marked intentional` | — |
| `hair_silhouette` | `underscore — vocabulary spells it with a space` | `wavy hair` |
| `eye_colour` | `not one of the 8,106 tags` | none — out of vocabulary has no honest fix |
| `clothes` | `capitals — vocabulary is lowercase` | `lace trim` |
| `mood` | `not a schema field — the sorter invented it` | — |
| `body_shape` | `absent from the sheet file, not empty` | — |

Clicking a suggestion replaces the offending tag in place: the bad tag is removed, the canonical one
committed, that queue line disappears, the token count updates. One undo step. ⌥⏎ does all
suggestions at once.

## 6a · Approved

`screens/08-approved.png`

- Header: `run 2026-09-17 · 3 inputs · 1 approved`. **Both receipts**, the approved one in
  `accent-300`, timestamps two seconds apart.
- Sheet header: `③ sheet — approved` / `16 fields, schema order. 10 filled · 6 empty, all marked
  intentional.` / **38** of 77.
- Empty rows now read `cleared on purpose` in mono `neutral-500` with a **filled** gutter dot — an
  approved sheet has no undecided fields in it by definition.
- Footer: `Editing stays open. Changing anything returns this input to edited — the approved file
  stays as it is until you approve again.` and, in place of the button, a 9px filled accent dot with
  `Approved 14:12:40` in `accent-200`. **The button becomes a fact, not a greyed-out twin.**
- Nothing locks. Editing from here returns the input to *edited*: rail mark follows, Approve live
  again, approved file unchanged until re-approved.

## 7a · Batch loading

`screens/09-batch-loading.png`

- Header: `reading run 2026-09-17 — 2 of 3 inputs` and `vocabulary 8,106 tags · loaded`. Counted,
  not spun — a local read finishes in a moment, and if it does not, the operator wants to know which
  file it is stuck on.
- **No photographs.** Every rail thumbnail and the hero are 135° striped placeholders
  (`repeating-linear-gradient(135deg, var(--color-neutral-900) 0 6px, var(--color-bg) 6px 12px)`).
  Photo meta reads `00003.png · reading…`. Half a photo is worse than none when the job is judging
  one.
- The input whose files have not been read carries a **dashed** rail ring; the read ones are hollow.
- All 16 field keys render immediately — they come from the schema, not the data — with 9px
  `neutral-900` bars where values will land and dashed gutter rings. Nothing reflows on arrival.
- Token total renders as `—`. Caption panel: four flat bars and the word `reading…`.
- Flat bars only. **No shimmer** — animated skeletons pull the eye off the photograph.

## 7b · All approved

`screens/10-all-approved.png`

The batch is finished and it is safe to return to the terminal.

- Header: `run 2026-09-17 · 3 inputs · 3 approved` and `nothing left to review` in `accent-300`.
- Rail: three filled marks, all still selectable, with `run · 3 of 3 approved` at the foot.
- Work area becomes a manifest, flush left with whitespace right:
  - `3 of 3 approved` as an h3, then `sheets written to runs/2026-09-17/` in mono `accent-300`
  - a three-column table — `sheet` / `tokens` / `approved` — one row per input:
    `00003.sheet.json` 38 `14:12:40`, `16_01.sheet.json` 41 `14:26:11`,
    `cowboy_shot_2.sheet.json` **94** (in `accent-300`) `14:38:05`
  - `One sheet is over the 77-token budget: cowboy_shot_2 at 94.` /
    `Approved deliberately. Stated here so it is not a surprise after the render.`
  - `Review again` (secondary) and `The server keeps running until you stop the CLI.`
- It states the artifact and gives no order. The operator wrote the CLI; they do not need to be told
  to run `generate`.
- Reached by approving the last unapproved input, or from the rail's `run` entry at any time.

---

## Not designed

**A file on disk changed underneath the page** and **the server went away.** Both were specified and
deliberately left out of this pass. If you build them, the established voice is a header-level line
stating the fact and naming the file — blunt, no modal, and it must never imply the operator's work
was lost.
