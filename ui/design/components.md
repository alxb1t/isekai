# Components, state and build order

Vue 3, `<script setup>`, Composition API. Names below are the ones the docs and the design frames
refer to — keep them, or the two drift apart.

## Tree

```
ReviewApp.vue                  root; owns the run, decides which pane the work area shows
├── AppHeader.vue              run line, ② draft toggle, the receipts
├── BatchRail.vue              thumbnails + status marks + legend + the run entry
│   └── StatusMark.vue         the whole shape system, one component
├── SourcePanel.vue            photo above caption; owns the 492/620px width rule
│   ├── PhotoFrame.vue         .lighten img, click opens the overlay
│   └── CaptionPanel.vue       paragraphs, mapped-phrase highlight, unmapped dashed runs
├── SheetForm.vue              the 16 rows + header + footer
│   ├── SheetHeader.vue        kicker, filled/empty line
│   │   └── TokenBudget.vue    total, bar, heaviest, the 77 hairline and over-budget chip
│   ├── FieldRow.vue           ×16, in schema order, never re-sorted
│   │   ├── StatusMark.vue
│   │   ├── TagChip.vue        valid | invalid variants
│   │   ├── TagInput.vue       fragment + caret; owns chip selection within the field
│   │   └── TagAutocomplete.vue  the 430px dropdown, keyboard-driven
│   ├── RefusalQueue.vue       the surface panel; suggestion buttons
│   └── ApproveBar.vue         empties action, Approve, or the "Approved HH:MM:SS" fact
├── PhotoOverlay.vue           3a; teleported to body
├── RunManifest.vue            7b
└── LoadingSkeleton.vue        7a's bars and striped placeholders
```

`ReviewApp` shows exactly one of `LoadingSkeleton`, the review layout, or `RunManifest`.
`PhotoOverlay` layers over any of them.

### Props worth fixing now

```ts
// StatusMark — the only place status shapes are drawn
type MarkKind = 'filled' | 'hollow' | 'dashed' | 'square' | 'half'
defineProps<{ kind: MarkKind; size?: 7 | 8 | 9 }>()

// FieldRow
defineProps<{
  fieldKey: string          // rendered verbatim, monospace
  tags: string[]
  tokens: number            // valid tags only — refused tags are excluded
  state: 'filled' | 'empty-unclaimed' | 'empty-claimed' | 'refused' | 'pending'
  refusal?: Refusal
  pastBudget: boolean       // draws the 4×14px accent bar
  focused: boolean
}>()

// TagAutocomplete
defineProps<{ fragment: string; matches: VocabEntry[]; total: number }>()
// VocabEntry = { tag: string; posts: number }; rare = posts < 2000

// Refusal
type Refusal = {
  field: string
  kind: 'empty-unclaimed' | 'wrong-spelling' | 'out-of-vocabulary'
      | 'unknown-field' | 'missing-field'
  tag?: string              // the offending tag, if any
  note: string              // shown verbatim in the queue — see states.md
  fix?: string              // canonical tag; only wrong-spelling has one
}
```

## Composables

```
useRun()          batch list, current index, per-input status, approved count.
                  Loads once. Nothing re-enters the loading state.
useSheet(inputId) the draft: fields, autosave, undo stack, dirty flag, last-saved time.
useVocabulary()   the tag list loaded once; fragment search; post counts.
useApproval()     approve(), the refusal list, the approved artifact's path and time.
useKeyboard()     the global bindings in ux-flow.md, so no component owns two of them.
```

### `useSheet`

- **The server is the source of truth.** Every edit mutates local state and schedules a debounced
  `PUT` of the whole draft (400ms is right for typing; the operator must never see a save control).
- The last-saved timestamp comes back from the server, not from the client clock — the receipt has to
  be true.
- Undo is a stack of **edit operations**, not sheet snapshots, crossing all fields: commit, remove,
  replace, accept-suggestion. One op per undo step. Cleared when the operator changes input.
- Token counting runs over valid tags only. Keep the tokenizer in one function; the per-row number,
  the total, the heaviest list and the 77 hairline all read from it.

### `useApproval`

- `approve()` is a `POST`. **Validation is the server's answer, not the client's guess** — the client
  may pre-empt obvious refusals for responsiveness, but the returned list is what renders.
- Success writes `<input>.sheet.json` and returns its path and time. Failure writes nothing and
  returns refusals. Either way the draft is untouched.
- Editing after approval clears the approved-and-current flag; the file on disk stays.

## API the page needs

The server's shape is out of scope, but the page assumes roughly:

```
GET  /api/run                    -> { id, inputs: [{ id, photo, width, height }], approved: [...] }
GET  /api/vocabulary             -> [{ tag, posts }]            (cache aggressively)
GET  /api/inputs/:id             -> { photo, caption, draft, approved? }
PUT  /api/inputs/:id/draft       -> { savedAt, path }
POST /api/inputs/:id/approve     -> { approvedAt, path } | { refusals: Refusal[] }
```

## Build order

1. **Shell and tokens.** Link `styles.css`, build `AppHeader` + `BatchRail` + `StatusMark` against a
   static fixture. Getting the five marks right first means every later state is already expressible.
2. **`SheetForm`, read-only.** 16 rows from a fixture, schema order, chips, per-row tokens,
   `TokenBudget`. No editing. This is most of the pixels.
3. **`useVocabulary` + `TagAutocomplete`.** Keyboard only. Get fragment-matches-any-word and the
   count column right here — this is the piece that decides whether the tool is fast.
4. **Editing.** `TagInput`, chip selection, add/remove/replace, `useSheet` with undo and autosave.
   The receipt in the header becomes live.
5. **Approve.** `ApproveBar`, the empties action, `useApproval`, `RefusalQueue`, the approved state
   and its second receipt.
6. **`PhotoOverlay`**, then **`LoadingSkeleton`** and **`RunManifest`**.

Steps 1–2 are a screenshot match against `screens/01-review-draft-loaded.png`. Step 3 against
`screens/02-editing-autocomplete.png`. Step 5 against `screens/07-refused.png` and
`screens/08-approved.png`.

## Three things that are easy to get wrong

1. **The dropdown must overlay, never displace.** It is absolutely positioned under its row. If rows
   below it move, the operator loses their place while typing.
2. **Approve has no enabled twin and no Save button anywhere.** The two receipts are the only thing
   that talks about saving. If a Save control appears, the design has been broken.
3. **The per-row token number excludes refused tags.** A field whose only tag is refused shows a
   blank token cell, not a count.
