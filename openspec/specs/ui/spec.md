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

### Requirement: An approved input is read-only on the surface until it is re-opened

The system SHALL present an input whose flow has an approved artifact and no later draft as not editable,
SHALL refuse a draft update against such an input, and SHALL state on the page that the input is approved
and name the artifact that holds it. Where a draft numbered above the approved artifact's `approved_from`
exists, the system SHALL present the input as **re-opened**: editable, with its approved artifact still
named.

**The previous wording assumed a state the pipeline can produce.** It read *"Approval deletes the draft
and opening the surface again writes no replacement, because a new version is an explicit act — so there
is nothing on disk for an edit after approval to be written into."* The second clause is true and the
inference from it is not: `review --flow F --new-version` is exactly that explicit act, and
`review:copy:second-review-appends` requires it to write a new numbered draft from the approved copy. Two
capabilities described one state and disagreed about it.

**`review` is the one that was right.** `--new-version` exists for this and is older and tested; the
surface is what had no way to show its result. `v0.22.1` closed the disagreement in the other direction
because that fix needed no spec delta, and said so in the refusal it shipped — *"this page keeps showing
the input approved and read-only either way, because the re-opened state is v0.22.2's."* This is that
version.

**Re-opened is a third status, not a second meaning for an existing one.** An input with an approved
artifact and no newer draft is finished and stays read-only; the approved artifact is never edited in
place in either case. What changes is that a deliberately re-opened input stops being reported as
something it is not.

#### Scenario: a draft update against an approved input is refused
- **Key:** `ui:approval:approved-input-refuses-a-draft-update`
- **Layers:** unit
- **WHEN** a draft update is submitted for an input whose flow is approved and holds no later draft
- **THEN** it is refused
- **AND** no file in the run directory is created, changed or removed

#### Scenario: an input approved in an earlier sitting opens read-only
- **Key:** `ui:approval:approved-input-opens-read-only`
- **Layers:** unit
- **WHEN** the surface serves an input whose flow has an approved artifact and no draft
- **THEN** the sheet it shows is the approved artifact's
- **AND** the input is presented as not editable

#### Scenario: an input re-opened with a new version is editable again
- **Key:** `ui:approval:a-re-opened-input-is-editable`
- **Layers:** unit
- **WHEN** the surface serves an input whose flow has an approved artifact and a draft numbered above the
  version that artifact records as its origin
- **THEN** the sheet it shows is the draft's
- **AND** the input is presented as editable
- **AND** a draft update against it is accepted

#### Scenario: a re-opened input is not counted as approved
- **Key:** `ui:approval:a-re-opened-input-is-not-counted-approved`
- **Layers:** unit
- **WHEN** the batch is read while one of its inputs is re-opened
- **THEN** that input's reported status is neither approved nor a plain draft
- **AND** the batch's approved count agrees with what the run directories hold

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

### Requirement: The source pane shows the caption one sentence to a block

The system SHALL render a caption's prose as one block per sentence rather than as paragraphs, and SHALL
derive that division in the browser from the prose it already holds, without a request and without a
second copy of the rule.

The complaint this answers is specific: *"I read the paragraph, go to the sheet, add a tag, come back —
and I have lost where I was reading."* A block boundary at every sentence gives the eye something to
return to, and it costs nothing, because the prose is already in the browser and the surface already
owns one rule for how a caption is divided. Putting the second rule beside the first is what stops the
two drifting; putting it on the server would send prose across a socket to be split and sent back.

Splitting on sentence-ending punctuation is naive against abbreviations and decimals. That is accepted
as a known edge rather than an unknown one: the prose is constrained by briefing to plain description of
a person, and the acceptance looks for it specifically.

#### Scenario: a caption is shown as sentences, not paragraphs
- **Key:** `ui:source:the-caption-is-shown-one-sentence-to-a-block`
- **Layers:** unit
- **WHEN** an input whose caption is a multi-sentence paragraph is opened
- **THEN** each sentence is rendered as its own block
- **AND** the prose's own text is unchanged, with nothing added, dropped or re-ordered

### Requirement: Both tag lists are shown beside the prose, read-only, and neither is editable there

The system SHALL show, beside the caption, the scored list the local tagger produced and the
committable tags the hosted tagger offered, and SHALL make neither list a way to change a sheet.

**The two lists are narrowed differently, and the asymmetry is measured rather than chosen.** The local
tagger is scored against the vocabulary it emits, so every tag it returns is committable by
construction and all of them are shown, with the confidence beside each — a wrong tag sorted below a
right one refutes itself. The hosted tagger free-associates: on the acceptance batch roughly nine in
ten of its tags were outside the vocabulary, could not be committed to any field, and the operator's
verdict was that only the marked ones carried any value. So its list is **filtered to what the
vocabulary carries** before it is shown.

**Filtered on the way to the page, never on the way to disk.** The artifact keeps every tag the model
returned — that is `tagging`'s requirement and it is untouched — because narrowing what is *stored*
would make the record disagree with what the model said, and the reason the artifact exists is to be
able to look behind the sorter. What changes is only which of those tags the surface spends the
operator's attention on.

