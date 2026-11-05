## MODIFIED Requirements

### Requirement: Tag suggestions are answered by the pipeline's own search

The system SHALL answer a tag query from the surface by returning matches from the vocabulary the
pipeline itself searches, ranked as the pipeline ranks them, with each match's post count, and SHALL
NOT transfer the whole vocabulary to the client for ranking there. It SHALL open the list of matches below its input
when the room below, to the foot of the sheet, holds it; else above when the room above, to the sheet's top, holds it;
else on the side with more room. Above, its first match SHALL be nearest the input and its footer on top.

The post count is the reason this surface exists at all: it predicts how strongly a tag lands, and an
operator choosing between a tag with a million posts and one with nine hundred is making the decision
the render will act on. Ranking in one place keeps that decision identical however it is reached, and
the whole searchable corpus is 93.5 KiB over 8,106 tags — a query costs about 0.25 ms against a debounce
two orders of magnitude longer, so serving it deletes a quarter-megabyte transfer and a second copy of
the ranking rule and buys nothing but correctness. A list below an input near the sheet's foot hangs past it; above
it, mirrored, the best match stays next to the input.

#### Scenario: matches come back ranked by post count with their counts
- **Key:** `ui:vocabulary:matches-are-ranked-by-post-count`
- **Layers:** unit
- **WHEN** the surface is queried with a tag fragment
- **THEN** the matches are those the pipeline's own search returns, in its order
- **AND** each match carries the number of posts behind it

#### Scenario: a fragment matching nothing yields nothing to commit
- **Key:** `ui:vocabulary:an-unmatched-fragment-commits-nothing`
- **Layers:** unit
- **WHEN** the surface is queried with a fragment no tag contains
- **THEN** no matches are returned
- **AND** the surface offers nothing that could be committed as a tag

#### Scenario: near the sheet's foot the list opens above its input
- **Key:** `ui:vocabulary:the-list-opens-above-near-the-foot`
- **Layers:** unit
- **WHEN** a tag input's list fits above it and not below it, to the sheet's foot
- **THEN** the list opens above the input, its first match nearest the input and its footer on top
- **AND** with the room below, it opens below, and fitting neither side, it opens on the larger

### Requirement: Render is confirmed in a dialog that quotes what renders, its limit and its price at most

The system SHALL offer Render from a bar on a collection's hub and its Renders view that counts the images short of
their approvals' counts, its collection's and, as `+n in other collections`, every other collection's, and SHALL show no
such bar when no collection is short and no count is refused, nor on the hub while changes wait for Prepare. While a
render runs the bar SHALL show the session's totals and *Session* in place of the count and Render, and name the images
short that the session does not render as waiting for the next session. The bar SHALL be disabled, with its reason, when
a pod may still be billing, when no RunPod key is in the surface's environment, and when an approval's count is refused.
It SHALL open a dialog listing a row per collection short of images, in the Library's order, each ticked, and in each
row per offered flow the photographs that will render and those left out, with the reason, as thumbnails grouped by
flow; unticking a row SHALL quote the rest again; the session's estimate and limit, and its price at most — the limit at
the hourly maximum `gpunit.toml` names, with the volume at its configured rate; an estimate past the ceiling
`gpunit.toml` names SHALL disable the confirmation, saying so. Its confirmation SHALL be the only act that rents; the
dialog SHALL hold no URL, and SHALL close when its page is left, and the confirmation SHALL close it and open the
session drawer over the page. The confirmation SHALL carry the ticked collections, the limit and the number of images
the dialog showed, and SHALL be refused, starting nothing, when the ticked collections' quote taken again has a longer
limit or another number of images. The bar SHALL show the newest offer asked for, whatever order the answers arrive in.

The quote is what the operator agrees to; gpunit refuses a card above the hourly maximum, so the price is a bound and
not a guess. A reload never reopens a confirmation that spends; a changed image total or longer limit requires a fresh
confirmation, even where the limit sits at its floor or cap. An equal-total change of sources or approvals is outside
that comparison. A bar that is absent needs no reason, and one forward action holds the screen's accent; a refused count
keeps the bar, so the refusal is never silent. A photograph is known by sight, so the dialog shows it rather than its
file name.

#### Scenario: the dialog lists what renders per flow
- **Key:** `ui:render:the-dialog-lists-what-renders`
- **Layers:** unit
- **WHEN** a collection's quote is asked for with approvals short of their count in two flows
- **THEN** it lists each flow's images and what is left out, with the reason
- **AND** it carries the estimate, the limit and the price at most

#### Scenario: the dialog shows each photograph as a thumbnail by flow
- **Key:** `ui:render:the-dialog-shows-thumbnails-by-flow`
- **Layers:** unit
- **WHEN** a collection's quote holds photographs to render in a flow and photographs left out
- **THEN** each flow shows its photographs' thumbnails, 15 and then `+n`, each counted only above one image
- **AND** those left out show dimmed, grouped by their reason and their flow

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
