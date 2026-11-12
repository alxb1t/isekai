## ADDED Requirements

### Requirement: The large view of a render offers Place a tattoo

The large view of a render SHALL offer *Place a tattoo* as a button and as the command `⇧P`,
declared once in the key store, and SHALL open the placement screen's first step on that render.

The placement screen is reached from the image it places on. `⇧T` stays the theme's
([D48](../../../docs/decisions.md#d48--a-theme-is-a-token-set-chosen-in-the-browser)).

#### Scenario: the button opens the picker on the render
- **Key:** `ui:place-offer:the-button-opens-the-picker`
- **Layers:** unit
- **WHEN** *Place a tattoo* is chosen on a render's large view
- **THEN** the route is the render's `place` route at the first step

#### Scenario: the command is declared once
- **Key:** `ui:place-offer:the-command-is-declared-once`
- **Layers:** unit
- **WHEN** the large view's commands are read
- **THEN** `place` is declared on `⇧P` and no other command takes that key

### Requirement: The placement screen has a route of its own per step

The system SHALL give the placement screen the route
`/c/<collection>/renders/<run>/<flow>/<version>/<seed>/place/<step>`, with the tattoo's name after the step
where the step needs one, and SHALL not mount the screen again when only its step or name changes.
A step the screen does not know SHALL redirect to its first.

A route under a render's path would collide with `compare` unless it is its own segment,
and the screen keeps its state across steps.

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

### Requirement: The placement screen holds no key of its own

The placement screen and the components it holds SHALL declare no command.
The keys the app answers everywhere SHALL stay, and a dialog SHALL close on `esc` as every dialog does.

The keys come once the screen has been used and shows which are useful; one declared now would be one to keep.

#### Scenario: the screen declares no command
- **Key:** `ui:place-keys:the-screen-declares-no-command`
- **Layers:** unit
- **WHEN** the sources of the screen and its components are read
- **THEN** none declares a command through `useKeys`

### Requirement: The panel zooms at the pointer, pans by a drag, and fits or shows 1:1

The panel SHALL show one image in a viewport, zoom it at the pointer by the wheel between the declared floor
and ceiling, pan it by a drag on the image, and offer *Fit* and *1:1*.
A zoom SHALL keep the image point under the pointer under it. A pan SHALL keep part of the image in the viewport.
The panel SHALL show its zoom as a percentage.

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

### Requirement: An outline is clicked, closed on its first point and edited by dragging

The outline editor SHALL add a vertex at each click on the image while the outline is open,
close the outline on a click within the declared radius of the first vertex, move a vertex by a drag on it,
insert a vertex on an edge by a shift-click, remove a vertex by a double click,
undo its last change and clear itself.
A closed outline SHALL need at least the declared floor of vertices and SHALL take no more than the ceiling.
The radius SHALL be the same on screen at every zoom.

A click that moves is a pan, not a vertex.

#### Scenario: a click adds a vertex and the first closes
- **Key:** `ui:outline-edit:a-click-adds-a-vertex-and-the-first-closes`
- **Layers:** unit
- **WHEN** vertices are clicked and then the first is clicked
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

### Requirement: The picker lists the kept tattoos and takes an upload or a cut

The picker, the first step, SHALL list every kept tattoo as a card with its image, its name, its state,
*outlined* or *not outlined*, and what it came from: when it was kept, the size it came with when downscaled,
or the photograph a cut is from.
It SHALL take an upload through the import's staging and keep it under a name the operator may change,
and SHALL offer *Cut from this photo*, which keeps a cut of the render's photograph under a name.
A cut of another photograph SHALL stay listed and SHALL not be chosen on this render, saying whose it is.
A refusal SHALL be shown with its fix. Choosing a card SHALL open the outline step on it.

The picker is where a tattoo enters the screen, so it shows nothing but state and the way forward.

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
While the outline is open the controls SHALL be disabled with their reason.

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
- **THEN** the ink view, the white point and the tone are disabled, each with *outline open*

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
