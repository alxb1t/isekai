## REMOVED Requirements

### Requirement: The review surface is started by a verb and refuses before it serves

**Reason:** the surface serves a library, not inputs named at the command line, so there is nothing to resolve
before binding a port; a refusal about one batch or one run is shown on the page, against what it concerns.

**Migration:** `isekai ui` takes no arguments. An input with no sheet shows on the hub at its stage; a draft is
written when Review opens the sheet. The startup refusals' scenarios are carried by *The surface serves one library,
from a verb that takes no arguments* and *Review is a queue of unapproved sheets, and opening one writes its draft*.

### Requirement: The batch is the invocation's arguments and lives only in memory

**Reason:** a batch is a folder in the library, holding its sources and its runs; the set of inputs is a directory
listing, not an argument list.

**Migration:** see *A folder in the library is a batch when it holds `sources/`*. Counts are still read from the run
directory on every request, and still no file records a batch.

## ADDED Requirements

### Requirement: The surface serves one library, from a verb that takes no arguments

The system SHALL serve the browser surface from a subcommand that takes no flow, no input and no runs root, over one
library directory named by `ISEKAI_LIBRARY` and defaulting to `~/isekai`, creating it when absent. It SHALL refuse,
before binding a port, a library inside the repository's working tree that is not under the ignored data root, and a
library it cannot create, naming the remedy.

