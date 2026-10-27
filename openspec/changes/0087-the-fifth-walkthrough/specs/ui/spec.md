## MODIFIED Requirements

### Requirement: Render is confirmed in a dialog that quotes what renders, its limit and its price at most

The system SHALL offer Render from a bar on a collection's hub and its Renders view that counts the images short of
their approvals' counts, its collection's and, as `+n in other collections`, every other collection's, and SHALL show no
such bar when no collection is short and no count is refused, nor on the hub while changes wait for Prepare. While a
render runs the bar SHALL show the session's totals and *Session* in place of the count and Render, and name the images
short that the session does not render as waiting for the next session. The bar SHALL be disabled, with its reason, when
a pod may still be billing, when no RunPod key is in the surface's environment, and when an approval's count is refused.
It SHALL open a dialog listing a row per collection short of images, in the Library's order, each ticked, and in each
row per offered flow the images that will render and what is left out, with the reason; unticking a row SHALL quote the
rest again; the session's estimate and limit, and its price at most — the limit at the hourly maximum `gpunit.toml`
names, with the volume at its configured rate; an estimate past the ceiling `gpunit.toml` names SHALL disable the
confirmation, saying so. Its confirmation SHALL be the only act that rents; the dialog SHALL hold no URL, and SHALL
close when its page is left, and the confirmation SHALL close it and open the session drawer over the page. The
confirmation SHALL carry the ticked collections, the limit and the number of images the dialog showed, and SHALL be
refused, starting nothing, when the ticked collections' quote taken again has a longer limit or another number of
images. The bar SHALL show the newest offer asked for, whatever order the answers arrive in.

The quote is what the operator agrees to; gpunit refuses a card above the hourly maximum, so the price is a bound and
not a guess. A reload never reopens a confirmation that spends; a changed image total or longer limit requires
a fresh confirmation, even where the limit sits at its floor or cap. An equal-total change of sources or approvals
is outside that comparison. A bar that is absent needs no reason, and one forward action holds the screen's accent;
a refused count keeps the bar, so the refusal is never silent.

#### Scenario: the dialog lists what renders per flow
- **Key:** `ui:render:the-dialog-lists-what-renders`
- **Layers:** unit
- **WHEN** a collection's quote is asked for with approvals short of their count in two flows
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
- **WHEN** every approval in a collection already has its count of images
- **THEN** the collection's Render offer counts no image
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
- **WHEN** a collection's only approval short of its count holds a count no render takes
- **THEN** its Render offer counts no image and carries the refusal, naming the file
- **AND** the Render bar shows, disabled, with its reason

#### Scenario: the confirmation starts the render
- **Key:** `ui:render:the-confirmation-starts-the-render`
- **Layers:** e2e
- **WHEN** the dialog's Render is confirmed
- **THEN** the session drawer opens over the hub, which keeps its URL
- **AND** the dialog is closed

#### Scenario: a quote that has grown is refused
- **Key:** `ui:render:a-grown-quote-is-refused`
- **Layers:** unit
- **WHEN** Render is confirmed with a shorter limit, or fewer images, than the collection's quote now gives
- **THEN** the confirmation is refused, naming that the quote changed
- **AND** no job starts

#### Scenario: a stale offer is dropped
- **Key:** `ui:render:a-stale-offer-is-dropped`
- **Layers:** unit
- **WHEN** an older offer request is answered after a newer one
- **THEN** the bar keeps the newer offer

#### Scenario: the dialog quotes every collection
- **Key:** `ui:render:the-dialog-quotes-every-collection`
- **Layers:** unit
- **WHEN** two collections are short of images and the quote is asked for both, then for one
- **THEN** the first quote lists both, with one estimate and one limit
- **AND** the second lists the one alone

#### Scenario: past the ceiling disables Render
- **Key:** `ui:render:past-the-ceiling-disables-render`
- **Layers:** unit
- **WHEN** the ticked collections' estimate passes the configured ceiling
- **THEN** the quote's confirmation is disabled, naming the ceiling

