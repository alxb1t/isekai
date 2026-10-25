## ADDED Requirements

### Requirement: Conjure from this drafts from an image's approval, and opens Review on it

The system SHALL offer, on an image's large view, one action per target — each flow of the batch that reads a sheet
alone, other than the image's own — named *Conjure from this* for `conjure-anime-wai`, the first on `f`. It SHALL
draft the target of the image's run from the approval the image was rendered under, then open Review on that draft;
a refusal SHALL show on the large view, and write nothing. On such a draft, Review SHALL mark each field that differs
from the target's sheet, name the source flow and approval in the sheet's kicker, and offer *Discard draft*.

```
large view · summon-anime-wai v1 · seed 7     [ Conjure from this f ]
        │ drafts conjure-anime-wai from summon-anime-wai v1
        ▼
Review · conjure-anime-wai   ③ SHEET — FROM SUMMON-ANIME-WAI V1   hair_colour  was …
```

The image the operator approved is where the next flow starts. A flow that reads a photograph has its own sheet of
the person, so it is no target. The marks show what the source changed, so the operator reads only the fields the
target adds.

#### Scenario: the large view names its targets
- **Key:** `ui:conjure-from:the-large-view-names-its-targets`
- **Layers:** unit
- **WHEN** a summon image's large view is read in a batch assigning conjure
- **THEN** its targets are conjure alone

#### Scenario: a refused draft writes nothing
- **Key:** `ui:conjure-from:a-refused-draft-writes-nothing`
- **Layers:** unit
- **WHEN** a draft is asked for a target holding no sheet
- **THEN** it is refused naming the way out
- **AND** no file is written

#### Scenario: Review reads the draft against the target's sheet
- **Key:** `ui:conjure-from:review-reads-the-draft-against-the-sheet`
- **Layers:** unit
- **WHEN** Review reads a draft written from another flow's approval
- **THEN** it names the source flow and approval, and carries the target sheet's fields

#### Scenario: Conjure from this opens Review on the draft
- **Key:** `ui:conjure-from:conjure-from-this-opens-review`
- **Layers:** e2e
- **WHEN** `f` is pressed on a summon image's large view
- **THEN** Review opens on conjure's draft, its kicker naming the summon approval
- **AND** a field summon changed is marked against conjure's sheet
