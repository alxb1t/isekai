## MODIFIED Requirements

### Requirement: Every command has one key, declared once, and none fires while typing

The system SHALL declare each keyboard command once, with its key and its label, on the screen or overlay that offers
it, and SHALL draw every key hint and the key list from those declarations, the list opening on `?` and on the app
bar's `?` button; no screen SHALL carry a key bar. It SHALL match a key by the physical key, whatever the keyboard
layout, and SHALL treat Mod as `⌘` on macOS and `Ctrl` elsewhere. An open overlay SHALL take every key before the
screen beneath it, and the screen before the keys offered everywhere. While focus is in a text field, no command
SHALL fire but `Esc`, `Mod+↵`, `Mod+Z`, `⇧Mod+Z` and `Mod+K`, and on macOS Review's `⌃H` and `⌃L`, which move between
its panes; the field SHALL keep its own editing keys. On a grid, a move between rows SHALL keep the column it is in,
held at a shorter row's end. On the hub, a focused button or link SHALL keep `↵` and `Space`. An `Esc` that ends an
input method's composition SHALL be the input method's, closing nothing. `Esc` SHALL close an open suggestion list
first, then leave the field, then close the top overlay, then go back on the screen, and SHALL never close a billing
alert. No key SHALL spend money but the Render dialog's `Mod+↵`, which confirms the price it quotes.

A key typed into a field is text, never a command; a list drawn from the declarations cannot disagree with the keys.
Option is the window manager's on Linux and types characters on macOS, and a layout moves letters but not keys.

```
keydown ─▶ in a text field? ─ yes ─▶ Esc · Mod+↵ · Mod+Z · ⇧Mod+Z · Mod+K, else the field's own
               │ no
               ▼
           top overlay ─▶ screen ─▶ everywhere        the first that declares the key runs
```

#### Scenario: a key is matched by the physical key
- **Key:** `ui:keys:a-key-is-matched-by-the-physical-key`
- **Layers:** unit
- **WHEN** `⇧H` is pressed on a Cyrillic layout
- **THEN** the command declared for `⇧H` runs

#### Scenario: Mod is Command or Control
- **Key:** `ui:keys:mod-is-command-or-control`
- **Layers:** unit
- **WHEN** a command declared for `Mod+K` is offered
- **THEN** `⌘K` and `Ctrl+K` each run it

#### Scenario: no command fires in a text field
- **Key:** `ui:keys:no-command-fires-in-a-text-field`
- **Layers:** unit
- **WHEN** a declared letter is pressed with focus in a text field
- **THEN** no command runs
- **AND** `Esc`, `Mod+↵`, `Mod+Z` and `Mod+K` still do

#### Scenario: a command waits until the field is left
- **Key:** `ui:keys:a-command-waits-until-the-field-is-left`
- **Layers:** e2e
- **WHEN** `⇧H` is typed into a tag field, then `Esc` and `⇧H` are pressed
- **THEN** the field holds the typed text and Review stays open
- **AND** the second `⇧H` opens the hub

#### Scenario: a focused control keeps Enter and Space
- **Key:** `ui:keys:a-focused-control-keeps-enter-and-space`
- **Layers:** unit
- **WHEN** `↵` or `Space` is pressed on the hub with focus on a button or a link
- **THEN** the control answers it and the cell's command does not run

#### Scenario: an overlay takes the keys first
- **Key:** `ui:keys:an-overlay-takes-the-keys-first`
- **Layers:** unit
- **WHEN** an overlay and the screen beneath it both declare a key
- **THEN** only the overlay's command runs

#### Scenario: Esc closes the nearest thing first
- **Key:** `ui:keys:esc-closes-the-nearest-thing-first`
- **Layers:** unit
- **WHEN** `Esc` is pressed with a suggestion list open in a field inside an overlay
- **THEN** the list closes, and the next `Esc` leaves the field, and the next closes the overlay

#### Scenario: the key list and the hints come from the declarations
- **Key:** `ui:keys:hints-come-from-the-declarations`
- **Layers:** unit
- **WHEN** a screen declares its commands
- **THEN** its button hints and the key list name each command's key and label
- **AND** no key bar is drawn

