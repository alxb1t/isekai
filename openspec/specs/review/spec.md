# Capability: `review`

## Purpose

Stage ③: the operator corrects a filled sheet — an editable copy in a directory of its own, validated against the
vocabulary and approved by a rename — so the machine's sheet is never altered.

## Requirements

### Requirement: The machine's sheet is never edited; review works on a copy

The system SHALL take the sheet into a separate directory before any edit is possible, and SHALL NOT
provide any path by which the stage that filled the sheet has its output altered.

```
sheet directory ──review──▶ review directory: draft ──approve, a rename──▶ approved
(never edited)               (edited in place)                          (never overwritten)
```

The machine's sheet is the baseline the correction is measured against, and editing it in place destroys that
baseline on every run. Separate directories make the guarantee a property of the layout, not a rule a tool is
trusted to follow.

#### Scenario: review copies rather than edits
- **Key:** `review:copy:review-writes-to-its-own-directory`
- **Layers:** unit
- **WHEN** review is invoked for a run and a flow
- **THEN** an editable copy is written into the review directory
- **AND** no file in the sheet directory is created, changed or removed

#### Scenario: review takes the highest available sheet
- **Key:** `review:copy:highest-sheet-is-copied`
- **Layers:** unit
- **WHEN** more than one sheet version exists for a flow
- **THEN** the highest-numbered one is copied
- **AND** the copy records which sheet version it came from

#### Scenario: reviewing again appends rather than replaces
- **Key:** `review:copy:second-review-appends`
- **Layers:** unit
- **WHEN** review is invoked for a flow that already has an approved copy
- **THEN** a new numbered draft is written from the approved one
- **AND** the existing approved copy is left exactly as it was

### Requirement: Saving is not approving

The system SHALL treat an edited but unapproved copy as a draft, SHALL leave it editable for as long as
the operator wants, and SHALL make approval a separate, explicit act.

A sheet must be parkable half-edited, because the whole reason the two directories exist is that sheets
diverge under human editing over minutes or days. Approval being its own act is also what lets the
directory listing answer whether the stage is finished.

#### Scenario: a draft is not treated as complete
- **Key:** `review:approval:draft-is-not-done`
- **Layers:** unit
- **WHEN** a draft exists and has not been approved
- **THEN** the stage is reported as not complete
- **AND** downstream stages refuse to proceed from it

#### Scenario: approval renames rather than rewrites
- **Key:** `review:approval:approve-validates-then-renames`
- **Layers:** unit
- **WHEN** a draft is approved
- **THEN** the artifact's bytes are unchanged and its name declares it approved
- **AND** approval is decidable from the filename alone

#### Scenario: the approved artifact is never silently replaced
- **Key:** `review:approval:approved-is-not-overwritten`
- **Layers:** unit
- **WHEN** an approved artifact exists for a flow
- **THEN** no command overwrites it
- **AND** producing a corrected version means writing the next number

### Requirement: Approval validates every tag against the vocabulary and refuses on an unknown one

The system SHALL check every tag in every field against the vocabulary at approval, SHALL refuse
approval naming each tag that is not in it, and SHALL state the reason honestly — that the tag is not
in the vocabulary's prediction set, rather than that it is not a real tag.

A tag that merely looks canonical passes every later check on its way into the prompt, so approval is
the last place it can be caught. The honest wording matters: the vocabulary is the set the tag list
predicts, which is a subset of the wider tag corpus, so calling an absent tag unreal overclaims.

#### Scenario: an unknown tag refuses approval
- **Key:** `review:validation:unknown-tag-refuses-approval`
- **Layers:** unit
- **WHEN** a draft contains a tag absent from the vocabulary
- **THEN** approval is refused naming that tag and its field
- **AND** the draft is left untouched for the operator to correct

#### Scenario: the refusal does not overclaim
- **Key:** `review:validation:message-states-the-prediction-set`
- **Layers:** unit
- **WHEN** approval is refused for an unknown tag
- **THEN** the message says the tag is not in the vocabulary's prediction set
- **AND** it does not assert that the tag does not exist

#### Scenario: a missing field refuses approval
- **Key:** `review:validation:missing-field-refuses-approval`
- **Layers:** unit
- **WHEN** a draft does not carry every field the schema declares
- **THEN** approval is refused naming the missing fields
- **AND** an empty field is not treated as missing

