## MODIFIED Requirements

### Requirement: The page's save state is true to the requests in flight, and a pending edit is sent on leaving

The system SHALL report a draft as saving exactly while a save it started is unanswered, whatever order saves and
input switches answer in, and SHALL send a pending edit when the page leaves the sheet — to another sheet, another
screen, or by closing — by a request the browser keeps alive past the page. A save SHALL wait for the sheet's save in
flight and state the draft it wrote, and a page closing while an edit waits behind a save in flight SHALL ask before
it goes. An approval SHALL wait for a save in flight, and state the draft that save wrote.

The saved receipt is the only thing on the page that speaks about saving, so a counter one stale answer can drive
below zero silences it for the rest of the input. An edit typed inside the debounce is the operator's work, and
closing the tab is an ordinary way to leave. An edit or an approval pressed inside a save's round trip is the
operator's own, not another tab's, and a closing page never reads the receipt it would have to state. A save waiting
behind another carries the whole draft, so a later edit replaces its payload instead of queueing a second request, and
a failed save leaves the draft pending only when no later save of the sheet waits. Of two reads of one sheet in
flight, only the newest SHALL land, so an older read answering late never replaces the operator's edits.

#### Scenario: a stale save cannot clear the saving state
- **Key:** `ui:save:a-stale-save-cannot-clear-saving`
- **Layers:** unit
- **WHEN** an input switch answers before the save it interrupted
- **THEN** the saving state clears only when that save answers
- **AND** the saved receipt returns

#### Scenario: a pending edit is sent on leaving
- **Key:** `ui:save:a-pending-edit-is-sent-on-leaving`
- **Layers:** unit
- **WHEN** the page leaves a sheet inside the debounce
- **THEN** the pending edit is sent with a request kept alive past the page
- **AND** a page closing while an edit waits behind an unanswered save asks before it goes

#### Scenario: an approval waits for a save in flight
- **Key:** `ui:save:an-approval-waits-for-a-save-in-flight`
- **Layers:** unit
- **WHEN** Approve is pressed while a save is unanswered
- **THEN** the approval is sent once that save answers, stating the draft it wrote

#### Scenario: edits inside one slow save are sent as one request
- **Key:** `ui:save:edits-inside-a-slow-save-are-sent-as-one-request`
- **Layers:** unit
- **WHEN** several edits each pause past the debounce while one save is unanswered
- **THEN** one further save is sent once it answers, holding every edit

#### Scenario: a failed save leaves nothing to send again
- **Key:** `ui:save:a-failed-save-leaves-nothing-to-send-again`
- **Layers:** unit
- **WHEN** a save fails while a later save of the sheet waits behind it
- **THEN** the later save holds every edit
- **AND** nothing is sent again once it answers

#### Scenario: a lone failed save is sent again
- **Key:** `ui:save:a-lone-failed-save-is-sent-again`
- **Layers:** unit
- **WHEN** a save fails and no later save of the sheet waits behind it
- **THEN** the edit is pending again
- **AND** the next flush sends it, holding that edit

#### Scenario: a burst of edits is one save
- **Key:** `ui:save:a-burst-of-edits-is-one-save`
- **Layers:** unit
- **WHEN** edits are typed less than the debounce apart
- **THEN** nothing is sent until the debounce has passed since the last
- **AND** one save then holds every edit

#### Scenario: the newest read of a sheet is the one that lands
- **Key:** `ui:save:the-newest-read-of-a-sheet-is-the-one-that-lands`
- **Layers:** unit
- **WHEN** two reads of one sheet are in flight and the older answers first
- **THEN** the sheet stays loading until the newest read answers
- **AND** an edit made after that is saved with the edit in it

#### Scenario: an approval waits for a save held at the network
- **Key:** `ui:save:an-approval-waits-for-a-save-held-at-the-network`
- **Layers:** e2e
- **WHEN** Approve is pressed while the draft's save is held at the network
- **THEN** no approval is sent until the save answers
- **AND** the approval then holds the edit that save wrote

#### Scenario: a refused save is sent again by the next approval
- **Key:** `ui:save:a-refused-save-is-sent-again-by-the-next-approval`
- **Layers:** e2e
- **WHEN** the draft's only save is refused and Approve is pressed
- **THEN** the edit is sent again
- **AND** the approval then holds it

#### Scenario: an edit is undone and redone
- **Key:** `ui:save:an-edit-is-undone-and-redone`
- **Layers:** unit
- **WHEN** a tag is added in one field, a tag is removed in another, and the operator undoes twice and redoes once
- **THEN** each undo and each redo is saved as an edit, the draft holding the removal taken back, then the addition taken back, then the addition again
- **AND** an undo or a redo with nothing to take back, as after the sheet is opened again, changes and sends nothing