#### Scenario: Renders moves by cell and by image
- **Key:** `ui:keys:renders-moves-by-cell-and-by-image`
- **Layers:** unit
- **WHEN** `l` and then `→` are pressed on a cell's last image of the Renders grid
- **THEN** each moves to the next image, crossing into the next cell, and `h` at a row's start reaches its source

#### Scenario: Review moves between its panes
- **Key:** `ui:keys:review-moves-between-its-panes`
- **Layers:** unit
- **WHEN** `l` is pressed from the rail three times
- **THEN** focus moves through the source pane and the sheet to ④

#### Scenario: a row move keeps the column
- **Key:** `ui:keys:a-row-move-keeps-the-column`
- **Layers:** unit
- **WHEN** `j` is pressed on the Renders grid's third image of a row whose next row holds two
- **THEN** the focus moves to that row's second image

#### Scenario: an Esc that ends a composition closes nothing
- **Key:** `ui:keys:an-esc-ending-a-composition-closes-nothing`
- **Layers:** unit
- **WHEN** `Esc` ends an input method's composition in a field inside an overlay
- **THEN** the field keeps the focus and the overlay stays open

#### Scenario: Review's panes move from a field on macOS
- **Key:** `ui:keys:review-panes-move-from-a-field-on-macos`
- **Layers:** unit
- **WHEN** `⌃L` is pressed with focus in a tag field, on macOS and then on Linux
- **THEN** on macOS the next pane takes the focus, and on Linux nothing moves


### Requirement: The Renders view shows each source's images by flow and version

The system SHALL list a batch's images by source and offered flow, each cell's approval versions newest first, and
SHALL show them as a grid of sources by flows, each cell one row of its images, its versions oldest to newest, each
image marked with its version, and open an image's large view, with the sheet it was rendered from, from any of them.
A cell whose newest approval lacks images of its count SHALL carry the number it lacks, as the render stage counts
it. Each source SHALL show its photograph's thumbnail, upright, opening the photograph in a viewer, its cell the
grid's first column, reached by the keys and opened by `↵`. `Esc` on a large
view SHALL return to the screen it was opened from, focused on the image it closed, and Renders SHALL keep its focus
across the Back button and a switch of tabs. It SHALL mark an approval it cannot read as damaged, naming the
file, and show every image, that version's own among them; and SHALL refuse an address whose version is not `v` and
ASCII digits. It SHALL serve each thumbnail, a render's or a source's, from a cache in the library's `.cache/`, made
on first request and named by the image's own bytes. It SHALL refuse an image it cannot read, one past Pillow's pixel
bound among them, naming the file. It SHALL serve a photograph, a source or a run's copy, as the image its bytes are,
whatever its name ends in, and a source in a format the render does not read as an upright JPEG of it.

The images come back to where the sheets were decided, version by version in the order they were approved; a cache the
library can lose costs only its rebuild. Two batches can hold one source rendered at one seed, so only the bytes say
which image a thumbnail shows. One damaged file costs only its own version, never the batch's page. The count a cell
lacks is the render stage's own, so the page and the render agree on what is ready. A source keeps the name it arrived
with, and one ending `.html` served by its name would run as a page on the surface's own origin; one placed by hand in
another format is still shown, as its thumbnail is.

#### Scenario: versions are listed newest first
- **Key:** `ui:renders:versions-newest-first`
- **Layers:** unit
- **WHEN** a cell holds images under two approvals
- **THEN** the newer approval's images are listed first

#### Scenario: a damaged approval marks its own version
- **Key:** `ui:renders:a-damaged-approval-marks-its-version`
- **Layers:** unit
- **WHEN** one of a cell's two approvals holds a count no render takes
- **THEN** its version is marked damaged, naming the file
- **AND** the other version and every image are still listed

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
- **WHEN** two batches hold different images of one source, flow, version and seed
- **THEN** each image's thumbnail is made from that image

#### Scenario: a source's thumbnail is upright
- **Key:** `ui:renders:a-source-thumbnail-is-upright`
- **Layers:** unit
- **WHEN** a source's thumbnail is asked for and its file declares a turning orientation
- **THEN** the thumbnail is drawn upright
- **AND** a second request reads it from `.cache/`

