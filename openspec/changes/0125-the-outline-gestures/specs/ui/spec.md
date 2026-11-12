## ADDED Requirements

### Requirement: The placement screen declares undo, redo and close and no other key

The placement screen SHALL declare, through the app's key store, `Mod+Z` to undo, `⇧Mod+Z` to redo and `↵` to close an
outline that can close, on the outline step, on the stages that hold pairs and on the render stage's sketch, and SHALL
declare no other command. The keys SHALL be listed with the app's keys. A text field SHALL keep its own `Mod+Z`, `⇧Mod+Z`
and `↵`, and a focused control SHALL keep `↵`. Only the panel SHALL listen to the keyboard, for Shift alone, to draw its
cursor. The keys the app answers everywhere SHALL stay, and a dialog SHALL close on `esc` as every dialog does.

A key of the screen is one the hand reaches for while it holds the mouse; every other key waits until the screen has been
used and shows which are useful.

#### Scenario: the screen declares only undo, redo and close
- **Key:** `ui:place-keys:the-screen-declares-only-undo-redo-and-close`
- **Layers:** unit
- **WHEN** the sources of the screen and its components are read
- **THEN** only the outline step and the two stages that hold pairs declare commands, each only `undo`, `redo` and `close`, and only the panel reads `keydown` and `keyup`

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

## MODIFIED Requirements

### Requirement: The panel zooms at the pointer, pans by a drag, and fits or shows 1:1

The panel SHALL show one image in a viewport, zoom it at the pointer by the wheel between the declared floor
and ceiling, pan it by a drag on the image while Shift is up, and offer *Fit* and *1:1*.
A zoom SHALL keep the image point under the pointer under it. A pan SHALL keep part of the image in the viewport.
The panel SHALL show its zoom as a percentage.

A press SHALL be one of three gestures. With Shift held it places, and a press that travels past the declared slop
does nothing. With Shift up on a point that the screen's editor names it moves that point, and with Shift up
elsewhere it pans. The cursor SHALL be a crosshair while Shift is held, the hand otherwise, and the grabbing hand while a
pan or a move is under way.

The ink is judged at 1:1, so the panel keeps the pixel under the pointer where it was.

#### Scenario: a zoom keeps the point under the pointer
- **Key:** `ui:panel:a-zoom-keeps-the-point-under-the-pointer`
- **Layers:** unit
- **WHEN** the view is zoomed at a pointer position
- **THEN** the image point that was under the pointer is still under it

#### Scenario: a zoom is held between the floor and the ceiling
- **Key:** `ui:panel:a-zoom-is-held-between-the-floor-and-the-ceiling`
- **Layers:** unit
- **WHEN** the view is zoomed in past the ceiling, or out past the floor
- **THEN** its scale is the ceiling, or the floor

#### Scenario: a pan keeps part of the image in view
- **Key:** `ui:panel:a-pan-keeps-part-of-the-image-in-view`
- **Layers:** unit
- **WHEN** the view is panned far past an edge
- **THEN** some of the image is still in the viewport

#### Scenario: fit and 1:1
- **Key:** `ui:panel:fit-and-one-to-one`
- **Layers:** unit
- **WHEN** the view is fitted, and then set to 1:1
- **THEN** fit shows the whole image centred, and 1:1 shows one image pixel for one screen pixel about the
  viewport's centre

#### Scenario: a point converts both ways
- **Key:** `ui:panel:a-point-converts-both-ways`
- **Layers:** unit
- **WHEN** a screen point is turned into an image point and back
- **THEN** it is the screen point

#### Scenario: shift places and a plain press pans
- **Key:** `ui:panel:shift-places-and-a-plain-press-pans`
- **Layers:** unit
- **WHEN** a press is read with Shift held, with Shift up on a point, and with Shift up elsewhere
- **THEN** the gestures are place, move and pan, in that order

#### Scenario: the cursor follows Shift and the pan
- **Key:** `ui:panel:the-cursor-follows-shift-and-the-pan`
- **Layers:** unit
- **WHEN** the cursor is read with Shift held, with Shift up, and with Shift up while a pan is under way
- **THEN** it is the crosshair, the hand and the grabbing hand

### Requirement: An outline is clicked, closed on its first point and edited by dragging

