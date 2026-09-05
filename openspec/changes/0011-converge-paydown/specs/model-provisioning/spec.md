## MODIFIED Requirements

### Requirement: Every source is pinned to an immutable revision and a digest

Every entry SHALL name its bytes by a revision that cannot move and by a SHA-256 digest. A source
that resolves a branch is not a pin: the same URL returns different bytes on different days, and no
record in this repository would show that it had.

Where an artifact has no first-party source at all — every host serving it is a mirror — the digest
is not merely a check on the transfer but the whole trust root, and it SHALL be the digest the
artifact's publisher states rather than one computed from whichever copy was fetched first. A digest
taken from a mirror attests only that the mirrors agree with each other.

These rules SHALL be enforced where the manifest is read on the pod, not only where it is asserted
against in the suite. A check that runs at commit time constrains the manifest this repository
tracks; it does not constrain a manifest the module is handed, and it is the module that joins a
destination onto the filesystem, hands a URL to a transfer, and decides what to fetch. Accordingly
the system SHALL refuse — before any transfer begins and with a message naming the entry — a
destination that does not resolve inside the models root, a source that is not a pinned URL free of
whitespace, and an entry declaring no sources at all.

The system SHALL also carry the resolved destination through to whatever performs the transfer,
rather than having that component join paths of its own, so the containment rule is enforced in one
place instead of being restated wherever a path is assembled.

#### Scenario: no source resolves a mutable ref
- **Key:** `model-provisioning:immutable-pins:no-source-resolves-a-mutable-ref`
- **Layers:** unit
- **WHEN** the manifest's sources are examined
- **THEN** every one addresses an immutable revision
- **AND** a source naming a branch rather than a revision fails the check

#### Scenario: every entry carries a digest
- **Key:** `model-provisioning:immutable-pins:every-entry-carries-a-digest`
- **Layers:** unit
- **WHEN** the manifest's entries are examined
- **THEN** each declares a SHA-256 digest of the file's full contents
- **AND** an entry with a missing or malformed digest fails the check

#### Scenario: an artifact with no first-party source carries an alternate
- **Key:** `model-provisioning:immutable-pins:third-party-artifact-carries-an-alternate`
- **Layers:** unit
- **WHEN** an entry's primary source is a third-party mirror rather than the publisher
- **THEN** the entry declares at least one additional source for the same digest
- **AND** the digest is what makes any of those sources acceptable, so the alternates add
  availability without adding trust

#### Scenario: an artifact its publisher does not host is pinned to the publisher's stated digest
- **Key:** `model-provisioning:immutable-pins:mirrored-artifact-pins-the-published-digest`
- **Layers:** unit
- **WHEN** an entry is served only by mirrors, none of them the publisher
- **THEN** its declared digest equals the one the publisher states for that artifact, and the check
  runs offline as part of the ordinary suite rather than only when a human re-derives the manifest
- **AND** the tie between the shipped bytes and the publisher's own digest is therefore held by the
  gate, so changing it is a deliberate test edit rather than a silent retrust of the mirrors
- **AND** that published digest is read from the publisher's own machine-readable record when the
  manifest is derived, rather than transcribed by hand into the files that compare against each
  other, because three copies of one transcription cross-check the copying and not the value

#### Scenario: a destination that escapes the models root is refused
- **Key:** `model-provisioning:immutable-pins:an-escaping-destination-is-refused`
- **Layers:** unit
- **WHEN** an entry names a destination that is absolute, or that resolves outside the models root
- **THEN** provisioning refuses before any transfer, naming the entry and the destination
- **AND** the destination handed to the transfer is the already-resolved path, so no component
  downstream joins a path of its own and the rule is enforced in exactly one place
- **AND** the digest offers no protection here, because whoever supplies the destination supplies the
  digest beside it — and a second project shares the volume this tree lives on

#### Scenario: a source that is not a pinned URL is refused at the point of use
- **Key:** `model-provisioning:immutable-pins:a-malformed-source-is-refused-at-runtime`
- **Layers:** unit
- **WHEN** an entry declares a source that is not a pinned URL, or that contains whitespace
- **THEN** provisioning refuses before any transfer, naming the entry and the source
- **AND** the transfer receives the sources as a list rather than as a string it must split, so a
  source's shape can never change how many arguments the transfer is given

#### Scenario: an entry declaring no sources is refused
- **Key:** `model-provisioning:immutable-pins:an-entry-with-no-sources-is-refused`
- **Layers:** unit
- **WHEN** an entry declares an empty list of sources
- **THEN** provisioning refuses with a message saying that no source was declared for that
  destination
