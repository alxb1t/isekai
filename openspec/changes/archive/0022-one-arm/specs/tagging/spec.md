## ADDED Requirements

### Requirement: The local tagger runs for every flow, and the hosted one runs on the model the flow names

The system SHALL resolve the local tagger without reference to any manifest key, for every flow, and
SHALL resolve the hosted tagger on the model that flow's manifest names. A hosted tagger that cannot
reach its model SHALL refuse without spending an attempt, and that refusal SHALL NOT prevent the local
tag list from being written.

The two are not implementations of one thing and must not be made to look like one. The hosted tagger is
selected by a string in a frozen manifest, because which model answers is a claim the flow makes about
itself. The local tagger makes no such claim: it is a file this build pins, it costs nothing, it reaches
no network, and there is no flow for which it would be wrong. Requiring a manifest key for it would mean
re-pinning every existing flow to get a capability none of them declares an opinion about.

**The hosted tagger reads the same key the reader does, and that is a decision rather than an economy.**
One alias answers both prompts, which is why the tag prompt is not chat-framed — two calls to one model
must not arrive framed differently. A key of its own would let a flow be written in which the prose and
the hosted tags came from different models with nothing in the record saying which was which, and it
would say twice what the manifest already says once.

#### Scenario: the local tagger needs no manifest key
- **Key:** `tagging:independence:the-local-tagger-needs-no-manifest-key`
- **Layers:** unit
- **WHEN** any tracked flow is captioned
- **THEN** the local tagger's artifact is written
- **AND** the flow's manifest and its committed digest are unchanged

#### Scenario: the hosted tagger runs the model the flow names
- **Key:** `tagging:independence:the-hosted-tagger-runs-the-flows-model`
- **Layers:** unit
- **WHEN** a flow is captioned
- **THEN** the hosted tag artifact's producer names the model that flow's manifest declares
- **AND** it is the same model the caption's producer names

## REMOVED Requirements

### Requirement: The local tagger runs for every flow and the hosted one only where a flow declares it

**Reason:** Both of its scenarios describe *a flow whose manifest declares no hosted model*, and this
change makes that state unrepresentable — the model key is required of every flow. The requirement's
surviving half, that the local tagger resolves through no manifest key at all, is true and load-bearing
and is carried into the replacement; the half about an absent block is not merely unreachable but
describes a manifest the loader now refuses.

**Migration:** *The local tagger runs for every flow, and the hosted one runs on the model the flow
names*, in this change's ADDED block.
`tagging:independence:the-local-tagger-needs-no-manifest-key` keeps its key and its bindings, with its
WHEN widened from *a flow whose manifest declares no hosted model* to *any tracked flow*.
`tagging:independence:the-hosted-tagger-is-absent-without-a-hosted-block` is replaced by
`tagging:independence:the-hosted-tagger-runs-the-flows-model`, which asserts what the tagger now does
instead of the case in which it did nothing.