#### Scenario: the local list is shown whole and the hosted list is shown filtered
- **Key:** `ui:source:both-tag-lists-are-shown-raw-and-read-only`
- **Layers:** unit
- **WHEN** an input whose tag artifacts contain tags outside the flow's vocabulary is opened
- **THEN** every tag the local tagger scored is present in the response the surface renders
- **AND** only the hosted tags the vocabulary contains are present in it
- **AND** no interaction on either list writes to a draft

#### Scenario: filtering the panel does not filter the artifact
- **Key:** `ui:source:the-artifact-keeps-what-the-panel-drops`
- **Layers:** unit
- **WHEN** a hosted tag outside the vocabulary is withheld from the payload
- **THEN** that tag is still present in the stored artifact, unchanged

### Requirement: Vocabulary membership is decided by the server, not by the browser

The system SHALL resolve, for each hosted tag, whether the flow's pinned vocabulary contains it and what
its post count is; SHALL use that to decide which of them reach the page; and SHALL deliver the count
with the input's own payload rather than through a per-tag query.

Membership is what makes the hosted list worth showing at all. Unfiltered it was measured at roughly
one usable tag in ten, and an operator reading nine unusable ones to find the tenth is spending
attention on the busiest pane in the surface. The count travels with each tag that survives, because a
number is what distinguishes a suggestion Danbooru can actually render from one a model merely said.

The tag search endpoint answers a **fragment query** and has no membership form, so deciding this in
the browser would be one round trip per tag. The vocabulary is already resolved at startup and already
held by the process that assembles this payload; the decision costs one dictionary lookup per tag and
no request at all.

#### Scenario: the server decides which hosted tags reach the page, and sends their counts
- **Key:** `ui:source:vocabulary-membership-is-marked-by-the-server`
- **Layers:** unit
- **WHEN** an input with a hosted tag artifact is requested
- **THEN** the payload carries only the tags the vocabulary contains, each with its post count
- **AND** the surface makes no additional request to resolve any of them

### Requirement: A tag artifact that is absent is silent

The system SHALL render the source pane without a tag list when its artifact does not exist, SHALL NOT
refuse to open the surface for the absence, and SHALL NOT display a message explaining it.

One is legitimately missing when the run was captioned before the stage existed, or when a tagger call
failed — and neither is a reason a sheet cannot be reviewed. The tag lists are an aid; a surface that
refuses to open because an aid is missing has confused an aid for an input, and the startup refusals
exist for what review genuinely cannot proceed without: the flow, the run, the draft, the photograph's
dimensions, the vocabulary and the bundle.

No message either. A line explaining an absence the operator caused by not running something is chrome
on the pane they spend the most time reading, and it would appear beside every input whose list is
missing.

#### Scenario: an input with no tag artifacts still opens
- **Key:** `ui:source:an-absent-tag-artifact-is-silent`
- **Layers:** unit
- **WHEN** an input whose run holds no tag artifacts is opened
- **THEN** the surface serves it and the payload reports the lists as absent
- **AND** no refusal is raised and no explanatory message is rendered

### Requirement: The surface can show every candidate tag for every criterion the flow declares

The system SHALL answer, in one response, the tags each field the acting flow declares can be filled with,
SHALL include a field the table holds no tags for as an empty group rather than omitting it, SHALL order the
tags within each group by post count, and SHALL NOT serve the list of tags no criterion can hold.

The measured gap this closes is not ranking and not speed: the operator looks at a photograph, goes to type
a tag, and does not know what Danbooru calls the thing he is looking at. The autocomplete cannot help because
it needs a fragment he already has, and a fragment that matches nothing commits nothing — so the failure is a
dead end rather than a bad tag. Answering in one response is what makes browsing free: the whole table is
tens of kilobytes, a surface that has it can filter without a round trip per keystroke, and a surface that
never opens the reference pays nothing because the response is not on the page's own payload.

Ordering by post count is deliberate and is the design's standing rule rather than a default. A group is a
**filter** and the ordering inside it is the same global count every other tag surface uses, so no second
ranking enters the system — which is the decision a per-field ranking would have forced, and it is deferred
rather than taken quietly. A post-count **cutoff** was measured against the operator's own approved sheets
and refused: any cutoff aggressive enough to shorten the largest group hides tags he actually uses, and the
tags he reaches for are in the tail.

An empty group is present because the alternative is silent. A criterion the vocabulary cannot express — four
tags in total for one of them, none at all for another — is a fact worth showing, and a missing row is
indistinguishable from a criterion nobody has authored yet. The excluded list is withheld for the mirror
reason: it is an assertion about the table, and showing the operator the tags that are never an answer is
the opposite of what he opened the reference for.

#### Scenario: every declared criterion is answered with its candidates
- **Key:** `ui:cheatsheet:every-declared-criterion-is-answered`
- **Layers:** unit
- **WHEN** the candidates are requested for a flow
- **THEN** the response carries one group per field that flow's schema declares
- **AND** it carries no group for a field the flow does not declare

#### Scenario: a criterion with no candidates is present and empty
- **Key:** `ui:cheatsheet:an-empty-group-is-present`
- **Layers:** unit
- **WHEN** the table holds no tags for a declared field
- **THEN** that field is present in the response with an empty group
- **AND** the request is not refused for it