With Shift held the outline editor SHALL close the outline on a click within the declared radius of the first vertex once
it holds the declared floor of vertices, insert a vertex on an edge within the radius, and otherwise add a vertex at the
click while the outline is open. A click within the radius of a vertex SHALL never add a vertex there: on the first it
closes when the outline can, and on any other it does nothing. With Shift up the editor SHALL pan by a drag, move a vertex
by a drag on it and remove a vertex by a double click on it. It SHALL close an open outline that holds the floor on `↵`,
undo its last change, redo what was undone until a new change, and clear itself.
A closed outline SHALL need at least the declared floor of vertices and SHALL take no more than the ceiling.
The radius SHALL be the same on screen at every zoom. Once the outline can close, the first vertex SHALL grow and read
*close* while the pointer is within the radius of it.

A press that moves is a pan or a drag, not a vertex.

#### Scenario: a click adds a vertex and the first closes
- **Key:** `ui:outline-edit:a-click-adds-a-vertex-and-the-first-closes`
- **Layers:** unit
- **WHEN** vertices are shift-clicked and then the first is shift-clicked
- **THEN** each click added a vertex, and the last closed the outline without adding one

#### Scenario: the closing radius is the same on screen at every zoom
- **Key:** `ui:outline-edit:the-radius-is-the-same-on-screen`
- **Layers:** unit
- **WHEN** a click lies the radius's screen distance from the first vertex at two zooms
- **THEN** it closes at both

#### Scenario: a drag moves a vertex
- **Key:** `ui:outline-edit:a-drag-moves-a-vertex`
- **Layers:** unit
- **WHEN** a vertex is dragged
- **THEN** it moves to the pointer's image point and the others stay

#### Scenario: a shift-click inserts on the nearest edge
- **Key:** `ui:outline-edit:a-shift-click-inserts-on-the-nearest-edge`
- **Layers:** unit
- **WHEN** a closed outline is shift-clicked near one edge
- **THEN** a vertex lies on that edge, between its ends

#### Scenario: a double click removes a vertex
- **Key:** `ui:outline-edit:a-double-click-removes-a-vertex`
- **Layers:** unit
- **WHEN** a vertex is double-clicked and the outline then has fewer than the floor
- **THEN** the vertex is gone and the outline reads as not ready

#### Scenario: undo and clear
- **Key:** `ui:outline-edit:undo-and-clear`
- **Layers:** unit
- **WHEN** a vertex is added, moved and removed, then undone three times, then cleared
- **THEN** each undo restores the state before its change, and clear leaves no vertex and an open outline

#### Scenario: the ceiling is held
- **Key:** `ui:outline-edit:the-ceiling-is-held`
- **Layers:** unit
- **WHEN** an outline of the ceiling's vertices is clicked once more
- **THEN** no vertex is added

#### Scenario: a shift-click places by where it lands
- **Key:** `ui:outline-edit:a-shift-click-places-by-where-it-lands`
- **Layers:** unit
- **WHEN** an open outline is shift-clicked on its first vertex, on another vertex, on an edge and on bare image, and a closed outline on bare image
- **THEN** the first closes it, another vertex changes nothing, the edge takes a vertex on it, bare image adds one, and a closed outline takes none

#### Scenario: a near miss never adds a vertex
- **Key:** `ui:outline-edit:a-near-miss-never-adds-a-vertex`
- **Layers:** unit
- **WHEN** an outline below the floor is shift-clicked within the radius of its first vertex, and one at the floor is shift-clicked a few image pixels from it
- **THEN** the first adds no vertex and the second closes

#### Scenario: redo restores what undo took
- **Key:** `ui:outline-edit:redo-restores-what-undo-took`
- **Layers:** unit
- **WHEN** a change is undone and redone, and a new change follows an undo
- **THEN** the redo restores the change, and the new change leaves nothing to redo

#### Scenario: closing needs the floor
- **Key:** `ui:outline-edit:closing-needs-the-floor`
- **Layers:** unit
- **WHEN** an open outline holds one vertex fewer than the floor, and then the floor
- **THEN** it cannot close and then can, and closing it leaves it closed

### Requirement: The outline step shows the ink and keeps its white point and tone

