## ADDED Requirements

### Requirement: The picker shows the render and lists the kept tattoos, and takes an upload or a cut

The picker, the first step, SHALL show at its top the render and the photograph it was made from, the render left and
the photograph right, each fitted to half the page's width, over the forms and the kept tattoos.
It SHALL list as a card each upload and each cut of this render's photograph, with its image, its name, its state,
*outlined*, *not outlined* or *ready for this photograph*, and what it came from: when it was kept,
the size it came with when downscaled, its stage-1 pairs on this photograph, or the photograph a cut is from.
It SHALL list no cut of another photograph.
A cut's card SHALL show its own crop of the photograph: the outline's box, drawn as the ink view once the cut is
outlined, and the whole photograph while the outline holds no box.
It SHALL take an upload through the import's staging and keep it under a name the operator may change,
and SHALL offer *Cut from this photo*, which keeps a cut of the render's photograph under a name.
Each form SHALL say in a line under its heading what it takes: the upload, the tattoo's design on its own,
a flat image and not a photo of skin; the cut, the tattoo as it shows on this render's photograph.
A card SHALL offer *Remove*, which opens a modal dialog, *Remove this tattoo?*, naming the tattoo, whose *No* comes
first and holds the focus; `h` `l` and `←` `→` SHALL move between *No* and *Yes*, `↵` SHALL press the focused one,
and `Esc` SHALL answer *No*. *Yes* SHALL remove the tattoo and list the rest again, and a refusal SHALL be shown in
the dialog.
A tattoo is ready for this photograph when it is outlined and, if uploaded,
holds the floor of stage-1 pairs on it or is flagged *not on this photo*.
An uploaded card SHALL offer *not on this photo*, a cut's SHALL not.
A refusal SHALL be shown with its fix. Choosing a card SHALL open the step its state asks:
the outline until the tattoo is outlined, then stage 1, the direct stage or stage 2 as its mode takes.

The picker is where a tattoo enters the screen, so it shows state and the way forward,
and a ready tattoo goes straight to the stage that places it.
A cut is the photograph's own, so another render of that photograph lists it and every other render does not.
The render and its photograph are what a tattoo is placed between, and two cuts of one photograph read alike
unless each shows its own crop. *No* first makes a stray `↵` remove nothing, as it does for a render's deletion.

```
render            │ photograph
upload form       │ cut form
kept tattoos      │ each card: its image, name, state, source, Remove
```

#### Scenario: the cards show the state and the source
- **Key:** `ui:picker:the-cards-show-the-state-and-the-source`
- **Layers:** unit
- **WHEN** an outlined upload and a cut that is not outlined are listed
- **THEN** the upload's card reads *outlined* and the cut's reads *not outlined* and *from* its photograph

#### Scenario: an upload's name starts as the file's stem
- **Key:** `ui:picker:an-uploads-name-starts-as-the-files-stem`
- **Layers:** unit
- **WHEN** `IMG_5521.heic` is chosen for upload
- **THEN** its name field starts as `IMG_5521`

#### Scenario: a cut of another photograph cannot be chosen here
- **Key:** `ui:picker:a-cut-of-another-photograph-cannot-be-chosen`
- **Layers:** unit
- **WHEN** the picker asks for the list of a render
- **THEN** the path it asks names the render's photograph digest
- **AND** a card reads a cut as that photograph's own, and carries no state for being another photograph's

#### Scenario: a refusal shows its fix
- **Key:** `ui:picker:a-refusal-shows-its-fix`
- **Layers:** unit
- **WHEN** an upload is refused because its name is taken
- **THEN** the card's form shows the refusal beside the name

#### Scenario: a card is ready for this photograph
- **Key:** `ui:picker:a-card-is-ready-for-this-photograph`
- **Layers:** unit
- **WHEN** an outlined upload holds six stage-1 pairs on this photograph, and an outlined cut is from it
- **THEN** both read *ready for this photograph*, and the upload's sub-line reads *stage 1 · 6 pairs*

