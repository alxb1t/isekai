## ADDED Requirements

### Requirement: Pairs are placed by clicks on two images

The pair editor SHALL place the next point on the image clicked and let the other image wait for its match, complete
the pair by a click on the waiting image, move the lone point by a click on the image that holds it, select a pair by
a click within the declared radius of one of its points, move a point by a drag, delete the selected pair so that the
later pairs renumber, undo the last placement, move or delete, and clear every pair. The radius SHALL be the same on
screen at every zoom, and the pairs SHALL have no maximum. A stage SHALL go forward only with its floor of pairs and
no lone point, and SHALL say why it waits, by the pairs it lacks or the point that has no match. The pairs SHALL stay
when the screen moves from one step to another.

Either image may go first, so the operator clicks where the tattoo is clearest. The floors are declared once and read
by the page and the server alike.

#### Scenario: a click places a point and the other image waits
- **Key:** `ui:pairs:a-click-places-a-point-and-the-other-image-waits`
- **Layers:** unit
- **WHEN** a point is clicked on the tattoo's image
- **THEN** the pair holds it as point 1, and the photograph is the waiting image

#### Scenario: a click on the waiting image completes the pair
- **Key:** `ui:pairs:a-click-on-the-waiting-image-completes-the-pair`
- **Layers:** unit
- **WHEN** the waiting image is clicked
- **THEN** the pair is complete and no image waits

#### Scenario: a click on the image that holds the lone point moves it
- **Key:** `ui:pairs:a-click-on-the-image-that-holds-the-lone-point-moves-it`
- **Layers:** unit
- **WHEN** the image that holds the lone point is clicked again
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

### Requirement: The live preview follows the pairs

The page SHALL ask the server for the preview once the preview's floor of complete pairs stand, a declared time after
the last change, and SHALL draw the newest answer only, by multiplying it over the target at the operator's opacity,
with a way to hide it. While an answer is asked, the last one SHALL stay at half opacity. A refusal SHALL be shown
with its fix and SHALL clear the answer before it.

The preview is what catches a bad click while it is made, so it follows each change and never shows an old warp as a
new one.

#### Scenario: nothing is asked below the floor
- **Key:** `ui:preview:nothing-is-asked-below-the-floor`
- **Layers:** unit
- **WHEN** two complete pairs stand against a floor of three
- **THEN** no preview is asked

#### Scenario: one ask follows a burst of changes
- **Key:** `ui:preview:one-ask-follows-a-burst-of-changes`
- **Layers:** unit
- **WHEN** three changes come within the declared time
- **THEN** one preview is asked, the declared time after the last

#### Scenario: the newest answer wins
- **Key:** `ui:preview:the-newest-answer-wins`
- **Layers:** unit
- **WHEN** an older ask is answered after a newer one
- **THEN** the older answer is dropped and the newer stays drawn

#### Scenario: the last answer is dimmed while the next is asked
- **Key:** `ui:preview:the-last-answer-is-dimmed-while-the-next-is-asked`
- **Layers:** unit
- **WHEN** a preview is drawn and a change asks for another
- **THEN** the drawn one is at half opacity until the new answer comes

#### Scenario: a refusal clears the answer and shows its fix
- **Key:** `ui:preview:a-refusal-clears-the-answer-and-shows-its-fix`
- **Layers:** unit
- **WHEN** an ask is refused
- **THEN** no answer is drawn, and the refusal's words are shown

### Requirement: The outline step goes forward to the stage its tattoo takes

The outline step SHALL go forward, once its outline is closed, to the stage the tattoo takes on this photograph: stage
1 for an uploaded tattoo, the direct stage for a tattoo that is not on this photo, and stage 2 for a cut. The stepper
SHALL list the steps of that mode, each keeping its number, so a number names one screen in every mode. While the
outline is open, forward SHALL wait and say so with the points placed.

