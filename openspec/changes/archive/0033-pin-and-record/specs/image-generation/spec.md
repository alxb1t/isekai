## MODIFIED Requirements

### Requirement: A flow is pinned by equality; changing any file in it is an explicit act

The system SHALL hold each tracked flow against a committed digest computed over every file in its
directory, so that altering a dial, a prompt fragment, the graph, the schema or either briefing fails the
suite naming the flow. Re-pinning SHALL be possible only as a deliberate edit to the committed digest, in
a change that states what moved and why.

**The freeze's job is that nothing changes silently, not that nothing changes.** The previous wording said
changing a file *"creates a new flow"*, and the repository then did otherwise: `v0.22.3` removed two tags
from both tracked flows' negative prompts and re-pinned, because the reason for the edit was that the
renders were better — a claim about output that the freeze exists to surface rather than to forbid.
Stating a rule the project does not follow is worse than stating the narrower one it does.

**A new identifier is still what a *divergence* costs.** Two flows exist to be compared over one cohort,
and that comparison is only possible if an identifier means one configuration. So the test is not whether
a file changed but whether the old configuration is still wanted: where both must exist — a variant, an
alternative base, a second generation — the answer is a new flow, and re-pinning would destroy the
comparison. Where the old configuration is simply abandoned, re-pinning records that in one place.

**Re-pinning is not free and must not become routine.** Runs rendered before the edit were produced by
bytes that no longer exist. A sheet, a prompt and a render record the flow's digest, so an artifact shows
which side of a re-pin it falls on; an artifact written before that record began shows nothing. A change that re-pins therefore owes a statement
of what moved, in prose a later reader can find; a change that re-pins without one has spent the rule and
left nothing in its place.

#### Scenario: editing any file in a tracked flow fails the suite
- **Key:** `image-generation:immutability:flow-manifest-is-pinned-by-equality`
- **Layers:** unit
- **WHEN** any file in a tracked flow directory differs from its committed digest
- **THEN** the suite fails naming the flow

#### Scenario: adding a file to a flow moves its digest
- **Key:** `image-generation:immutability:a-new-file-moves-the-digest`
- **Layers:** unit
- **WHEN** a file is added to a tracked flow's directory
- **THEN** that flow's digest differs from the committed one
- **AND** the suite fails naming the flow

#### Scenario: an output's provenance carries the graph digest
- **Key:** `image-generation:immutability:output-records-the-graph-digest`
- **Layers:** unit
- **WHEN** a render is written
- **THEN** its provenance records the flow identifier, the flow's digest, the seed, the sheet it came from
  and the digest of the submitted graph
- **AND** two renders from the same flow identifier with different graphs are distinguishable

#### Scenario: a re-pin states what moved
- **Key:** `image-generation:immutability:a-re-pin-is-recorded`
- **Layers:** unit
- **WHEN** a tracked flow's committed digest is changed
- **THEN** every tracked flow still matches its committed digest
- **AND** the change that moved it records which flow moved and what changed in it

## REMOVED Requirements

### Requirement: Seeds are explicit or drawn, and an output is named by its seed

**Reason**: Its SHALL and a scenario title said outputs are grouped under the *sheet version*, while the code
groups them under the approval's number; the render now records the sheet's number, so the two words must
mean two things.

**Migration**: None. The directory layout does not change; only the requirement's wording does.

## ADDED Requirements

### Requirement: Seeds are explicit or drawn, and an output is named by its seed under its approval

The system SHALL accept either a count of renders or an explicit list of seeds, SHALL NOT accept both,
SHALL draw seeds from an injectable source when given a count, and SHALL name each output by its seed
under the number of the approval it was rendered from.

Naming the output by its seed is the reproducibility contract at the finest grain the system has: one
image, one integer. The two ways of asking are separate verbs — one explores, one reproduces — and
combining them has no meaning. Drawing from an injectable source is what keeps the suite deterministic
without making production output predictable.

**The directory is the approval's number, and the requirement now says so.** It said *sheet version* while
the code grouped by approval; one sheet approved twice renders into two directories. The sheet's own number
is recorded in the render instead.

#### Scenario: a count draws that many distinct seeds
- **Key:** `image-generation:seeds:count-draws-distinct-seeds`
- **Layers:** unit
- **WHEN** a count of renders is requested
- **THEN** that many distinct seeds are drawn from the injected source
- **AND** each render is named by the seed that produced it

#### Scenario: explicit seeds render exactly those
- **Key:** `image-generation:seeds:explicit-seeds-render-exactly-those`
- **Layers:** unit
- **WHEN** seeds are named explicitly
- **THEN** exactly those seeds are rendered
- **AND** no additional seed is drawn

#### Scenario: asking for both is refused
- **Key:** `image-generation:seeds:count-and-seeds-are-exclusive`
- **Layers:** unit
- **WHEN** both a count and explicit seeds are given
- **THEN** the invocation is refused
- **AND** the message states that the two are alternatives

#### Scenario: outputs are grouped under the approval they came from
- **Key:** `image-generation:seeds:outputs-carry-the-approval`
- **Layers:** unit
- **WHEN** the same seed is rendered against two different approved versions
- **THEN** both renders exist
- **AND** neither overwrites the other

### Requirement: A prompt and a render record the flow's digest and the sheet they came from

The system SHALL record in every prompt and every render the digest of the flow's directory and the number
of the sheet the approval was made from. The number of the approval itself stays the producer's `from`.

A flow's identifier can mean two configurations across a re-pin, and only the digest tells them apart. The
sheet's number was recorded nowhere past the approval, so a render could name its approval but not the
sheet the person corrected.

#### Scenario: a render records its flow's digest and its sheet
- **Key:** `image-generation:provenance:the-flow-digest-and-the-sheet-are-recorded`
- **Layers:** unit
- **WHEN** a prompt and a render are written from an approval of a sheet whose number differs from the
  approval's
- **THEN** each records the flow's digest and the sheet's number
- **AND** the producer's `from` still names the approval

### Requirement: A render records the image and the runtime it ran on

The system SHALL record in every render the image reference a pod was booted from, and declare the render
pinned, when the pod-boot record names one; otherwise it SHALL record no image and declare the render
unpinned. It SHALL also record the ComfyUI, Python and PyTorch versions the endpoint reports about itself,
read once per session and only when a render will run.

The declared image says what should have run; the endpoint's own report says what did. Recording both is
what catches a pod that is not what the pin says, and an endpoint that is not a pod at all declares itself
unpinned rather than borrowing a pin it never had. Reading the report only when a render will run keeps a
completed batch inert.

#### Scenario: a render on a pinned pod records its image and runtime
- **Key:** `image-generation:runtime:a-pinned-pod-is-recorded`
- **Layers:** unit
- **WHEN** a render is written while the pod-boot record names an image
- **THEN** the render records that image and declares itself pinned
- **AND** it records the ComfyUI, Python and PyTorch versions the endpoint reported

#### Scenario: a render on an endpoint no pod-boot record names is unpinned
- **Key:** `image-generation:runtime:an-unrecorded-endpoint-is-unpinned`
- **Layers:** unit
- **WHEN** a render is written with no pod-boot record
- **THEN** the render records no image and declares itself unpinned

#### Scenario: a complete batch asks the endpoint nothing
- **Key:** `image-generation:runtime:a-complete-batch-reads-no-report`
- **Layers:** unit
- **WHEN** every requested seed is already rendered
- **THEN** the endpoint's report is not read
