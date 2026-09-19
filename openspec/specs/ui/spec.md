# Capability: `ui`

## Purpose

The browser surface for stage ③: a local server started by a verb, which establishes a batch of inputs
for one flow, refuses everything it can refuse before it prints a URL, and serves a page on which a
draft sheet is corrected against the vocabulary and approved — never constructing an artifact itself.

## Requirements

### Requirement: The review surface is started by a verb and refuses before it serves

The system SHALL expose the review surface through a subcommand of the pipeline entry point, SHALL
resolve the flow, every named input, a draft for each, each photograph's dimensions, the vocabulary and
the built bundle **before** binding a port, and SHALL print the surface's address only once all of them
have succeeded. It SHALL report every failure in that batch together rather than stopping at the first.

A refusal the operator cannot read is a refusal that did not happen. The terminal is where the operator
already is when they start the surface, and where a `Refusal` can name a command and a path without a
designed home to put it in; the browser has neither until a refusal surface exists. Resolving
everything first is also what makes a whole page state unnecessary — the design carries no *this input
is not ready* state, because no reachable path produces one. Reporting together matters at batch size:
ten photographs with two missing sheets must name both and start nothing, rather than making the
operator discover them one restart at a time.

#### Scenario: the surface refuses a flow this build does not track
- **Key:** `ui:startup:untracked-flow-is-refused`
- **Layers:** unit
- **WHEN** the review surface is asked for a flow that is not tracked
- **THEN** the invocation is refused before any port is bound
- **AND** the message lists the flows that are tracked

#### Scenario: an input with no sheet to review is refused by name
- **Key:** `ui:startup:input-without-a-sheet-is-refused`
- **Layers:** unit
- **WHEN** the review surface is asked for an input that has no sheet for the flow
- **THEN** the invocation is refused before any port is bound
- **AND** the message names the input and an action that this build can perform

#### Scenario: every startup failure in the batch is reported together
- **Key:** `ui:startup:refusals-are-reported-together`
- **Layers:** unit
- **WHEN** more than one input in the batch cannot be prepared
- **THEN** every one of them is named in the refusal
- **AND** no address is printed and no port is bound

#### Scenario: opening the surface takes a draft where none exists
- **Key:** `ui:startup:a-draft-is-opened-for-each-input`
- **Layers:** unit
- **WHEN** the review surface is started for an input whose flow has a sheet and no draft
- **THEN** a draft is written for that input before the address is printed
- **AND** starting the surface again for the same input writes no second draft

### Requirement: The batch is the invocation's arguments and lives only in memory

The system SHALL treat the set of inputs under review as the argument list of the invocation that
started the surface, SHALL NOT write any artifact describing that set, and SHALL derive how many of
them are approved by reading the run directory rather than from anything it holds in memory.

Nothing on disk says that ten photographs belong together: a run is one input and the layout has no
batch object, so recording one would add an artifact to a layout whose own rules make a shape change a
hand migration. Holding it in memory costs a retyped command after a restart and loses no work, because
the sheets are independent of it. Reading the approved count from disk rather than from memory is what
keeps the surface truthful when something is approved by the verb while the surface is running.

#### Scenario: the batch is not written to disk
- **Key:** `ui:batch:no-batch-artifact-is-written`
- **Layers:** unit
- **WHEN** the review surface establishes a batch of inputs
- **THEN** no file describing that batch is created anywhere under the run root

#### Scenario: the approved count is read from the directory
- **Key:** `ui:batch:approved-count-comes-from-disk`
- **Layers:** unit
- **WHEN** an input's flow gains an approved artifact after the surface has started
- **THEN** the surface reports that input as approved
- **AND** the count it reports for the batch reflects the directory

### Requirement: The server never constructs an artifact body or an artifact filename

The system SHALL confine the construction of artifact envelopes and artifact filenames to the pipeline
functions that own them, and the review surface SHALL pass field values to those functions rather than
writing into a run directory itself.

