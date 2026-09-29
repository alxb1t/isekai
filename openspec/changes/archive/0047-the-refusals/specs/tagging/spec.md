## MODIFIED Requirements

### Requirement: Both taggers run for a flow that declares the tagger, and the hosted one runs on the model the flow names

The system SHALL run both taggers for a flow whose manifest declares the tagger, SHALL resolve the local
tagger through no key that names its model, and SHALL resolve the hosted tagger on the model that flow's
manifest names. The tag verb SHALL refuse, before any artifact is written, an invocation naming a flow
whose manifest declares no tagger, naming the flow and the key. A hosted tagger that cannot reach its
model, or whose model is not built from the files the reader's manifest pins, SHALL refuse without
spending an attempt, and that refusal SHALL NOT prevent the local tag list from being written.

The two taggers are not one thing. The hosted tagger is chosen by a string in a frozen manifest, because which model
answers is a claim the flow makes; the local tagger is a file this build pins, costs nothing, reaches no network and
is never the wrong model. The hosted tagger reads the reader's key, so one alias answers both prompts, framed alike,
and no flow can take its prose and its hosted tags from different models. Whether a flow is tagged is the
manifest's own key ([D31](../../../docs/decisions.md#d31--a-flow-declares-whether-it-is-tagged)); a flow that
declares none is refused, not skipped, because a skip reports success for a flow that wrote nothing.

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

#### Scenario: a command naming only untagged flows names the next verb
- **Key:** `tagging:declaration:only-untagged-flows-name-the-next-verb`
- **Layers:** unit
- **WHEN** the tag verb names only flows whose manifests declare no tagger
- **THEN** the invocation is refused, saying `tag` has nothing to do for them
- **AND** the message names the `sheet` command to run next
