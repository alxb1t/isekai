# Handoff: isekai review step

## Overview

The review step of a photo → anime image pipeline. A CLI runs `isekai caption` (a VLM describes each
photo) then `isekai sheet` (an LLM sorts that prose into a draft sheet of danbooru tags), starts a
local HTTP server and prints a URL. The operator opens it, corrects every draft sheet, approves each
one, closes the tab and runs `isekai generate`.

One operator, their own laptop, localhost, desktop browser, no auth, no other users. Photos are
personal — this is a private tool, not a product. A run is a batch: 1–10 photos in one sitting.

The operator's job per photo: **look at the photograph, read what the tagger offered, and correct
the tags the router placed.** Since v0.21 the draft comes from the local WD14 tagger through one
authored `tag ↔ field` table, not from a language model; the router cannot invent a tag, and what it
can get wrong is which criterion a tag answers. The gap between that draft and a corrected sheet is
the entire reason this step exists. Then approve.

## About the design files

The files in `screens/` are **design references written in HTML** — prototypes showing intended look
and behaviour, not production code to copy. The task is to **recreate them as a Vue 3 SPA** served
from the existing local HTTP server, using the token sheet in `design-system/`.

- `screens/isekai-review-design.html` — the whole design as one self-contained file. Open it in a
  browser. This is the most useful artifact: every frame, every state, with the rationale for each
  decision written in a column beside it.
- `screens/*.png` — one image per frame, for checking a build against the design.
- `screens/source/` — the unbundled source of the same page, if you want to read the markup.

## Fidelity

**High fidelity.** Colours, type, spacing, radii and copy are final and come from a real design
system (Nocturne, in `design-system/`). Recreate the UI to match. Where this document gives an exact
px value or an exact string, it is deliberate.

## Target

Vue 3 SPA, Vite, no router needed. Desktop viewports **1280px and up**; the design is drawn at
1600×1000. Dark theme only — the main content is a photograph being judged for colour and detail, so
there is no light mode and no theme toggle.

## The sample data is invented

Captions, tag post counts, filenames, timestamps and the "8,106 tag vocabulary" figures in the
design are **plausible fabrications made for the mockups**. Do not ship them, do not seed fixtures
from them without checking, and do not treat any specific post count as real. The three photographs
are the user's own files, used as placeholders.

## Read in this order

1. `design-system/notes.md` — how the system is applied, and the two rules that are easy to get
   wrong (shape-coding, and the accent is a line not a fill).
2. `ux-flow.md` — the six states, how they connect, and the full keyboard model.
3. `states.md` — every state with its exact copy, counts and layout deltas.
4. `components.md` — named Vue components, where state lives, build order.

## Hard requirements the design answers

1. Photograph, caption and form visible together. Tall and wide photos both happen.
2. Autocomplete over the tag vocabulary, keyboard-first, fragment matching any word.
3. The post count is shown and is not decoration — tag frequency predicts strength of effect.
4. A live token count against a 77-token budget. Soft, not a block.
5. Approve is a distinct, deliberate act, separate from editing. **Saving is not approving.**
6. Invalid input is visible. An empty field is legal and common.
7. Batch navigation with per-input status at a glance.
8. Nothing lives only in the browser. A closed tab or reload loses no work.

## Decisions log

Every choice below was made deliberately. Where a reason is given, it is the reason — if you change
the decision, the reason is what you are arguing with.

### Layout

- **Two columns, source left, work right.** Rail · (photo above caption) · form. The operator's eyes
  travel one short horizontal hop between the photograph and the field being typed. The caption is
  reference material, not a third thing to compare.
- **Dark ground.** The photograph is the only saturated thing on screen; no white surround to shift
  its perceived colour.
- **All 16 fields always open**, dense 34px rows, no grouping, no collapsing. Schema order is fixed
  and must not be re-sorted. 16 rows fit a 1000px viewport without scrolling — the wall was a density
  problem, not a hiding problem.
- **Source column resizes, the photo does not letterbox.** 492px for a portrait input, 620px for a
  landscape one; the photo always fills its column's width and the form column absorbs the
  difference. One rule, two shapes, no second layout.
- **Batch rail on the left**, always visible, medium width with real thumbnails at their true aspect
  ratio. Orientation is part of how the operator recognises an input.

### The sheet

- **Field labels are the schema keys verbatim**, monospace (`hair_colour`, not "Hair colour"). The
  operator wrote the schema; the keys are the clearer language.
- **`scored` is not shown.** Evaluation is not the operator's concern while reviewing.
- **Committed tags are bordered chips with an ×.** In-flight text is bare with a caret. Committed and
  in-flight never look alike.
- **Per-row token number** in the rightmost column. The counter says the total; the rows say where it
  sits.