#### Scenario: a card opens the step its state asks
- **Key:** `ui:picker:a-card-opens-the-step-its-state-asks`
- **Layers:** unit
- **WHEN** a card is chosen that is not outlined, one that is outlined with no pairs, and one that is ready
- **THEN** they open the outline, stage 1 and stage 2

#### Scenario: not on this photo is offered on an upload alone
- **Key:** `ui:picker:not-on-this-photo-is-offered-on-an-upload-alone`
- **Layers:** unit
- **WHEN** an upload's card and a cut's card are read
- **THEN** the upload's offers *not on this photo*, and the cut's does not

#### Scenario: remove asks in a dialog
- **Key:** `ui:picker:remove-asks-in-a-dialog`
- **Layers:** unit
- **WHEN** *Remove* is pressed on the card `bow`, and *Delete* on a render's large view
- **THEN** the first dialog is titled *Remove this tattoo?* and names `bow`, and the second is titled *Delete this render?*
- **AND** the second names nothing under its title

#### Scenario: a cut's card shows its own crop
- **Key:** `ui:picker:a-cuts-card-shows-its-own-crop`
- **Layers:** unit
- **WHEN** two cuts of one photograph are outlined in different boxes, and a third holds no point
- **THEN** the first two crops differ, each its box fitted to the card's frame, and the third has no crop

#### Scenario: each form says what it takes
- **Key:** `ui:picker:each-form-says-what-it-takes`
- **Layers:** unit
- **WHEN** the lines under the upload form's and the cut form's headings are read
- **THEN** the upload's says the tattoo's design on its own, a flat image and not a photo of skin
- **AND** the cut's says the tattoo as it shows on this render's photograph

### Requirement: Stage 2 proposes its pairs when it opens with none, once the saved outline is read

The photograph-to-render stage, for a tattoo placed in two stages and for a cut, SHALL ask the server for proposed pairs
once, when it opens on a tattoo and render with no pair held, sending the tattoo's points on the photograph: the
photograph side of the stage-1 pairs, or a cut's outline. It SHALL ask only once the tattoo's saved outline is read,
and SHALL ask nothing for a tattoo with no point to send. It SHALL show that it is asking, and SHALL show a refusal as
one plain line, with the pair editor still taking clicks. An answer with no pair SHALL say so. A stage that holds a
pair, the direct stage, and a stage already asked on this tattoo and render while the tattoo is held SHALL ask nothing.
Leaving the tattoo for another SHALL forget the ask, with any answer still on its way, so that returning to the tattoo
with no pair held asks again.

Proposing is a convenience on top of clicking, so it never blocks the editor and never asks twice for the same work.
The pairs of a tattoo that was left are gone, and so is the ask that made them. A stage that opens before the saved
outline arrives would send the outline it held before, and the server refuses a request with no point.

#### Scenario: a stage with no pairs asks once
- **Key:** `ui:proposal:a-stage-with-no-pairs-asks-once`
- **Layers:** unit
- **WHEN** stage 2 opens on a two-stage tattoo with no pair held, and is opened again after the answer
- **THEN** the first opening asks and the second does not

#### Scenario: a stage with pairs asks nothing
- **Key:** `ui:proposal:a-stage-with-pairs-asks-nothing`
- **Layers:** unit
- **WHEN** stage 2 opens with one pair held
- **THEN** no proposal is asked

#### Scenario: the direct stage asks nothing
- **Key:** `ui:proposal:the-direct-stage-asks-nothing`
- **Layers:** unit
- **WHEN** the stage between a tattoo and a render opens with no pair held
- **THEN** no proposal is asked

#### Scenario: the points sent are the tattoo's on the photograph
- **Key:** `ui:proposal:the-points-sent-are-the-tattoos-on-the-photograph`
- **Layers:** unit
- **WHEN** a proposal is asked for an upload with stage-1 pairs, and then for a cut with an outline
- **THEN** the first sends the stage-1 pairs' photograph points and the second sends the outline's points

