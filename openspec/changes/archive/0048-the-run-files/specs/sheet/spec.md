## ADDED Requirements

### Requirement: A kept sheet filled from a superseded tag list is named

When a flow that declares the tagger already has a sheet and no new version is asked for, the system SHALL write
nothing, and SHALL warn where the flow holds a tag list numbered above the one its latest sheet was filled from,
naming both numbers and the command that fills a new sheet. A kept sheet it cannot read SHALL leave the command
silent.

```
sheet, no new version asked, a sheet exists
        │
        ▼
latest tag list above the sheet's source? ──yes──▶ warn: both numbers, the command
        │
        no ──▶ silent
        ▼
nothing written, either way
```

`tag --new-version` writes a newer list and leaves the sheet filled from the old one, so "already complete" alone
hides it. The warning names the fix and changes nothing: a new version is an explicit act. A sheet that cannot be
read is refused by name at review.

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