#### Scenario: candidates are ordered by post count
- **Key:** `ui:cheatsheet:candidates-are-ordered-by-post-count`
- **Layers:** unit
- **WHEN** a group carries more than one tag
- **THEN** the tags are ordered by descending post count
- **AND** each tag carries the count the pinned vocabulary records for it

#### Scenario: the excluded list is never served
- **Key:** `ui:cheatsheet:the-excluded-list-is-not-served`
- **Layers:** unit
- **WHEN** the candidates are requested
- **THEN** no tag from the excluded list appears in any group
- **AND** the excluded list is not carried in the response

### Requirement: The surface answers only requests addressed to the address it bound

The system SHALL refuse a request whose `Host` header names an address other than the loopback address
and port the surface bound, and SHALL refuse a state-changing request whose `Origin` header, when
present, names a different origin. The refusal SHALL NOT depend on the browser honouring any policy the
surface states.

An unauthenticated API on a loopback port is reachable by any page the operator's browser happens to
load: DNS rebinding resolves an attacker's hostname to `127.0.0.1` and the browser then sends requests
the surface would otherwise answer, including the one that returns a photograph. Checking the header the
browser is obliged to send is what makes the address, rather than the network, the boundary.

`Origin` is validated only where it is offered, because a client that is not a browser sends none, and
requiring it would refuse every such client to close a hole only browsers can open.

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

### Requirement: A draft update states the version of the draft it replaces

The system SHALL refuse a draft update whose stated precondition does not match the draft on disk, and
SHALL accept an update that states no precondition.

The surface autosaves on a debounce, so two updates can be in flight at once, and the server runs them
in a threadpool — which leaves the order they commit in decided by whichever finishes first rather than
by which keystroke came last. A precondition makes that order observable instead of silent: the loser is
told, rather than the winner's text being replaced by older text and the receipt describing a save that
is not on disk.

An update stating no precondition is accepted because the artifact carries no revision of its own to
state, and a client that cannot read one must still be able to write.

#### Scenario: an update against a stale draft is refused
- **Key:** `ui:draft-update:a-stale-precondition-is-refused`
- **Layers:** unit
- **WHEN** a draft update states a precondition that does not match the draft on disk
- **THEN** it is refused
- **AND** the draft on disk is unchanged

#### Scenario: an update stating no precondition is accepted
- **Key:** `ui:draft-update:no-precondition-is-accepted`
- **Layers:** unit
- **WHEN** a draft update states no precondition
- **THEN** it is accepted

### Requirement: The bundle is rebuilt when anything it is built from has moved

The system SHALL treat a built bundle as stale when any tracked input to the build has changed since it
was written — its source, its entry document, or the build's own configuration and declared dependencies
— and SHALL bound the build so that one that does not finish is stopped and named rather than waited on.

Comparing only the source leaves the build configuration and the dependency manifest uncounted, so a
dependency bump or a config change serves a bundle built from neither. Nothing in the gate can catch it:
the type check compiles source while the surface reads the build.

A fetched dependency tree is not source. It is derived from the manifest that declares it, so watching
the manifest is what detects a change; watching the tree would make every install look like an edit.

#### Scenario: a build config edited after the build makes the bundle stale
- **Key:** `ui:bundle:a-changed-build-input-makes-the-bundle-stale`
- **Layers:** unit
- **WHEN** the build's configuration or its declared dependencies change after the bundle was written
- **THEN** the bundle is rebuilt before the surface serves

#### Scenario: a fetched dependency tree is not an input
- **Key:** `ui:bundle:a-fetched-tree-is-not-an-input`
- **Layers:** unit
- **WHEN** only the fetched dependency tree has changed
- **THEN** the bundle is not rebuilt for that reason alone

#### Scenario: a build that does not finish is stopped and named
- **Key:** `ui:bundle:an-unfinished-build-is-stopped-and-named`
- **Layers:** unit
- **WHEN** the build does not finish within the time the surface allows it
- **THEN** it is stopped
- **AND** the refusal names the build as what did not finish

### Requirement: Each tag the panel offers is shown once

The system SHALL send each hosted tag to the surface at most once, and SHALL send every row the local
tagger scored.

The two lists are not symmetric and must not be made so. The hosted tagger returns free text split on a
separator and can repeat itself; a repeated tag carries nothing, because the count beside it is a
property of the tag rather than of the occurrence. The local tagger emits one row per label with the
score that label was given, so two rows bearing one name would differ in the number that matters and
dropping either would hide a reading.

Narrowing the panel is not narrowing the artifact. What the tagger returned is stored whole, which is the
tagging capability's own rule and is untouched here.

#### Scenario: the hosted panel shows each tag once and the local one shows every row
- **Key:** `ui:source:each-hosted-tag-is-offered-once`
- **Layers:** unit
- **WHEN** the hosted tag artifact repeats a tag and the local artifact holds rows sharing a name
- **THEN** the hosted list the surface renders carries that tag once
- **AND** every row the local tagger scored is present in it
- **AND** both artifacts on disk are unchanged