#### Scenario: the page shows that it is asking
- **Key:** `ui:proposal:the-page-shows-that-it-is-asking`
- **Layers:** unit
- **WHEN** a proposal is asked and not yet answered
- **THEN** the view is asking, and after the answer it is not

#### Scenario: a refusal says so in a plain line and the clicks still work
- **Key:** `ui:proposal:a-refusal-says-so-in-a-plain-line-and-the-clicks-still-work`
- **Layers:** unit
- **WHEN** the proposal is refused, whatever its words, and a point is then clicked
- **THEN** the view shows one plain line and none of the words, and the click places the point

#### Scenario: an empty answer says so
- **Key:** `ui:proposal:an-empty-answer-says-so`
- **Layers:** unit
- **WHEN** the proposal is answered with no pair
- **THEN** the view says nothing was proposed, and no pair is added

#### Scenario: returning to a tattoo asks again
- **Key:** `ui:proposal:returning-to-a-tattoo-asks-again`
- **Layers:** unit
- **WHEN** a tattoo's proposal is answered, another tattoo is held, and the first is held again
- **THEN** the first is due again, and an answer still on its way from before is not applied

#### Scenario: an ask waits for the saved outline
- **Key:** `ui:proposal:an-ask-waits-for-the-saved-outline`
- **Layers:** unit
- **WHEN** stage 2 opens on a cut while its tattoo is read again, and then on a tattoo with no point
- **THEN** no ask is due while the read is on its way or with no point, and one is due once a saved outline has arrived

## MODIFIED Requirements

### Requirement: The outline step shows the ink and keeps its white point and tone

The outline step SHALL show the tattoo in the panel and let its outline be drawn, saving it as it changes.
Its head SHALL read the tattoo's state as the last save answered it: *outlined* once a closed outline is saved, and
*not outlined* while the saved outline is open.
Once the outline is closed it SHALL offer the ink view beside the photograph or image,
drawn from the server's answer on the crop's offset.
It SHALL show the automatic white point as an 8-bit grey and let the operator set one by hand,
stored as the scale on the automatic point, and return to automatic.
It SHALL offer *neutral* and *depth* from 1.0 to 2.0, and *Reset* to the kind's defaults once either differs.
On a cut it SHALL show the photograph with the ink at full strength inside the outline
and the photograph dimmed around it, and the size of the ink on the photograph,
and offer *Upload a tattoo instead*, which keeps a new tattoo under its own name and leaves the cut kept.
While the outline is open the controls SHALL be disabled, and one line above them SHALL say how to close it:
*add N more points to close · K of F* while the outline holds K points, fewer than the floor F of `outline_min`, and
*close the outline on its first point · K points* from the floor on; once it is closed the line SHALL go.
The step SHALL carry no line that explains its gestures.

The ink view is the judge: nothing on the screen grades the cut. The head reads what the server kept, so a close shows
at once and not at the next visit.

#### Scenario: the white grey converts to a scale and back
- **Key:** `ui:outline-step:the-white-grey-converts-to-a-scale-and-back`
- **Layers:** unit
- **WHEN** an 8-bit grey is set by hand against an automatic grey
- **THEN** the stored scale is their ratio, and the grey shown is the automatic grey times the scale, rounded

#### Scenario: a scale of one is automatic
- **Key:** `ui:outline-step:a-scale-of-one-is-automatic`
- **Layers:** unit
- **WHEN** the white scale is 1.0
- **THEN** the state reads *auto*, and any other scale reads *set by hand*

#### Scenario: reset appears when the tone differs from the default
- **Key:** `ui:outline-step:reset-appears-when-the-tone-differs`
- **Layers:** unit
- **WHEN** a cut's depth is changed from 1.6
- **THEN** *Reset* is offered, and choosing it restores neutral on and depth 1.6

