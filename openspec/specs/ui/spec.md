# Capability: `ui`

## Purpose

The browser surface for stage ③: a local server started by a verb, which establishes a batch of inputs
for one flow, refuses everything it can refuse before it prints a URL, and serves a page on which a
draft sheet is corrected against the vocabulary and approved — never constructing an artifact itself.

## Requirements

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

#### Scenario: a stale lower draft does not re-open an approved input
- **Key:** `ui:approval:a-stale-lower-draft-does-not-reopen`
- **Layers:** unit
- **WHEN** the surface serves an input whose flow has an approved artifact and a draft numbered below it
- **THEN** the sheet it shows is the approved artifact's
- **AND** the input is presented as not editable, naming no draft

#### Scenario: an update that overlaps an approval is refused
- **Key:** `ui:approval:an-update-overlapping-an-approval-is-refused`
- **Layers:** unit
- **WHEN** a draft update is in flight while the same input is approved
- **THEN** the update is refused once the approval has written
- **AND** the approved artifact is the one the approval wrote

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

### Requirement: A draft update states the version of the draft it replaces

The system SHALL refuse a draft update, or an approval, whose stated precondition does not match the draft on
disk, and SHALL accept an update that states no precondition.

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

#### Scenario: overlapping updates cannot both commit
- **Key:** `ui:draft-update:overlapping-updates-cannot-both-commit`
- **Layers:** unit
- **WHEN** two draft updates stating the same precondition are in flight at once
- **THEN** one is accepted and the other is refused
- **AND** the draft on disk is the accepted update's

#### Scenario: an approval against a stale draft is refused
- **Key:** `ui:draft-update:a-stale-approval-is-refused`
- **Layers:** unit
- **WHEN** an approval states a precondition that does not match the draft on disk
- **THEN** it is refused
- **AND** nothing is approved

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

### Requirement: A damaged run file or a malformed draft update is refused, never failed

The system SHALL answer a request that reads a run file lacking a key it needs, or holding one in the wrong shape,
with a refusal naming the file and its fix: the command that rewrites it, naming the runs root the surface serves
when that is not the default, or -- for an approved sheet, which no command rewrites -- the file to restore. It SHALL
refuse a draft update whose fields are not an object of lists of strings, naming the field, and SHALL NOT store a value
it did not accept. It SHALL NOT answer either with a server error.

The stages already refuse the same damage by name. A server error names nothing and offers no remedy, and a string
saved as its letters corrupts a draft without a word.

#### Scenario: a damaged file is refused by name
- **Key:** `ui:damage:a-damaged-file-is-refused-by-name`
- **Layers:** unit
- **WHEN** a draft, an approved sheet, a caption or a tag list the surface reads lacks a key it needs or holds it in
  the wrong shape
- **THEN** the request is refused naming the file and the command that rewrites it under the surface's runs root, or
  for an approved sheet the file to restore
- **AND** the surface keeps serving

#### Scenario: a malformed draft update is refused naming the field
- **Key:** `ui:damage:a-malformed-update-is-refused-naming-the-field`
- **Layers:** unit
- **WHEN** a draft update sends a field whose value is not a list of strings
- **THEN** the update is refused naming the field
- **AND** the draft on disk is unchanged

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
count, for each flow the surface offers that is present the counts approved and rendered out of the sources that have
that flow, the count of sources with no flow, and the time and kind of the newest file written in it. Batches SHALL be
ordered by that time, newest first, and folders that are not batches after them.

A folder is a batch by its layout alone, so no marker file can disagree with what is on disk, and the row is a
listing read on every request. A folder that is not a batch is shown rather than hidden so the screen matches the
folder, and nothing in the app writes into it. The flows the surface offers are named in its configuration; a flow
approved from another's sheet stays the CLI's.

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

#### Scenario: a flow the surface does not offer has no count
- **Key:** `ui:batch-folder:an-unoffered-flow-has-no-count`
- **Layers:** unit
- **WHEN** a batch's runs hold a tracked flow the configuration does not offer
- **THEN** its row carries no count for that flow

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

### Requirement: The hub shows each source's stage in each offered flow, and a tick assigns it

