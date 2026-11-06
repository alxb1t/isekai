## MODIFIED Requirements

### Requirement: Render is confirmed in a dialog that quotes what renders, its limit and its price at most

The system SHALL offer Render from a bar on a collection's hub and its Renders view that counts the images short of
their approvals' counts, its collection's and, as `+n in other collections`, every other collection's, and SHALL show no
such bar when no collection is short and no count is refused, nor on the hub while changes wait for Prepare. While a
render runs the bar SHALL show the session's totals and *Session* in place of the count and Render, and name the images
short that the session does not render as waiting for the next session. The bar SHALL be disabled, with its reason, when
a pod may still be billing, when no RunPod key is in the surface's environment, and when an approval's count is refused.
It SHALL open a dialog listing a row per collection short of images, in the Library's order, each ticked, and in each
row per offered flow the photographs that will render, as tiles grouped by flow, and none that is left out; unticking a
row SHALL quote the rest again; the session's estimate and limit, and its price at most — the limit at the hourly
maximum `gpunit.toml` names, with the volume at its configured rate; an estimate past the ceiling `gpunit.toml` names
SHALL disable the confirmation, saying so. A tile's `×`, or `⌫` while the tile holds the focus, SHALL take its
photograph's flow out of the session and quote the rest again, show the next photograph past the cap, and move the focus
to the next tile; a refused count SHALL show no tile. A row whose every tile is taken out SHALL read *all removed*,
unticked, and leave the confirmation, and with every row so emptied the confirmation SHALL be disabled, saying *Nothing
left to render.* The tiles SHALL be one stop in the `Tab` order: `h` and `l` SHALL move the focus along a flow's tiles,
`j` and `k` to the next and the previous flow's, its place held at the shorter's end, and a key's move SHALL scroll the
focused tile to the centre of the list where the scroll allows, the first flow's to the list's top and the last's to its
foot. Its confirmation SHALL be the only act that rents; the dialog SHALL hold no URL, and SHALL close when its page is
left, and the confirmation SHALL close it and open the session drawer over the page. The confirmation SHALL carry the
ticked collections, the limit, the number of images the dialog showed and the photographs taken out, which the session
SHALL not render, and SHALL be refused, starting nothing, when the ticked collections' quote taken again has a longer
limit or another number of images, or names a photograph that is not one of a quoted collection's runs. The bar SHALL
show the newest offer asked for, whatever order the answers arrive in.