Both front ends now call the stage functions in process, so the surface is no longer prevented from
writing its own artifact by the shape of the system — it is prevented by this rule. The consequence of
losing it is specific and silent: an approved artifact written around the one function that validates
would carry a tag outside the vocabulary into a prompt, and the first symptom would be a render that
looks wrong, minutes and money later. The same claim held elsewhere in this repository by habit alone
was false six times before two releases closed it.

#### Scenario: the surface's modules name no artifact-writing primitive
- **Key:** `ui:invariant:server-never-names-an-artifact`
- **Layers:** unit
- **WHEN** the review surface's own modules are read
- **THEN** none of them names the envelope, artifact-name or JSON-writing primitives
- **AND** every write reaching a run directory has passed through a pipeline function

### Requirement: Tag suggestions are answered by the pipeline's own search

The system SHALL answer a tag query from the surface by returning matches from the vocabulary the
pipeline itself searches, ranked as the pipeline ranks them, with each match's post count, and SHALL
NOT transfer the whole vocabulary to the client for ranking there.

The post count is the reason this surface exists at all: it predicts how strongly a tag lands, and an
operator choosing between a tag with a million posts and one with nine hundred is making the decision
the render will act on. Ranking in one place keeps that decision identical however it is reached, and
the whole searchable corpus is 93.5 KiB over 8,106 tags — a query costs about 0.25 ms against a debounce
two orders of magnitude longer, so serving it deletes a quarter-megabyte transfer and a second copy of
the ranking rule and buys nothing but correctness.

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

### Requirement: An approved input is read-only on the surface

The system SHALL present an input whose flow already has an approved artifact as not editable, SHALL
refuse a draft update against such an input, and SHALL state on the page that the input is approved and
name the artifact that holds it.

Approval deletes the draft and opening the surface again writes no replacement, because a new version is
an explicit act — so there is nothing on disk for an edit after approval to be written into. A surface
that offered editing anyway would either appear to save and not, or silently spend a version number on
a keystroke, and it has no Save control and no confirmation step with which to attribute that. Naming
the artifact is what keeps the state legible rather than merely closed.

#### Scenario: a draft update against an approved input is refused
- **Key:** `ui:approval:approved-input-refuses-a-draft-update`
- **Layers:** unit
- **WHEN** a draft update is submitted for an input whose flow is already approved
- **THEN** it is refused
- **AND** no file in the run directory is created, changed or removed

#### Scenario: an input approved in an earlier sitting opens read-only
- **Key:** `ui:approval:approved-input-opens-read-only`
- **Layers:** unit
- **WHEN** the surface serves an input whose flow has an approved artifact and no draft
- **THEN** the sheet it shows is the approved artifact's
- **AND** the input is presented as not editable

### Requirement: The browser bundle is generated, never committed, and its toolchain refuses by name

The system SHALL build the surface's browser bundle from tracked source when it is absent, SHALL NOT
track the built bundle or its fetched dependencies in version control, and SHALL refuse with the command
that would resolve it when the toolchain needed to build is unavailable.

A built bundle carries content-hashed filenames, so committing it churns version control on every build
for no reading a human does. The build itself is local and free and may run implicitly; fetching
dependencies is not, because it pulls arbitrary third-party packages, so a verb that did it silently
would be the surprise that every other network-touching default in this system avoids. The refusal names
the command for the same reason every refusal here does — a missing toolchain is fixable in one line by
whoever hit it.

#### Scenario: a missing bundle is built before the surface serves
- **Key:** `ui:bundle:a-missing-bundle-is-built`
- **Layers:** unit
- **WHEN** the review surface starts and no built bundle exists
- **THEN** it is built before the address is printed

#### Scenario: missing fetched dependencies refuse rather than fetch
- **Key:** `ui:bundle:missing-dependencies-refuse-by-name`
- **Layers:** unit
- **WHEN** the review surface starts and the bundle's fetched dependencies are absent
- **THEN** the invocation is refused
- **AND** the message names the command that would install them