```
two stages   ① tattoo · ② outline · ③ tattoo ↔ photograph · ④ photograph ↔ render · ⑤ review
direct       ① tattoo · ② outline · ③ tattoo ↔ render · ⑤ review
cut          ① tattoo · ② outline · ④ photograph ↔ render · ⑤ review
```

A number that meant stage 2 in one mode and stage 1 in another would mislead an operator who moves between modes on
one photograph.

#### Scenario: the stepper lists the steps of the mode
- **Key:** `ui:stages:the-stepper-lists-the-steps-of-the-mode`
- **Layers:** unit
- **WHEN** the steps of an uploaded tattoo, a direct tattoo and a cut are listed
- **THEN** each list holds the steps drawn above, with the numbers kept

#### Scenario: forward goes to the stage of the mode
- **Key:** `ui:stages:forward-goes-to-the-stage-of-the-mode`
- **Layers:** unit
- **WHEN** the outline is closed on an uploaded tattoo, a direct tattoo and a cut
- **THEN** forward is stage 1, the direct stage and stage 2

#### Scenario: forward waits for a closed outline
- **Key:** `ui:stages:forward-waits-for-a-closed-outline`
- **Layers:** unit
- **WHEN** the outline is open with 27 points
- **THEN** forward waits, saying *outline open · 27 points*

### Requirement: A tattoo not on this photo is paired with the render directly

The direct stage SHALL pair the tattoo's ink view with the render, with a floor of pairs of its own, preview the ink
on the render, and carry the limb and exclusion tools of the render stage. Choosing *not on this photo* SHALL keep the
tattoo's stage-1 pairs, and clearing it SHALL restore them. A cut SHALL not offer the choice.

A tattoo newer than its photograph has no ink to match there, so its pairs go to the render.

#### Scenario: the flag skips stage 1
- **Key:** `ui:direct:the-flag-skips-stage-1`
- **Layers:** unit
- **WHEN** an outlined upload is chosen as *not on this photo*
- **THEN** its mode is direct, and its steps hold no stage 1

#### Scenario: the direct stage has its own floor
- **Key:** `ui:direct:the-direct-stage-has-its-own-floor`
- **Layers:** unit
- **WHEN** five pairs stand on the direct stage against a floor of six
- **THEN** forward waits, saying *6 pairs needed · 5 placed*

#### Scenario: a cut does not offer the flag
- **Key:** `ui:direct:a-cut-does-not-offer-the-flag`
- **Layers:** unit
- **WHEN** a cut's card is read
- **THEN** it offers no *not on this photo*

### Requirement: The render stage draws a limb outline and exclusions

The render stage and the direct stage SHALL let the operator draw one limb outline, which keeps the ink inside it, and
any number of exclusion outlines, each removing the ink inside it, by clicks closed on the first point, and edit any
of them by its row. While an outline is drawn, the pairs SHALL not take a click. Each outline SHALL list as a row
saying its points and what it does. The page SHALL offer no way to remove an outline.

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

### Requirement: The review shows the tattoo placed and bakes it

The review SHALL show the image the tattoo is placed on with the tattoo over it, and its crop before and after at
twice the size, the before being the image placed on. It SHALL summarise the placement: the image it is placed on,
the tattoo with its source, its outline's points and its white point, its tone only where it differs from the tattoo
kind's default, the pairs of each stage, and the outlines. It SHALL offer a button to go back to each earlier stage.
*Bake* SHALL ask the server for the bake and then say that the bake is queued for the next render session, with the
edit's number. It SHALL wait while a stage lacks its floor, saying which.

Nothing here spends: the bake is a request and the pod runs it in a later session.

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

### Requirement: Leaving with a point unmatched asks first

The page SHALL, when the operator leaves a stage that holds a point with no match, ask first, naming the point and
the image that lacks its match, the pairs that stand and, for stage 1, when they were saved. *Stay* SHALL keep the
stage open. *Leave* SHALL drop the lone point alone and keep every pair. A stage with no lone point SHALL be left
without asking.

A pair is saved as it is made, so the one thing a leave loses is the point that has no match.