### Requirement: Approval warns when the assembled prompt exceeds the encoder's window

The system SHALL estimate the assembled prompt's token count at approval and SHALL warn — not refuse —
when it exceeds the text encoder's window.

A prompt past the window is silently chunked and averaged, so the operator is told. It is a warning, not a
refusal, because the sheet is the truth of what the render was asked to contain; deleting fields to fit would hide
whether a criterion survived.

#### Scenario: an over-long prompt warns and still approves
- **Key:** `review:budget:over-window-warns-not-refuses`
- **Layers:** unit
- **WHEN** the assembled prompt's estimated tokens exceed the encoder's window
- **THEN** a warning states the estimate and the window
- **AND** approval still succeeds

### Requirement: The approved artifact records whether a human changed anything

The system SHALL record on the approved artifact whether its content differs from the sheet it was
copied from.

Whether a sheet was corrected decides which route a render measures, and without this record it is an assumption
rather than a fact on disk. It also lets the machine's draft be rendered as a control — approved unedited, and
recorded as such.

#### Scenario: an untouched copy is recorded as unedited
- **Key:** `review:provenance:unedited-copy-is-declared`
- **Layers:** unit
- **WHEN** a draft is approved without having been changed
- **THEN** the artifact records that it was not edited
- **AND** it records the sheet version it came from

#### Scenario: a changed copy is recorded as edited
- **Key:** `review:provenance:edited-copy-is-declared`
- **Layers:** unit
- **WHEN** a draft's content differs from its source sheet
- **THEN** the artifact records that it was edited
- **AND** the record does not depend on the operator having said so

### Requirement: This stage refuses to the operator and writes no error record

The system SHALL report a refusal from review or approval to the operator and exit with a failure
status, and SHALL NOT write an error record or consume a retry budget for it.

Error records keep a batch from halting on one photograph. Review has no batch and no unattended retry: the
operator is present, and a refusal is a message to them, not state for a later resume.

#### Scenario: a refusal is reported and leaves no error record
- **Key:** `review:refusal:no-error-record-is-written`
- **Layers:** unit
- **WHEN** review or approval refuses
- **THEN** the reason is reported and the command exits with a failure status
- **AND** no error record is written into the run directory

### Requirement: A draft is updated in place by one function, and a changed field set is refused

The system SHALL provide one way to replace a draft's field values in place, SHALL leave the draft's
version number and the sheet it records as its source unchanged, and SHALL refuse an update whose set of
field names differs from the set the draft already carries.

A second writer without a single owner is how two envelopes drift apart in one directory. Checking the field set at
the one write point turns a missing field and a field the schema lacks from a property the editing surface is
trusted to have into a property of the pipeline, at the cost of one comparison.

#### Scenario: an update replaces the values and keeps the version
- **Key:** `review:draft-update:values-are-replaced-in-place`
- **Layers:** unit
- **WHEN** a draft's field values are updated
- **THEN** the draft keeps its version number and the sheet version it records
- **AND** no new artifact is created in the review directory

#### Scenario: an update that adds or drops a field is refused
- **Key:** `review:draft-update:a-changed-field-set-is-refused`
- **Layers:** unit
- **WHEN** an update is submitted whose field names differ from the draft's
- **THEN** it is refused
- **AND** the draft on disk is unchanged

#### Scenario: an update against a flow with no draft is refused
- **Key:** `review:draft-update:no-draft-refuses-the-update`
- **Layers:** unit
- **WHEN** an update is submitted for a flow whose review directory holds no draft
- **THEN** it is refused
- **AND** nothing in the review directory is created

### Requirement: The token budget is counted over the prompt the renderer reads

The system SHALL report a sheet's token cost as a count over the assembled positive prompt — the flow's
prefix, the sheet's tags and the flow's trailer, joined as the renderer joins them — and SHALL report
alongside it each field's own share of that count and the fixed overhead that is not any field's.

The count is steered by while a sheet is corrected, when tags are added and the budget is crossed. A count that
omits the prefix and trailer understates what the text encoder reads, so a sheet reported inside the budget can be
past it and silently chunked. The shares and the overhead come from the same call, so they sum to the total and
answer the operator's real question: which tag goes.

