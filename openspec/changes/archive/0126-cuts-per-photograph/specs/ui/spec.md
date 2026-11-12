## MODIFIED Requirements

### Requirement: The picker lists the kept tattoos and takes an upload or a cut

The picker, the first step, SHALL list as a card each upload and each cut of this render's photograph, with its image,
its name, its state, *outlined*, *not outlined* or *ready for this photograph*, and what it came from: when it was kept,
the size it came with when downscaled, its stage-1 pairs on this photograph, or the photograph a cut is from.
It SHALL list no cut of another photograph.
It SHALL take an upload through the import's staging and keep it under a name the operator may change,
and SHALL offer *Cut from this photo*, which keeps a cut of the render's photograph under a name.
Each form SHALL say in a line under its heading what it takes: the upload, the tattoo's design on its own,
a flat image and not a photo of skin; the cut, the tattoo as it shows on this render's photograph.
A card SHALL offer *Remove*, which asks a second click before it removes the tattoo and lists the rest again.
A tattoo is ready for this photograph when it is outlined and, if uploaded,
holds the floor of stage-1 pairs on it or is flagged *not on this photo*.
An uploaded card SHALL offer *not on this photo*, a cut's SHALL not.
A refusal SHALL be shown with its fix. Choosing a card SHALL open the step its state asks:
the outline until the tattoo is outlined, then stage 1, the direct stage or stage 2 as its mode takes.

The picker is where a tattoo enters the screen, so it shows state and the way forward,
and a ready tattoo goes straight to the stage that places it.
A cut is the photograph's own, so another render of that photograph lists it and every other render does not.

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

#### Scenario: remove takes a second click
- **Key:** `ui:picker:remove-takes-a-second-click`
- **Layers:** unit
- **WHEN** *Remove* is pressed on a card, then on the same card again, and on one card then another
- **THEN** the first press arms that card and removes nothing, and the second on the same card removes it
- **AND** a press on another card arms that card and removes nothing

#### Scenario: each form says what it takes
- **Key:** `ui:picker:each-form-says-what-it-takes`
- **Layers:** unit
- **WHEN** the lines under the upload form's and the cut form's headings are read
- **THEN** the upload's says the tattoo's design on its own, a flat image and not a photo of skin
- **AND** the cut's says the tattoo as it shows on this render's photograph