#### Scenario: a lone point asks and a clean stage does not
- **Key:** `ui:leave:a-lone-point-asks-and-a-clean-stage-does-not`
- **Layers:** unit
- **WHEN** a stage with a lone point is left, and then one without
- **THEN** the first asks and the second leaves

#### Scenario: the dialog names the point and its missing match
- **Key:** `ui:leave:the-dialog-names-the-point-and-its-missing-match`
- **Layers:** unit
- **WHEN** point 8 lies on the tattoo and has no match on the photograph
- **THEN** the dialog reads *Point 8 has no match on the photograph*, and names the pairs that stand

#### Scenario: leaving drops the lone point and keeps the pairs
- **Key:** `ui:leave:leaving-drops-the-lone-point-and-keeps-the-pairs`
- **Layers:** unit
- **WHEN** *Leave* is chosen with seven pairs and a lone point 8
- **THEN** seven pairs stand and point 8 is gone

## MODIFIED Requirements

### Requirement: The placement screen has a route of its own per step

The system SHALL give the placement screen the route
`/c/<collection>/renders/<run>/<flow>/<version>/<seed>/place/<step>`, with the tattoo's name after the step where the
step needs one, and SHALL not mount the screen again when only its step or name changes. The steps SHALL be `tattoo`, `outline`, `photo`, `render` and `review`. A step the screen does
not know SHALL redirect to its first, and a step the tattoo's mode skips SHALL redirect to the step the mode takes in
its place.

A route under a render's path would collide with `compare` unless it is its own segment, and the screen keeps its
state across steps.

#### Scenario: a step change keeps the screen mounted
- **Key:** `ui:place-route:a-step-change-keeps-the-screen-mounted`
- **Layers:** unit
- **WHEN** the route moves from the first step to the outline step of one tattoo
- **THEN** the view's key is the same

#### Scenario: an unknown step redirects to the first
- **Key:** `ui:place-route:an-unknown-step-redirects-to-the-first`
- **Layers:** unit
- **WHEN** the route names a step the screen does not know
- **THEN** it redirects to the first step of the same render

#### Scenario: the route does not collide with compare
- **Key:** `ui:place-route:the-route-does-not-collide-with-compare`
- **Layers:** unit
- **WHEN** a render's `compare` and `place` paths are resolved
- **THEN** each resolves to its own route

#### Scenario: a skipped step redirects to the step in its place
- **Key:** `ui:place-route:a-skipped-step-redirects-to-the-step-in-its-place`
- **Layers:** unit
- **WHEN** the route names `photo` for a cut, or for a tattoo that is not on this photo
- **THEN** it redirects to the step that mode takes, `render` for both

### Requirement: The picker lists the kept tattoos and takes an upload or a cut

The picker, the first step, SHALL list every kept tattoo as a card with its image, its name, its state, *outlined*,
*not outlined* or *ready for this photograph*, and what it came from: when it was kept, the size it came with when
downscaled, its stage-1 pairs on this photograph, or the photograph a cut is from. It SHALL take an upload through the
import's staging and keep it under a name the operator may change, and SHALL offer *Cut from this photo*, which keeps
a cut of the render's photograph under a name. A tattoo is ready for this photograph when it is outlined and, if
uploaded, holds the floor of stage-1 pairs on it or is flagged *not on this photo*. An uploaded card SHALL offer *not
on this photo*, a cut's SHALL not. A cut of another photograph SHALL stay listed and SHALL not be chosen on this
render, saying whose it is. A refusal SHALL be shown with its fix. Choosing a card SHALL open the step its state
asks: the outline until the tattoo is outlined, then stage 1, the direct stage or stage 2 as its mode takes.

The picker is where a tattoo enters the screen, so it shows state and the way forward, and a ready tattoo goes
straight to the stage that places it.

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
- **WHEN** a cut from another photograph is listed on this render
- **THEN** its card cannot be chosen and says whose photograph it is

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