The outline step SHALL show the tattoo in the panel and let its outline be drawn, saving it as it changes.
Once the outline is closed it SHALL offer the ink view beside the photograph or image,
drawn from the server's answer on the crop's offset.
It SHALL show the automatic white point as an 8-bit grey and let the operator set one by hand,
stored as the scale on the automatic point, and return to automatic.
It SHALL offer *neutral* and *depth* from 1.0 to 2.0, and *Reset* to the kind's defaults once either differs.
On a cut it SHALL show the photograph with the ink at full strength inside the outline
and the photograph dimmed around it, and the size of the ink on the photograph,
and offer *Upload a tattoo instead*, which keeps a new tattoo under its own name and leaves the cut kept.
While the outline is open the controls SHALL be disabled, and one line above them SHALL say
*close the outline on its first point · N points*; once it is closed the line SHALL go.
The step SHALL carry no line that explains its gestures.

The ink view is the judge: nothing on the screen grades the cut.

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
- **WHEN** an outline of one vertex and of five vertices is open, and then closed
- **THEN** the line reads *close the outline on its first point · 1 point* and then *· 5 points*, and a closed outline has none

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

### Requirement: Pairs are placed by clicks on two images

With Shift held the pair editor SHALL place the next point on the image clicked and let the other image wait for its match,
complete the pair by a click on the waiting image, and move the lone point by a click on the image that holds it. A click
within the declared radius of a point SHALL select its pair and place nothing, with Shift held or not. With Shift up a drag
SHALL move a point that it starts on and otherwise pan. The editor SHALL delete the selected pair so that the later pairs
renumber, undo the last placement, move or delete, redo what was undone until a new change, and clear every pair. The
radius SHALL be the same on screen at every zoom, and the pairs SHALL have no maximum. A stage SHALL go forward only with
its floor of pairs and no lone point, and SHALL say why it waits, by the pairs it lacks or the point that has no match. The
pairs SHALL stay when the screen moves from one step to another.

Either image may go first, so the operator clicks where the tattoo is clearest. The floors are declared once and read
by the page and the server alike.

#### Scenario: a click places a point and the other image waits
- **Key:** `ui:pairs:a-click-places-a-point-and-the-other-image-waits`
- **Layers:** unit
- **WHEN** a point is shift-clicked on the tattoo's image
- **THEN** the pair holds it as point 1, and the photograph is the waiting image

#### Scenario: a click on the waiting image completes the pair
- **Key:** `ui:pairs:a-click-on-the-waiting-image-completes-the-pair`
- **Layers:** unit
- **WHEN** the waiting image is shift-clicked
- **THEN** the pair is complete and no image waits

#### Scenario: a click on the image that holds the lone point moves it
- **Key:** `ui:pairs:a-click-on-the-image-that-holds-the-lone-point-moves-it`
- **Layers:** unit
- **WHEN** the image that holds the lone point is shift-clicked again
- **THEN** the lone point is at the new place, and the other image still waits

#### Scenario: a click near a point selects its pair
- **Key:** `ui:pairs:a-click-near-a-point-selects-its-pair`
- **Layers:** unit
- **WHEN** a click lies within the radius of a placed point
- **THEN** that point's pair is selected, and no point is placed

#### Scenario: the radius is the same on screen at every zoom
- **Key:** `ui:pairs:the-radius-is-the-same-on-screen-at-every-zoom`
- **Layers:** unit
- **WHEN** a click lies the radius's screen distance from a point at two zooms
- **THEN** it selects the pair at both

#### Scenario: a drag moves a point
- **Key:** `ui:pairs:a-drag-moves-a-point`
- **Layers:** unit
- **WHEN** a placed point is dragged
- **THEN** it is at the pointer's image point, and the other points stay

#### Scenario: a delete renumbers the later pairs
- **Key:** `ui:pairs:a-delete-renumbers-the-later-pairs`
- **Layers:** unit
- **WHEN** the second of four pairs is deleted
- **THEN** three pairs stand, numbered 1 to 3, in their old order

#### Scenario: undo and clear
- **Key:** `ui:pairs:undo-and-clear`
- **Layers:** unit
- **WHEN** a point is placed, moved and then deleted, and each is undone, and then every pair is cleared
- **THEN** each undo restores the state before its change, and clear leaves no pair

#### Scenario: there is no maximum
- **Key:** `ui:pairs:there-is-no-maximum`
- **Layers:** unit
- **WHEN** forty pairs are placed
- **THEN** all forty stand

