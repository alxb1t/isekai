## MODIFIED Requirements

### Requirement: The large view deletes its render after asking, and the Hub opens on its cell

The system SHALL offer *Delete* on a render's large view, on `⇧⌫`, after *Compare with…*, opening a modal dialog,
*Delete this render?*, whose *No* comes first and holds the focus; `h` `l` and `←` `→` SHALL move between *No* and
*Yes*, `↵` SHALL press the focused one, and `Esc` SHALL answer *No*. *Yes* SHALL delete the render's own thumbnails from
the library's cache, discard the render through the render stage — its approval going with its last render, and a flow
left with no approval keeping only its assignment — and open the Hub focused on the render's cell, from whichever screen
opened the view. The server SHALL refuse the delete while a render session runs for the collection, deleting nothing,
and the dialog SHALL show the refusal.

A failed render is deleted where it is seen. *No* first makes a stray `↵` harmless, and a write beside a running session
is refused, as *Cancel approve* is. The cell is where the delete shows: one image fewer, an older approval's images once
the newest's last image goes, or *tagged* once the flow's last approval goes, with nothing to review. A thumbnail is
told from another collection's of the same photograph and seed by its image's digest, so only the render's own goes.

```
large view ──⇧⌫──▶ Delete this render?  [No] [Yes]
                     │ Esc · No              │ Yes
                     ▼                       ▼
                 large view           thumbnails ─▶ discard ─▶ its approval, if emptied ─▶ the Hub on the cell
```

#### Scenario: the dialog opens on No
- **Key:** `ui:delete-render:the-dialog-opens-on-no`
- **Layers:** e2e
- **WHEN** `⇧⌫` is pressed on a large view, then `l`, `h` and `Esc`
- **THEN** *Delete this render?* opens with *No* focused, `l` focusing *Yes* and `h` *No*
- **AND** `Esc` closes it, the image still shown

#### Scenario: Yes deletes the render and opens the Hub on its cell
- **Key:** `ui:delete-render:yes-opens-the-hub-on-the-cell`
- **Layers:** e2e
- **WHEN** `⇧⌫`, `l` and `↵` are pressed on the large view of a cell's only image, opened at its address
- **THEN** the Hub opens focused on that cell, reading *tagged*
- **AND** the image, its approval's prompt and the flow's sheet are gone from the run

#### Scenario: the Hub opens without the deleted render
- **Key:** `ui:delete-render:the-hub-opens-without-the-deleted-render`
- **Layers:** e2e
- **WHEN** `⇧⌫`, `l` and `↵` are pressed on the large view of a cell's only image
- **THEN** the Hub is read again before it opens, and no thumbnail of the deleted render is asked for

#### Scenario: the route deletes the render and its thumbnail
- **Key:** `ui:delete-render:the-route-deletes-the-render-and-its-thumbnail`
- **Layers:** unit
- **WHEN** a render whose thumbnail is cached is deleted at its address
- **THEN** its image, its record and its thumbnail are gone
- **AND** the other render and its thumbnail stay, and so does another collection's thumbnail of the same photograph
  and seed

#### Scenario: the delete is refused while a render runs
- **Key:** `ui:delete-render:refused-while-a-render-runs`
- **Layers:** unit
- **WHEN** a render is deleted while a render session runs for its collection
- **THEN** the delete is refused, saying a render session is running
- **AND** no file is deleted

#### Scenario: a reload that lands after leaving moves nothing
- **Key:** `ui:delete-render:a-reload-that-lands-after-leaving-moves-nothing`
- **Layers:** unit
- **WHEN** a render is deleted, the operator leaves the large view, and the Hub's read that followed the deletion ends
- **THEN** the Hub is not opened, whether that read was answered or refused
- **AND** a read that ends while the view stays opens the Hub on the render's cell

#### Scenario: a dismissed dialog still opens the Hub
- **Key:** `ui:delete-render:a-dismissed-dialog-still-opens-the-hub`
- **Layers:** unit
- **WHEN** *Yes* is pressed, the dialog is dismissed before the deletion answers, and the deletion succeeds
- **THEN** the Hub is read again and opens on the render's cell
- **AND** a deletion that is refused opens nothing

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
- **THEN** the first dialog is titled *Remove this tattoo?* and names `bow`
- **AND** the second is titled *Delete this render?*
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

#### Scenario: a dismissed removal still lists the rest
- **Key:** `ui:picker:a-dismissed-removal-still-lists-the-rest`
- **Layers:** unit
- **WHEN** *Yes* is pressed on a tattoo, the dialog is dismissed before the removal answers, and the removal succeeds
- **THEN** the picker is told the tattoo is removed, so the list is read again without it
- **AND** a removal that is refused tells it nothing

#### Scenario: a crop that lands after leaving is dropped
- **Key:** `ui:picker:a-crop-that-lands-after-leaving-is-dropped`
- **Layers:** unit
- **WHEN** a cut's card is left before its ink view answers, and the answer then lands
- **THEN** no object URL is made for it
- **AND** an answer that lands while the card stays is shown