#### Scenario: the total is the assembled prompt's, not the tags' alone
- **Key:** `review:budget:count-covers-the-assembled-prompt`
- **Layers:** unit
- **WHEN** a sheet's token budget is reported for a flow
- **THEN** the total accounts for the flow's prompt prefix and trailer as well as the sheet's tags

#### Scenario: the per-field shares and the overhead reconcile with the total
- **Key:** `review:budget:shares-and-overhead-sum-to-the-total`
- **Layers:** unit
- **WHEN** a sheet's token budget is reported
- **THEN** the per-field shares and the stated overhead sum to the total
- **AND** a field with no tags contributes nothing

#### Scenario: a field absent from the sheet does not fail the count
- **Key:** `review:budget:an-absent-field-is-counted-as-empty`
- **Layers:** unit
- **WHEN** a token budget is reported for a sheet that is missing one of the schema's fields
- **THEN** the count succeeds
- **AND** the absent field contributes nothing to the total

### Requirement: A draft carries the sheet's schema document and field map through to its approval

The system SHALL copy into each draft the schema document and the field map the sheet records, and SHALL
copy them from the draft into the approval, where the sheet records them.

The approval is what the render reads, and a person's corrections are checked against the sheet's schema and
vocabulary. The field map routed the sheet before any correction; carrying it forward keeps the approval
able to say, from its own record, which table the fields it started from came through.

#### Scenario: an approval names the schema document and field map of its sheet
- **Key:** `review:copy:the-sheet-records-are-carried`
- **Layers:** unit
- **WHEN** a sheet recording a schema document and a field map is copied to a draft and approved
- **THEN** the draft and the approval each record the same schema document and field map
- **AND** a sheet that records no field map yields a draft and an approval that record none

### Requirement: An approval is copied from another flow's approval, recording where it came from

When the operator names a source flow, the system SHALL write an approval under the target flow whose fields
are the source flow's latest approval's, validated against the target flow's schema and the vocabulary as any
approval is, and whose record names the source flow and the approval it was copied from. It SHALL refuse a
run whose source flow has no approval, naming the way out. It SHALL write nothing where the target's latest
approval is already a copy of the source's latest, and SHALL otherwise copy under the target's next number. It
SHALL refuse a source that is the target itself or no tracked flow, before any run is opened.

```
runs/<id>/summon-anime-wai/review/001.approved.json
        │  approve --flow control-anime-wai --from summon-anime-wai <run>
        ▼
runs/<id>/control-anime-wai/review/001.approved.json   same fields; the record names the source
```

Two flows are compared only on one prompt. A copy by hand carries the source's identifier and lies about its
provenance; a second approval by hand lets the prompts drift and voids the comparison. The target's own
validation is what keeps the copy honest: a schema the fields do not fit refuses as it would any draft. A
source approved again after a copy would otherwise leave the target on the old sheet with nothing saying so.

#### Scenario: the fields are copied and validated against the target
- **Key:** `review:copy-from:fields-are-copied-and-validated`
- **Layers:** unit
- **WHEN** a target flow is approved from a source flow's approval
- **THEN** the target's approval carries the source's fields
- **AND** a field the target's schema does not declare refuses the copy naming it

#### Scenario: the record names its origin
- **Key:** `review:copy-from:the-origin-is-recorded`
- **Layers:** unit
- **WHEN** a target flow is approved from a source flow's approval
- **THEN** the approval's identifier is the target flow's
- **AND** its record names the source flow and the source approval's version

#### Scenario: no source approval refuses the copy
- **Key:** `review:copy-from:no-source-approval-is-refused`
- **Layers:** unit
- **WHEN** the source flow holds no approval for the run
- **THEN** the copy is refused naming the source flow and the command that approves it

#### Scenario: a copy already in step writes nothing
- **Key:** `review:copy-from:an-approved-target-writes-nothing`
- **Layers:** unit
- **WHEN** the target's latest approval is a copy of the source's latest approval
- **THEN** nothing is written
- **AND** the existing approval is unchanged

#### Scenario: a newer source approval is copied again
- **Key:** `review:copy-from:a-newer-source-approval-is-copied-again`
- **Layers:** unit
- **WHEN** the source holds an approval newer than the one the target's latest was copied from
- **THEN** the source's latest is copied under the target's next number
- **AND** the target's earlier approval is unchanged

