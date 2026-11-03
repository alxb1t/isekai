## MODIFIED Requirements

### Requirement: The running render opens in a drawer every screen offers

The system SHALL show the running render in a session drawer: a modal dialog as wide as its widest grid, at least half
the window and 480 px, at most the window less 100 px, a wider grid scrolling inside it, on the right, over a dark
backdrop, holding no URL. `⌃;` SHALL open and close it on every screen, from a field too, and the running render's
link SHALL open it; confirming a render SHALL open it, and a render started from the terminal SHALL open nothing. Its
bar and the Render bar SHALL show one progress, the images done over the images asked, from one function, the drawer
keeping the time against the limit as text. It SHALL read the running render's record, live while it runs, with the
volume steps and Stop the job adds; after it ends it SHALL show that session's outcome, its images and its time until
the app reloads or another render starts; with neither it SHALL say no render runs. Its images SHALL be a grid per
collection the session renders, stacked in its recorded collection order, retaining scan order for older records
without it, each headed by its name: a column for each photograph the session was asked to render, a row for each
flow, the photographs' row at the foot, a cell holding that flow's images of that photograph and a waiting tile for
each still to come, drawn at the tile size Renders draws and moved through by `h j k l` and the arrows, `j` `↓` on a
grid's last row moving into the first row of the grid below and `k` `↑` back, keeping the column, held at a shorter
row's end. `↵` SHALL open the focused row in the viewer over the drawer, which SHALL follow its list when it changes
while open; `⇧I` SHALL close the drawer and open the focused image's collection's Renders. A click on the backdrop,
`⌃;` and `Esc` SHALL close it, `Esc` closing the viewer first.

```
any screen ──⌃; or ●──▶ the drawer, half the window ──↵──▶ the viewer over it
                         esc / ⌃; / the backdrop ◀──esc── closes one layer
```

A running render bills by the minute wherever the operator is, so it is the app's, not a collection's: it is glanced at,
not gone to. A session is the record the render wrote, so the drawer and the terminal agree; once it ends its images are
on Renders.

#### Scenario: the drawer holds the render
- **Key:** `ui:sessions:the-drawer-holds-the-render`
- **Layers:** e2e
- **WHEN** a render is confirmed, `↵` is pressed on its image, then `Esc` twice, then `⌃;`
- **THEN** the drawer shows the render over the hub, the viewer its image, then the drawer again, then the page alone
- **AND** `⌃;` opens the drawer again on the finished session's outcome

#### Scenario: the drawer keeps the last session
- **Key:** `ui:sessions:the-drawer-keeps-the-last-session`
- **Layers:** unit
- **WHEN** a running render ends, then another starts
- **THEN** the drawer shows the first's outcome until the second starts, then the second

#### Scenario: the viewer closes for a replacement session
- **Key:** `ui:sessions:the-viewer-closes-for-a-replacement-session`
- **Layers:** unit
- **WHEN** another terminal render starts while the finished session's photograph viewer is open
- **THEN** the viewer closes while the drawer waits for the replacement record
- **AND** the drawer shows the replacement session without an error

#### Scenario: a session's page reads its record
- **Key:** `ui:sessions:a-session-reads-its-record`
- **Layers:** unit
- **WHEN** a session is asked for by its id
- **THEN** its record's images, steps and outcome are served
- **AND** an id no record holds is refused, naming the id

#### Scenario: a terminal render stays live
- **Key:** `ui:sessions:a-terminal-render-stays-live`
- **Layers:** unit
- **WHEN** a terminal render runs across collections in reverse name order without an app job slot
- **THEN** its records read running and the global running-session read carries their id and complete traversal order
- **AND** after its process releases ownership without an outcome the record reads ended without an outcome

#### Scenario: the selected record keeps the newest response
- **Key:** `ui:sessions:the-selected-record-keeps-the-newest-response`
- **Layers:** unit
- **WHEN** an older record read answers after a newer read of the same session
- **THEN** the selected record keeps the newer outcome and images

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

#### Scenario: the grids stack by collection
- **Key:** `ui:sessions:the-grids-stack-by-collection`
- **Layers:** unit
- **WHEN** `j` is pressed on the first grid's last row, then `k`
- **THEN** the focus moves into the second grid's first row, in the same column, then back

#### Scenario: one progress for the Render bar and the drawer
- **Key:** `ui:sessions:one-progress-for-the-bar-and-the-drawer`
- **Layers:** unit
- **WHEN** a session has rendered three of four images
- **THEN** the Render bar and the drawer's bar are each three quarters full
- **AND** with no plan the bar slides, sized by nothing

#### Scenario: the drawer fits its widest grid
- **Key:** `ui:sessions:the-drawer-fits-its-widest-grid`
- **Layers:** e2e
- **WHEN** the drawer holds a session whose grid is wider than half the window
- **THEN** the drawer is as wide as that grid, short of the window by 100 px at most

### Requirement: A version says what it was, and Compare sets an image beside any image of its source

The system SHALL head each image's large view with its approval version, the version it came from, read from its
producer, naming it a revision when its fields differ from that version's and a re-roll when only its count or seeds
do, and the approval's time, count and seeds. `⇧C` on a large view SHALL open a pick of its source's images: the
photograph's row on top, then a row per flow holding images of the source, each row its images oldest to newest, each
captioned by its version, the image compare started from marked, the pick's head naming the focused image's flow,
version and seed on two lines, `Compare <the image started from>` and `with <the focused image>`, each cut at its end;
the pick SHALL be as wide as its longest row, its images 20 px apart, at least 480 px and at most the window less 96
px, a longer row scrolling inside it, whatever is focused; the focus SHALL start on the newest older version of its
seed, else the image before it, else the photograph; `h j k l` and the arrows SHALL move it, keeping the column, held
at a shorter row's end, `↵` SHALL compare the image picked and `Esc` close the pick. Compare SHALL set the image
picked on the left and the image compare started from on the right, at equal size, each headed by its flow, version
and seed, and nothing else: the pair as tall as the window less the app bar and the heads, centred. The large view
SHALL offer no *Side by side*.

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

#### Scenario: the pick holds its width
- **Key:** `ui:compare:the-pick-holds-its-width`
- **Layers:** e2e
- **WHEN** the focus moves in the pick from an image to the photograph
- **THEN** the pick's width does not change