#### Scenario: a running session shows its totals
- **Key:** `ui:render:a-running-session-shows-its-totals`
- **Layers:** unit
- **WHEN** the bar is read while a session renders three images and a fourth is short outside it
- **THEN** it shows the session's totals and *Session*, and one image waiting for the next session
- **AND** it shows no count ready to render and no Render

### Requirement: The Renders view shows each source's images by flow and version

The system SHALL list a collection's images by source and offered flow, each cell's approval versions newest first, and
SHALL show them as a grid of sources by flows, each cell one row of its images, its versions oldest to newest, each
image marked with its version, and open an image's large view, with the sheet it was rendered from, from any of them. A
cell whose newest approval lacks images of its count SHALL carry the number it lacks, as the render stage counts it.
Each source SHALL show its photograph's thumbnail, upright, opening the photograph in a viewer, its cell the grid's
first column, reached by the keys and opened by `↵`. `h` `l` and the arrows on a large view SHALL step through the
renders of the screen it was opened from — Renders: the source's row across its flows; the hub: the cell's images —
replacing its address, held at either end, its head naming the step, `2 of 5`. `Esc` on a large view SHALL return to the
screen it was opened from, focused on the image it closed and scrolled to the window's centre, and Renders SHALL keep
its focus across the Back button and a switch of tabs. It SHALL mark an approval it cannot read as damaged, naming the
file, and show every image, that version's own among them; and SHALL refuse an address whose version is not `v` and
ASCII digits. It SHALL serve each thumbnail, a render's or a source's, from a cache in the library's `.cache/`, made on
first request and named by the image's own bytes. It SHALL refuse an image it cannot read, one past Pillow's pixel bound
among them, naming the file. It SHALL serve a photograph, a source or a run's copy, as the image its bytes are, whatever
its name ends in, and a source in a format the render does not read as an upright JPEG of it.

The images come back to where the sheets were decided, version by version in the order they were approved; a cache the
library can lose costs only its rebuild. Two collections can hold one source rendered at one seed, so only the bytes say
which image a thumbnail shows. One damaged file costs only its own version, never the collection's page. The count a
cell lacks is the render stage's own, so the page and the render agree on what is ready. A source keeps the name it
arrived with, and one ending `.html` served by its name would run as a page on the surface's own origin; one placed by
hand in another format is still shown, as its thumbnail is.

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
- **WHEN** two collections hold different images of one source, flow, version and seed
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
- **AND** `Esc` returns to the grid focused on that image, and that image in view
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
- **WHEN** a collection's grid focus is moved, then its view is opened again
- **THEN** the focus is where it was left, or on the first spot when that one is gone

#### Scenario: the large view steps through its screen's order
- **Key:** `ui:renders:the-large-view-steps-its-screens-order`
- **Layers:** unit
- **WHEN** `l` is pressed on the large view of a source's first image, opened from Renders, then from the hub
- **THEN** it shows the row's next image across the flows, then the cell's next image
- **AND** at the last image `l` holds

### Requirement: The hub shows each source's stage in each offered flow, and a tick assigns it