#### Scenario: forward waits for the floor and says why
- **Key:** `ui:pairs:forward-waits-for-the-floor-and-says-why`
- **Layers:** unit
- **WHEN** two pairs stand against a floor of six, and then six stand with a lone point 7
- **THEN** forward waits with *6 pairs needed · 2 placed*, and then with *point 7 has no match*

#### Scenario: the pairs stay across steps
- **Key:** `ui:pairs:the-pairs-stay-across-steps`
- **Layers:** unit
- **WHEN** pairs are placed on one step and the screen moves to the next step and back
- **THEN** the same pairs stand

#### Scenario: a plain click selects and places nothing
- **Key:** `ui:pairs:a-plain-click-selects-and-places-nothing`
- **Layers:** unit
- **WHEN** a click with Shift up lies within the radius of a placed point, and another lies on bare image
- **THEN** the first selects that point's pair and the second changes nothing

#### Scenario: redo restores what undo took
- **Key:** `ui:pairs:redo-restores-what-undo-took`
- **Layers:** unit
- **WHEN** a placement is undone and redone, and a new change follows an undo
- **THEN** the redo restores the placement, and the new change leaves nothing to redo

### Requirement: The render stage draws a limb outline and exclusions

The render stage and the direct stage SHALL let the operator draw one limb outline, which keeps the ink inside it, and
any number of exclusion outlines, each removing the ink inside it, by shift-clicks closed on the first point or on `↵`
as the outline editor does, and edit any of them by its row. While an outline is drawn, the pairs SHALL not take a
click, and `Mod+Z`, `⇧Mod+Z` and `↵` SHALL act on the outline. Each outline SHALL list as a row saying its points and what
it does. The page SHALL offer no way to remove an outline and SHALL carry no line that explains the gestures.

The hair or the clothing in front of a limb must stay free of ink, and the render's pixels, not the photograph's, show
where it is.

#### Scenario: one limb and any number of exclusions
- **Key:** `ui:render-stage:one-limb-and-any-number-of-exclusions`
- **Layers:** unit
- **WHEN** a limb is drawn and closed, a second limb is begun, and three exclusions are drawn
- **THEN** the second limb edits the first, and four outlines are listed

#### Scenario: a row says what the outline does
- **Key:** `ui:render-stage:a-row-says-what-the-outline-does`
- **Layers:** unit
- **WHEN** a limb of 9 points and an exclusion of 8 points are listed
- **THEN** the rows read *9 points · keeps* and *8 points · removes*

#### Scenario: the pairs take no click while an outline is drawn
- **Key:** `ui:render-stage:the-pairs-take-no-click-while-an-outline-is-drawn`
- **Layers:** unit
- **WHEN** an exclusion is being drawn
- **THEN** the pair editor is held, and the row reads *drawing · n points*

### Requirement: Stage 2 proposes its pairs when it opens with none

The photograph-to-render stage, for a tattoo placed in two stages and for a cut, SHALL ask the server for proposed pairs
once, when it opens on a tattoo and render with no pair held, sending the tattoo's points on the photograph: the
photograph side of the stage-1 pairs, or a cut's outline. It SHALL show that it is asking, and SHALL show a refusal with
its fix, with the pair editor still taking clicks. An answer with no pair SHALL say so. A stage that holds a pair, the
direct stage, and a stage already asked on this tattoo and render while the tattoo is held SHALL ask nothing. Leaving the
tattoo for another SHALL forget the ask, with any answer still on its way, so that returning to the tattoo with no pair held
asks again.

Proposing is a convenience on top of clicking, so it never blocks the editor and never asks twice for the same work.
The pairs of a tattoo that was left are gone, and so is the ask that made them.

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

#### Scenario: a refusal shows its words and the clicks still work
- **Key:** `ui:proposal:a-refusal-shows-its-words-and-the-clicks-still-work`
- **Layers:** unit
- **WHEN** the proposal is refused with the fetch command in its words, and a point is then clicked
- **THEN** the view shows the words, and the click places the point

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

## REMOVED Requirements

### Requirement: The placement screen holds no key of its own

**Reason:** the screen now declares `Mod+Z`, `⇧Mod+Z` and `↵`, the keys the hand reaches for while it holds the mouse.
**Migration:** *The placement screen declares undo, redo and close and no other key* holds the rule, and its scenario
`ui:place-keys:the-screen-declares-only-undo-redo-and-close` replaces `ui:place-keys:the-screen-declares-no-command`.
