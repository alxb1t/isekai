## MODIFIED Requirements

### Requirement: An image's large view shows its sheet and walks the photograph's row, and its thumbnail is made once

The system SHALL open an image's large view, with the sheet it was rendered from, from the hub's cell modal. `h` `l` and
the arrows on a large view SHALL walk the photograph's row — its flows in the hub's column order, each version oldest
first, each version's seeds in numeric order — replacing its address, held at either end, its head naming the step, `2
of 5`. `Esc` and *Back to Hub* on a large view SHALL open the hub focused on the cell of the image it closed, scrolled
to the window's centre, whatever opened the view. The large view of an image whose approval no hand can read SHALL be
headed damaged, naming the file, and count nothing. It SHALL refuse an address whose version is not `v` and ASCII
digits. It SHALL serve each thumbnail, a render's or a source's, from a cache in the library's `.cache/`, made on first
request and named by the image's own bytes, a source's upright. It SHALL refuse an image it cannot read, one past
Pillow's pixel bound among them, naming the file. It SHALL serve a photograph, a source or a run's copy, as the image
its bytes are, whatever its name ends in, and a source in a format the render does not read as an upright JPEG of it.

A cache the library can lose costs only its rebuild. Two collections can hold one source rendered at one seed, so only
the bytes say which image a thumbnail shows. One damaged file costs only its own image's heading. A source keeps the
name it arrived with, and one ending `.html` served by its name would run as a page on the surface's own origin; one
placed by hand in another format is still shown, as its thumbnail is. One order on every screen keeps a render's place,
and the image a large view closes may be another flow's than the one it opened on, so the hub lands on that image's
cell; the hub is the one screen of images, so a pasted address goes back there too.

#### Scenario: an address naming no version is refused
- **Key:** `ui:renders:an-address-naming-no-version-is-refused`
- **Layers:** unit
- **WHEN** an image is asked for at a version spelled in digits outside ASCII
- **THEN** the request is refused naming the version, never failed

#### Scenario: a thumbnail is made once
- **Key:** `ui:renders:a-thumbnail-is-made-once`
- **Layers:** unit
- **WHEN** an image's thumbnail is asked for twice
- **THEN** the second answer is read from `.cache/` without decoding the image

#### Scenario: a thumbnail is its own image's
- **Key:** `ui:renders:a-thumbnail-is-its-own-images`
- **Layers:** unit
- **WHEN** two collections hold different images of one source, flow, version and seed
- **THEN** each image's thumbnail is made from that image

#### Scenario: a source's thumbnail is upright
- **Key:** `ui:renders:a-source-thumbnail-is-upright`
- **Layers:** unit
- **WHEN** a source's thumbnail is asked for and its file declares a turning orientation
- **THEN** the thumbnail is drawn upright
- **AND** a second request reads it from `.cache/`

#### Scenario: the large view shows its sheet
- **Key:** `ui:renders:the-large-view-shows-its-sheet`
- **Layers:** e2e
- **WHEN** an image is opened from the cell modal
- **THEN** its large view shows the approval it was rendered from
- **AND** `Esc` returns to the hub focused on that image's cell, and that cell in view

#### Scenario: a damaged approval marks its own version
- **Key:** `ui:renders:a-damaged-approval-marks-its-version`
- **Layers:** unit
- **WHEN** one of a cell's two approvals holds a count no render takes
- **THEN** its image's large view is headed damaged, naming the file, and counts nothing
- **AND** the other version's large view is not damaged

#### Scenario: a photograph is served as the image its bytes are
- **Key:** `ui:renders:a-photograph-is-served-as-its-bytes`
- **Layers:** unit
- **WHEN** a source whose name ends `.html` holds a PNG and is asked for whole
- **THEN** it is served as `image/png`, and the browser is told not to guess another type
- **AND** a run's photograph is served the same way
- **AND** a source in another format is served as an upright JPEG of it

#### Scenario: a photograph in a third format is refused
- **Key:** `ui:renders:a-photograph-in-a-third-format-is-refused`
- **Layers:** unit
- **WHEN** a run's photograph holds bytes that are neither JPEG nor PNG and is asked for
- **THEN** the request is refused, not served
- **AND** the refusal says the bytes are neither

#### Scenario: an image it cannot read is refused
- **Key:** `ui:renders:an-unreadable-image-is-refused`
- **Layers:** unit
- **WHEN** an image past Pillow's pixel bound is read for a thumbnail, or served whole
- **THEN** it is refused, naming the file

#### Scenario: the large view walks the photograph's row
- **Key:** `ui:renders:the-large-view-walks-the-photographs-row`
- **Layers:** unit
- **WHEN** `l` is pressed on the large view of a source's first image
- **THEN** it shows the row's next image, then the next flow's first image, in the hub's column order
- **AND** at the last image `l` holds
