## MODIFIED Requirements

### Requirement: Render is confirmed in a dialog that quotes what renders, its limit and its price at most

The system SHALL offer Render from a bar on a collection's hub and its Renders view that counts the images short of
their approvals' counts, its collection's and, as `+n in other collections`, every other collection's, and SHALL show no
such bar when no collection is short and no count is refused, nor on the hub while changes wait for Prepare. The bar
SHALL be disabled, with its reason, when a render runs, when a pod may still be billing, when no RunPod key is in the
surface's environment, and when an approval's count is refused. It SHALL open a dialog listing a row per collection
short of images, in the Library's order, each ticked, and in each row per offered flow the images that will render and
what is left out, with the reason; unticking a row SHALL quote the rest again; the session's estimate and limit, and its
price at most — the limit at the hourly maximum `gpunit.toml` names, with the volume at its configured rate; an estimate
past the ceiling `gpunit.toml` names SHALL disable the confirmation, saying so. Its confirmation SHALL be the only act
that rents; the dialog SHALL hold no URL, and SHALL close when its page is left, and the confirmation SHALL close it and
open the session drawer over the page. The confirmation SHALL carry the ticked collections, the limit and the number of
images the dialog showed, and SHALL be refused, starting nothing, when the ticked collections' quote taken again has a
longer limit or another number of images. The bar SHALL show the newest offer asked for, whatever order the answers
arrive in.

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

### Requirement: The running render opens in a drawer every screen offers

The system SHALL show the running render in a session drawer: a modal dialog over half the window, at least 480 px wide,
on the right, over a dark backdrop, holding no URL. `⌃;` SHALL open and close it on every screen, from a field too, and
the running render's link SHALL open it; confirming a render SHALL open it, and a render started from the terminal SHALL
open nothing. It SHALL read the running render's record, live while it runs, with the volume steps and Stop the job
adds; after it ends it SHALL show that session's outcome, its images and its time until the app reloads or another
render starts; with neither it SHALL say no render runs. Its images SHALL be a grid per collection the session renders,
stacked in its recorded collection order, retaining scan order for older records without it, each headed by its
name: a column for each photograph the session was asked to render, a row for
each flow, the photographs' row at the foot, a cell holding that flow's images of that photograph and a waiting tile for
each still to come, drawn at the tile size Renders draws and moved through by `h j k l` and the arrows, `j` `↓` on a
grid's last row moving into the first row of the grid below and `k` `↑` back, keeping the column, held at a shorter
row's end. `↵` SHALL open the focused row in the viewer over the drawer, which SHALL follow its list when it changes
while open; `⇧I` SHALL close the drawer and open the focused image's collection's Renders. A click on the backdrop, `⌃;`
and `Esc` SHALL close it, `Esc` closing the viewer first.

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