The system SHALL show a collection's hub as a grid of its sources by the flows the surface offers, each cell carrying
the stage read from that run's directory — no flow, assigned, tagged, sheet, draft, approved or rendered — and SHALL
ignore any other flow's directory. A cell whose run file cannot be read SHALL show that it is unreadable, with the
refusal the pipeline raised, and the rest of the grid SHALL still be shown. Reading the hub SHALL write nothing; a tick
SHALL write only through the assigning verb, and an untick only while the cell is assigned. A source imported as it is,
still carrying metadata, SHALL be marked on its row. Each source SHALL show its name and its thumbnail, and its row
SHALL carry the size read from its own file, with or without a run, which the viewer's title names. A source's thumbnail
and a cell's images SHALL sit at the foot of their cells, level across the row, whatever text stands above them; a
cell's refusal SHALL stand above its images, and `↵ view photo` SHALL take no line of the source's cell. A cell SHALL
name its newest image — the newest version holding images, then its last-written image — and a click or `↵` SHALL follow
the cell's stage: tick while unassigned or assigned, open Review on a sheet or a draft, open the sheet read-only on an
approval with no image, and open the viewer on the newest of the cell's images where it holds any, stepping through
them, `↵` opening an image's large view; a tagged or unreadable cell SHALL do nothing. A cell holding images SHALL show
every one of them, oldest to newest, each marked with its version. A source's cell SHALL be the grid's first column,
reached by `h` and `←`, and `↵` there SHALL open its photograph in the viewer, stepping through the collection's
sources. The hub SHALL keep its focus across a large view, the Back button and a switch of tabs, a restored focus
scrolled to the window's centre. The header SHALL leave a 12 px gap between items.

A stage is a directory listing, the rule every stage already follows, so the grid cannot drift from the disk, and a tick
survives a reload. The mark and the size are read from the source itself, so no file records them. An approved cell can
hold an older version's images, so its newest image is named by the server rather than guessed by the page. A row's
pictures share a foot, so a long name, a mark or a refusal moves only the text above them.

#### Scenario: a cell's stage comes from its run's directory
- **Key:** `ui:hub:a-cells-stage-comes-from-its-run`
- **Layers:** unit
- **WHEN** a run holds a flow's approved sheet and no render
- **THEN** that cell's stage is approved

#### Scenario: a flow the surface does not offer is ignored
- **Key:** `ui:hub:an-untracked-flow-is-ignored`
- **Layers:** unit
- **WHEN** a run holds a directory for a flow the surface does not offer
- **THEN** the hub shows no column and no refusal for it

#### Scenario: an unreadable run file marks its cell alone
- **Key:** `ui:hub:an-unreadable-file-marks-its-cell`
- **Layers:** unit
- **WHEN** one cell's run file cannot be read
- **THEN** that cell is unreadable, with the pipeline's refusal
- **AND** every other cell shows its stage

#### Scenario: the hub writes nothing
- **Key:** `ui:hub:the-hub-writes-nothing`
- **Layers:** unit
- **WHEN** a collection's hub is read
- **THEN** no file in the collection is created, changed or removed

#### Scenario: a tick assigns the flow
- **Key:** `ui:hub:a-tick-assigns-the-flow`
- **Layers:** e2e
- **WHEN** an unassigned cell is ticked
- **THEN** the cell reads assigned
- **AND** it still reads assigned after a reload
- **AND** the header keeps a 12 px gap between its items

#### Scenario: a prepared cell's tick stays
- **Key:** `ui:hub:a-prepared-tick-stays`
- **Layers:** unit
- **WHEN** an untick is asked for a cell past assigned
- **THEN** it is refused and no file changes

#### Scenario: a source imported as it is is marked
- **Key:** `ui:hub:an-uncleaned-source-is-marked`
- **Layers:** unit
- **WHEN** a source still carries metadata
- **THEN** its row is marked not cleaned

#### Scenario: a source is sized from its file
- **Key:** `ui:hub:a-source-is-sized-from-its-file`
- **Layers:** unit
- **WHEN** the hub is read for a source that has no run
- **THEN** its row carries the width and height of its file

#### Scenario: a cell names its newest image
- **Key:** `ui:hub:a-cell-names-its-newest-image`
- **Layers:** unit
- **WHEN** an approved cell holds images only under an older version
- **THEN** it names that version and its last-written image

#### Scenario: a click follows the cell's stage
- **Key:** `ui:hub:a-click-follows-the-cells-stage`
- **Layers:** unit
- **WHEN** a cell is clicked at each stage
- **THEN** it ticks up to assigned, opens Review on a sheet, a draft or an unrendered approval, and opens an image
- **AND** a tagged or an unreadable cell does nothing