#### Scenario: a cell counts what is ready
- **Key:** `ui:renders:a-cell-counts-what-is-ready`
- **Layers:** unit
- **WHEN** a cell's newest approval holds fewer images than its count
- **THEN** the cell carries the number of images it lacks

#### Scenario: the large view shows its sheet
- **Key:** `ui:renders:the-large-view-shows-its-sheet`
- **Layers:** e2e
- **WHEN** an image is opened from the grid
- **THEN** its large view shows the approval it was rendered from
- **AND** `Esc` returns to the grid focused on that image
- **AND** `h` from a row's first image reaches its source, and `↵` there opens its photograph

#### Scenario: a source opens in the viewer
- **Key:** `ui:renders:a-source-opens-in-the-viewer`
- **Layers:** e2e
- **WHEN** a source's thumbnail is clicked in the Renders view
- **THEN** its photograph opens in a dialog, fitted to the window
- **AND** `Esc` closes the dialog and leaves the address unchanged

#### Scenario: a damaged version's images are drawn
- **Key:** `ui:renders:a-damaged-versions-images-are-drawn`
- **Layers:** e2e
- **WHEN** the Renders view opens on a cell whose one approval is damaged
- **THEN** that version's images are drawn beside its damaged mark
- **AND** the first of them holds the focus

#### Scenario: a photograph is served as the image its bytes are
- **Key:** `ui:renders:a-photograph-is-served-as-its-bytes`
- **Layers:** unit
- **WHEN** a source whose name ends `.html` holds a PNG and is asked for whole
- **THEN** it is served as `image/png`, and the browser is told not to guess another type
- **AND** a run's photograph is served the same way
- **AND** a source in another format is served as an upright JPEG of it

#### Scenario: an image it cannot read is refused
- **Key:** `ui:renders:an-unreadable-image-is-refused`
- **Layers:** unit
- **WHEN** an image past Pillow's pixel bound is read for a thumbnail, or served whole
- **THEN** it is refused, naming the file

#### Scenario: a grid keeps its focus
- **Key:** `ui:renders:a-grid-keeps-its-focus`
- **Layers:** unit
- **WHEN** a batch's grid focus is moved, then its view is opened again
- **THEN** the focus is where it was left, or on the first spot when that one is gone


### Requirement: A version says what it was, and Compare shows a seed's two versions

The system SHALL head each image's large view with its approval version, the version it came from, read from its
producer, naming it a revision when its fields differ from that version's and a re-roll when only its count or seeds
do, and the approval's time, count and seeds. A large view whose seed is rendered under an older version of the same
source and flow SHALL offer Compare with the newest such version first, and every large view SHALL offer Compare with
any other image of its source and flow, picked in the viewer, saying so when the two seeds differ or the two share a
sheet, showing both images at equal size, the fields that changed, what changed in the count and seeds, and the
tokens before and after. Every large view SHALL offer *Side by side*, the image beside its run's photograph at equal
height.

The origin is already on disk, so nothing new records it. Same seed, same composition: the difference left is the
edit. The grid carries the images; the large view, which carries the sheet, carries what the version was.

#### Scenario: a version is named a revision or a re-roll
- **Key:** `ui:compare:a-version-is-named-by-what-changed`
- **Layers:** unit
- **WHEN** one version changes a field of the version it came from and another changes only its seeds
- **THEN** the first's large view is headed a revision and the second's a re-roll

#### Scenario: Compare pairs a seed with its newest older version
- **Key:** `ui:compare:a-seed-pairs-with-its-newest-older-version`
- **Layers:** unit
- **WHEN** a seed is rendered under versions one, two and three
- **THEN** version three's large view compares with version two

#### Scenario: Compare shows the pair and the changed fields
- **Key:** `ui:compare:compare-shows-the-pair-and-the-change`
- **Layers:** e2e
- **WHEN** Compare is opened on a revised image
- **THEN** both images and the changed fields are shown
- **AND** a pick of another seed's image compares it, saying the seeds differ

