## MODIFIED Requirements

### Requirement: Render is confirmed in a dialog that quotes what renders, its limit and its price at most

The system SHALL offer Render from a bar on a collection's hub that counts the images short of their approvals' counts and the bakes queued, its collection's and, as `+n in other collections`, every other collection's, and SHALL show no such bar when no collection is short of images or holds a queued bake and no count is refused, nor on the hub while changes wait for Prepare. While a render runs the bar SHALL show the session's totals and *Session* in place of the counts and Render, and name the images short that the session does not render as waiting for the next session. The bar SHALL be disabled, with its reason, when a pod may still be billing, when no RunPod key is in the surface's environment, and when an approval's count is refused. It SHALL open a dialog titled *Render n images*, *Render n images · m bakes* or, with no image short, *Bake m*, listing a row per collection short of images or holding a queued bake, in the Library's order, each ticked, and in each row per offered flow the photographs that will render, as tiles grouped by flow, then a row per queued bake naming its photograph, version, seed and edit number, and none that is left out; unticking a row SHALL quote the rest again; the session's estimate, counting each bake, and limit, and its price at most — the limit at the hourly maximum `gpunit.toml` names, with the volume at its configured rate; an estimate past the ceiling `gpunit.toml` names SHALL disable the confirmation, saying so. A tile's `×`, or `⌫` while the tile holds the focus, SHALL take its photograph's flow out of the session, its bakes with it, and quote the rest again, show the next photograph past the cap, and move the focus to the next tile; a bake row's `×` SHALL take its photograph's flow out the same way; a refused count SHALL show no tile. A row whose every tile and bake is taken out SHALL read *all removed*, unticked, and leave the confirmation, and with every row so emptied the confirmation SHALL be disabled, saying *Nothing left to render.* The tiles SHALL be one stop in the `Tab` order: `h` and `l` SHALL move the focus along a flow's tiles, `j` and `k` to the next and the previous flow's, its place held at the shorter's end, and a key's move SHALL scroll the focused tile to the centre of the list where the scroll allows, the first flow's to the list's top and the last's to its foot. Its confirmation SHALL be the only act that rents; the dialog SHALL hold no URL, and SHALL close when its page is left, and the confirmation SHALL close it and open the session drawer over the page. The confirmation SHALL carry the ticked collections, the limit, the number of images and the number of bakes the dialog showed and the photographs taken out, which the session SHALL not render, and SHALL be refused, starting nothing, when the ticked collections' quote taken again has a longer limit, another number of images or another number of bakes, or names a photograph that is not one of a quoted collection's runs. A session of bakes alone SHALL be allowed. The bar SHALL show the newest offer asked for, whatever order the answers arrive in.

The quote is what the operator agrees to; gpunit refuses a card above the hourly maximum, so the price is a bound and not a guess. A reload never reopens a confirmation that spends; a changed image total, bake total or longer limit requires a fresh confirmation, even where the limit sits at its floor or cap. An equal-total change of sources or approvals is outside that comparison. A bar that is absent needs no reason, and one forward action holds the screen's accent; a refused count keeps the bar, so the refusal is never silent. A photograph is known by sight, so the dialog shows it rather than its file name, and is taken out where it is seen; the dialog shows only what renders, as that is what the operator agrees to. A removal is the render verb's `--without`, so the page's session is one the terminal can run ([D3](../../../docs/decisions.md#d3--the-hand-path-stays)). A bake is an edit request with no image, run by the same session as the images ([D4](../../../docs/decisions.md#d4--the-ui-runs-stages-only-as-the-clis-children), [D36](../../../docs/decisions.md#d36--a-render-session-is-isekai-render)), and `--without` names a photograph's flow, so a bake leaves with its photograph's flow and no other way.

#### Scenario: the dialog lists what renders per flow
- **Key:** `ui:render:the-dialog-lists-what-renders`
- **Layers:** unit
- **WHEN** a collection's quote is asked for with approvals short of their count in two flows, and a draft in one
- **THEN** it lists each flow's images, each photograph with its run, and nothing left out
- **AND** it carries the estimate, the limit and the price at most

#### Scenario: the dialog lists each queued bake
- **Key:** `ui:render:the-dialog-lists-each-queued-bake`
- **Layers:** unit
- **WHEN** a collection's quote is asked for with an approval short of its count and a queued bake of another photograph's render
- **THEN** it lists the images by flow, and the bake with its photograph, version, seed and edit number
- **AND** the estimate counts the bake beside the images

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

#### Scenario: a photograph taken out takes its bakes
- **Key:** `ui:render:a-photograph-taken-out-takes-its-bakes`
- **Layers:** unit
- **WHEN** one run's flow holds an image short and a queued bake, and the quote names that run's flow taken out
- **THEN** the quote lists neither the image nor the bake
- **AND** the confirmation carries the number of bakes of the runs that stay

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
- **WHEN** every tile and every bake of every row is taken out
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
- **WHEN** every approval in a collection already has its count of images and no bake is queued
- **THEN** the collection's Render offer counts no image and no bake
- **AND** it names why

#### Scenario: a bake alone is a session
- **Key:** `ui:render:a-bake-alone-is-a-session`
- **Layers:** unit
- **WHEN** every approval has its count of images and one bake is queued
- **THEN** the offer counts the bake and no image, and the quote lists the collection and prices the bake
- **AND** the confirmation starts a render that plans no image

#### Scenario: the dialog is titled for what it does
- **Key:** `ui:render:the-dialog-is-titled-for-what-it-does`
- **Layers:** unit
- **WHEN** the quote holds images alone, images and a bake, and a bake alone
- **THEN** the titles read *Render 2 images*, *Render 2 images · 1 bake* and *Bake 1*

