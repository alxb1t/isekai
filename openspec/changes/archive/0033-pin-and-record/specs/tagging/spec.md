## MODIFIED Requirements

### Requirement: A tagger's producer names what made the artifact, and claims a pin only when it has one

The system SHALL record in each tag artifact's producer the implementation and the model that ran, SHALL
record the digest of the prompt where the tagger was given one, SHALL record the sampling options where
the tagger was sampled and the confidence floor where it filtered, and SHALL declare the artifact pinned
only where every artifact the tagger read is verified against a committed digest.

A producer that names only a model cannot explain its own result, and the instruction text is the
variable with the largest measured effect on what comes back. But a prompt held as a module constant has
no path, so the record carries its digest without claiming a location it does not have. The pin claim is
the sharper half: a pin claimed where the bytes were not checked would be worse than no claim at all. The
local tagger reads a file whose bytes this repository has committed a digest for; the hosted tagger's model
is checked against its pinned files before its first call, so it names those files and claims its pin too.

**The options and the floor are recorded because they are constants, not keys.** Neither is declared by a
flow, and both shape what the list holds: the options what the model answers, the floor which scored tags
are kept at all.

#### Scenario: the local tagger declares its pin and names both digests
- **Key:** `tagging:provenance:the-local-tagger-declares-its-pin`
- **Layers:** unit
- **WHEN** the local tagger writes an artifact
- **THEN** its producer declares the artifact pinned
- **AND** it names the digest of the model and the digest of the label index it read

#### Scenario: the hosted tagger records its prompt's digest without a path
- **Key:** `tagging:provenance:the-hosted-tagger-records-its-prompt-digest`
- **Layers:** unit
- **WHEN** a hosted tagger produced under a prompt held as a constant writes an artifact
- **THEN** its producer records that prompt's digest
- **AND** it records no path for it, and two artifacts produced under different prompts are
  distinguishable from the record alone

#### Scenario: the hosted tagger declares its pin and names both files
- **Key:** `tagging:provenance:the-hosted-tagger-declares-its-pin`
- **Layers:** unit
- **WHEN** a hosted tagger whose model was verified against the reader's manifest writes an artifact
- **THEN** its producer declares the artifact pinned
- **AND** it names the digest of the model file and of the projector file

#### Scenario: the hosted tagger records its options, and the local tagger its floor
- **Key:** `tagging:provenance:options-and-floor-are-recorded`
- **Layers:** unit
- **WHEN** each tagger writes an artifact
- **THEN** the hosted tagger's producer records the sampling options it sent, key for key
- **AND** the local tagger's producer records the confidence floor its list was filtered at

### Requirement: Both taggers run for a flow that declares the tagger, and the hosted one runs on the model the flow names

The system SHALL run both taggers for a flow whose manifest declares the tagger, SHALL resolve the local
tagger through no key that names its model, and SHALL resolve the hosted tagger on the model that flow's
manifest names. The tag verb SHALL refuse, before any artifact is written, an invocation naming a flow
whose manifest declares no tagger, naming the flow and the key. A hosted tagger that cannot reach its
model, or whose model is not built from the files the reader's manifest pins, SHALL refuse without
spending an attempt, and that refusal SHALL NOT prevent the local tag list from being written.

The two are not implementations of one thing and must not be made to look like one. The hosted tagger is
selected by a string in a frozen manifest, because which model answers is a claim the flow makes about
itself. The local tagger makes no such claim: it is a file this build pins, it costs nothing, it reaches
no network, and there is no flow for which it would be the wrong model. **Whether a flow is tagged at all
is a claim the flow does make**, now that flows needing no tag list are coming — so the manifest declares
it, and still names nothing about which model tags.

**The hosted tagger reads the same key the reader does, and that is a decision rather than an economy.**
One alias answers both prompts, which is why the tag prompt is not chat-framed — two calls to one model
must not arrive framed differently. A key of its own would let a flow be written in which the prose and
the hosted tags came from different models with nothing in the record saying which was which, and it
would say twice what the manifest already says once.

**A flow that declares no tagger is refused rather than skipped.** An operator who names it asked for work
the flow does not do; a skip would report success for a flow that wrote nothing, and the refusal says which
flow to drop from the command.

#### Scenario: the local tagger needs no model key
- **Key:** `tagging:independence:the-local-tagger-needs-no-model-key`
- **Layers:** unit
- **WHEN** any tracked flow is tagged
- **THEN** the local tagger's artifact is written
- **AND** the flow's manifest names none of the local tagger's files

#### Scenario: the hosted tagger runs the model the flow names
- **Key:** `tagging:independence:the-hosted-tagger-runs-the-flows-model`
- **Layers:** unit
- **WHEN** a flow is tagged
- **THEN** the hosted tag artifact's producer names the model that flow's manifest declares
- **AND** it is the same model the caption's producer names

#### Scenario: a flow that declares no tagger is refused by the tag verb
- **Key:** `tagging:declaration:a-flow-without-a-tagger-is-refused`
- **Layers:** unit
- **WHEN** the tag verb names a flow whose manifest declares no tagger
- **THEN** the invocation is refused before any artifact is written, naming the flow and the key
- **AND** no other flow named with it is tagged

#### Scenario: a hosted tagger on an unpinned build refuses and the local list is written
- **Key:** `tagging:independence:an-unpinned-hosted-model-costs-no-local-list`
- **Layers:** unit
- **WHEN** the hosted tagger's model is built from files the reader's manifest does not pin
- **THEN** the tag verb refuses the hosted list, naming both digests, and spends no attempt
- **AND** the local tag list is written