- **Empty must be claimed.** An empty field is legal, but unmarked-empty reads as *not done*: hollow
  gutter ring. One action near Approve marks all remaining empties intentional, and Approve refuses
  until it happens. Empty-on-purpose becomes a recorded act rather than an absence.

### Autocomplete

- **Raw post count**, right-aligned, monospace tabular. Digit count does the work: 143,201 against
  903 is a shape difference, not a reading task. Rejected a log bar (compresses a 150× difference to
  under 2× of bar) and a magnitude glyph (adds a legend to learn).
- **One word, `rare`**, on tags under roughly 2,000 posts. Not a colour, a label — it says what the
  number means: the render will exaggerate what the tag names.
- **Ranking is global** — post count only, everywhere, no field-context narrowing. `wavy mouth`
  outranking `wavy hair strand` in a hair field is accepted, because nothing is ever unreachable and
  the rule never surprises. Field-aware ranking is helpful right up until a field means something
  unexpected.
- **Fragment matches any word**, not just prefixes. `blonde` reaches `platinum blonde hair`.
- **First row is pre-selected** — the highest post count is one ⏎ away, and reaching a rare tag takes
  a deliberate ↓.

### Approve and refusals

- **Approve is an accent-outlined button, always live.** No scroll gate, no dwell timer, no
  confirmation step. Clicking it runs validation; refusals come back. The only thing that stops an
  approve is a refusal, never a ritual.
- **Approving stays put.** It marks the input and does not auto-advance. The one exception: approving
  the *last* unapproved input opens the run manifest, because at that moment no sheet is left to
  review.
- **Two artifacts, two receipts.** The header always shows the draft path with its save time; once
  approved it also shows the approved path with its approval time, in the accent. That pairing is the
  whole of "saving is not approving", stated without words.
- **Refusals are shape-coded, not colour-coded** — square gutter mark, dashed chip. Nocturne has one
  accent and no error colour; inventing a red would break the system, and shape reads as fast.
- **Refusals list at the bottom as a persistent queue**, walkable with ⌃↓, each line focusing its
  row. Recoverable refusals (wrong spelling) carry the canonical tag as a button; ⌥⏎ takes all of
  them. Out-of-vocabulary gets no suggestion, because there is no honest one.
- **A refusal never loses work.** The header says nothing was written; the footer says the draft
  keeps saving. The refusal is of the approved artifact, not of the operator's editing.
- **No separate "approved then edited" state.** Editing an approved sheet simply returns the input to
  *edited*: the rail mark follows, Approve goes live again, and the approved file on disk stays as it
  was until re-approved. Considered and rejected a stale-artifact banner as a complication.

### Everything else

- **The ② draft diff is behind a toggle, off by default.** The diff between the routed draft and the
  human's correction is interesting, but not while typing.
- **Clicking the photograph opens a full-window overlay** on a ground one shade below the app's, with
  the caption expanded beside it and a Fit / 1:1 toggle. This is the one place the `.lighten` blend is
  **not** applied — the photo must be seen as it is. Arrow keys still move through the batch, so the
  overlay doubles as a way to compare inputs. Nothing in it can change the sheet.
- **The caption shows all paragraphs, expanded.** It is a reading aid and no longer a machine input:
  since v0.21 nothing downstream reads it, so there is no per-phrase mapping to highlight. The
  operator's cheapest clue about what is missing is the raw WD14 list beside it — every tag the
  tagger offered, including the ones the table routed nowhere.
- **Undo is per edit across the whole sheet**, like a text editor, not per field.
- **Token budget is soft.** 104 tokens is approvable. Real sheets run 80–122, so over-budget is the
  normal case and is styled as information, not an error.
- **Loading is counted, not spun.** "2 of 3 inputs", "vocabulary 8,106 tags · loaded". No spinner, no
  shimmer. No photograph is shown until it is decoded — half a photo is worse than none when the job
  is judging one.

## Out of scope — do not build

Uploading photos · running the caption or sheet steps · generating or previewing output images · a
gallery of results · evaluation scores · flow selection or authoring · cost or GPU monitoring ·
login, accounts, multi-user, sharing · mobile · light mode.

Two page-level states were specified but deliberately not designed: *a file on disk changed
underneath the page* and *the server went away*. If you need them, the established language is a
header-level line stating the fact and naming the file, in the same voice as the receipts.

## Files

```
README.md                          this file
design-system/styles.css           the token sheet + component layer — drop into the Vue app
design-system/notes.md             how the system is applied here
ux-flow.md                         states, transitions, full keyboard model
states.md                          every state: copy, counts, layout deltas
components.md                      named Vue components, state ownership, build order
screens/isekai-review-design.html  the whole design, self-contained — open this first
screens/01..11-*.png               one image per frame
screens/source/                    unbundled source of the design page
```
