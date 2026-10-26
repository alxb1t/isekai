## MODIFIED Requirements

### Requirement: A missing caption is shown with the command that writes it

The system SHALL, when an input's flow holds no caption, show in the source pane the caption of the flow its
sheet's tags came from, named as that flow's, and else that there is none and the command that writes it, naming
the flow, the run and the runs root. It SHALL NOT refuse to open the surface for
the absence.

**The prose is the one artifact a skipped verb leaves missing on a page under review.** The tag lists keep
their silence: a list is missing because a tagger failed, because the run predates it, or because the flow
declares no tagger. Skipping `tag` never reaches review, because the sheet refuses without a tag list the
flow declares.

The caption is now its own verb and nothing downstream needs it, so an input can reach review having never
been read. A blank pane cannot be told from a photograph with nothing to say, and the one-verb design kept
the caption bundled for exactly that reason; naming the command keeps the reason without the bundle.

The server builds the command, as it builds every other command a refusal prints, and it names the run and its
runs root so it works when pasted: a batch's runs root in the library is never the default.

#### Scenario: an input with no caption names the command that writes it
- **Key:** `ui:source:a-missing-caption-names-its-command`
- **Layers:** unit
- **WHEN** an input whose flow holds no caption is opened
- **THEN** the payload carries no prose and the command that writes it, naming the flow, the run and the runs root
- **AND** the surface serves the input without a refusal

#### Scenario: a sheet filled from another flow's tags shows that flow's caption
- **Key:** `ui:source:a-borrowed-sheet-shows-its-sources-caption`
- **Layers:** unit
- **WHEN** an input is opened whose flow holds no caption and whose sheet names another flow's tags
- **THEN** the payload carries that flow's caption prose and names that flow
- **AND** it carries no command

### Requirement: Conjure from this drafts from an image's approval, and opens Review on it

The system SHALL offer, on an image's large view, one action per target — each flow the surface offers that reads a
sheet alone, other than the image's own, assigned or not — named *Conjure from this* for `conjure-anime-wai`, the first
on `⇧F`. It SHALL draft the target of the image's run from the approval the image was rendered under, as the review
verb's `--from` does — assigning it and filling its sheet first where it holds none — then open Review on that draft;
where the target holds a waiting draft with edits of its own, it SHALL write nothing and open Review on that draft; a
refusal SHALL show on the large view, and write nothing. On such a draft, approved or not, Review SHALL mark each field
that differs from the target's sheet and name the source flow and approval in the sheet's kicker, and on the draft offer
*Discard draft*.

```
large view · summon-anime-wai v1 · seed 7     [ Conjure from this ⇧F ]
        │ drafts conjure-anime-wai from summon-anime-wai v1
        ▼
Review · conjure-anime-wai   ③ SHEET — FROM SUMMON-ANIME-WAI V1   hair_colour  was …
```

The image the operator approved is where the next flow starts. A flow that reads a photograph has its own sheet of
the person, so it is no target. The press assigns, so no tick and no Prepare come first; an edited draft is the
work in hand. The marks show what the source changed, so the operator reads only the fields the
target adds.

#### Scenario: the large view names its targets
- **Key:** `ui:conjure-from:the-large-view-names-its-targets`
- **Layers:** unit
- **WHEN** a summon image's large view is read in a batch where no source is assigned conjure
- **THEN** its targets are conjure alone

#### Scenario: a refused draft writes nothing
- **Key:** `ui:conjure-from:a-refused-draft-writes-nothing`
- **Layers:** unit
- **WHEN** a draft is asked from an approval version the source does not hold
- **THEN** it is refused naming that version
- **AND** no file is written

#### Scenario: a waiting edit is opened
- **Key:** `ui:conjure-from:a-waiting-edit-is-opened`
- **Layers:** unit
- **WHEN** a draft is asked for a target whose waiting draft has edits of its own
- **THEN** it answers with that draft and writes nothing

#### Scenario: an approved draft keeps its marks
- **Key:** `ui:conjure-from:an-approved-draft-keeps-its-marks`
- **Layers:** unit
- **WHEN** Review reads the approval of a draft written from another flow's approval
- **THEN** it names the source flow and approval, and carries the target sheet's fields

#### Scenario: Review reads the draft against the target's sheet
- **Key:** `ui:conjure-from:review-reads-the-draft-against-the-sheet`
- **Layers:** unit
- **WHEN** Review reads a draft written from another flow's approval
- **THEN** it names the source flow and approval, and carries the target sheet's fields

#### Scenario: Conjure from this opens Review on the draft
- **Key:** `ui:conjure-from:conjure-from-this-opens-review`
- **Layers:** e2e
- **WHEN** `⇧F` is pressed on a summon image whose source is not assigned conjure
- **THEN** Review opens on conjure's draft, its kicker naming the summon approval
- **AND** a field summon changed is marked against conjure's sheet
- **AND** its caption pane shows summon's caption, named as summon's
