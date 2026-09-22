## MODIFIED Requirements

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

## ADDED Requirements

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