#### Scenario: Side by side sets the image beside its photograph
- **Key:** `ui:compare:side-by-side-sets-the-image-beside-its-photograph`
- **Layers:** e2e
- **WHEN** *Side by side* is opened on an image's large view
- **THEN** one dialog shows the run's photograph and the image at equal height

#### Scenario: Compare takes any two images of a cell
- **Key:** `ui:compare:any-two-images-of-a-cell`
- **Layers:** unit
- **WHEN** Compare is asked for an image of v4 against an image of v2 with another seed
- **THEN** it serves both, the changed fields and that the seeds differ


### Requirement: Render is confirmed in a dialog that quotes what renders, its limit and its price at most

The system SHALL offer Render from a bar on a batch's hub and its Renders view that counts the images short of their
approvals' counts, and SHALL show no such bar when none is short and no count is refused, nor on the hub while
changes wait for Prepare. The bar SHALL be disabled, with its reason, when a render runs, when a pod may still be
billing, when no RunPod key is in the surface's environment, and when an approval's count is refused. It SHALL open a
dialog listing per offered flow the images that will render and what is left out, with the reason, the session's
estimate and limit, and its price at most — the limit at the hourly maximum `gpunit.toml` names, with the volume at
its configured rate. Its confirmation SHALL be the only act that rents; the dialog SHALL hold no URL, and SHALL close
when its page is left, the confirmation's own navigation among the ways out. The confirmation SHALL carry the limit
and the number of images the dialog showed, and SHALL be refused, starting nothing, when the batch's quote taken
again has a longer limit or another number of images. The bar SHALL show the newest offer asked for, whatever order
the answers arrive in.

The quote is what the operator agrees to; gpunit refuses a card above the hourly maximum, so the price is a bound and
not a guess. A reload never reopens a confirmation that spends; a changed image total or longer limit requires
a fresh confirmation, even where the limit sits at its floor or cap. An equal-total change of sources or approvals
is outside that comparison. A bar that is absent needs no reason, and one forward action holds the screen's accent;
a refused count keeps the bar, so the refusal is never silent.

#### Scenario: the dialog lists what renders per flow
- **Key:** `ui:render:the-dialog-lists-what-renders`
- **Layers:** unit
- **WHEN** a batch's quote is asked for with approvals short of their count in two flows
- **THEN** it lists each flow's images and what is left out, with the reason
- **AND** it carries the estimate, the limit and the price at most

#### Scenario: without a key Render is disabled
- **Key:** `ui:render:without-a-key-render-is-disabled`
- **Layers:** unit
- **WHEN** the surface's environment holds no RunPod key
- **THEN** Render is disabled, naming the fix

#### Scenario: nothing short disables Render
- **Key:** `ui:render:nothing-short-disables-render`
- **Layers:** unit
- **WHEN** every approval in a batch already has its count of images
- **THEN** the batch's Render offer counts no image
- **AND** it names why

#### Scenario: Prepare takes the bar first
- **Key:** `ui:render:prepare-takes-the-bar-first`
- **Layers:** unit
- **WHEN** a hub has images short and changes waiting for Prepare
- **THEN** the Prepare bar shows and the Render bar does not
- **AND** with nothing waiting the Render bar shows, and with nothing short neither does

#### Scenario: a refused count is shown
- **Key:** `ui:render:a-refused-count-is-shown`
- **Layers:** unit
- **WHEN** a batch's only approval short of its count holds a count no render takes
- **THEN** its Render offer counts no image and carries the refusal, naming the file
- **AND** the Render bar shows, disabled, with its reason

#### Scenario: the confirmation starts the render
- **Key:** `ui:render:the-confirmation-starts-the-render`
- **Layers:** e2e
- **WHEN** the dialog's Render is confirmed
- **THEN** the session's page opens at `/b/<batch>/sessions/<id>`
- **AND** back on the hub the dialog is closed

#### Scenario: a quote that has grown is refused
- **Key:** `ui:render:a-grown-quote-is-refused`
- **Layers:** unit
- **WHEN** Render is confirmed with a shorter limit, or fewer images, than the batch's quote now gives
- **THEN** the confirmation is refused, naming that the quote changed
- **AND** no job starts