The quote is what the operator agrees to; gpunit refuses a card above the hourly maximum, so the price is a bound and
not a guess. A reload never reopens a confirmation that spends; a changed image total or longer limit requires a fresh
confirmation, even where the limit sits at its floor or cap. An equal-total change of sources or approvals is outside
that comparison. A bar that is absent needs no reason, and one forward action holds the screen's accent; a refused count
keeps the bar, so the refusal is never silent. A photograph is known by sight, so the dialog shows it rather than its
file name, and is taken out where it is seen; the dialog shows only what renders, as that is what the operator agrees
to. A removal is the render verb's `--without`, so the page's session is one the terminal can run
([D3](../../../docs/decisions.md#d3--the-hand-path-stays)).

#### Scenario: the dialog lists what renders per flow
- **Key:** `ui:render:the-dialog-lists-what-renders`
- **Layers:** unit
- **WHEN** a collection's quote is asked for with approvals short of their count in two flows, and a draft in one
- **THEN** it lists each flow's images, each photograph with its run, and nothing left out
- **AND** it carries the estimate, the limit and the price at most

#### Scenario: the dialog shows each photograph as a thumbnail by flow
- **Key:** `ui:render:the-dialog-shows-thumbnails-by-flow`
- **Layers:** unit
- **WHEN** a collection's quote holds photographs to render in a flow
- **THEN** each flow shows its photographs' thumbnails, 15 and then `+n`, each counted only above one image

#### Scenario: a photograph taken out leaves the quote and the session
- **Key:** `ui:render:a-photograph-taken-out-leaves-the-quote`
- **Layers:** unit
- **WHEN** the quote and the confirmation name one run's flow taken out of a collection short in two runs
- **THEN** the quote counts the other run's images alone
- **AND** the render job's verb carries a `--without` for the run's flow

#### Scenario: a photograph no quoted run holds is refused
- **Key:** `ui:render:a-photograph-not-quoted-is-refused`
- **Layers:** unit
- **WHEN** the quote names a photograph taken out whose run is not one of the collection's runs
- **THEN** the quote is refused, naming that the dialog must be opened again

#### Scenario: taking a photograph out shows the next past the cap
- **Key:** `ui:render:taking-out-shows-the-next`
- **Layers:** unit
- **WHEN** a flow holds more photographs than the cap and one of its shown photographs is taken out
- **THEN** the next photograph past the cap shows
- **AND** `+n` counts one fewer

#### Scenario: a tile is taken out by its key and by its ×
- **Key:** `ui:render:a-tile-is-taken-out-by-its-key`
- **Layers:** e2e
- **WHEN** a flow's first tile holds the focus, then `l` and `⌫` are pressed, then each tile left is taken out by
  its `×`
- **THEN** `l` moved the focus to the second tile, `⌫` took it out of the row and its quote, the focus on the next
- **AND** the row reads *all removed* and is unticked

#### Scenario: with every row taken out nothing is left to render
- **Key:** `ui:render:nothing-left-disables-render`
- **Layers:** unit
- **WHEN** every tile of every row is taken out
- **THEN** each row reads *all removed*
- **AND** the confirmation is disabled, saying *Nothing left to render.*

#### Scenario: the tiles move by flow
- **Key:** `ui:render:the-tiles-move-by-flow`
- **Layers:** unit
- **WHEN** `h`, `l`, `j` and `k` move the focus over a flow of three tiles and a flow of two
- **THEN** `h` and `l` step along a flow's tiles and stay at its ends
- **AND** `j` and `k` move to the next and the previous flow's, held at the shorter's end

#### Scenario: a key's move centres the focused tile
- **Key:** `ui:render:a-key-move-centres-the-tile`
- **Layers:** unit
- **WHEN** a key moves the focus to a middle flow's tile, then to the first flow's, then to the last's
- **THEN** the middle tile scrolls to the list's centre
- **AND** the first scrolls the list to its top, and the last to its foot

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

## REMOVED Requirements

### Requirement: A dialog holds the focus while it is open

**Reason**: the Render dialog's first control is its first photograph's tile, not *Keep the volume open*, so its
scenario's title no longer holds.

**Migration**: *A dialog holds the focus from its first control while it is open* replaces it; its other key stays, and
`ui:dialogs:the-render-dialog-opens-on-its-checkbox` gives way to
`ui:dialogs:the-render-dialog-opens-on-its-first-photograph`.

## ADDED Requirements

### Requirement: A dialog holds the focus from its first control while it is open

The system SHALL open every confirming dialog — Render, Revise, Delete, and New collection or Add sources — and the key
list as a modal dialog, the page behind it inert, the focus on its first control and held inside it, and SHALL return
the focus to where it was when it closes. The Render dialog's first control SHALL be its first photograph's tile, on
which `↵` does nothing, and `Tab` SHALL move on from the tiles in the dialog's order, past each later collection's tick,
to *Keep the volume open*, which `Space` toggles and `↵` leaves alone; with no tile, the checkbox SHALL be first. The
Revise dialog's first control SHALL be its confirm button, and the Delete dialog's its *No*. The key list SHALL stand
centred over most of the window, its keys in columns by scope — everywhere, then the screen's — and `⌃/`, `Esc` and
the backdrop SHALL close it.

A key goes where the eye is. A dialog over a grid that leaves the focus on the grid sends `↵` and `Tab` to what it
covers. The Render dialog asks first which photographs render, so its first focus is on them, the checkbox one stop
after; only `Mod+↵` spends money, so `↵` on a tile or the checkbox never renders.

#### Scenario: the Render dialog opens on its first photograph
- **Key:** `ui:dialogs:the-render-dialog-opens-on-its-first-photograph`
- **Layers:** e2e
- **WHEN** the Render dialog opens on the hub, then `↵`, then `Tab` until the focus has passed every control
- **THEN** the first photograph's tile held the focus first, `↵` rendered nothing, and the focus never left the dialog
- **AND** `Esc` returns the focus to the hub cell it left

#### Scenario: the key list is a dialog
- **Key:** `ui:dialogs:the-key-list-is-a-dialog`
- **Layers:** unit
- **WHEN** `⌃/` opens the key list on a screen
- **THEN** it is a modal dialog holding the focus, the everywhere keys in one column and the screen's in another
- **AND** `⌃/`, `Esc` and a click on the backdrop each close it