- **AND** it does not report that every source was rejected, because an entry that offered nothing
  and an entry whose every offer was refused are different failures with different fixes

### Requirement: A provisioning failure leaves the pod reachable

When provisioning aborts, the pod SHALL stay up with its SSH daemon running rather than terminating.
The abort policy leaves a mismatched file on disk for a human to inspect, and that is only true if
the human can get in: a container whose entrypoint exits takes its daemon with it and dies again on
every subsequent boot, within seconds of start.

That hold SHALL cover preparing the models namespace as well as fetching into it. Preparing the
volume is provisioning by any reading a human would give the word, and a failure there — an
unwritable volume, a link onto a path that could not be cleared — terminates the entrypoint exactly
as a fetch failure used to.

The hold SHALL be bounded rather than indefinite, and the failure SHALL be legible from outside the
container's log. A pod holding open reports as running and healthy while it bills, so an unattended
failure that looks like success is the one that outlasts the session's spending ceiling; the bound
SHALL be shorter than that ceiling allows.

#### Scenario: a provisioning abort holds the pod open instead of stopping it
- **Key:** `model-provisioning:reachability:a-provisioning-abort-holds-the-pod-open`
- **Layers:** unit
- **WHEN** the pod entrypoint's provisioning step exits non-zero
- **THEN** the entrypoint reports the failure and holds in the foreground with the SSH daemon alive
- **AND** the inference server is not started, and nothing on the volume is removed

#### Scenario: preparing the namespace is held open the same way fetching is
- **Key:** `model-provisioning:reachability:namespace-setup-is-held-open-too`
- **Layers:** unit
- **WHEN** preparing the models namespace fails before any artifact is fetched
- **THEN** the entrypoint reports the failure and holds the pod open exactly as a fetch failure does
- **AND** no step of preparing the namespace can terminate the entrypoint, because the guarantee is
  about provisioning and not about one of its steps

#### Scenario: the hold is bounded and leaves a marker outside the log
- **Key:** `model-provisioning:reachability:the-hold-is-bounded-and-marked`
- **Layers:** unit
- **WHEN** the entrypoint holds the pod open after a provisioning failure
- **THEN** the hold ends on its own within a stated window shorter than the session's spending
  ceiling allows, and a marker recording the failure is written where the failure itself cannot have
  made it unwritable
- **AND** the marker is therefore not written onto the volume, because the volume is exactly the
  thing that may have failed

#### Scenario: the pod refuses to provision onto anything but its network volume
- **Key:** `model-provisioning:reachability:provisioning-requires-the-network-volume`
- **Layers:** unit
- **WHEN** the pod is created without the network volume it expects, or the models namespace would
  otherwise be prepared somewhere that is not that volume
- **THEN** the pod is refused before it is created if the volume it expects is not named, and the
  entrypoint refuses before preparing the namespace if what it finds is not that volume
- **AND** the entrypoint is told which volume to expect rather than inferring it, because the failure
  this prevents — a full model stack downloaded onto storage that does not survive the pod — renders
  correctly, bills fully and is discovered only on the next metered session

### Requirement: Model artifacts resolve inside the project's own namespace

Every artifact this project provisions SHALL resolve within a directory tree belonging to this
project, including artifacts a custom node downloads for itself. Files written outside that tree
land on storage that does not survive the pod, so they are re-fetched during metered renders and
cannot be verified against the manifest at all.

A node that fetches its own models SHALL be bound to the manifest by name rather than by a naming
convention. A rule that recognises such nodes by how their class is spelled binds the ones that
happen to be spelled that way and silently passes the ones that are not, so the artifacts of an
unrecognised node are load-bearing while nothing checks that they are still declared.

#### Scenario: annotator checkpoints resolve onto the project's models tree
- **Key:** `model-provisioning:namespace:annotator-checkpoints-resolve-onto-the-models-tree`
- **Layers:** unit
- **WHEN** the pod's configuration is examined
- **THEN** the preprocessor pack's checkpoint directory is set to a path inside the project's models
  tree
- **AND** a configuration that leaves it at the pack's own default fails the check

#### Scenario: every self-fetching node in the graph is bound to the manifest by name
- **Key:** `model-provisioning:namespace:self-fetching-nodes-are-bound-by-name`
- **Layers:** unit
- **WHEN** the shipped graph is examined against the set of node classes known to fetch their own
  models
- **THEN** every such class present in the graph has its artifacts declared in the manifest, and a
  class in the graph that is absent from that set fails the check
- **AND** membership is by name rather than by how a class is spelled, so a node that fetches for
  itself cannot pass by not matching a pattern
</content>