#### Scenario: a stale offer is dropped
- **Key:** `ui:render:a-stale-offer-is-dropped`
- **Layers:** unit
- **WHEN** an older offer request is answered after a newer one
- **THEN** the bar keeps the newer offer


### Requirement: Each batch's render sessions are listed and shown from their records

The system SHALL list a batch's render sessions from its records, the running one first and the rest newest first,
each with its start, its duration against its limit, its outcome and its images, and SHALL show one session's page
from its record, live while it runs, with the volume steps and Stop the job adds. A Sessions tab SHALL sit beside the
hub, Review and Renders. While a render runs, every screen SHALL show it running, with its clock, linking to its
session's page. A finished image SHALL open in the viewer, and the page SHALL be a grid: a column for each photograph
the session was asked to render, a row for each flow it renders, the photographs' row at the foot, a cell holding
that flow's images of that photograph and a waiting tile for each still to come, each opening in the viewer, moved
through by the keys; images and photographs SHALL be drawn at the tile size Renders draws. The viewer SHALL follow
its list when it changes while open.

A session is the record the render wrote, so the page, the list and the terminal agree, and a finished session can
be found again. A running render is the one thing on the surface that bills by the minute.

#### Scenario: a batch lists its sessions
- **Key:** `ui:sessions:a-batch-lists-its-sessions`
- **Layers:** unit
- **WHEN** a batch holds a running record and two finished ones
- **THEN** its sessions are listed running first, then newest first

#### Scenario: a session's page reads its record
- **Key:** `ui:sessions:a-session-reads-its-record`
- **Layers:** unit
- **WHEN** a session is asked for by its id
- **THEN** its record's images, steps and outcome are served
- **AND** an id no record holds is refused, naming the batch's sessions

#### Scenario: the list shows a finished session
- **Key:** `ui:sessions:the-list-shows-a-finished-session`
- **Layers:** e2e
- **WHEN** the Sessions tab is opened on a batch holding a finished record
- **THEN** the session is listed with its images, and its page opens from it

#### Scenario: a terminal render stays live
- **Key:** `ui:sessions:a-terminal-render-stays-live`
- **Layers:** unit
- **WHEN** a terminal render runs without an app job slot
- **THEN** its record reads running and the global running-session read names its batch and id
- **AND** after its process releases ownership without an outcome the record reads ended without an outcome

#### Scenario: the selected record keeps the newest response
- **Key:** `ui:sessions:the-selected-record-keeps-the-newest-response`
- **Layers:** unit
- **WHEN** an older record read answers after a newer read of the same session
- **THEN** the selected record keeps the newer outcome and images

#### Scenario: an observed list follows its render
- **Key:** `ui:sessions:an-observed-list-follows-its-render`
- **Layers:** unit
- **WHEN** a render starts and lands images while its batch's sessions list is observed
- **THEN** the list reads the running record and its images again
- **AND** overlapping refreshes coalesce without an older response replacing newer state

#### Scenario: the viewer follows image identity
- **Key:** `ui:sessions:the-viewer-follows-image-identity`
- **Layers:** unit
- **WHEN** an open viewer's list shrinks, reorders, grows or becomes empty
- **THEN** it keeps the selected image by identity while present, otherwise a valid neighbour
- **AND** an empty list closes the viewer

#### Scenario: the session grid holds each flow over the originals
- **Key:** `ui:sessions:the-grid-holds-each-flow-over-the-originals`
- **Layers:** unit
- **WHEN** a record plans two images of one photograph in summon and one of another in conjure
- **THEN** the grid has a column per photograph, a row per flow over the photographs' row, and three waiting tiles
- **AND** a record without a plan places its landed images and no waiting tiles

#### Scenario: the session grid moves by photograph and by row
- **Key:** `ui:sessions:the-grid-moves-by-photograph-and-row`
- **Layers:** unit
- **WHEN** `l` and then `j` are pressed on the grid's first render
- **THEN** `l` moves to the next photograph's column and `j` to the row below, held at the photographs' row

