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
and when, naming no file. Where a draft numbered above the approved artifact's `approved_from`
exists, the system SHALL present the input as **re-opened**: editable, its approval still
stated.

`review --flow F --new-version` writes a new numbered draft from the approved copy, and the surface shows that
state as its own rather than as something it is not: re-opened is a third status, and the approved artifact is
never edited in place in either case. The library counts every approval the run directories hold; Review's rail
holds the sheets not yet rendered and the one open, and its footer counts the approved among them.

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
- **WHEN** the collection is read while one of its inputs is re-opened
- **THEN** that input's reported status is neither approved nor a plain draft
- **AND** the collection's approved count agrees with what the run directories hold
- **AND** Review's footer counts the approved among the rail's sheets, the re-opened one included

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
right one refutes itself. The hosted tagger free-associates: on the acceptance collection roughly nine in
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

The system SHALL refuse a draft update, an approval or a discard whose stated precondition does not match the draft
on disk, and SHALL accept an update that states no precondition.

The surface autosaves on a debounce, so two updates can be in flight at once, and the server runs them
in a threadpool — which leaves the order they commit in decided by whichever finishes first rather than
by which keystroke came last. A precondition makes that order observable instead of silent: the loser is
told, rather than the winner's text being replaced by older text and the receipt describing a save that
is not on disk. A discard deletes, so a page deletes only the draft it last read.

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

#### Scenario: a discard against a stale draft is refused
- **Key:** `ui:draft-update:a-stale-discard-is-refused`
- **Layers:** unit
- **WHEN** a discard states a precondition that does not match the draft on disk
- **THEN** it is refused
- **AND** the draft on disk is not deleted

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

The system SHALL, when an input's flow holds no caption, show in the source pane the caption of the flow its
sheet's tags came from, named as that flow's, and else that there is none and the command that writes it, naming
the flow, the run and the runs root. It SHALL NOT refuse to open the surface for
the absence.

**The prose is the one artifact a skipped verb leaves missing on a page under review.** The tag lists keep
their silence: a list is missing because a tagger failed, because the run predates it, or because the flow
declares no tagger. Skipping `tag` never reaches review, because the sheet refuses without a tag list the
flow declares.

The caption is now its own verb and nothing downstream needs it, so an input can reach review having never
been read. A blank pane cannot be told from a photograph with nothing to say, and the one-verb design kept
the caption bundled for exactly that reason; naming the command keeps the reason without the bundle.

The server builds the command, as it builds every other command a refusal prints, and it names the run and its
runs root so it works when pasted: a collection's runs root in the library is never the default.

#### Scenario: an input with no caption names the command that writes it
- **Key:** `ui:source:a-missing-caption-names-its-command`
- **Layers:** unit
- **WHEN** an input whose flow holds no caption is opened
- **THEN** the payload carries no prose and the command that writes it, naming the flow, the run and the runs root
- **AND** the surface serves the input without a refusal

#### Scenario: a sheet filled from another flow's tags shows that flow's caption
- **Key:** `ui:source:a-borrowed-sheet-shows-its-sources-caption`
- **Layers:** unit
- **WHEN** an input is opened whose flow holds no caption and whose sheet names another flow's tags
- **THEN** the payload carries that flow's caption prose and names that flow
- **AND** it carries no command

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