#### Scenario: the source is a tracked flow other than the target
- **Key:** `review:copy-from:the-source-is-another-tracked-flow`
- **Layers:** unit
- **WHEN** the source named is the target itself or no tracked flow
- **THEN** the invocation is refused naming it
- **AND** no run is opened

### Requirement: A draft carries how many images to render and which seeds, and approval checks them

The system SHALL carry in a draft, and into its approval, a count of images and a list of seeds, SHALL read a draft
or approval without them as a count of one and no seeds, and SHALL refuse approval of a count below the number of
seeds listed, a seed outside the range a render accepts, or a seed listed twice, naming the field.

What the operator approves includes how many attempts the sheet gets and at which seeds. An old draft reads as it
always rendered. A seed listed twice would render one image twice.

#### Scenario: an old draft reads as one image
- **Key:** `review:renders:an-old-draft-reads-as-one`
- **Layers:** unit
- **WHEN** a draft without a count or seeds is read
- **THEN** it reads as a count of one and no seeds

#### Scenario: a count below its seeds is refused
- **Key:** `review:renders:a-count-below-its-seeds-is-refused`
- **Layers:** unit
- **WHEN** approval is asked for a draft with a count of one and two seeds
- **THEN** it is refused naming the count

#### Scenario: a seed out of range is refused
- **Key:** `review:renders:a-seed-out-of-range-is-refused`
- **Layers:** unit
- **WHEN** approval is asked for a draft with a negative seed
- **THEN** it is refused naming the seed

#### Scenario: a repeated seed is refused
- **Key:** `review:renders:a-repeated-seed-is-refused`
- **Layers:** unit
- **WHEN** approval is asked for a draft listing seed 144 twice
- **THEN** it is refused naming the seed

### Requirement: A revision is a draft from the approval that made the image, its seed prefilled

The system SHALL write, for a rendered image, the next numbered draft of its flow copied from the approval the image was
rendered under — whether or not that is the newest — naming that approval in its producer, with a count of one and the
image's seed listed, and recording the image itself — its flow, version and seed — which the approval keeps. It SHALL
refuse, naming why, while the flow holds an unapproved draft.

A revision starts from what the operator looked at, not from what came after it. Keeping the seed puts the edited sheet
on the same composition; the seed stays editable, so a re-roll is the same act. The image is recorded apart from the
seeds, so an edited seed never loses it.

#### Scenario: a revision copies the image's approval and keeps its seed
- **Key:** `review:revise:a-revision-copies-the-images-approval`
- **Layers:** unit
- **WHEN** an image rendered under approval one is revised after approval two exists
- **THEN** the new draft's fields are approval one's and its producer names approval one
- **AND** its count is one and its seeds are the image's seed

#### Scenario: a revision records its image, and its approval keeps it
- **Key:** `review:revise:a-revision-records-its-image`
- **Layers:** unit
- **WHEN** an image is revised, its seed changed, and the draft approved
- **THEN** the draft and the approval record the image's flow, version and seed

#### Scenario: a waiting draft refuses a revision
- **Key:** `review:revise:a-waiting-draft-refuses`
- **Layers:** unit
- **WHEN** an image is revised while its flow holds an unapproved draft
- **THEN** the revision is refused naming that draft
- **AND** no file is written

### Requirement: Approval refuses a revision that would reproduce its images

The system SHALL refuse approval of a draft copied from an approval when its fields are that approval's and every
image it would render is of a seed that approval lists or rendered, naming the images it would reproduce.

An unchanged revision renders images that already exist, so refusing costs nothing and rendering costs money. A seed
the approval neither lists nor rendered is a change, and so is a count above the listed seeds, which draws new ones.

#### Scenario: an unchanged revision is refused
- **Key:** `review:revise:an-unchanged-revision-is-refused`
- **Layers:** unit
- **WHEN** approval is asked for a revision with its approval's fields and only seeds that approval lists or rendered
- **THEN** it is refused naming the images it would reproduce

#### Scenario: new seeds alone are a change
- **Key:** `review:revise:new-seeds-alone-are-a-change`
- **Layers:** unit
- **WHEN** approval is asked for a revision whose only difference is a seed its approval neither lists nor rendered
- **THEN** it is approved

### Requirement: An unapproved draft can be discarded

The system SHALL delete a flow's highest-numbered draft when asked, only while it is unapproved, and SHALL refuse,
naming the approval, when that number is approved.

