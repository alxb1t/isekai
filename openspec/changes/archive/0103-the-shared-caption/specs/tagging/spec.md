## ADDED Requirements

### Requirement: Both taggers run over the photograph, and the hosted one runs on the reader's model

The system SHALL run both taggers over the photograph, once for every flow, SHALL resolve the local tagger through no
key that names its model, and SHALL resolve the hosted tagger on the model the reader runs, which the caption config
names. A hosted tagger that cannot reach its model, or whose model is not built from the files the reader's manifest
pins, SHALL refuse without spending an attempt, and that refusal SHALL NOT prevent the local tag list from being
written.

The two taggers are not one thing. The hosted tagger runs the model the caption config names, because which model
answers is a claim the library makes once; the local tagger is a file this build pins, costs nothing, reaches no network
and is never the wrong model. The hosted tagger runs the reader's model, so one alias answers both prompts, framed
alike, and no photograph's prose and hosted tags come from different models. Whether a flow's sheet reads the tags is
the manifest's own key ([D31](../../../docs/decisions.md#d31--a-flow-declares-whether-it-is-tagged)); the lists are the
photograph's either way, so tagging names no flow.

#### Scenario: the local tagger needs no model key
- **Key:** `tagging:independence:the-local-tagger-needs-no-model-key`
- **Layers:** unit
- **WHEN** a photograph is tagged
- **THEN** the local tagger's artifact is written
- **AND** no flow's manifest names any of the local tagger's files

#### Scenario: the hosted tagger runs the reader's model
- **Key:** `tagging:independence:the-hosted-tagger-runs-the-readers-model`
- **Layers:** unit
- **WHEN** a photograph is tagged
- **THEN** the hosted tag artifact's producer names the model the caption config names
- **AND** it is the same model the caption's producer names

#### Scenario: a hosted tagger on an unpinned build refuses and the local list is written
- **Key:** `tagging:independence:an-unpinned-hosted-model-costs-no-local-list`
- **Layers:** unit
- **WHEN** the hosted tagger's model is built from files the reader's manifest does not pin
- **THEN** the tag verb refuses the hosted list, naming both digests, and spends no attempt
- **AND** the local tag list is written

## MODIFIED Requirements

### Requirement: Each tagger has its own directory, its own budget and its own idempotence

The system SHALL write each tagger's output to its own directory under `photo/`, SHALL give each its own
retry budget, and SHALL decide each one's completeness independently of the others and of the caption.

The two taggers fail for unrelated reasons and at unrelated cost. One is a network call to a host that
may be down, timing out or returning a truncated body; the other is a deterministic pass over a file,
which either works or names a missing file. Sharing a completeness check between them would spend a
model call to retry a matrix multiplication, and sharing one with the caption would re-read a photograph
to recover a tag list. Separate directories are also what make the partial state legible in a listing
rather than by opening files: a run with prose and one tag list is one directory short, and the next
invocation produces exactly what is missing.

#### Scenario: one tagger's completeness does not decide another's
- **Key:** `tagging:independence:each-tagger-resumes-on-its-own`
- **Layers:** unit
- **WHEN** one tagger has written an artifact and another has not
- **THEN** re-running produces only the missing one
- **AND** the existing artifact is neither read nor rewritten

#### Scenario: a complete tagger makes no call
- **Key:** `tagging:independence:a-complete-tagger-makes-no-call`
- **Layers:** unit
- **WHEN** a tagger whose artifact already exists is run again without a new version being asked for
- **THEN** no call is made to the model
- **AND** nothing is written

#### Scenario: each tagger refuses on its own budget, naming its own directory
- **Key:** `tagging:budget:each-tagger-has-its-own-budget`
- **Layers:** unit
- **WHEN** a tagger has spent its attempts
- **THEN** the command refuses naming that tagger's own directory and the records in it
- **AND** the refusal is a named refusal rather than an unhandled error

### Requirement: Each tagger's failure is its own, and the local tagger runs first

The system SHALL produce the local tag list, then the hosted tag list, under the tag verb, and a failure
in either SHALL NOT remove, prevent or invalidate the other's artifact — whether the failure is the
photograph's or the build's. The caption verb SHALL write no tag list.

Failures are collected per photograph, and the local list is the sheet's only input, so a refusal of the prose or of
the hosted list must not cost it ([D1](../../../docs/decisions.md#d1--stage--is-two-independent-verbs)). Inside the
tag verb each tagger's refusal is collected on its own. The local tagger runs first because it is the sheet's input
and reaches no network.

#### Scenario: a hosted tagger failure leaves the local tag list on disk
- **Key:** `tagging:order:a-late-failure-leaves-the-earlier-artifacts-complete`
- **Layers:** unit
- **WHEN** the hosted tagger fails for a photograph whose local tag list succeeded
- **THEN** that list is complete on disk
- **AND** the next invocation produces only the missing tag list

#### Scenario: a local tagger failure leaves the hosted list written
- **Key:** `tagging:order:a-local-failure-leaves-the-hosted-list-written`
- **Layers:** unit
- **WHEN** the local tagger fails for a photograph, or cannot be opened at all
- **THEN** the hosted tagger still runs for that photograph and its list is written
- **AND** the command refuses naming the local tagger's failure

#### Scenario: captioning writes no tag list
- **Key:** `tagging:order:captioning-writes-no-tag-list`
- **Layers:** unit
- **WHEN** a photograph is captioned
- **THEN** the prose is written
- **AND** no tag list is written and no tagger is called

## REMOVED Requirements

### Requirement: Both taggers run for a flow that declares the tagger, and the hosted one runs on the reader's model

**Reason**: tagging names no flow: both taggers run over the photograph, whose lists every flow reads.

**Migration**: *Both taggers run over the photograph, and the hosted one runs on the reader's model* replaces it with
its other keys; `tagging:declaration:a-flow-without-a-tagger-is-refused` and
`tagging:declaration:only-untagged-flows-name-the-next-verb` go with the flow `tag` named. A flow that declares no
tagger still gets a sheet with every field empty.
