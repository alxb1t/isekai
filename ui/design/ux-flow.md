# UX flow

Diagram: `screens/11-ux-flow.png`, frame `8a` in the design page.

## The sitting

One run, three inputs (1–10 in practice). The operator opens the printed URL, works through every
input, and leaves when the run manifest says the batch is done.

```
  [7a Loading] --read--> [1a Draft loaded] --types--> [2a Editing] --⌘↩--> [5a Refused]
                                                                             |
                                                                            ⌘↩
                                                                             v
                              [7b Batch done] <--last one-- [6a Approved]
```

Forward edges, each triggered by the operator except the first:

| From | To | Trigger |
| --- | --- | --- |
| 7a | 1a | batch read from disk — **the only automatic transition in the flow** |
| 1a | 2a | operator types in any field |
| 2a | 5a | ⌘↩ on a sheet with refusals |
| 2a | 6a | ⌘↩ on a valid sheet (skips 5a) |
| 5a | 6a | ⌘↩ after the refusals are cleared |
| 6a | 7b | the approved input was the last unapproved one |

Returns — every one is a choice, never a redirect:

| From | To | Trigger |
| --- | --- | --- |
| 5a | 2a | fixes a refusal (click a suggestion, or ⌥⏎) |
| 6a | 2a | edits after approving — the input becomes *edited* again |
| 6a | 1a | clicks the next thumbnail in the rail (twice, for three inputs) |
| 7b | 1a | "Review again", or any rail thumbnail |

Off the diagram: **3a** (expanded photo) opens over any state and changes nothing — it is a lens, not
a step. **4a** is the same flow for a landscape input; only the column widths differ.

Nothing returns to 7a. The batch is read once. A reload re-enters at 7a and lands on 1a with the
draft read back off disk, which is how §8 ("nothing lives only in the browser") shows up in the flow:
**no path through this diagram can lose work.**

## Keyboard model

The whole job is doable without the mouse. Nothing below requires a modifier the operator has to
discover — the dropdown and the refusal queue state their own contracts on screen.

### Moving

| Keys | Effect |
| --- | --- |
| `Tab` | next field (schema order) |
| `Shift+Tab` | previous field |
| `Alt+←` / `Alt+→` | previous / next input in the batch |
| `←` / `→` | move chip selection within the focused field |
| `Ctrl+↓` / `Ctrl+↑` | walk the refusal queue; each stop focuses its field |

### Adding a tag

| Keys | Effect |
| --- | --- |
| any character | opens the autocomplete on the first keystroke; fragment matches any word of a tag |
| `↑` / `↓` | move the selection; row 1 (highest post count) is preselected |
| `Enter` | commit the selected tag as a chip; the input stays in the field, fragment cleared, ready for the next tag |
| `Esc` | close the dropdown, keep the fragment |
| `Esc` again | clear the fragment |

A fragment that matches nothing shows no rows and cannot be committed — there is no way to type free
text into a chip. **The out-of-vocabulary refusal kind is now unreachable**: it existed because a
sorter could emit a tag that merely looked canonical, and since v0.21 the draft is routed from a
tagger whose output layer *is* the vocabulary. It is kept as a guard on what a later producer would
have to satisfy, not as a state this surface can reach.

### Removing a tag

| Keys | Effect |
| --- | --- |
| `Backspace` on an empty input | removes the last chip in the field |
| `Backspace` / `Delete` with a chip selected | removes that chip |

### Replacing a tag

Select the chip with `←`/`→`, then type. The autocomplete opens and `Enter` **replaces** the selected
chip rather than appending. This is the single most common edit in the job — `waves` → `wavy hair`,
`camera` → `looking at viewer`, `parted lips` → `open mouth` — so it must be three keystrokes, not
delete-then-add.

### Undo

| Keys | Effect |
| --- | --- |
| `Cmd/Ctrl+Z` | undo one edit, anywhere in the sheet |
| `Cmd/Ctrl+Shift+Z` | redo |

Per **edit**, not per field, and the stack crosses fields — it behaves like a text editor. One commit,
one removal, one replacement, or one accepted spelling suggestion is one undo step. The stack is
per input and is discarded when the operator moves to another input.

### Finishing

| Keys | Effect |
| --- | --- |
| `Alt+Enter` | accept every suggested spelling in the refusal queue at once |
| `Cmd/Ctrl+Enter` | approve — runs validation, writes the approved artifact or returns refusals |
| `Esc` (no dropdown open) | close the expanded photo overlay |

### A full input, mouse-free

```
Tab Tab            move to count
1 g i r l  ⏎       commit "1girl"
s o l o  ⏎         commit "solo"
Tab Tab Tab        move to hair_silhouette
→ →                select the "waves" chip
w a v  ↓ ⏎         replace it with "wavy hair"
…
⌘↩                 approve
Alt+→              next input
```