A waiting draft blocks a revision; deleting the operator's own unfinished edit is the way out, and the one deletion
review makes.

#### Scenario: a draft is discarded
- **Key:** `review:discard:a-draft-is-discarded`
- **Layers:** unit
- **WHEN** a flow's highest draft is unapproved and is discarded
- **THEN** that draft is gone and every approval is unchanged

#### Scenario: an approval is never discarded
- **Key:** `review:discard:an-approval-is-never-discarded`
- **Layers:** unit
- **WHEN** discarding is asked for a flow whose highest number is approved
- **THEN** it is refused and no file changes

### Requirement: An approval nothing derives from can be cancelled back to its draft

The system SHALL cancel a flow's newest approval by writing the draft it was approved from — its fields, renders,
sheet, vocabulary, schema document and field map, and its producer without what approval added — and then deleting
the approval, leaving every older approval in place, and SHALL cancel an approval that is itself a copy by deleting
it, naming what the flow is left on: the draft open above what lies beneath, else the approval beneath, which stays
approved. It SHALL refuse, writing nothing and naming the reason and a way on that succeeds, while anything derives
from the approval — a prompt, a render group or a failure record numbered for it, or another flow's approval copied
from it — and while a later draft exists, naming a waiting draft rather than its discard while anything derives. A
cancel interrupted between its writing and its deleting SHALL be finished by running it again.

An approved artifact is never silently replaced: cancelling is an explicit act, and it is refused once anything has
been made from the approval, so no output loses the sheet that made it. A copy has no draft of its own, and `approve
--from` copies the source's newest approval again; deleting it takes back only the copy, so what it was written over
stands. A draft written before the delete leaves a crash reading as still approved, which approving already does.

```
NNN.approved.json ─▶ write NNN.draft.json ─▶ delete NNN.approved.json
                         crash here: both on disk, read as approved; cancel again finishes
```

#### Scenario: a cancel restores the draft
- **Key:** `review:cancel:a-cancel-restores-the-draft`
- **Layers:** unit
- **WHEN** an approval nothing derives from is cancelled
- **THEN** its draft holds the approval's fields and renders, and the approval is gone
- **AND** the flow reads as a draft

#### Scenario: an older approval stays
- **Key:** `review:cancel:an-older-approval-stays`
- **Layers:** unit
- **WHEN** a revision approved over a rendered approval is cancelled
- **THEN** the older approval is unchanged and the flow reads as re-opened

#### Scenario: anything made from it refuses the cancel
- **Key:** `review:cancel:anything-made-from-it-refuses`
- **Layers:** unit
- **WHEN** a cancel is asked while a prompt, a render group or a failure record is numbered for the approval
- **THEN** it is refused naming what derives and the way on
- **AND** no file changes
- **AND** with a draft waiting above it, that draft is named rather than its discard

#### Scenario: a copy taken from it refuses the cancel
- **Key:** `review:cancel:a-copy-taken-from-it-refuses`
- **Layers:** unit
- **WHEN** another flow's approval is copied from the approval
- **THEN** the cancel is refused naming that flow's cancel
- **AND** once that copy is cancelled, the cancel succeeds

#### Scenario: a copy is deleted, and a re-opened sheet is refused
- **Key:** `review:cancel:a-copy-is-deleted-and-a-reopened-sheet-refused`
- **Layers:** unit
- **WHEN** a cancel is asked for an approval with a later draft, then for a copy over the flow's own approval
- **THEN** the first is refused naming its draft's discard, and the copy alone is deleted
- **AND** the cancel names the approval beneath, and the flow reads as approved
- **AND** copying again writes the same copy

#### Scenario: an interrupted cancel finishes when run again
- **Key:** `review:cancel:an-interrupted-cancel-finishes`
- **Layers:** unit
- **WHEN** a flow holds an approval and the draft a cancel wrote beside it
- **THEN** it reads as approved, and cancelling again leaves only the draft

### Requirement: A draft is written from another flow's approval, its own fields from its own sheet