#### Scenario: the controls wait for a closed outline
- **Key:** `ui:outline-step:the-controls-wait-for-a-closed-outline`
- **Layers:** unit
- **WHEN** the outline is open
- **THEN** the ink view, the white point and the tone are disabled

#### Scenario: one line says how to close
- **Key:** `ui:outline-step:one-line-says-how-to-close`
- **Layers:** unit
- **WHEN** an outline of three vertices and of five vertices is open under a floor of 3, and then closed
- **THEN** the line reads *close the outline on its first point · 3 points* and then *· 5 points*, and a closed outline
  has none

#### Scenario: the line names the floor while the outline is short of it
- **Key:** `ui:outline-step:the-line-names-the-floor-while-the-outline-is-short`
- **Layers:** unit
- **WHEN** an outline of no vertex, one vertex and two vertices is open under a floor of 3
- **THEN** the line reads *add 3 more points to close · 0 of 3*, then *add 2 more points to close · 1 of 3*, then
  *add 1 more point to close · 2 of 3*

#### Scenario: the size of the cut's ink is the outline's box
- **Key:** `ui:outline-step:the-size-of-the-cuts-ink-is-the-outlines-box`
- **Layers:** unit
- **WHEN** a cut's closed outline spans a box of the photograph
- **THEN** the source line gives that box's width and height in photograph pixels

#### Scenario: uploading instead keeps the cut
- **Key:** `ui:outline-step:uploading-instead-keeps-the-cut`
- **Layers:** unit
- **WHEN** a tattoo is uploaded instead of a cut named `bow`
- **THEN** its name starts as `bow_closeup`, and `bow` is still kept

#### Scenario: the head reads the save's answer
- **Key:** `ui:outline-step:the-head-reads-the-saves-answer`
- **Layers:** unit
- **WHEN** a closed outline is saved on a tattoo read as not outlined, and then an open one is saved
- **THEN** the head's state reads *outlined* after the first answer and *not outlined* after the second

### Requirement: The review shows the tattoo placed and bakes it

The review SHALL show the crop of the image the tattoo is placed on before and after, side by side, each fitted to its
column, the before being the image placed on and the after the image with the tattoo over it, and no other image. It
SHALL summarise the placement: the image it is placed on, the tattoo with its source, its outline's points and its white
point, its tone only where it differs from the tattoo kind's default, the pairs of each stage, and the outlines. The
summary SHALL stand in a column to the right of the crops, with a button to go back to each earlier stage and *Bake* in
one row. *Bake* SHALL ask the server for the bake and then say that the bake is queued for the next render session, with
the edit's number. It SHALL wait while a stage lacks its floor, saying which.

Nothing here spends: the bake is a request and the pod runs it in a later session. The crops fit their columns so that
the before and the after are seen together.

```
┌────────────┬────────────┬─────────────────┐
│ before     │ after      │ summary         │
│            │            │ [Back…] [Bake]  │
└────────────┴────────────┴─────────────────┘
```

#### Scenario: the tattoo row names the source and the white point
- **Key:** `ui:review:the-tattoo-row-names-the-source-and-the-white-point`
- **Layers:** unit
- **WHEN** a cut with 36 outline points, an automatic white of 119 and the photograph's default tone is summarised
- **THEN** the row reads *bow · cut from meadow_02 · outline 36 points · white 119 · neutral · depth 1.6*

#### Scenario: an upload's default tone is left out
- **Key:** `ui:review:an-uploads-default-tone-is-left-out`
- **Layers:** unit
- **WHEN** an upload with neutral off and depth 1.0 is summarised, and then one with depth 1.4
- **THEN** the first row names no tone, and the second names depth 1.4