The library is where the app keeps every batch, so the operator never types a path. Its batches hold copies of
photographs, so the rule that keeps a runs root out of what git tracks holds for the library too
([D18](../../../docs/decisions.md#d18--runs-stay-out-of-what-git-tracks)).

```
~/isekai/                      the library
  <batch>/ sources/ runs/ log.txt
  .staging/                    a dot-folder: never listed
```

#### Scenario: the verb takes no arguments
- **Key:** `ui:library:the-verb-takes-no-arguments`
- **Layers:** unit
- **WHEN** the surface's subcommand is given a flow, an input or a runs root
- **THEN** the invocation is refused at parse time

#### Scenario: an absent library is created
- **Key:** `ui:library:an-absent-library-is-created`
- **Layers:** unit
- **WHEN** the surface starts and the library directory does not exist
- **THEN** it is created before the address is printed

#### Scenario: a library git can reach is refused
- **Key:** `ui:library:a-library-git-can-reach-is-refused`
- **Layers:** unit
- **WHEN** the library resolves inside the working tree and outside the ignored data root
- **THEN** the surface refuses before binding a port
- **AND** the message names the variable that moves it

### Requirement: A folder in the library is a batch when it holds `sources/`

The system SHALL list as a batch every folder in the library that holds `sources/`, SHALL list any other folder as
not a batch and open none of it, and SHALL list no dot-folder. Each batch's row SHALL carry its name, its source
count, for each tracked flow present the counts approved and rendered out of the sources that have that flow, the
count of sources with no flow, and the time and kind of the newest file written in it. Batches SHALL be ordered by
that time, newest first, and folders that are not batches after them.

A folder is a batch by its layout alone, so no marker file can disagree with what is on disk, and the row is a
listing read on every request. A folder that is not a batch is shown rather than hidden so the screen matches the
folder, and nothing in the app writes into it.

#### Scenario: a folder with `sources/` is a batch
- **Key:** `ui:batch-folder:a-folder-with-sources-is-a-batch`
- **Layers:** unit
- **WHEN** the library holds a folder with `sources/` and one without
- **THEN** the first is listed as a batch
- **AND** the second is listed as not a batch, and cannot be opened

#### Scenario: a dot-folder is not listed
- **Key:** `ui:batch-folder:a-dot-folder-is-not-listed`
- **Layers:** unit
- **WHEN** the library holds a folder whose name starts with a dot
- **THEN** it is not listed at all

#### Scenario: a flow's counts are of the sources that have it
- **Key:** `ui:batch-folder:a-flows-counts-are-of-its-sources`
- **Layers:** unit
- **WHEN** a batch's sources have different sets of flows
- **THEN** each flow's approved and rendered counts are out of the sources whose runs hold that flow
- **AND** the sources with no flow are counted apart

#### Scenario: batches are ordered by their newest file
- **Key:** `ui:batch-folder:batches-are-ordered-by-their-newest-file`
- **Layers:** unit
- **WHEN** the library holds batches written at different times
- **THEN** they are listed newest first, by the newest file written in each

#### Scenario: no file records a batch
- **Key:** `ui:batch-folder:no-file-records-a-batch`
- **Layers:** unit
- **WHEN** the surface lists the library and opens a batch
- **THEN** no file describing a batch is created anywhere in the library

### Requirement: Every screen has a URL naming its batch and its run

The system SHALL give Home, a batch's hub and a review of a source in a flow each its own URL, SHALL name the batch
in every URL inside one, and SHALL name a run by the twelve-character digest its identifier begins with. It SHALL
answer any of them on a fresh load, and SHALL refuse one naming a batch or a run the library does not hold, naming
the way back.

A reload, a second tab or a bookmark then lands where it was, never on whatever the server last held open. A run's
short name is a sanitised filename and can repeat; its digest cannot.

```
/                                  Home
/b/<batch>/hub                     the hub
/b/<batch>/review/<digest>/<flow>  Review
```

#### Scenario: a reload lands on the same screen
- **Key:** `ui:routes:a-reload-lands-on-the-same-screen`
- **Layers:** e2e
- **WHEN** a hub or a review is reloaded
- **THEN** the same batch, source and flow are shown

#### Scenario: a run is named by its digest
- **Key:** `ui:routes:a-run-is-named-by-its-digest`
- **Layers:** unit
- **WHEN** a review URL names a run
- **THEN** the run is the one whose identifier begins with that digest

#### Scenario: an unknown batch is refused with the way back
- **Key:** `ui:routes:an-unknown-batch-is-refused`
- **Layers:** e2e
- **WHEN** a URL names a batch the library does not hold
- **THEN** the page refuses, naming the batch
- **AND** it offers the way back to Home

### Requirement: The hub shows each source's stage in each tracked flow, read from the run directory

The system SHALL show a batch's hub as a grid of its sources by its tracked flows, each cell carrying the stage read
from that run's directory — no flow, assigned, tagged, sheet, draft, approved or rendered — and SHALL ignore a flow
directory the build does not track. A cell whose run file cannot be read SHALL show that it is unreadable, with the
refusal the pipeline raised, and the rest of the grid SHALL still be shown. The hub SHALL write nothing.

A stage is a directory listing, the rule every stage already follows, so the grid cannot drift from the disk. A run
moved in from elsewhere may hold a retired flow, or a file in a format this build does not know; the batch still
opens, and the one cell says why it cannot be read.

#### Scenario: a cell's stage comes from its run's directory
- **Key:** `ui:hub:a-cells-stage-comes-from-its-run`
- **Layers:** unit
- **WHEN** a run holds a flow's approved sheet and no render
- **THEN** that cell's stage is approved

#### Scenario: an untracked flow's directory is ignored
- **Key:** `ui:hub:an-untracked-flow-is-ignored`
- **Layers:** unit
- **WHEN** a run holds a directory for a flow the build does not track
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
- **WHEN** a batch's hub is read
- **THEN** no file in the batch is created, changed or removed

### Requirement: Review is a queue of unapproved sheets, and opening one writes its draft

The system SHALL open Review from the hub on the unapproved sheets of the first flow that has any, in the hub's
order, SHALL move to the next sheet in that queue on approval, and SHALL return to the hub after the last. Opening a
sheet that has no draft SHALL write one through the review stage's own function, and opening it again SHALL write
no second draft. A failure after approval SHALL be shown in the approve bar, never dropped.

The queue is the batch, one flow at a time, so approving is the only step between sheets. The draft is written where
review always writes it, by the function that owns its shape.

#### Scenario: approve moves to the next sheet in the flow
- **Key:** `ui:queue:approve-moves-to-the-next-sheet`
- **Layers:** e2e
- **WHEN** a sheet is approved and the flow has another unapproved sheet
- **THEN** Review opens that sheet

#### Scenario: after the last sheet the hub opens
- **Key:** `ui:queue:after-the-last-sheet-the-hub-opens`
- **Layers:** e2e
- **WHEN** the last unapproved sheet in the queue is approved
- **THEN** the hub opens

#### Scenario: opening a sheet with no draft writes one
- **Key:** `ui:queue:opening-a-sheet-writes-its-draft`
- **Layers:** unit
- **WHEN** Review opens a sheet whose flow has a sheet and no draft
- **THEN** a draft is written through the review stage
- **AND** opening it again writes no second draft

#### Scenario: a failure after approval is shown
- **Key:** `ui:queue:a-failure-after-approval-is-shown`
- **Layers:** e2e
- **WHEN** an approval succeeds and reading the next state fails
- **THEN** the approve bar shows the refusal

### Requirement: The page's save state is true to the requests in flight, and a pending edit is sent on leaving

The system SHALL report a draft as saving exactly while a save it started is unanswered, whatever order saves and
input switches answer in, and SHALL send a pending edit when the page leaves the sheet — to another sheet, another
screen, or by closing — by a request the browser keeps alive past the page.

The saved receipt is the only thing on the page that speaks about saving, so a counter one stale answer can drive
below zero silences it for the rest of the input. An edit typed inside the debounce is the operator's work, and
closing the tab is an ordinary way to leave.

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

## MODIFIED Requirements

### Requirement: The surface answers only requests addressed to the address it bound

The system SHALL refuse a request whose `Host` header names an address other than the loopback address
and port the surface bound, SHALL refuse a request whose `Origin` header names a different origin, and SHALL refuse
a request without `Origin` unless its `Sec-Fetch-Site` header is `same-origin` or `none`, or it carries no
`Sec-Fetch-Site` either. The refusal SHALL NOT depend on the browser honouring any policy the surface states.

An unauthenticated API on a loopback port is reachable by any page the operator's browser happens to
load: DNS rebinding resolves an attacker's hostname to `127.0.0.1` and the browser then sends requests
the surface would otherwise answer, including the one that returns a photograph. Checking the header the
browser is obliged to send is what makes the address, rather than the network, the boundary.

A browser marks every request with `Sec-Fetch-Site`, so a request from another site that omits `Origin` — an image
tag probing for a photograph — is still refused. A client that is not a browser sends neither header, and is
answered.

#### Scenario: a request addressed to the bound address is answered
- **Key:** `ui:address:a-request-to-the-bound-address-is-answered`
- **Layers:** unit
- **WHEN** a request carries the `Host` the surface bound
- **THEN** it is answered normally

#### Scenario: a request carrying another host is refused
- **Key:** `ui:address:another-host-is-refused`
- **Layers:** unit
- **WHEN** a request carries a `Host` naming any other address
- **THEN** it is refused
- **AND** no artifact is read and none is written

#### Scenario: a write carrying another page's origin is refused
- **Key:** `ui:address:another-origin-is-refused`
- **Layers:** unit
- **WHEN** a state-changing request carries an `Origin` naming a different origin
- **THEN** it is refused

#### Scenario: every loopback spelling of the bound port is answered
- **Key:** `ui:address:every-loopback-spelling-is-answered`
- **Layers:** unit
- **WHEN** a request carries a `Host` that is a different spelling of the same loopback address and port
- **THEN** it is answered normally

#### Scenario: a cross-site request without an origin is refused
- **Key:** `ui:address:a-cross-site-request-without-origin-is-refused`
- **Layers:** unit
- **WHEN** a request carries no `Origin` and a `Sec-Fetch-Site` of `cross-site`
- **THEN** it is refused
- **AND** no photograph is read

### Requirement: A missing caption is shown with the command that writes it

The system SHALL, when an input's flow holds no caption, show in the source pane that there is none and
the command that writes it, naming the flow, the run and the runs root. It SHALL NOT refuse to open the surface for
the absence.

**The prose is the one artifact a skipped verb leaves missing on a page under review.** The tag lists keep
their silence: a list is missing because a tagger failed, because the run predates it, or because the flow
declares no tagger. Skipping `tag` never reaches review, because the sheet refuses without a tag list the
flow declares.

The caption is now its own verb and nothing downstream needs it, so an input can reach review having never
been read. A blank pane cannot be told from a photograph with nothing to say, and the one-verb design kept
the caption bundled for exactly that reason; naming the command keeps the reason without the bundle.

The server builds the command, as it builds every other command a refusal prints, and it names the run and its
runs root so it works when pasted: a batch's runs root in the library is never the default.

#### Scenario: an input with no caption names the command that writes it
- **Key:** `ui:source:a-missing-caption-names-its-command`
- **Layers:** unit
- **WHEN** an input whose flow holds no caption is opened
- **THEN** the payload carries no prose and the command that writes it, naming the flow, the run and the runs root
- **AND** the surface serves the input without a refusal
