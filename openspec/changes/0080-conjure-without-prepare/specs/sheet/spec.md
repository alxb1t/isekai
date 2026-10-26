## ADDED Requirements

### Requirement: A sheet is filled from another flow's tag list when the operator names it

The system SHALL fill a flow's sheet from another flow's tag list when the operator names that flow as the source,
through the target flow's own schema, vocabulary and field map, and SHALL record the source flow in the sheet's
producer. Where the source holds no tag list, it SHALL write every field empty, as for a flow that declares no
tagger.

```
summon-anime-wai/wd14/001.json ──▶ conjure's schema · vocabulary · field map ──▶ conjure-anime-wai/sheets/001.json
                                                                                  producer.tags_from: summon-anime-wai
```

Two flows that tag with the same pinned model read the same photograph the same way, so the second needs no tagging
of its own. A flow reads another's artifacts only when the operator names it
([D17](../../../docs/decisions.md#d17--input-above-flow-below)), and the sheet says whose tags it holds.

#### Scenario: a sheet is filled from the source's tag list
- **Key:** `sheet:tags-from:filled-from-the-sources-tag-list`
- **Layers:** unit
- **WHEN** a sheet is asked for a flow with another flow named as the source of its tags
- **THEN** its fields are routed from the source's tag list through the target's schema and field map
- **AND** its producer names the source flow

#### Scenario: no source tag list gives an empty sheet
- **Key:** `sheet:tags-from:no-source-tag-list-gives-an-empty-sheet`
- **Layers:** unit
- **WHEN** a sheet is asked from a source flow that holds no tag list
- **THEN** a sheet is written with every field present and empty
- **AND** its producer names the source flow

## MODIFIED Requirements

### Requirement: A kept sheet filled from a superseded tag list is named

When a flow that declares the tagger already has a sheet and no new version is asked for, the system SHALL write
nothing, and SHALL warn where the flow holds a tag list numbered above the one its latest sheet was filled from,
naming both numbers and the command that fills a new sheet. A kept sheet it cannot read, or one filled from another
flow's tags, SHALL leave the command silent.

```
sheet, no new version asked, a sheet exists
        │
        ▼
filled from another flow's tags? ──yes──▶ silent
        │
        no
        ▼
latest tag list above the sheet's source? ──yes──▶ warn: both numbers, the command
        │
        no ──▶ silent
        ▼
nothing written, either way
```

`tag --new-version` writes a newer list and leaves the sheet filled from the old one, so "already complete" alone
hides it. The warning names the fix and changes nothing: a new version is an explicit act. A sheet that cannot be
read is refused by name at review. A sheet filled from another flow's tags is built from that flow's approval, so a
later tag list under either flow does not supersede it.

#### Scenario: a newer tag list is named
- **Key:** `sheet:superseded:a-newer-tag-list-is-named`
- **Layers:** unit
- **WHEN** the sheet verb runs without a new version for a flow whose latest tag list is above its sheet's source
- **THEN** nothing is written
- **AND** a warning names both numbers and the command that fills a new sheet

#### Scenario: a sheet from the latest list is silent
- **Key:** `sheet:superseded:the-latest-list-is-silent`
- **Layers:** unit
- **WHEN** the sheet verb runs without a new version for a flow whose sheet was filled from its latest tag list
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

#### Scenario: a sheet filled from another flow's tags is silent
- **Key:** `sheet:superseded:a-borrowed-sheet-is-silent`
- **Layers:** unit
- **WHEN** the sheet verb runs without a new version for a flow whose sheet was filled from another flow's tags
- **THEN** nothing is written
- **AND** no warning is given, whichever flow holds a newer tag list