The system SHALL show a batch's hub as a grid of its sources by the flows the surface offers, each cell carrying the
stage read from that run's directory — no flow, assigned, tagged, sheet, draft, approved or rendered — and SHALL
ignore any other flow's directory. A cell whose run file cannot be read SHALL show that it is unreadable, with the
refusal the pipeline raised, and the rest of the grid SHALL still be shown. Reading the hub SHALL write nothing; a
tick SHALL write only through the assigning verb, and an untick only while the cell is assigned. A source imported
as it is, still carrying metadata, SHALL be marked on its row.

A stage is a directory listing, the rule every stage already follows, so the grid cannot drift from the disk, and a
tick survives a reload. The mark is read from the source itself, so no file records it.

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
- **WHEN** a batch's hub is read
- **THEN** no file in the batch is created, changed or removed

#### Scenario: a tick assigns the flow
- **Key:** `ui:hub:a-tick-assigns-the-flow`
- **Layers:** e2e
- **WHEN** an unassigned cell is ticked
- **THEN** the cell reads assigned
- **AND** it still reads assigned after a reload

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

### Requirement: Sources are chosen in the file dialog, and each shows its own upload

The system SHALL take sources through the browser's file dialog, sending each file in its own request, and SHALL show
for each its upload's progress, then its reading, then whether it is ready, converted, refused or not cleaned, with
the reason, and a preview of each file read. Import SHALL stay disabled, with its reason, until every chosen file is
read, and SHALL commit only the ready files and those the operator chose to import as they are.

Each file's bar answers which one is slow; each reason sits on the file it concerns.

#### Scenario: each file shows its own progress, then its result
- **Key:** `ui:sheet:each-file-shows-its-progress`
- **Layers:** e2e
- **WHEN** files are chosen in the dialog
- **THEN** each tile shows its upload, then its result
- **AND** a refused file names its reason

#### Scenario: import waits for every file to be read
- **Key:** `ui:sheet:import-waits-for-reading`
- **Layers:** e2e
- **WHEN** a chosen file is still being read
- **THEN** Import is disabled, naming how many are read

#### Scenario: an imported batch opens its hub
- **Key:** `ui:sheet:an-import-opens-the-hub`
- **Layers:** e2e
- **WHEN** Import is pressed on a new batch
- **THEN** the batch's hub opens with every source unassigned

#### Scenario: a staged file serves its preview
- **Key:** `ui:sheet:a-staged-file-serves-its-preview`
- **Layers:** unit
- **WHEN** a staged file's preview is asked for
- **THEN** a downscaled JPEG of it is served
- **AND** nothing of it is kept

#### Scenario: the stream reports each file's reading
- **Key:** `ui:sheet:the-stream-reports-each-files-reading`
- **Layers:** unit
- **WHEN** an uploaded file is read
- **THEN** the import's stream reports it waiting, then converting, then its result

#### Scenario: an upload is answered before it is read
- **Key:** `ui:sheet:an-upload-is-answered-before-reading`
- **Layers:** unit
- **WHEN** a file's bytes have all arrived
- **THEN** its request is answered before the file is read
- **AND** the files are read one at a time, in the order their uploads ended

### Requirement: Prepare runs what changed as one job, and refuses before it starts when Ollama does not answer

The system SHALL run Prepare as one job over every assigned cell with no sheet: for each flow, the tagging, reading
and sheet stages, each one invocation of the pipeline's own verb over that flow's cells. Only one job SHALL run at a
time; a job SHALL keep running when its page closes; Stop SHALL interrupt the current stage and start no other;
stopping the surface SHALL interrupt a running job; and a stage that fails having reported nothing SHALL end the job
as failed, naming the batch's log, and start no other. Before any stage starts, the surface SHALL check that the
local model server answers, and SHALL refuse with its message, starting nothing, when it does not.

The pipeline's verb is the one path, so Prepare is exactly what the verbs do. A refusal before the start leaves every
cell assigned, so pressing Prepare again is the whole fix.

#### Scenario: Prepare runs each stage over the assigned cells
- **Key:** `ui:prepare:prepare-runs-the-assigned-cells`
- **Layers:** e2e
- **WHEN** Prepare is pressed with cells assigned
- **THEN** each cell reaches sheet
- **AND** no cell outside the assignment changes

#### Scenario: a second job is refused while one runs
- **Key:** `ui:prepare:one-job-at-a-time`
- **Layers:** unit
- **WHEN** a job is asked for while another runs
- **THEN** it is refused naming the running job