#### Scenario: a rendered cell opens its newest image
- **Key:** `ui:hub:a-rendered-cell-opens-its-newest-image`
- **Layers:** e2e
- **WHEN** a rendered cell is clicked, then `↵` is pressed in the viewer
- **THEN** the viewer opens on its newest image, then that image's large view
- **AND** `Esc` returns to the hub, focused on that cell, and that cell in view

#### Scenario: a cell lists its images
- **Key:** `ui:hub:a-cell-lists-its-images`
- **Layers:** unit
- **WHEN** a cell holds images under two versions
- **THEN** the hub carries them oldest to newest, each with its version and seed

#### Scenario: the source cell opens its photograph
- **Key:** `ui:hub:the-source-cell-opens-its-photograph`
- **Layers:** e2e
- **WHEN** `h` is pressed on a row's first flow cell, then `↵`
- **THEN** the row's photograph opens in the viewer
- **AND** while the source cell holds the focus, its thumbnail's foot is level with the row's images' foot

### Requirement: Every command has one key, declared once, and none fires while typing

The system SHALL declare each keyboard command once, with its key and its label, on the screen or overlay that offers
it, and SHALL draw every key hint and the key list from those declarations, the list opening on `⌃/` on every screen and
on the app bar's `?` button; no screen SHALL carry a key bar. It SHALL match a key by the physical key, whatever the
keyboard layout, and SHALL treat Mod as `⌘` on macOS and `Ctrl` elsewhere. An open overlay SHALL take every key before
the screen beneath it, and the screen before the keys offered everywhere. While focus is in a text field, no command
SHALL fire but `Esc`, `Mod+↵`, `Mod+Z`, `⇧Mod+Z`, `Mod+K`, `⌃/` and `⌃;`, Review's `⌃P`, and on macOS Review's `⌃H` and
`⌃L`, which move between its panes, and `⌃J` and `⌃K`, which move between its fields as `↓` and `↑` do; the field SHALL
keep its own editing keys. On a grid, a move between rows SHALL keep the column it is in, held at a shorter row's end.
On the hub and in the session drawer, a focused button or link SHALL keep `↵` and `Space`. An `Esc` that ends an input
method's composition SHALL be the input method's, closing nothing. `Esc` SHALL close an open suggestion list first, then
leave the field, then close the top overlay, then go back on the screen, and SHALL never close a billing alert. A plain
letter SHALL move the focus, and a command SHALL take `⇧` and a letter. No key
SHALL spend money but the Render dialog's `Mod+↵`, which confirms the price it quotes.

A key typed into a field is text, never a command; a list drawn from the declarations cannot disagree with the keys.
Option is the window manager's on Linux and types characters on macOS, and a layout moves letters but not keys.
On Linux `Ctrl+J` is the browser's and `Ctrl+K` is `Mod+K`, so the field moves are macOS's alone. A shifted letter is
not pressed in passing, so it guards what writes.