When the operator names a source flow and one of its approvals, the system SHALL write the target flow's draft whose
every field both flows' schemas declare is the source approval's, and whose every other field the target declares is the
target's newest sheet's, recording the target's sheet and the source flow and approval it was drafted from, and, where
the operator names one of that approval's images, the image itself — its flow, version and seed. It SHALL approve that
draft as an ordinary approval of the target, never as a copy. It SHALL refuse, naming the way out: a target holding no
sheet; a source holding no such approval; a named image that approval never rendered; a source that is the target or
no tracked flow; and a waiting draft of the target whose fields differ from its sheet's or that renders anything but one
drawn seed. A waiting draft equal to its
sheet, rendering one drawn seed, SHALL be replaced at its own number. The system SHALL refuse cancelling a source
approval while a target approval or waiting draft drafted from it stands, naming the target's cancel or the command that
discards that draft.

```
source approval vN ──▶ every field both declare ─┐
target newest sheet ──▶ every field it alone has ┴─▶ target draft · drafted from source vN
```

The operator corrects a sheet once, in the flow that reads the photograph, and finishes only the fields another flow
adds. A draft the operator never touched holds no work, so replacing it loses nothing; an edited one does, and a
count, a seed or a revision's seed is an edit. A target draft or approval names the source approval it was drafted
from, so that approval stands while the record does, as a copy's source does.

#### Scenario: the shared fields come from the source and the rest from the sheet
- **Key:** `review:draft-from:the-shared-fields-come-from-the-source`
- **Layers:** unit
- **WHEN** a target is drafted from a source approval
- **THEN** each field both flows declare holds the source approval's tags
- **AND** each field only the target declares holds its sheet's tags

#### Scenario: the draft names where it came from
- **Key:** `review:draft-from:the-draft-names-where-it-came-from`
- **Layers:** unit
- **WHEN** a target is drafted from a source approval
- **THEN** its record names the target's sheet, the source flow and the source approval's version

#### Scenario: its approval is an ordinary approval
- **Key:** `review:draft-from:its-approval-is-an-ordinary-approval`
- **Layers:** unit
- **WHEN** a draft written from a source approval that differs from the target's sheet is approved
- **THEN** the approval is written, recorded as edited
- **AND** its record names no copy
- **AND** cancelling it restores the draft, still naming where it came from

#### Scenario: a target with no sheet is refused
- **Key:** `review:draft-from:a-target-with-no-sheet-is-refused`
- **Layers:** unit
- **WHEN** the target holds no sheet
- **THEN** it is refused naming the command that assigns the target, then Prepare
- **AND** no file is written

#### Scenario: a missing source approval is refused
- **Key:** `review:draft-from:a-missing-source-approval-is-refused`
- **Layers:** unit
- **WHEN** the source holds no approval of the version named
- **THEN** it is refused naming the source flow and that version

#### Scenario: an unedited waiting draft is replaced
- **Key:** `review:draft-from:an-unedited-waiting-draft-is-replaced`
- **Layers:** unit
- **WHEN** the target's waiting draft holds its sheet's fields
- **THEN** a draft from the source approval is written at that draft's number

#### Scenario: an edited waiting draft is refused
- **Key:** `review:draft-from:an-edited-waiting-draft-is-refused`
- **Layers:** unit
- **WHEN** the target's waiting draft differs from its sheet, lists seeds, or asks for more than one image
- **THEN** it is refused naming that draft and the command that discards it
- **AND** the draft is unchanged

#### Scenario: what is drafted from it refuses the source's cancel
- **Key:** `review:draft-from:what-is-drafted-from-it-refuses-the-sources-cancel`
- **Layers:** unit
- **WHEN** a cancel is asked for a source approval a target approval or waiting draft was drafted from
- **THEN** it is refused naming the target's cancel, or its draft's discard, and no file changes
- **AND** once the target's approval is cancelled and its draft discarded, the source's cancel succeeds

#### Scenario: a draft from an image records it
- **Key:** `review:draft-from:a-draft-from-an-image-records-it`
- **Layers:** unit
- **WHEN** a target is drafted from a source approval naming one of its images
- **THEN** the draft records that image's flow, version and seed
- **AND** a draft naming no image records none

#### Scenario: an image the approval never rendered is refused
- **Key:** `review:draft-from:an-image-the-approval-never-rendered-is-refused`
- **Layers:** unit
- **WHEN** a target is drafted from a source approval naming a seed it rendered no image for
- **THEN** it is refused naming that seed and the command that lists the rendered seeds
- **AND** no file is written