#### Scenario: Prepare refuses when Ollama does not answer
- **Key:** `ui:prepare:refused-when-ollama-does-not-answer`
- **Layers:** unit
- **WHEN** Prepare is asked for and the local model server does not answer
- **THEN** it is refused with the reader's message
- **AND** no stage starts

#### Scenario: Stop interrupts the job
- **Key:** `ui:prepare:stop-interrupts-the-job`
- **Layers:** unit
- **WHEN** Stop is asked for during a stage
- **THEN** that stage is interrupted and no later stage starts
- **AND** cells already at sheet stay at sheet

#### Scenario: a stage that fails before it reports ends the job
- **Key:** `ui:prepare:a-silent-failure-ends-the-job`
- **Layers:** unit
- **WHEN** a stage exits in failure having reported no item
- **THEN** the job ends as failed, naming the batch's log
- **AND** no later stage starts

### Requirement: The page is told of a job as it runs

The system SHALL serve an event stream that, on every connection, sends a snapshot of the job slot and, when a batch
is named, that batch's hub, and then sends each change as the job's stages report it.

A reload or a second tab gets the whole truth at once; a job's progress reaches the page as the verbs report it.

#### Scenario: a connection starts with a snapshot
- **Key:** `ui:events:a-connection-starts-with-a-snapshot`
- **Layers:** unit
- **WHEN** the stream is opened for a batch
- **THEN** its first event carries the job slot and that batch's hub

#### Scenario: a stage's report reaches the stream
- **Key:** `ui:events:a-stages-report-reaches-the-stream`
- **Layers:** unit
- **WHEN** a running stage reports an item done
- **THEN** the stream sends that cell's new stage

### Requirement: Render is confirmed in a dialog that quotes what renders, its limit and its price at most

The system SHALL open, for a batch, a dialog listing per offered flow the images that will render and what is left
out, with the reason, the session's estimate and limit, and its price at most — the limit at the hourly maximum
`gpunit.toml` names, with the volume at its configured rate. Its confirmation SHALL be the only act that rents; the
dialog SHALL hold no URL. The confirmation SHALL carry the limit and the number of images the dialog showed, and SHALL
be refused, starting nothing, when the batch's quote taken again has a longer limit or another number of images.
Render SHALL be disabled, with its reason, when nothing is short of its count, when a job runs, when a pod may still
be billing, and when no RunPod key is in the surface's environment.

The quote is what the operator agrees to; gpunit refuses a card above the hourly maximum, so the price is a bound and
not a guess. A reload never reopens a confirmation that spends, and an approval made while the dialog is open never
renders what the operator did not see, even where the limit already sits at its floor or its cap.

#### Scenario: the dialog lists what renders per flow
- **Key:** `ui:render:the-dialog-lists-what-renders`
- **Layers:** unit
- **WHEN** a batch's quote is asked for with approvals short of their count in two flows
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
- **WHEN** every approval in a batch already has its count of images
- **THEN** Render is disabled, naming why

#### Scenario: the confirmation starts the render
- **Key:** `ui:render:the-confirmation-starts-the-render`
- **Layers:** e2e
- **WHEN** the dialog's Render is confirmed
- **THEN** the session view opens at `/session`

#### Scenario: a quote that has grown is refused
- **Key:** `ui:render:a-grown-quote-is-refused`
- **Layers:** unit
- **WHEN** Render is confirmed with a shorter limit, or fewer images, than the batch's quote now gives
- **THEN** the confirmation is refused, naming that the quote changed
- **AND** no job starts

### Requirement: The render job opens the volume, renders, and closes the volume unless kept

The system SHALL run a render as one job: the volume window opened or extended, then the rendering verb with the
session's limit and its progress, then the window closed unless the operator kept it open. A lost answer from the
window's opening SHALL render nothing and raise the volume alert; a failed close SHALL raise it too. A job whose verb
cannot be started SHALL end failed, naming the batch's log, and still close the window. Stop SHALL interrupt the
rendering verb, which tears its pod down. The surface stopping SHALL do the same, and SHALL wait for the pod's
teardown and the window's close before it exits, for at most the teardown's estimate and one volume verb, saying so
on its terminal as the wait begins; a wait that runs out with the window not closed SHALL name the command that
closes it. An interrupt at the surface's terminal SHALL reach no child of the job.

