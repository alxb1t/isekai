## MODIFIED Requirements

### Requirement: A tag artifact that is absent is silent

The system SHALL render the source pane without a tag list when its artifact does not exist, SHALL NOT
refuse to open the surface for the absence, and SHALL NOT display a message explaining it.

One is legitimately missing when the run was captioned before the stage existed, or when a tagger call
failed — and neither is a reason a sheet cannot be reviewed. The tag lists are an aid; a surface that
refuses to open because an aid is missing has confused an aid for an input, and the startup refusals
exist for what review genuinely cannot proceed without: the flow, the run, the draft, the photograph's
dimensions, the vocabulary and the bundle.

No message either. A line explaining an absence the operator caused by not running something is chrome
on the pane they spend the most time reading, and it would appear beside every input whose list is
missing.

#### Scenario: an input with no tag artifacts still opens
- **Key:** `ui:source:an-absent-tag-artifact-is-silent`
- **Layers:** unit
- **WHEN** an input whose run holds no tag artifacts is opened
- **THEN** the surface serves it and the payload reports the lists as absent
- **AND** no refusal is raised and no explanatory message is rendered

