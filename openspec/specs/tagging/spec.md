# Capability: `tagging`

## Purpose

Producing a list of Danbooru tags for a photograph, from a model given the photograph and nothing else,
stored raw and unnarrowed so the operator can see what was offered before any stage narrowed it. Two
taggers ship and they are not alike: one reaches a hosted model a flow's manifest declares, the other
opens a pinned file on this machine. Neither writes prose, neither is a reader, and neither may block
the other or the caption.

**Source:** `isekai/pipeline/tagging.py`, `isekai/boundary/wd14.py`, `isekai/boundary/ollama.py`,
`scripts/vocabulary.json` ·
**Tests:** `tests/test_tagging.py`, `tests/test_wd14.py`

## Requirements

### Requirement: A tagger is given the photograph and nothing else, and returns tags

The system SHALL pass a tagger exactly one input — the photograph — and SHALL NOT pass it a schema, a
field list, a vocabulary, a caption, a flow identifier or any prose. It SHALL accept exactly one output:
a list of tags.

This is the reader's own rule, applied to a different producer for the same measured reason. Pressing a
model into a schema is what makes it invent: instructed never to leave a field blank, a reader
manufactured nineteen identity marks across seven of ten subjects and its score fell from 0.518 to
0.307. A tagger is at greater risk than a reader, not less, because its output is already a list and a
field list would look like help. Withholding the caption also keeps the two producers independent: a
tagger shown the prose would agree with it, and agreement between two producers that saw the same text
is not corroboration.

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

**The reason changes with this version and gets stronger.** It used to be that the raw list was what a model
offered *before the sorter narrowed it*, and the sorter's narrowing was what the operator was trying to see
behind. There is no sorter now: the local tagger's list **is** the sheet's source, and the thing that
narrows it is a committed table that drops every tag no criterion can hold. So the raw artifact is the only
place the dropped tags survive — it is how the operator sees what the router refused, and it is what makes a
missing group in the table findable instead of invisible. A filtered artifact would leave the table's gaps
unobservable from disk, which is the one failure mode an authored artifact has.

The same rule still holds for a tagger whose output reaches no sheet: its list is advisory, it will contain
wrong tags, and nothing is dropped for being outside the vocabulary. Marking which tags a vocabulary
contains is a display concern and is not filtering — the surface may mark, and this stage may not drop.

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
record the digest of the prompt where the tagger was given one, and SHALL declare the artifact pinned
only where every artifact the tagger read is verified against a committed digest.

A producer that names only a model cannot explain its own result, and the instruction text is the
variable with the largest measured effect on what comes back. But a prompt held as a module constant has
no path, so the record carries its digest without claiming a location it does not have. The pin claim is
the sharper half: every producer in this build so far has been a hosted model exposing no immutable
revision, so every artifact has declared itself unpinned. A tagger reading a file whose bytes this
repository has committed a digest for is the first that can say otherwise, and a pin claimed where the
bytes were not checked would be worse than no claim at all.

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

### Requirement: The model and its label index are verified together or not used

The system SHALL verify the local tagger's model file and its label index against the digests this
repository commits before the first inference, SHALL refuse naming the command that would fetch either
when it is absent or its bytes differ, and SHALL NOT use one without the other.

They are one artifact split across two files: row N of the label index names output neuron N of the
model. A mismatched pair does not fail — it produces a complete, well-formed, confidently-scored tag
list in which every tag is the wrong tag, and nothing downstream could detect it. That is the worst
failure shape this stage has, and verifying the pair together is the only thing that closes it. Checking
at first use rather than at construction is what lets a machine that never tags avoid touching a
467 MB file.

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

The model this stage reads is nearly half a gigabyte and is not in the repository; a suite that needed
it would be a suite that does not run on a fresh clone, and the gate would silently stop covering this
capability. Proving that a completed stage makes no call also requires something that counts calls, which
is the same reason the reader has a double. The seam is at the boundary as well as at the stage, because
the preparation rule and the label-index ordering are logic that has to be tested and neither is
reachable through the stage's own double.

#### Scenario: the suite produces both tag artifacts with no network and no model file
- **Key:** `tagging:seam:offline-double-satisfies-the-interface`
- **Layers:** unit
- **WHEN** the stage runs with the test doubles in place
- **THEN** both tag artifacts are written
- **AND** no network call is attempted and no model file is opened

### Requirement: A failing tagger leaves every artifact produced before it complete

The system SHALL produce the caption, then the local tag list, then the hosted tag list, and a failure in
any of them SHALL NOT remove, prevent or invalidate an artifact an earlier one already wrote.

Failures are collected per photograph rather than per stage, so the first refusal ends that photograph's
work — which makes the order load-bearing rather than cosmetic. The caption is first because it is the
only one of the three anything downstream reads. The local tagger is second because it is deterministic
and reaches no network, so it cannot fail transiently. The hosted tagger is last because it is the only
one with a port, a timeout and a retry budget, and putting it anywhere else would let a host being down
cost a tag list that takes a second and cannot fail.

#### Scenario: a hosted tagger failure leaves the caption and the local tag list on disk
- **Key:** `tagging:order:a-late-failure-leaves-the-earlier-artifacts-complete`
- **Layers:** unit
- **WHEN** the hosted tagger fails for a photograph whose caption and local tag list succeeded
- **THEN** both of those artifacts are complete on disk
- **AND** the next invocation produces only the missing tag list

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