#### Scenario: Prepare takes the bar first
- **Key:** `ui:render:prepare-takes-the-bar-first`
- **Layers:** unit
- **WHEN** a hub has images short and changes waiting for Prepare
- **THEN** the Prepare bar shows and the Render bar does not
- **AND** with nothing waiting the Render bar shows, and with nothing short and no bake queued neither does

#### Scenario: a bar counts a bake alone
- **Key:** `ui:render:a-bar-counts-a-bake-alone`
- **Layers:** unit
- **WHEN** a hub has no image short and a bake queued, here or in another collection
- **THEN** the Render bar shows, counting the bakes, with Render

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

#### Scenario: a changed bake count is refused
- **Key:** `ui:render:a-changed-bake-count-is-refused`
- **Layers:** unit
- **WHEN** Render is confirmed with fewer bakes than the quote now gives, or none named
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

## ADDED Requirements

### Requirement: A render's large view shows its photograph and its bakes, and each bake has its own address

The system SHALL show on an image's large view the photograph it was rendered from as a thumbnail and, when the render has bakes, the chain of them: the render first, then each bake of its seed by its number, each one level further in for each bake it descends through, a row naming its number and, baked, its time, or, queued, that it waits for the next session. A baked row SHALL open that bake's large view at `…/<seed>/edit/<k>`, showing the bake's image, the approval's fields the render has, and the bake's record: its edit, the image it was placed on and its time. A queued bake's view SHALL show the image it is placed on, marked queued. A bake's view SHALL offer no *Draft from this*, no *Compare with…* and no *Delete*; `Esc`, *Back to Hub*, `h` and `l` SHALL act as on its render's. The server SHALL serve a bake's record, its image and its thumbnail, made in the library's cache once, and SHALL refuse a number the seed has no edit for and the image of a queued bake, naming the render session that bakes it. A bake whose record cannot be read SHALL be listed damaged, naming its file, and open no view, and SHALL not hide the render's other bakes. Deleting a render SHALL delete its bakes' thumbnails with its own.

A bake is not a render: it holds no sheet of its own and no seed, so its view borrows its render's, and a delete there would take the render and every bake with it ([D4](../../../docs/decisions.md#d4--the-ui-runs-stages-only-as-the-clis-children), [D50](../../../docs/decisions.md#d50--the-last-render-takes-its-approval-and-a-flow-holds-only-its-own-files)). A bake's files are named by the run's own functions, never by the surface ([D3](../../../docs/decisions.md#d3--the-hand-path-stays)).

```
the render      ·  seed 42              the large view of the render
  ↳ edit 1      ·  baked 21:52:40       opens …/42/edit/1
      ↳ edit 2  ·  queued               waits for the next session
```

#### Scenario: the chain lists the bakes in order
- **Key:** `ui:bakes:the-chain-lists-the-bakes-in-order`
- **Layers:** unit
- **WHEN** a render's seed holds a baked edit placed on the render and a queued edit placed on it
- **THEN** the render's detail lists both by number, each with its state and what it was placed on
- **AND** the page draws the second one level in from the first

#### Scenario: a bake's image and thumbnail are served
- **Key:** `ui:bakes:a-bakes-image-and-thumbnail-are-served`
- **Layers:** unit
- **WHEN** a baked edit's image and thumbnail are asked for, the thumbnail twice
- **THEN** the image is served as its bytes, and the thumbnail is a JPEG
- **AND** the second thumbnail is read from `.cache/` without decoding the image

#### Scenario: a bake's record names its edit and what it was placed on
- **Key:** `ui:bakes:a-bakes-record-names-its-edit`
- **Layers:** unit
- **WHEN** the record of an edit placed on another edit's image is asked for
- **THEN** it names the edit, that other edit's number and the state

#### Scenario: a queued bake has no image
- **Key:** `ui:bakes:a-queued-bake-has-no-image`
- **Layers:** unit
- **WHEN** the image of an edit with no image is asked for
- **THEN** the request is refused, naming the render session that bakes it

#### Scenario: a number the seed has no edit for is refused
- **Key:** `ui:bakes:an-unknown-bake-is-refused`
- **Layers:** unit
- **WHEN** a bake's record, image or thumbnail is asked for at a number the seed has no edit for, or one that is no number
- **THEN** the request is refused, naming the number and the render, never failed

#### Scenario: a damaged record marks its own bake
- **Key:** `ui:bakes:a-damaged-record-marks-its-bake`
- **Layers:** unit
- **WHEN** a render's seed holds a baked edit and an edit whose record is not valid JSON
- **THEN** the render's detail lists the first as baked and the second as damaged, naming its file
- **AND** the second's record, image and thumbnail routes are refused, naming the file

#### Scenario: deleting a render deletes its bakes' thumbnails
- **Key:** `ui:bakes:deleting-a-render-deletes-its-bakes-thumbnails`
- **Layers:** unit
- **WHEN** a render with a baked edit whose thumbnail is cached is deleted
- **THEN** the render's thumbnail and the bake's are deleted
- **AND** another collection's thumbnail of the same seed stays

#### Scenario: a bake's view offers no writes
- **Key:** `ui:bakes:a-bakes-view-offers-no-writes`
- **Layers:** unit
- **WHEN** the large view is opened on a bake's address, and on a render's
- **THEN** the bake's offers no *Draft from this*, no *Compare with…* and no *Delete*
- **AND** the render's offers each