```
keydown ─▶ in a text field? ─ yes ─▶ Esc · Mod+↵ · Mod+Z · ⇧Mod+Z · Mod+K · ⌃/ · ⌃;, Review's ⌃P,
               │                     on macOS Review's ⌃H ⌃L ⌃J ⌃K, else the field's own
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
- **WHEN** `↵` or `Space` is pressed on the hub or in the session drawer with focus on a button or a link
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

#### Scenario: the key list opens from a field
- **Key:** `ui:keys:the-key-list-opens-from-a-field`
- **Layers:** unit
- **WHEN** `⌃/` and then `?` are pressed with focus in a text field
- **THEN** `⌃/` opens the key list and `?` is typed into the field

#### Scenario: Review's fields move from a field on macOS
- **Key:** `ui:keys:review-fields-move-from-a-field-on-macos`
- **Layers:** unit
- **WHEN** Review's commands are declared on macOS and then on Linux
- **THEN** on macOS `⌃J` and `⌃K` move to the next and the previous field from a text field
- **AND** on Linux neither is declared

### Requirement: A version says what it was, and Compare sets an image beside any image of its source

The system SHALL head each image's large view with its approval version, the version it came from, read from its
producer, naming it a revision when its fields differ from that version's and a re-roll when only its count or seeds do,
and the approval's time, count and seeds. `⇧C` on a large view SHALL open a pick of its source's images: the
photograph's row on top, then a row per flow holding images of the source, each row its images oldest to newest, each
captioned by its version, the image compare started from marked, the pick's head naming the focused image's flow,
version and seed; the focus SHALL start on the newest older version of its seed, else the image before it, else the
photograph; `h j k l` and the arrows SHALL move it, keeping the column, held at a shorter row's end, `↵` SHALL compare
the image picked and `Esc` close the pick. Compare SHALL set the image picked on the left and the image compare started
from on the right, at equal size, each headed by its flow, version and seed, and nothing else: the pair as tall as the
window less the app bar and the heads, centred. The large view SHALL offer no *Side by side*.

```
large view · summon v2 · seed 9423  ⇧C ─▶  photo                  [▣]
                                           summon-anime-wai       [v1][v2·][v3]
                                           summon-flat-anime-wai  [v1]
                                       ↵ ─▶ Compare: the image picked │ summon v2 · seed 9423
```

The origin is already on disk, so nothing new records it. A pick reads as a choice when every choice is in view; one
source's images are every comparison the operator makes for one person. The eye returns to where it came from, on the
right. The images are what is compared, so they take the room.

#### Scenario: a version is named a revision or a re-roll
- **Key:** `ui:compare:a-version-is-named-by-what-changed`
- **Layers:** unit
- **WHEN** one version changes a field of the version it came from and another changes only its seeds
- **THEN** the first's large view is headed a revision and the second's a re-roll

#### Scenario: Compare pairs a seed with its newest older version
- **Key:** `ui:compare:a-seed-pairs-with-its-newest-older-version`
- **Layers:** unit
- **WHEN** a seed is rendered under versions one, two and three
- **THEN** version three's pick opens focused on version two

#### Scenario: Compare shows the pair and the changed fields
- **Key:** `ui:compare:compare-shows-the-pair-and-the-change`
- **Layers:** e2e
- **WHEN** `⇧C` is pressed on a revised image, then `↵`
- **THEN** the older version is on the left and the revised image on the right, each under its head alone
- **AND** a pick of another flow's image compares it, saying the seeds differ

#### Scenario: the photograph's pick sets it beside the image
- **Key:** `ui:compare:side-by-side-sets-the-image-beside-its-photograph`
- **Layers:** e2e
- **WHEN** `⇧C` is pressed on an image's large view, then `k` to the photograph's row and `↵`
- **THEN** the photograph is on the left and the image on the right, at equal height, with no fields

#### Scenario: Compare takes any two images of a source
- **Key:** `ui:compare:any-two-images-of-a-cell`
- **Layers:** unit
- **WHEN** Compare is asked for a summon image of v4 against a flat summon image of v1 with another seed
- **THEN** it serves both images' heads, and no changed field
- **AND** the image picked is on the left, the image compare started from on the right

#### Scenario: the pick moves by row and column
- **Key:** `ui:compare:the-pick-moves-by-row-and-column`
- **Layers:** unit
- **WHEN** `j` is pressed on the photograph's row, then `l` twice, then `j` onto a shorter row
- **THEN** the focus moves to the first flow's first image, then its third, then the shorter row's last

#### Scenario: the pick names the focused tile
- **Key:** `ui:compare:the-pick-names-the-focused-tile`
- **Layers:** unit
- **WHEN** the focus moves to the second of two seeds of one version
- **THEN** its caption reads the version alone, and the pick's head names its flow, version and seed