#### Scenario: the summary lists the pairs of the mode
- **Key:** `ui:review:the-summary-lists-the-pairs-of-the-mode`
- **Layers:** unit
- **WHEN** a two-stage placement, a direct one and a cut are summarised
- **THEN** the first lists stage 1 and stage 2, the second the tattoo ↔ render pairs, and the cut stage 2 alone

#### Scenario: bake waits for a stage and then queues
- **Key:** `ui:review:bake-waits-for-a-stage-and-then-queues`
- **Layers:** unit
- **WHEN** stage 2 holds fewer pairs than its floor, and then the bake is answered with edit 3
- **THEN** *Bake* waits with the pairs lacking, and then the state reads *queued · edit 3 · next render session*

#### Scenario: the crops are fitted to their columns
- **Key:** `ui:review:the-crops-are-fitted-to-their-columns`
- **Layers:** unit
- **WHEN** the crop of a 100 by 50 box at 250, 275 is fitted on a render of 1100 by 600
- **THEN** the frame's aspect ratio is the box's, 100 / 50
- **AND** the render is sized at 1100% and placed at 25% 50%, so the box fills the frame

### Requirement: The placement screen declares undo, redo and close and no other key

The placement screen SHALL declare, through the app's key store, `Mod+Z` to undo, `⇧Mod+Z` to redo and `↵` to close an
outline that can close, on the outline step, on the stages that hold pairs and on the render stage's sketch, and SHALL
declare no other command. The keys SHALL be listed with the app's keys. A text field SHALL keep its own `Mod+Z`,
`⇧Mod+Z`
and `↵`, and a focused control SHALL keep `↵`. Only the panel SHALL listen to the keyboard, for Shift alone, to draw its
cursor. The keys the app answers everywhere SHALL stay, and a dialog SHALL close on `esc` as every dialog does. The
confirmation dialog the screen opens SHALL declare its own overlay keys while it is open, as the app's dialogs do.

A key of the screen is one the hand reaches for while it holds the mouse; every other key waits until the screen has
been
used and shows which are useful. A dialog is an overlay of the app and holds its keys only while it is open.

#### Scenario: the screen declares only undo, redo and close
- **Key:** `ui:place-keys:the-screen-declares-only-undo-redo-and-close`
- **Layers:** unit
- **WHEN** the sources of the screen and its components are read
- **THEN** only the outline step and the two stages that hold pairs declare commands, each only `undo`, `redo` and
  `close`, the confirmation dialog alone declares overlay commands, and only the panel reads `keydown` and `keyup`

#### Scenario: undo, redo and close run from the keys
- **Key:** `ui:place-keys:undo-redo-and-close-run-from-the-keys`
- **Layers:** unit
- **WHEN** `⌘Z`, `⇧⌘Z` and `↵` are pressed on a Mac, and `Ctrl+Z`, `Ctrl+⇧Z` and `↵` elsewhere
- **THEN** undo, redo and close run, once each
- **AND** none runs with focus in a text field, and `↵` does not run with focus on a button

#### Scenario: the keys are listed with the app's keys
- **Key:** `ui:place-keys:the-keys-are-listed-with-the-apps`
- **Layers:** unit
- **WHEN** the three commands are declared on the screen
- **THEN** the key list holds `undo`, `redo` and `close` with their keys

## REMOVED Requirements

### Requirement: The picker lists the kept tattoos and takes an upload or a cut

**Reason:** The picker now shows the render and its photograph, a cut's own crop and a *Remove* that asks in a dialog; its
scenario *remove takes a second click* no longer holds.
**Migration:** The picker shows the render and lists the kept tattoos, and takes an upload or a cut, carries every
other scenario under its key.

### Requirement: Stage 2 proposes its pairs when it opens with none

**Reason:** The ask now waits for the saved outline and a refusal is one plain line; its scenario *a refusal shows its
words and the clicks still work* no longer holds.
**Migration:** Stage 2 proposes its pairs when it opens with none, once the saved outline is read, carries every other
scenario under its key.
