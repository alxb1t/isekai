# Capability: `tagging`

## Purpose

Producing a raw list of Danbooru tags for a photograph, from a model given the photograph alone, stored unnarrowed
so the operator sees what was offered. Two taggers ship — a hosted one the flow's manifest names and a local one
reading a pinned file — and neither blocks the other or the caption.

## Requirements

### Requirement: A tagger is given the photograph and nothing else, and returns tags

The system SHALL pass a tagger exactly one input — the photograph — and SHALL NOT pass it a schema, a
field list, a vocabulary, a caption, a flow identifier or any prose. It SHALL accept exactly one output:
a list of tags.

Pressing a model into a schema makes it invent: told never to leave a field blank, a reader manufactures identity
marks. A tagger is at greater risk, because its output is already a list and a field list would look like help.
Withholding the caption keeps the two producers independent: a tagger shown the prose agrees with it, and that is
not corroboration.

#### Scenario: the tagger receives the photograph and nothing else
- **Key:** `tagging:inputs:only-the-photograph-is-passed`
- **Layers:** unit
- **WHEN** a tag list is produced
- **THEN** the tagger receives the photograph
- **AND** it receives no schema, no field list, no vocabulary, no caption and no flow identifier

#### Scenario: the artifact holds a list of tags
- **Key:** `tagging:output:artifact-is-a-list-of-tags`
- **Layers:** unit
- **WHEN** a tag artifact is written
- **THEN** its body is a list of tags, one entry per tag
- **AND** no prose and no field structure is stored alongside them

### Requirement: The list is stored as it came, and narrowing it is another stage's job

The system SHALL store a tagger's output without canonicalising it, without filtering it against any
vocabulary and without re-ordering it by anything other than a score the tagger itself returned.

The local list is the sheet's source, and a committed table narrows it by dropping every tag no criterion holds
([D2](../../../docs/decisions.md#d2--a-table-fills-the-sheet)). The raw artifact is the only place the dropped tags
survive, so it shows what the router refused and makes a gap in the table findable from disk. A list that reaches no
sheet is advisory and keeps its wrong tags too. Marking which tags a vocabulary holds is display, not filtering: the
surface may mark, and this stage may not drop.

#### Scenario: nothing is dropped for being outside the vocabulary
- **Key:** `tagging:output:the-list-is-stored-unnarrowed`
- **Layers:** unit
- **WHEN** a tagger returns tags that are not in the flow's pinned vocabulary
- **THEN** every one of them is stored
- **AND** the stored order is the tagger's own

### Requirement: An answer that is not a list at all is a permanent failure

The system SHALL treat a hosted tagger's response that contains no separator as unusable, SHALL record
it as a permanent failure, and SHALL write no artifact for it.

A wrong tag is not an error here — the list is advisory and the operator has accepted that it will
contain wrong tags. What must be caught is a different thing: a model that answers in prose yields one
element the length of a paragraph, which no chip can render and which is indistinguishable from a
single legitimate tag to anything that does not look. This is the smallest test that separates *wrong*
from *not a list*, and it touches no content, which is what keeps the previous requirement true.

#### Scenario: a prose answer is refused rather than stored as one enormous tag
- **Key:** `tagging:failure:a-response-with-no-comma-is-permanent`
- **Layers:** unit
- **WHEN** a hosted tagger returns a response containing no separator
- **THEN** the failure is recorded as permanent
- **AND** no tag artifact is written

### Requirement: Each tagger has its own directory, its own budget and its own idempotence

The system SHALL write each tagger's output to its own directory under the flow, SHALL give each its own
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

### Requirement: A tagger's producer names what made the artifact, and claims a pin only when it has one

The system SHALL record in each tag artifact's producer the implementation and the model that ran, SHALL
record the digest of the prompt where the tagger was given one, SHALL record the sampling options where
the tagger was sampled and the confidence floor where it filtered, and SHALL declare the artifact pinned
only where every artifact the tagger read is verified against a committed digest.

A producer that names only a model cannot explain its result. The instruction text shapes what comes back, and a
prompt held as a module constant has no path, so the record carries its digest alone. A pin claimed over unchecked
bytes is worse than none: the local tagger reads a file whose digest is committed, and the hosted tagger's model is
checked against its pinned files before its first call
([D6](../../../docs/decisions.md#d6--ollama-at-a-fixed-local-address-on-a-checked-model)). The options and the floor are
constants, not manifest keys, and both shape what the list holds.

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

### Requirement: The model and its label index are verified together or not used

The system SHALL verify the local tagger's model file and its label index against the digests this
repository commits before the first inference, SHALL refuse naming the command that would fetch either
when it is absent or its bytes differ, and SHALL NOT use one without the other.

They are one artifact in two files: row N of the label index names output N of the model
([D7](../../../docs/decisions.md#d7--wd14-is-one-artifact-in-two-files)). A mismatched pair does not fail — it yields a
well-formed, confidently scored list in which every tag is wrong, and nothing downstream can tell. Checking at first
use lets a machine that never tags leave the model file unopened.

#### Scenario: a model and label index from different revisions are refused
- **Key:** `tagging:pin:the-label-index-and-the-model-are-verified-together`
- **Layers:** unit
- **WHEN** the model file or the label index does not match the digest this build commits for it
- **THEN** the command refuses naming what to fetch and where it belongs
- **AND** no inference is attempted and no attempt is recorded

#### Scenario: the check does not fire until a flow asks
- **Key:** `tagging:pin:the-check-fires-at-first-use`
- **Layers:** unit
- **WHEN** a wiring is composed and no tagging is performed
- **THEN** no model file is opened and no digest is computed

### Requirement: The tagger is an injectable seam with an offline stand-in

The system SHALL reach every tagger through an interface a test double satisfies, so the suite exercises
this stage with no network call and without the model file present, and the double SHALL make it
provable that a complete stage made no call.

The model is not in the repository, and a suite that needed it would not run on a fresh clone, so the gate would
silently stop covering this stage. Proving that a complete stage made no call needs something that counts calls.
The seam sits at the boundary as well as at the stage, because the preparation rule and the label-index ordering
are logic the stage's own double does not reach.

#### Scenario: the suite produces both tag artifacts with no network and no model file
- **Key:** `tagging:seam:offline-double-satisfies-the-interface`
- **Layers:** unit
- **WHEN** the stage runs with the test doubles in place
- **THEN** both tag artifacts are written
- **AND** no network call is attempted and no model file is opened

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
- **WHEN** a flow is captioned
- **THEN** the prose is written
- **AND** no tag list is written and no tagger is called

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
