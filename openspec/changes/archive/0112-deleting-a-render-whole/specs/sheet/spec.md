## ADDED Requirements

### Requirement: The stage fills fields from the tag list of a flow that declares the tagger, leaves them empty for a flow that declares none, and names no other flow

The system SHALL fill a sheet from a schema, a vocabulary, a field map and, for a flow that declares the tagger, the
photograph's local tag list, and SHALL store fields only. It SHALL NOT store an assembled prompt in a sheet, SHALL NOT
be told which flow requested the work beyond whether a tag list is expected and the flow's digest it records, SHALL
record no other flow, a first sheet a draft writes included, and SHALL NOT read prose. For a flow that declares the
tagger it SHALL refuse naming the verb that produces the tag list when that list is absent, and for a flow that declares
none it SHALL write every field empty, and the sheet's producer SHALL record that no tag list and no model filled it.
Every sheet SHALL record the digest of the flow it was filled for, and SHALL carry the tag list's confidence floor into
its producer where the list records one.

```
flow declares the tagger? ──yes──▶ photo/wd14/ holds a list? ──yes──▶ fill through the field map
         │                                  │
         no                                 no ──▶ refuse, naming the verb that produces it
         ▼
every field empty; the producer names no tag list and no model
```

A prompt stored in the sheet would be edited by a person and silently overwritten by a rebuild. The stage learns only
whether a tag list is expected and the flow's digest, which it records and never reads, so one stage serves every flow;
a sheet naming another flow would tie the two
([D50](../../../docs/decisions.md#d50--the-last-render-takes-its-approval-and-a-flow-holds-only-its-own-files)); the
digest ties a sheet to the schema it was filled against across a re-pin. Every flow reads the photograph's one tag list
([D17](../../../docs/decisions.md#d17--input-above-flow-below)). It reads a tag list, not prose, because a tagger whose
output layer is the vocabulary cannot name a tag outside it
([D2](../../../docs/decisions.md#d2--a-table-fills-the-sheet)). An empty sheet is legal and so silent: for a tagged flow
it would hide a tagger that never ran, and for a flow that declares none there is nothing to hide — a person fills it,
and approval still gates the render ([D31](../../../docs/decisions.md#d31--a-flow-declares-whether-it-is-tagged)).

#### Scenario: a sheet stores fields and no prompt
- **Key:** `sheet:output:sheet-stores-fields-only`
- **Layers:** unit
- **WHEN** a sheet is written
- **THEN** it carries one entry per schema field
- **AND** it carries no assembled prompt

#### Scenario: an empty field is a legal answer
- **Key:** `sheet:output:empty-field-is-legal`
- **Layers:** unit
- **WHEN** the tag list carries nothing a field can be filled from
- **THEN** that field is present and empty
- **AND** the sheet is not rejected for it

#### Scenario: the sheet records the vocabulary it was filled from
- **Key:** `sheet:output:sheet-names-its-vocabulary`
- **Layers:** unit
- **WHEN** a sheet is written
- **THEN** it records the vocabulary's name, revision and digest
- **AND** that record is what a later reader checks the fill against

#### Scenario: the sheet records the field map it was routed by
- **Key:** `sheet:output:sheet-names-its-field-map`
- **Layers:** unit
- **WHEN** a sheet is written
- **THEN** it records the field map's name, revision and digest beside the vocabulary's
- **AND** two sheets routed by different revisions of the table are distinguishable from the record alone

#### Scenario: the stage reads the tag list and not the prose
- **Key:** `sheet:output:the-stage-reads-the-tag-list`
- **Layers:** unit
- **WHEN** a sheet is filled for an input that has both a caption and a local tagger's list
- **THEN** the fields are filled from the tag list
- **AND** the caption is not read

#### Scenario: an absent tag list is a refusal naming the verb that fills it
- **Key:** `sheet:output:an-absent-tag-list-is-refused`
- **Layers:** unit
- **WHEN** a sheet is asked, for a flow that declares the tagger, for a photograph whose local tag list is absent
- **THEN** the stage refuses, naming the verb that would produce it
- **AND** no sheet is written

#### Scenario: a flow that declares no tagger gets a sheet with every field empty
- **Key:** `sheet:output:a-flow-without-a-tagger-gets-empty-fields`
- **Layers:** unit
- **WHEN** a sheet is asked for an input of a flow that declares no tagger
- **THEN** a sheet is written with every schema field present and empty
- **AND** its producer names no tag list and no model

#### Scenario: a sheet records the digest of the flow it was filled for
- **Key:** `sheet:output:sheet-names-its-flow-digest`
- **Layers:** unit
- **WHEN** a sheet is written, from a tag list or empty
- **THEN** it records the digest of the flow's directory
- **AND** two sheets filled for a flow before and after a re-pin are distinguishable from the record alone

#### Scenario: a sheet carries the tag list's floor
- **Key:** `sheet:output:sheet-carries-the-floor`
- **Layers:** unit
- **WHEN** a sheet is filled from a tag list whose producer records a confidence floor
- **THEN** the sheet's producer records the same floor
- **AND** a tag list that records none yields a sheet that records none

#### Scenario: a first sheet a draft writes names no source
- **Key:** `sheet:output:a-drafted-sheet-names-no-source`
- **Layers:** unit
- **WHEN** a draft from another flow's approval writes a target's first sheet
- **THEN** its fields are routed from the photograph's tag list through the target's schema and field map
- **AND** its producer names no other flow

### Requirement: A kept sheet filled from a tag list older than the photograph's newest is named, whoever filled it

When a flow that declares the tagger already has a sheet and no new version is asked for, the system SHALL write
nothing, and SHALL warn where the photograph holds a tag list numbered above the one its latest sheet was filled from,
naming both numbers and the command that fills a new sheet, whoever filled it. A kept sheet it cannot read SHALL leave
the command silent.

```
sheet, no new version asked, a sheet exists
        │
        ▼
photo/wd14/'s latest above the sheet's source? ──yes──▶ warn: both numbers, the command
        │
        no ──▶ silent
        ▼
nothing written, either way
```

`tag --new-version` writes a newer list and leaves the sheet filled from the old one, so "already complete" alone
hides it. The warning names the fix and changes nothing: a new version is an explicit act. A sheet that cannot be
read is refused by name at review. A first sheet a draft wrote is filled from the photograph's tag list like any
other, so a later list supersedes it too.

#### Scenario: a newer tag list is named
- **Key:** `sheet:superseded:a-newer-tag-list-is-named`
- **Layers:** unit
- **WHEN** the sheet verb runs without a new version for a flow whose photograph's latest tag list is above its sheet's
  source
- **THEN** nothing is written
- **AND** a warning names both numbers and the command that fills a new sheet

#### Scenario: a sheet from the latest list is silent
- **Key:** `sheet:superseded:the-latest-list-is-silent`
- **Layers:** unit
- **WHEN** the sheet verb runs without a new version for a flow whose sheet was filled from the photograph's latest
  tag list
- **THEN** nothing is written
- **AND** no warning is given

#### Scenario: a flow that declares no tagger is silent
- **Key:** `sheet:superseded:an-untagged-flow-is-silent`
- **Layers:** unit
- **WHEN** the sheet verb runs without a new version for a flow that declares no tagger
- **THEN** nothing is written
- **AND** no warning is given

#### Scenario: a kept sheet it cannot read is silent
- **Key:** `sheet:superseded:an-unreadable-sheet-is-silent`
- **Layers:** unit
- **WHEN** the sheet verb runs without a new version for a flow whose latest sheet cannot be read
- **THEN** nothing is written
- **AND** no warning is given

## REMOVED Requirements

### Requirement: The stage fills fields from the tag list of a flow that declares the tagger, and leaves them empty for a flow that declares none

**Reason**: a first sheet a draft writes no longer records the source flow
([D5](../../changes/0112-deleting-a-render-whole/design.md#d5)).
**Migration**: replaced by *The stage fills fields from the tag list of a flow that declares the tagger, leaves them
empty for a flow that declares none, and names no other flow*; an old sheet keeps its `tags_from`, unread.

### Requirement: A kept sheet filled from a tag list older than the photograph's newest is named

**Reason**: a sheet a draft wrote is weighed against a newer tag list like any other
([D5](../../changes/0112-deleting-a-render-whole/design.md#d5)).
**Migration**: replaced by *A kept sheet filled from a tag list older than the photograph's newest is named, whoever
filled it*; nothing on disk moves.