The volume is the job's to open and to close, so no step depends on the operator remembering one, and a surface that
exits mid-render leaves no window billing that was not kept. The wait is bounded so a hung verb cannot hold the
surface forever; a stop that says nothing looks hung, and the kill it invites is the one exit that leaves a window
open.

#### Scenario: a render job opens, renders and closes
- **Key:** `ui:render-job:opens-renders-and-closes`
- **Layers:** unit
- **WHEN** a render job runs to its end with keep open unticked
- **THEN** the window is opened, the verb runs with the limit, and the window is closed, in that order

#### Scenario: a lost window opening renders nothing
- **Key:** `ui:render-job:a-lost-opening-renders-nothing`
- **Layers:** unit
- **WHEN** opening the window answers that the create's answer was lost
- **THEN** the rendering verb does not run
- **AND** the volume alert is raised

#### Scenario: a surface stopped mid-render still closes the window
- **Key:** `ui:render-job:a-stopped-surface-closes-the-window`
- **Layers:** unit
- **WHEN** the surface stops while a render job runs with keep open unticked
- **THEN** the window is closed after the pod's teardown, before the surface exits
- **AND** no gpunit verb shares the terminal's interrupt
- **AND** the surface says it waits, naming how long

#### Scenario: a stop that outlasts its wait names the fix
- **Key:** `ui:render-job:an-outlasted-stop-names-the-fix`
- **Layers:** unit
- **WHEN** the surface stops mid-render and the pod's teardown outlasts the wait
- **THEN** the surface names the command that closes the window

#### Scenario: a verb that cannot start fails the job
- **Key:** `ui:render-job:a-verb-that-cannot-start-fails-the-job`
- **Layers:** unit
- **WHEN** the rendering verb cannot be started after the window opens
- **THEN** the job ends failed, naming the batch's log
- **AND** the window is closed

### Requirement: Billing state is read from gpunit's own records

The system SHALL show a pod as possibly billing when gpunit holds a pod record or a pending create while no session
runs, SHALL ask gpunit for its status only on start, every half minute while a session runs or an alert is open, and
on Check again, and SHALL clear an alert only when gpunit confirms the pod or volume gone. It SHALL show an open
volume as a quiet item until the end gpunit recorded for its window, and as the alert band after it.

gpunit already records what it created; reading those records adds no state to disagree with them. Idle, the surface
reaches nothing.

#### Scenario: a pod record without a session is an alert
- **Key:** `ui:billing:a-pod-record-is-an-alert`
- **Layers:** unit
- **WHEN** gpunit holds a pod record and no session runs
- **THEN** the pod alert is shown
- **AND** Render is disabled

#### Scenario: an alert clears only on gpunit's word
- **Key:** `ui:billing:an-alert-clears-on-evidence`
- **Layers:** unit
- **WHEN** Check again is asked for and gpunit still reports the pod
- **THEN** the alert stays

#### Scenario: a volume past its window takes the band
- **Key:** `ui:billing:a-volume-past-its-window-takes-the-band`
- **Layers:** unit
- **WHEN** gpunit's window record ends in the past and the volume is still recorded
- **THEN** the alert band is shown in place of the quiet item

### Requirement: The Renders view shows each source's images by flow and version

The system SHALL show a batch's images as a grid of sources by offered flows, each cell's approval versions newest
first with their images, and open an image's large view, with the sheet it was rendered from, from any of them. It
SHALL mark an approval it cannot read as damaged, naming the file, and show every other image; and SHALL refuse an
address whose version is not `v` and ASCII digits. It SHALL serve each image's thumbnail from a cache in the library's
`.cache/`, made on first request and named by the image's own bytes.

The images come back to where the sheets were decided; a cache the library can lose costs only its rebuild. Two
batches can hold one source rendered at one seed, so only the bytes say which image a thumbnail shows. One damaged
file costs only its own version, never the batch's page.

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
- **WHEN** two batches hold different images of one source, flow, version and seed
- **THEN** each image's thumbnail is made from that image

#### Scenario: the large view shows its sheet
- **Key:** `ui:renders:the-large-view-shows-its-sheet`
- **Layers:** e2e
- **WHEN** an image is opened from the grid
- **THEN** its large view shows the approval it was rendered from