The library is where the app keeps every collection, so the operator never types a path. Its collections hold copies of
photographs, so the rule that keeps a runs root out of what git tracks holds for the library too
([D18](../../../docs/decisions.md#d18--runs-stay-out-of-what-git-tracks)).

```
~/isekai/                      the library
  <collection>/ sources/ runs/ log.txt
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

### Requirement: The page's save state is true to the requests in flight, and a pending edit is sent on leaving

The system SHALL report a draft as saving exactly while a save it started is unanswered, whatever order saves and
input switches answer in, and SHALL send a pending edit when the page leaves the sheet — to another sheet, another
screen, or by closing — by a request the browser keeps alive past the page. A save SHALL wait for the sheet's save in
flight and state the draft it wrote, and a page closing while an edit waits behind a save in flight SHALL ask before
it goes. An approval SHALL wait for a save in flight, and state the draft that save wrote.

The saved receipt is the only thing on the page that speaks about saving, so a counter one stale answer can drive
below zero silences it for the rest of the input. An edit typed inside the debounce is the operator's work, and
closing the tab is an ordinary way to leave. An edit or an approval pressed inside a save's round trip is the
operator's own, not another tab's, and a closing page never reads the receipt it would have to state.

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

### Requirement: The hub shows each source's stage in each offered flow, and a tick assigns it

The system SHALL show a collection's hub as a grid of its sources by the flows the surface offers, each cell carrying
the stage read from that run's directory — no flow, assigned, tagged, sheet, draft, approved or rendered — and SHALL
ignore any other flow's directory. A cell whose run file cannot be read SHALL show that it is unreadable, with the
refusal the pipeline raised, and the rest of the grid SHALL still be shown. Reading the hub SHALL write nothing; a tick
SHALL write only through the assigning verb, and an untick only while the cell is assigned. A source imported as it is,
still carrying metadata, SHALL be marked on its row. Each source SHALL show its name and its thumbnail, and its row
SHALL carry the size read from its own file, with or without a run, which the viewer's title names. A source's thumbnail
and a cell's images SHALL sit at the foot of their cells, level across the row, whatever text stands above them; a
cell's refusal SHALL stand above its images, and `↵ view photo` SHALL take no line of the source's cell. A cell SHALL
name its newest image — the newest version holding images, then its last-written image — and a click or `↵` SHALL follow
the cell's stage: tick while unassigned or assigned, open Review on a sheet or a draft, open the sheet read-only on an
approval with no image, and open the viewer on the newest of the cell's images where it holds any, stepping through
them, `↵` opening an image's large view; a tagged or unreadable cell SHALL do nothing. A cell holding images SHALL show
every one of them, oldest to newest, each marked with its version. A source's cell SHALL be the grid's first column,
reached by `h` and `←`, and `↵` there SHALL open its photograph in the viewer, stepping through the collection's
sources. The hub SHALL keep its focus across a large view, the Back button and a switch of tabs. The header SHALL leave
a 12 px gap between items.

A stage is a directory listing, the rule every stage already follows, so the grid cannot drift from the disk, and a tick
survives a reload. The mark and the size are read from the source itself, so no file records them. An approved cell can
hold an older version's images, so its newest image is named by the server rather than guessed by the page. A row's
pictures share a foot, so a long name, a mark or a refusal moves only the text above them.

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
- **WHEN** a collection's hub is read
- **THEN** no file in the collection is created, changed or removed

#### Scenario: a tick assigns the flow
- **Key:** `ui:hub:a-tick-assigns-the-flow`
- **Layers:** e2e
- **WHEN** an unassigned cell is ticked
- **THEN** the cell reads assigned
- **AND** it still reads assigned after a reload
- **AND** the header keeps a 12 px gap between its items

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

#### Scenario: a source is sized from its file
- **Key:** `ui:hub:a-source-is-sized-from-its-file`
- **Layers:** unit
- **WHEN** the hub is read for a source that has no run
- **THEN** its row carries the width and height of its file

#### Scenario: a cell names its newest image
- **Key:** `ui:hub:a-cell-names-its-newest-image`
- **Layers:** unit
- **WHEN** an approved cell holds images only under an older version
- **THEN** it names that version and its last-written image

#### Scenario: a click follows the cell's stage
- **Key:** `ui:hub:a-click-follows-the-cells-stage`
- **Layers:** unit
- **WHEN** a cell is clicked at each stage
- **THEN** it ticks up to assigned, opens Review on a sheet, a draft or an unrendered approval, and opens an image
- **AND** a tagged or an unreadable cell does nothing

#### Scenario: a rendered cell opens its newest image
- **Key:** `ui:hub:a-rendered-cell-opens-its-newest-image`
- **Layers:** e2e
- **WHEN** a rendered cell is clicked, then `↵` is pressed in the viewer
- **THEN** the viewer opens on its newest image, then that image's large view
- **AND** `Esc` returns to the hub, focused on that cell

#### Scenario: a cell lists its images
- **Key:** `ui:hub:a-cell-lists-its-images`
- **Layers:** unit
- **WHEN** a cell holds images under two versions
- **THEN** the hub carries them oldest to newest, each with its version and seed

#### Scenario: the source cell opens its photograph
- **Key:** `ui:hub:the-source-cell-opens-its-photograph`
- **Layers:** e2e
- **WHEN** `h` is pressed on a row's first flow cell, then `↵`
- **THEN** the row's photograph opens in the viewer
- **AND** while the source cell holds the focus, its thumbnail's foot is level with the row's images' foot

### Requirement: Sources are chosen in the file dialog, and each shows its own upload

The system SHALL take sources through the browser's file dialog, sending each file in its own request, and SHALL show
for each its upload's progress, then its reading, then whether it is ready, converted, refused or not cleaned, with
the reason. Import SHALL stay disabled, with its reason, until every chosen file is read, and SHALL commit only the
ready files and those the operator chose to import as they are. Each upload SHALL keep its own state, whatever its
name; an upload SHALL be refused once Import begins committing; and a file whose reading fails SHALL be refused
alone, the next file still read. While Import commits, the sheet SHALL take no file, no second Import and no
cancel, by button, by `Esc` or by leaving the screen; a commit refused after the screen is left SHALL cancel its
staged folder.

Each file's bar answers which one is slow; each reason sits on the file it concerns, so two files of one name are
two uploads. A file that lands while the folder is committed would be dropped from the collection unseen, and a cancel
then would delete the folder the commit is moving.

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
- **WHEN** Import is pressed on a new collection
- **THEN** the collection's hub opens with every source unassigned

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

#### Scenario: two uploads of one name keep their own states
- **Key:** `ui:sheet:two-uploads-of-one-name-keep-their-own-states`
- **Layers:** unit
- **WHEN** two files of one name are uploaded to one import, and one is refused
- **THEN** each upload is reported under its own id
- **AND** only the refused one carries the refusal

#### Scenario: an upload after Import is pressed is refused
- **Key:** `ui:sheet:an-upload-after-import-is-refused`
- **Layers:** unit
- **WHEN** a file is uploaded once Import has begun committing
- **THEN** the upload is refused, naming the way to add it
- **AND** the committed collection is unchanged by it

#### Scenario: a failed read refuses its file alone
- **Key:** `ui:sheet:a-failed-read-refuses-its-file-alone`
- **Layers:** unit
- **WHEN** reading one uploaded file raises
- **THEN** that file is refused, naming why
- **AND** the next file is still read

#### Scenario: a commit in flight holds the sheet
- **Key:** `ui:sheet:a-commit-in-flight-holds-the-sheet`
- **Layers:** e2e
- **WHEN** Import's commit is in flight
- **THEN** Add files…, Import and Cancel are disabled
- **AND** `Esc` leaves the sheet open

#### Scenario: leaving the screen mid-commit keeps the staged folder
- **Key:** `ui:sheet:leaving-mid-commit-keeps-the-folder`
- **Layers:** unit
- **WHEN** the sheet closes while Import's commit is in flight
- **THEN** its staging folder is not cancelled
- **AND** a commit refused after it closes cancels the folder

### Requirement: Prepare runs what changed as one job, and refuses before it starts when Ollama does not answer

The system SHALL run Prepare as one job over every assigned cell with no sheet: for each flow, the tagging, reading and
sheet stages, each one invocation of the pipeline's own verb over that flow's cells. One job of each kind, a Prepare and
a render, SHALL run at a time, the two side by side in any collections; a job SHALL keep running when its page closes;
Stop SHALL interrupt the current stage of the job it names and start no other, leaving the other job running; stopping
the surface SHALL interrupt every running job; each line a job's verbs write to the collection's log SHALL name its job;
and a stage that fails having reported nothing SHALL end the job as failed, naming the collection's log, and start no
other. Before any stage starts, the surface SHALL check that the local model server answers, and SHALL refuse with its
message, starting nothing, when it does not. While Prepare runs, the job strip and Prepare bar SHALL show completed
cells out of the accepted total and elapsed time; the total SHALL stay fixed, a cell SHALL count as completed only at
sheet, and elapsed time SHALL tick every second.

The pipeline's verb is the one path, so Prepare is exactly what the verbs do. Prepare runs on the local models and a
render on a rented GPU, and they write no file in common, so neither waits for the other. A refusal before the start
leaves every cell assigned, so pressing Prepare again is the whole fix.

#### Scenario: Prepare runs each stage over the assigned cells
- **Key:** `ui:prepare:prepare-runs-the-assigned-cells`
- **Layers:** e2e
- **WHEN** Prepare is pressed with cells assigned
- **THEN** each cell reaches sheet
- **AND** no cell outside the assignment changes
- **AND** while it runs, the strip and bar show matching totals and ticking elapsed time across a reload, and Render
  is offered beside it

#### Scenario: a second job is refused while one runs
- **Key:** `ui:prepare:one-job-at-a-time`
- **Layers:** unit
- **WHEN** a job is asked for while another of its kind runs
- **THEN** it is refused naming the running job

#### Scenario: another batch's Prepare is disabled while one runs
- **Key:** `ui:prepare:another-batchs-prepare-is-disabled`
- **Layers:** unit
- **WHEN** a hub has changes waiting while a Prepare runs for another collection
- **THEN** its Prepare is disabled, naming the collection that runs

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
- **THEN** the job ends as failed, naming the collection's log
- **AND** no later stage starts

#### Scenario: totals count cells rather than stage reports
- **Key:** `ui:prepare:totals-count-cells-not-stages`
- **Layers:** unit
- **WHEN** assigned cells report tagging, reading, sheet completion and a refusal
- **THEN** each cell counts once in the fixed total and only cells reaching sheet count as completed
- **AND** a repeated completion never increments the count again

#### Scenario: a render runs beside a Prepare
- **Key:** `ui:prepare:a-render-runs-beside-a-prepare`
- **Layers:** unit
- **WHEN** a render is asked for while a Prepare runs
- **THEN** both run, and Stop of the render leaves the Prepare running

#### Scenario: stopping the surface interrupts both jobs
- **Key:** `ui:prepare:stopping-the-surface-interrupts-both`
- **Layers:** unit
- **WHEN** the surface stops while a Prepare and a render run
- **THEN** both are interrupted, and the render's window closes before the surface exits

#### Scenario: the log names each job
- **Key:** `ui:prepare:the-log-names-each-job`
- **Layers:** unit
- **WHEN** a Prepare and a render write to one collection's log
- **THEN** each line begins with its job's name

### Requirement: The page is told of a job as it runs

The system SHALL serve an event stream that, on every connection, sends a snapshot of both job slots, the Prepare and
the render, and, when a collection is named, that collection's hub, and then sends each change as the job's stages
report it. A running Prepare snapshot SHALL carry its accepted total, completed count and start time. A hub opened while
the slot holds its collection's failed Prepare SHALL show that job's message until Discard on that collection's hub
dismisses it in that page. A page SHALL hold one event stream, naming the collection its screen shows and the import it
has open, and SHALL open it again when either changes. When the surface stops, its streams SHALL end before the server's
graceful wait expires, without cancellation errors; a terminal interrupt SHALL exit quietly after cleanup.

A reload or a second tab gets the whole truth at once; a job's progress reaches the page as the verbs report it. A
job outlives its page, so a failure that happened while no page was open is still told. Every connect brings a
snapshot, so a stream opened again loses nothing, and one connection a page leaves the browser's others free.

#### Scenario: a connection starts with a snapshot
- **Key:** `ui:events:a-connection-starts-with-a-snapshot`
- **Layers:** unit
- **WHEN** the stream is opened for a collection
- **THEN** its first event carries both job slots and that collection's hub

#### Scenario: a stage's report reaches the stream
- **Key:** `ui:events:a-stages-report-reaches-the-stream`
- **Layers:** unit
- **WHEN** a running stage reports an item done
- **THEN** the stream sends that cell's new stage

#### Scenario: a reconnect keeps Prepare progress
- **Key:** `ui:events:a-reconnect-keeps-prepare-progress`
- **Layers:** unit
- **WHEN** a connection is opened while Prepare has completed part of its work
- **THEN** its snapshot carries the same fixed total, completed count and start time as the running job

#### Scenario: stopping ends open streams quietly
- **Key:** `ui:events:stopping-ends-open-streams-quietly`
- **Layers:** unit
- **WHEN** the surface receives a terminal interrupt with event streams open
- **THEN** the streams end within the graceful wait and the surface exits with status 130 without cancellation errors
- **AND** a running job is interrupted and its cleanup and recovery messages remain visible

#### Scenario: a hub opened after a failure shows it
- **Key:** `ui:events:a-hub-opened-after-a-failure-shows-it`
- **Layers:** unit
- **WHEN** a hub opens while the slot holds its collection's failed Prepare
- **THEN** the Prepare bar shows the job's message
- **AND** once Discard dismisses it, a hub opened again in that page does not

#### Scenario: one stream follows the batch and the import
- **Key:** `ui:events:one-stream-follows-the-batch-and-the-import`
- **Layers:** unit
- **WHEN** a page opens a collection, then an import inside it
- **THEN** it holds one stream, opened again naming the collection and then the import too
- **AND** the stream it closed is the only other one it opened

#### Scenario: a job event fills its kind's slot
- **Key:** `ui:events:a-job-event-fills-its-kinds-slot`
- **Layers:** unit
- **WHEN** a render's event arrives while a Prepare runs
- **THEN** the page holds both jobs, each in its own slot

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

### Requirement: The render job opens the volume, renders, and closes the volume unless kept

The system SHALL run a render as one job: the volume window opened or extended, then the rendering verb with the
session's limit, its id and its progress, then the window closed unless the operator kept it open. A lost answer from
the window's opening SHALL render nothing and raise the volume alert, and an opening that raises SHALL mark its step
failed; a failed close SHALL raise it too. A job whose verb cannot be started SHALL end failed, naming the collection's
log, and still close the window. Stop SHALL interrupt the rendering verb, which tears its pod down. The surface
stopping SHALL do the same, and SHALL wait for the pod's teardown and the window's close before it exits, for at most
the teardown's estimate and one volume verb, saying so on its terminal as the wait begins. After that wait, a window
not kept whose close has failed or remains unfinished SHALL cause the terminal to name the command that closes it,
even when the worker has ended; kept and successfully closed windows SHALL need no close remedy. An interrupt at the
surface's terminal SHALL reach no child of the job.

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
- **WHEN** the surface stops mid-render with its window not kept and teardown outlasts the wait
- **THEN** the surface names the command that closes the window

#### Scenario: a verb that cannot start fails the job
- **Key:** `ui:render-job:a-verb-that-cannot-start-fails-the-job`
- **Layers:** unit
- **WHEN** the rendering verb cannot be started after the window opens
- **THEN** the job ends failed, naming the collection's log
- **AND** the window is closed

#### Scenario: a failed close at stop names the fix
- **Key:** `ui:render-job:a-failed-close-at-stop-names-the-fix`
- **Layers:** unit
- **WHEN** the surface stops mid-render and the window close fails before the wait ends
- **THEN** the terminal names the command that closes the window even though its worker has ended

#### Scenario: a kept window needs no close remedy
- **Key:** `ui:render-job:a-kept-window-needs-no-close-remedy`
- **Layers:** unit
- **WHEN** the surface stops mid-render with the window kept
- **THEN** the pod is torn down and the window is left open without a close-remedy warning

#### Scenario: an opening that raises fails its step
- **Key:** `ui:render-job:an-opening-that-raises-fails-its-step`
- **Layers:** unit
- **WHEN** opening the window raises
- **THEN** the job ends failed and the volume step reads failed

### Requirement: Billing state is read from gpunit's own records

The system SHALL show a pod as possibly billing when gpunit holds a pod record or a pending create while no session
runs, SHALL ask gpunit for its status only on start, every half minute while a session runs or an alert is open, and
on Check again, and SHALL clear an alert only when gpunit confirms the pod or volume gone. It SHALL offer the alert's
way out on its own page, `/billing`, which the alert band opens. It SHALL show an open volume as a quiet item until
the end gpunit recorded for its window, and as the alert band after it. The page SHALL show unknown billing while
its first snapshot is pending and an open volume while one is recorded; it SHALL say nothing is billing only when
both pod and volume are known absent.

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


#### Scenario: billing clearance requires known absence
- **Key:** `ui:billing:clearance-requires-known-absence`
- **Layers:** unit
- **WHEN** billing is unknown, a volume is open, or both resources are known absent
- **THEN** the page respectively shows pending state, the open volume, or nothing billing

### Requirement: The Renders view shows each source's images by flow and version

The system SHALL list a collection's images by source and offered flow, each cell's approval versions newest first, and
SHALL show them as a grid of sources by flows, each cell one row of its images, its versions oldest to newest, each
image marked with its version, and open an image's large view, with the sheet it was rendered from, from any of them.
A cell whose newest approval lacks images of its count SHALL carry the number it lacks, as the render stage counts
it. Each source SHALL show its photograph's thumbnail, upright, opening the photograph in a viewer, its cell the
grid's first column, reached by the keys and opened by `↵`. `Esc` on a large
view SHALL return to the screen it was opened from, focused on the image it closed, and Renders SHALL keep its focus
across the Back button and a switch of tabs. It SHALL mark an approval it cannot read as damaged, naming the
file, and show every image, that version's own among them; and SHALL refuse an address whose version is not `v` and
ASCII digits. It SHALL serve each thumbnail, a render's or a source's, from a cache in the library's `.cache/`, made
on first request and named by the image's own bytes. It SHALL refuse an image it cannot read, one past Pillow's pixel
bound among them, naming the file. It SHALL serve a photograph, a source or a run's copy, as the image its bytes are,
whatever its name ends in, and a source in a format the render does not read as an upright JPEG of it.

The images come back to where the sheets were decided, version by version in the order they were approved; a cache the
library can lose costs only its rebuild. Two collections can hold one source rendered at one seed, so only the bytes say
which image a thumbnail shows. One damaged file costs only its own version, never the collection's page. The count a
cell lacks is the render stage's own, so the page and the render agree on what is ready. A source keeps the name it
arrived with, and one ending `.html` served by its name would run as a page on the surface's own origin; one placed by
hand in another format is still shown, as its thumbnail is.

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
- **WHEN** two collections hold different images of one source, flow, version and seed
- **THEN** each image's thumbnail is made from that image

#### Scenario: a source's thumbnail is upright
- **Key:** `ui:renders:a-source-thumbnail-is-upright`
- **Layers:** unit
- **WHEN** a source's thumbnail is asked for and its file declares a turning orientation
- **THEN** the thumbnail is drawn upright
- **AND** a second request reads it from `.cache/`

#### Scenario: a cell counts what is ready
- **Key:** `ui:renders:a-cell-counts-what-is-ready`
- **Layers:** unit
- **WHEN** a cell's newest approval holds fewer images than its count
- **THEN** the cell carries the number of images it lacks

#### Scenario: the large view shows its sheet
- **Key:** `ui:renders:the-large-view-shows-its-sheet`
- **Layers:** e2e
- **WHEN** an image is opened from the grid
- **THEN** its large view shows the approval it was rendered from
- **AND** `Esc` returns to the grid focused on that image
- **AND** `h` from a row's first image reaches its source, and `↵` there opens its photograph

#### Scenario: a source opens in the viewer
- **Key:** `ui:renders:a-source-opens-in-the-viewer`
- **Layers:** e2e
- **WHEN** a source's thumbnail is clicked in the Renders view
- **THEN** its photograph opens in a dialog, fitted to the window
- **AND** `Esc` closes the dialog and leaves the address unchanged

#### Scenario: a damaged version's images are drawn
- **Key:** `ui:renders:a-damaged-versions-images-are-drawn`
- **Layers:** e2e
- **WHEN** the Renders view opens on a cell whose one approval is damaged
- **THEN** that version's images are drawn beside its damaged mark
- **AND** the first of them holds the focus

#### Scenario: a photograph is served as the image its bytes are
- **Key:** `ui:renders:a-photograph-is-served-as-its-bytes`
- **Layers:** unit
- **WHEN** a source whose name ends `.html` holds a PNG and is asked for whole
- **THEN** it is served as `image/png`, and the browser is told not to guess another type
- **AND** a run's photograph is served the same way
- **AND** a source in another format is served as an upright JPEG of it

#### Scenario: an image it cannot read is refused
- **Key:** `ui:renders:an-unreadable-image-is-refused`
- **Layers:** unit
- **WHEN** an image past Pillow's pixel bound is read for a thumbnail, or served whole
- **THEN** it is refused, naming the file

#### Scenario: a grid keeps its focus
- **Key:** `ui:renders:a-grid-keeps-its-focus`
- **Layers:** unit
- **WHEN** a collection's grid focus is moved, then its view is opened again
- **THEN** the focus is where it was left, or on the first spot when that one is gone

### Requirement: Every command has one key, declared once, and none fires while typing

The system SHALL declare each keyboard command once, with its key and its label, on the screen or overlay that offers
it, and SHALL draw every key hint and the key list from those declarations, the list opening on `⌃/` on every screen and
on the app bar's `?` button; no screen SHALL carry a key bar. It SHALL match a key by the physical key, whatever the
keyboard layout, and SHALL treat Mod as `⌘` on macOS and `Ctrl` elsewhere. An open overlay SHALL take every key before
the screen beneath it, and the screen before the keys offered everywhere. While focus is in a text field, no command
SHALL fire but `Esc`, `Mod+↵`, `Mod+Z`, `⇧Mod+Z`, `Mod+K`, `⌃/` and `⌃;`, Review's `⌃P`, and on macOS Review's `⌃H` and
`⌃L`, which move between its panes, and `⌃J` and `⌃K`, which move between its fields as `↓` and `↑` do; the field SHALL
keep its own editing keys. On a grid, a move between rows SHALL keep the column it is in, held at a shorter row's end.
On the hub and in the session drawer, a focused button or link SHALL keep `↵` and `Space`. An `Esc` that ends an input
method's composition SHALL be the input method's, closing nothing. `Esc` SHALL close an open suggestion list first, then
leave the field, then close the top overlay, then go back on the screen, and SHALL never close a billing alert. On the
large view and on Renders a command that writes SHALL take a shifted letter and one that only looks a plain one. No key
SHALL spend money but the Render dialog's `Mod+↵`, which confirms the price it quotes.

A key typed into a field is text, never a command; a list drawn from the declarations cannot disagree with the keys.
Option is the window manager's on Linux and types characters on macOS, and a layout moves letters but not keys.
On Linux `Ctrl+J` is the browser's and `Ctrl+K` is `Mod+K`, so the field moves are macOS's alone. A shifted letter is
not pressed in passing, so it guards what writes.

```
keydown ─▶ in a text field? ─ yes ─▶ Esc · Mod+↵ · Mod+Z · ⇧Mod+Z · Mod+K · ⌃/ · ⌃;, Review's ⌃P,
               │                     on macOS Review's ⌃H ⌃L ⌃J ⌃K, else the field's own
               │ no
               ▼
           top overlay ─▶ screen ─▶ everywhere        the first that declares the key runs
```

#### Scenario: a key is matched by the physical key
- **Key:** `ui:keys:a-key-is-matched-by-the-physical-key`
- **Layers:** unit
- **WHEN** `⇧H` is pressed on a Cyrillic layout
- **THEN** the command declared for `⇧H` runs

#### Scenario: Mod is Command or Control
- **Key:** `ui:keys:mod-is-command-or-control`
- **Layers:** unit
- **WHEN** a command declared for `Mod+K` is offered
- **THEN** `⌘K` and `Ctrl+K` each run it

#### Scenario: no command fires in a text field
- **Key:** `ui:keys:no-command-fires-in-a-text-field`
- **Layers:** unit
- **WHEN** a declared letter is pressed with focus in a text field
- **THEN** no command runs
- **AND** `Esc`, `Mod+↵`, `Mod+Z` and `Mod+K` still do

#### Scenario: a command waits until the field is left
- **Key:** `ui:keys:a-command-waits-until-the-field-is-left`
- **Layers:** e2e
- **WHEN** `⇧H` is typed into a tag field, then `Esc` and `⇧H` are pressed
- **THEN** the field holds the typed text and Review stays open
- **AND** the second `⇧H` opens the hub

#### Scenario: a focused control keeps Enter and Space
- **Key:** `ui:keys:a-focused-control-keeps-enter-and-space`
- **Layers:** unit
- **WHEN** `↵` or `Space` is pressed on the hub or in the session drawer with focus on a button or a link
- **THEN** the control answers it and the cell's command does not run

#### Scenario: an overlay takes the keys first
- **Key:** `ui:keys:an-overlay-takes-the-keys-first`
- **Layers:** unit
- **WHEN** an overlay and the screen beneath it both declare a key
- **THEN** only the overlay's command runs

#### Scenario: Esc closes the nearest thing first
- **Key:** `ui:keys:esc-closes-the-nearest-thing-first`
- **Layers:** unit
- **WHEN** `Esc` is pressed with a suggestion list open in a field inside an overlay
- **THEN** the list closes, and the next `Esc` leaves the field, and the next closes the overlay

#### Scenario: the key list and the hints come from the declarations
- **Key:** `ui:keys:hints-come-from-the-declarations`
- **Layers:** unit
- **WHEN** a screen declares its commands
- **THEN** its button hints and the key list name each command's key and label
- **AND** no key bar is drawn

#### Scenario: Renders moves by cell and by image
- **Key:** `ui:keys:renders-moves-by-cell-and-by-image`
- **Layers:** unit
- **WHEN** `l` and then `→` are pressed on a cell's last image of the Renders grid
- **THEN** each moves to the next image, crossing into the next cell, and `h` at a row's start reaches its source

#### Scenario: Review moves between its panes
- **Key:** `ui:keys:review-moves-between-its-panes`
- **Layers:** unit
- **WHEN** `l` is pressed from the rail three times
- **THEN** focus moves through the source pane and the sheet to ④

#### Scenario: a row move keeps the column
- **Key:** `ui:keys:a-row-move-keeps-the-column`
- **Layers:** unit
- **WHEN** `j` is pressed on the Renders grid's third image of a row whose next row holds two
- **THEN** the focus moves to that row's second image

#### Scenario: an Esc that ends a composition closes nothing
- **Key:** `ui:keys:an-esc-ending-a-composition-closes-nothing`
- **Layers:** unit
- **WHEN** `Esc` ends an input method's composition in a field inside an overlay
- **THEN** the field keeps the focus and the overlay stays open

#### Scenario: Review's panes move from a field on macOS
- **Key:** `ui:keys:review-panes-move-from-a-field-on-macos`
- **Layers:** unit
- **WHEN** `⌃L` is pressed with focus in a tag field, on macOS and then on Linux
- **THEN** on macOS the next pane takes the focus, and on Linux nothing moves

#### Scenario: the key list opens from a field
- **Key:** `ui:keys:the-key-list-opens-from-a-field`
- **Layers:** unit
- **WHEN** `⌃/` and then `?` are pressed with focus in a text field
- **THEN** `⌃/` opens the key list and `?` is typed into the field

#### Scenario: Review's fields move from a field on macOS
- **Key:** `ui:keys:review-fields-move-from-a-field-on-macos`
- **Layers:** unit
- **WHEN** Review's commands are declared on macOS and then on Linux
- **THEN** on macOS `⌃J` and `⌃K` move to the next and the previous field from a text field
- **AND** on Linux neither is declared

### Requirement: A dialog holds the focus while it is open

The system SHALL open every confirming dialog — Render, Revise, and New collection or Add sources — as a modal dialog,
the page behind it inert, the focus on its first control and held inside it, and SHALL return the focus to where it
was when it closes. The Render dialog's first control SHALL be *Keep the volume open*, which `Space` toggles and
`↵` leaves alone; the Revise dialog's SHALL be its confirm button.

A key goes where the eye is. A dialog over a grid that leaves the focus on the grid sends `↵` and `Tab` to what it
covers; and only `Mod+↵` spends money, so `↵` on the checkbox never renders.

#### Scenario: the Render dialog opens on its checkbox
- **Key:** `ui:dialogs:the-render-dialog-opens-on-its-checkbox`
- **Layers:** e2e
- **WHEN** the Render dialog opens on the hub, then `Tab` is pressed until the focus has passed every control
- **THEN** *Keep the volume open* held the focus first, and the focus never left the dialog
- **AND** `Esc` returns the focus to the hub cell it left

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

### Requirement: A folder in the library is a collection when it holds `sources/`

The system SHALL list as a collection every folder in the library that holds `sources/`, SHALL list any other folder as
not a collection and open none of it, and SHALL list no dot-folder. Each collection's row SHALL carry its name, its
source count, the names of its first fifteen sources, whose thumbnails it shows, for each flow the surface offers that
is present the counts approved and rendered out of the sources that have that flow, the count of sources with no flow,
and the time and kind of the newest file written in it. Collections SHALL be ordered by that time, newest first, and
folders that are not collections after them. Home SHALL carry New collection at the right of the library's header row,
and on an empty library below the privacy line. Count labels on the surface SHALL use a singular noun at one and a
plural noun otherwise.

A folder is a collection by its layout alone, so no marker file can disagree with what is on disk, and the row is a
listing read on every request. A folder that is not a collection is shown rather than hidden so the screen matches the
folder, and nothing in the app writes into it. The flows the surface offers are named in its configuration; a flow
approved from another's sheet stays the CLI's. On first start the privacy line is read before the first import.

#### Scenario: a folder with `sources/` is a collection
- **Key:** `ui:batch-folder:a-folder-with-sources-is-a-batch`
- **Layers:** unit
- **WHEN** the library holds a folder with `sources/` and one without
- **THEN** the first is listed as a collection
- **AND** the second is listed as not a collection, and cannot be opened

#### Scenario: a dot-folder is not listed
- **Key:** `ui:batch-folder:a-dot-folder-is-not-listed`
- **Layers:** unit
- **WHEN** the library holds a folder whose name starts with a dot
- **THEN** it is not listed at all

#### Scenario: a flow's counts are of the sources that have it
- **Key:** `ui:batch-folder:a-flows-counts-are-of-its-sources`
- **Layers:** unit
- **WHEN** a collection's sources have different sets of flows
- **THEN** each flow's approved and rendered counts are out of the sources whose runs hold that flow
- **AND** the sources with no flow are counted apart

#### Scenario: collections are ordered by their newest file
- **Key:** `ui:batch-folder:batches-are-ordered-by-their-newest-file`
- **Layers:** unit
- **WHEN** the library holds collections written at different times
- **THEN** they are listed newest first, by the newest file written in each

#### Scenario: no file records a collection
- **Key:** `ui:batch-folder:no-file-records-a-batch`
- **Layers:** unit
- **WHEN** the surface lists the library and opens a collection
- **THEN** no file describing a collection is created anywhere in the library

#### Scenario: a flow the surface does not offer has no count
- **Key:** `ui:batch-folder:an-unoffered-flow-has-no-count`
- **Layers:** unit
- **WHEN** a collection's runs hold a tracked flow the configuration does not offer
- **THEN** its row carries no count for that flow

#### Scenario: count labels use singular at one
- **Key:** `ui:batch-folder:count-labels-use-singular-at-one`
- **Layers:** unit
- **WHEN** a count label is drawn for zero, one and several items
- **THEN** one uses the singular noun and the other counts use the plural noun

#### Scenario: a row names its first sources
- **Key:** `ui:batch-folder:a-row-names-its-first-sources`
- **Layers:** unit
- **WHEN** a collection holds seventeen sources
- **THEN** its row names the first fifteen in the hub's order
- **AND** its source count is seventeen

#### Scenario: first start shows New collection under the privacy line
- **Key:** `ui:batch-folder:first-start-shows-new-batch-under-the-privacy-line`
- **Layers:** e2e
- **WHEN** Home opens on an empty library
- **THEN** New collection sits below the privacy line

### Requirement: Every screen has a URL naming its collection and its run

The system SHALL give Home, a collection's hub, a collection's Review, a review of a source in a flow and the billing
alert's way out each its own URL, the session drawer holding none, SHALL name the collection in every URL inside one,
and SHALL name a run by the twelve-character digest its identifier begins with. A collection's Review SHALL open the
sheet Review starts from and put that sheet's URL in its place. It SHALL answer any of them on a fresh load, and SHALL
refuse one naming a collection or a run the library does not hold, naming the way back.

A reload, a second tab or a bookmark then lands where it was, never on whatever the server last held open. A run's
short name is a sanitised filename and can repeat; its digest cannot.

```
/                                       Home
/c/<collection>/hub                     the hub
/c/<collection>/review                  the head of Review, replaced by its sheet's URL
/c/<collection>/review/<digest>/<flow>  Review
/billing                                the billing alert's way out
```

#### Scenario: a reload lands on the same screen
- **Key:** `ui:routes:a-reload-lands-on-the-same-screen`
- **Layers:** e2e
- **WHEN** a hub, a review or a collection's Review address is loaded again
- **THEN** the same collection, source and flow are shown
- **AND** a collection's Review address is replaced by its head's sheet URL
- **AND** a collection with no sheet waiting says none waits

#### Scenario: a run is named by its digest
- **Key:** `ui:routes:a-run-is-named-by-its-digest`
- **Layers:** unit
- **WHEN** a review URL names a run
- **THEN** the run is the one whose identifier begins with that digest

#### Scenario: an unknown collection is refused with the way back
- **Key:** `ui:routes:an-unknown-batch-is-refused`
- **Layers:** e2e
- **WHEN** a URL names a collection the library does not hold
- **THEN** the page refuses, naming the collection
- **AND** it offers the way back to Home

### Requirement: Review opens a collection at its own address, lists every unrendered sheet, and Approve stays on the sheet

The system SHALL open a collection's Review on a chooser when two or more flows hold sheets to review: a row per flow,
its name, how many wait to be approved and how many lack images, and up to fifteen of its waiting photographs, then
`+n`; `j` `k` and the arrows SHALL move between rows, `↵` or a click on a row SHALL open that flow's head, and a click
on a photograph that sheet. With one such flow it SHALL open that flow's head: its first unapproved sheet in the hub's
order, else its first approved sheet whose newest approval lacks images of its count, read-only; with none, a page
saying no sheet waits for review, with the way to the hub. `Esc` on Review, with no overlay open and outside a field,
SHALL return to the chooser. The hub SHALL carry for each cell the number of images its newest approval lacks, as the
render stage counts it. Review's rail SHALL list every sheet of the flow that is unapproved or lacks images, each marked
untouched, edited, approved or re-opened, and its footer SHALL count the approved among them; the Review tab SHALL count
the unapproved, every flow's, and the rail's head SHALL name each other flow holding some, with how many and the key to
the chooser. Approve SHALL leave the sheet open and read-only, the approve bar naming the approval it shows, offering
*Cancel approve* while the review stage can cancel it, else the reason beside it, and while no render runs for the
collection; a cancel SHALL leave the sheet open on what the flow is left on: its draft, editable, or for a copy the
draft open above what lies beneath, else the approval beneath it, read-only. Opening a sheet that has no draft SHALL
write one through the review stage's own function, and opening it again SHALL write no second draft; a failure after
approval SHALL be shown in the approve bar, never dropped. ④ SHALL show one slot per image, a set seed or random, beside
the sheet rows. `⌃P` SHALL open the photograph in the viewer — on a revision or a draft from an image, *Side by side* —
from any pane and from a field, stepping through the rail's sheets, and `Esc` SHALL return the focus where it was.

A sheet is done when its images are, not when it is approved, so the rail keeps it until then; the count is the
render stage's own. Approving is an act, not a navigation, and a copy's cancel takes back only the copy. A slot per
image says what the next render draws before it is approved. The operator chooses the flow to review; the page
does not choose it for them.

```
two or more flows waiting ─▶ the chooser ─↵─▶ that flow's head
one flow waiting          ─▶ its head: first unapproved ─▶ else first approved and short
none                      ─▶ "No sheet waits for review"
```

#### Scenario: a collection's Review opens its head
- **Key:** `ui:review:a-batch-opens-its-head`
- **Layers:** unit
- **WHEN** a collection's one flow holds an approved, short sheet and an unapproved one, then neither
- **THEN** its Review opens the unapproved sheet, then the approved one
- **AND** with no sheet left it opens none

#### Scenario: two flows waiting open the chooser
- **Key:** `ui:review:two-flows-waiting-open-the-chooser`
- **Layers:** unit
- **WHEN** a collection's two flows each hold an unapproved sheet
- **THEN** its Review is a row per flow, each naming its count and its waiting photographs

#### Scenario: the chooser opens a flow
- **Key:** `ui:review:the-chooser-opens-a-flow`
- **Layers:** e2e
- **WHEN** the Review tab opens on two waiting flows, `j` then `↵` are pressed
- **THEN** Review opens on the second flow's first waiting sheet
- **AND** `Esc` returns to the chooser, its second row focused

#### Scenario: a cell counts what its newest approval lacks
- **Key:** `ui:review:a-cell-counts-what-it-lacks`
- **Layers:** unit
- **WHEN** a cell's newest approval holds one image of a count of three
- **THEN** the hub carries two for that cell

#### Scenario: the rail holds every sheet not yet rendered
- **Key:** `ui:review:the-rail-holds-every-unrendered-sheet`
- **Layers:** unit
- **WHEN** a flow holds an unapproved sheet, an approved short one and an approved one with all its images
- **THEN** the rail lists the first two, marked by their state

#### Scenario: Approve stays on the sheet
- **Key:** `ui:review:approve-stays-on-the-sheet`
- **Layers:** e2e
- **WHEN** a sheet is approved
- **THEN** the same sheet stays open, read-only, and its rail mark reads approved
- **AND** the approve bar names its approval

#### Scenario: opening a sheet with no draft writes one
- **Key:** `ui:review:opening-a-sheet-writes-its-draft`
- **Layers:** unit
- **WHEN** Review opens a sheet whose flow has a sheet and no draft
- **THEN** a draft is written through the review stage
- **AND** opening it again writes no second draft

#### Scenario: a failure after approval is shown
- **Key:** `ui:review:a-failure-after-approval-is-shown`
- **Layers:** e2e
- **WHEN** an approval succeeds and reading the collection again fails
- **THEN** the approve bar shows the refusal

#### Scenario: each image has a slot
- **Key:** `ui:review:each-image-has-a-slot`
- **Layers:** unit
- **WHEN** a draft renders four images with seed 144 listed
- **THEN** ④ shows four slots, the first holding 144 and three random
- **AND** removing a slot takes a random one first

#### Scenario: the photograph opens in the viewer
- **Key:** `ui:review:the-photograph-opens-in-the-viewer`
- **Layers:** e2e
- **WHEN** `⌃P` is pressed in a tag field, then `→`
- **THEN** the viewer shows the photograph fitted, then the next sheet's photograph
- **AND** `Esc` returns the focus to the field

#### Scenario: Cancel approve opens the sheet again
- **Key:** `ui:review:cancel-approve-opens-the-sheet-again`
- **Layers:** e2e
- **WHEN** a sheet is approved, then *Cancel approve* is pressed
- **THEN** the same sheet is editable again

#### Scenario: an approved sheet says why it cannot be cancelled
- **Key:** `ui:review:the-sheet-says-why-it-cannot-be-cancelled`
- **Layers:** unit
- **WHEN** Review reads an approved sheet whose prompt is assembled
- **THEN** its payload carries the review stage's reason

#### Scenario: the rail names the other flows' waiting sheets
- **Key:** `ui:review:the-rail-names-the-other-flows-waiting`
- **Layers:** unit
- **WHEN** Review is open on one flow and another flow holds one unapproved sheet
- **THEN** the rail's head names that flow and one waiting

### Requirement: Draft from this starts from an image, for any flow the app offers, and opens Review on the draft

The system SHALL offer *Draft from this* on `⇧D` from an image's large view and over a selection in the Renders grid,
opening a dialog that lists every flow the app offers, the image's own first, named *revise*, focused, and the others
after it, assigned or not; `↵` SHALL draft the chosen flow from each image's approval, as the draft verb does — a
revision for the image's own flow, a draft from that approval for another, assigning a target and filling its sheet
from the source's tags where it holds none, the image's seed prefilled and the image recorded — then open Review on the
first draft, the others of its flow in the rail. A target holding a waiting draft with edits of its own SHALL write
nothing for that image and open Review on that draft; one equal to its sheet SHALL be replaced. A selection SHALL be
drafted all or none, refusing by name an image of a flow this build does not track, and refusing a selection that names
a version or a seed no run can hold. On such a draft, draft or approved, Review SHALL show the photograph and the image
the draft records — whatever its seeds became, else, for a revision, the first of its seeds rendered under its approval
— on one line, at equal height under one header row, headed by its flow, version and seed, and offer *Side by side*,
also on `⌃P`, both in one dialog, `⌃P` in it showing the photograph alone and back; it SHALL mark each field that
differs from the approval a revision came from, or from the target's sheet for another flow, naming the source flow and
approval in the sheet's kicker; on a draft it SHALL offer to discard it from the approve bar, deleting it only once the
operator confirms.

```
large view · summon-anime-wai v2 · seed 9423…   ⇧D
  Draft from this
  ▸ summon-anime-wai        revise
    summon-flat-anime-wai
    conjure-anime-wai
  ↵ ─▶ Review on the draft: the photograph │ the image it came from
```

An image the operator approved is where the next draft starts, in its own flow or another: one act, whatever the flows
become. The comparison that matters is the render against the photograph, read against the sheet. A waiting edit is the
work in hand; a draft the operator never touched holds no work. A discard deletes the operator's edits, so one click
never does.

#### Scenario: Revise opens Review on the revision
- **Key:** `ui:revise:revise-opens-review-on-the-revision`
- **Layers:** e2e
- **WHEN** *Draft from this* is drafted into the image's own flow on its large view
- **THEN** Review opens on its draft with the render beside the photograph and the seed prefilled
- **AND** once approved, the render still stands beside the photograph

#### Scenario: a revision keeps its image after its seed changes
- **Key:** `ui:revise:a-revision-keeps-its-image-after-its-seed-changes`
- **Layers:** unit
- **WHEN** Review reads a revision whose seed was changed, draft and then approved
- **THEN** its payload names the image the revision was written from

#### Scenario: an approved revision keeps its image
- **Key:** `ui:revise:an-approved-revision-keeps-its-image`
- **Layers:** unit
- **WHEN** Review reads a revision's approval
- **THEN** its payload names the approval it came from, its image and that approval's fields

#### Scenario: a waiting draft is opened, not refused
- **Key:** `ui:revise:a-waiting-draft-is-opened`
- **Layers:** unit
- **WHEN** a revision is asked for an image whose flow holds a waiting draft with edits of its own
- **THEN** it answers with that draft and writes nothing

#### Scenario: an untracked flow refuses its image
- **Key:** `ui:revise:an-untracked-flow-refuses-its-image`
- **Layers:** unit
- **WHEN** a draft is asked for a selection holding an image of a flow this build does not track
- **THEN** that image is refused naming its flow
- **AND** no draft is written for any image

#### Scenario: an image no run can hold is refused
- **Key:** `ui:revise:an-image-no-run-can-hold-is-refused`
- **Layers:** unit
- **WHEN** a draft is asked for an image whose version or seed no run can hold
- **THEN** the selection is refused
- **AND** no draft is written

#### Scenario: a discard deletes the draft the page read
- **Key:** `ui:revise:a-discard-deletes-the-draft-the-page-read`
- **Layers:** unit
- **WHEN** a discard states the draft on disk
- **THEN** that draft is deleted
- **AND** every approval is unchanged

#### Scenario: Discard asks before it deletes
- **Key:** `ui:revise:discard-asks-before-it-deletes`
- **Layers:** e2e
- **WHEN** Discard is pressed on a revision, then Keep
- **THEN** the draft is still on disk and the sheet still open

#### Scenario: Side by side shows the pair
- **Key:** `ui:revise:side-by-side-shows-the-pair`
- **Layers:** e2e
- **WHEN** `⌃P` is pressed on a revision with focus in a tag field, then `⌃P` again
- **THEN** one dialog shows the photograph and the render at equal height, then the photograph alone
- **AND** `Esc` closes it

#### Scenario: the large view names its targets
- **Key:** `ui:conjure-from:the-large-view-names-its-targets`
- **Layers:** unit
- **WHEN** a summon image's large view is read in a collection where no source is assigned another flow
- **THEN** its targets are every flow the app offers, summon first

#### Scenario: a refused draft writes nothing
- **Key:** `ui:conjure-from:a-refused-draft-writes-nothing`
- **Layers:** unit
- **WHEN** a draft is asked from an approval version the source does not hold
- **THEN** it is refused naming that version
- **AND** no file is written

#### Scenario: a waiting edit is opened
- **Key:** `ui:conjure-from:a-waiting-edit-is-opened`
- **Layers:** unit
- **WHEN** a draft is asked for a target whose waiting draft has edits of its own
- **THEN** it answers with that draft and writes nothing

#### Scenario: an approved draft keeps its marks
- **Key:** `ui:conjure-from:an-approved-draft-keeps-its-marks`
- **Layers:** unit
- **WHEN** Review reads the approval of a draft written from another flow's approval
- **THEN** it names the source flow and approval, and carries the target sheet's fields

#### Scenario: Review reads the draft against the target's sheet
- **Key:** `ui:conjure-from:review-reads-the-draft-against-the-sheet`
- **Layers:** unit
- **WHEN** Review reads a draft written from another flow's approval
- **THEN** it names the source flow and approval, and carries the target sheet's fields

#### Scenario: Conjure from this opens Review on the draft
- **Key:** `ui:conjure-from:conjure-from-this-opens-review`
- **Layers:** e2e
- **WHEN** `⇧D` is pressed on a summon image whose source is not assigned conjure, conjure chosen and `↵` pressed
- **THEN** Review opens on conjure's draft, its kicker naming the summon approval
- **AND** a field summon changed is marked against conjure's sheet
- **AND** its caption pane shows summon's caption, named as summon's, and the summon image stands beside the photograph

#### Scenario: an unedited waiting draft is replaced
- **Key:** `ui:draft-from:an-unedited-waiting-draft-is-replaced`
- **Layers:** unit
- **WHEN** a draft is asked for a target whose waiting draft equals its sheet
- **THEN** the draft from the image is written at that draft's number

#### Scenario: a selection drafts into the flow chosen
- **Key:** `ui:draft-from:a-selection-drafts-into-the-flow-chosen`
- **Layers:** unit
- **WHEN** a selection of two images from different runs is drafted into another flow
- **THEN** each run's target gains a draft from its image's approval, its seed prefilled

### Requirement: A version says what it was, and Compare sets an image beside any image of its source

The system SHALL head each image's large view with its approval version, the version it came from, read from its
producer, naming it a revision when its fields differ from that version's and a re-roll when only its count or seeds do,
and the approval's time, count and seeds. `c` on a large view SHALL open a pick of its source's images: the photograph's
row on top, then a row per flow holding images of the source, each row its images oldest to newest, each named by its
version and seed, the image compare started from marked; the focus SHALL start on the newest older version of its seed,
else the image before it, else the photograph; `h j k l` and the arrows SHALL move it, keeping the column, held at a
shorter row's end, `↵` SHALL compare the image picked and `Esc` close the pick. Compare SHALL set the image picked on
the left and the image compare started from on the right, at equal size, each headed by its flow, version and seed:
between two renders it SHALL show the fields both flows declare, marked where they differ, and say when the two seeds
differ or the two share a sheet; with the photograph, the pair alone. The large view SHALL offer no *Side by side*.

```
large view · summon v2 · seed 9423   c ─▶  photo                  [▣]
                                           summon-anime-wai       [v1][v2·][v3]
                                           summon-flat-anime-wai  [v1]
                                       ↵ ─▶ Compare: the image picked │ summon v2 · seed 9423
```

The origin is already on disk, so nothing new records it. A pick reads as a choice when every choice is in view; one
source's images are every comparison the operator makes for one person. The eye returns to where it came from, on the
right.

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
- **WHEN** `c` is pressed on a revised image, then `↵`
- **THEN** the older version is on the left and the revised image on the right, with the changed fields
- **AND** a pick of another flow's image compares it, saying the seeds differ

#### Scenario: the photograph's pick sets it beside the image
- **Key:** `ui:compare:side-by-side-sets-the-image-beside-its-photograph`
- **Layers:** e2e
- **WHEN** `c` is pressed on an image's large view, then `k` to the photograph's row and `↵`
- **THEN** the photograph is on the left and the image on the right, at equal height, with no fields

#### Scenario: Compare takes any two images of a source
- **Key:** `ui:compare:any-two-images-of-a-cell`
- **Layers:** unit
- **WHEN** Compare is asked for a summon image of v4 against a flat summon image of v1 with another seed
- **THEN** it serves both, the shared fields that differ and that the seeds differ
- **AND** the image picked is on the left, the image compare started from on the right

#### Scenario: the pick moves by row and column
- **Key:** `ui:compare:the-pick-moves-by-row-and-column`
- **Layers:** unit
- **WHEN** `j` is pressed on the photograph's row, then `l` twice, then `j` onto a shorter row
- **THEN** the focus moves to the first flow's first image, then its third, then the shorter row's last
