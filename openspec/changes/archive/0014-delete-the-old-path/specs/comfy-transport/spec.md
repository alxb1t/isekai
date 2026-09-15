## MODIFIED Requirements

### Requirement: Render completion polling

The system SHALL wait for a queued prompt to finish by polling the server's history, rather than
assuming a render is ready when it was submitted.

The transport supplies the call and the render stage supplies the loop. That division is unchanged by
this version; what changes is which module holds the loop, and therefore which suite exercises it.

#### Scenario: history is polled until the prompt completes
- **Key:** `comfy-transport:polling:polls-history-until-complete`
- **Layers:** unit
- **WHEN** a workflow is queued and the server does not report it finished immediately
- **THEN** the run keeps polling the history for that prompt until its record appears
- **AND** proceeds only once the render is actually complete

### Requirement: Result retrieval

The system SHALL download the images the completed history record names, rather than guessing an output
path.

#### Scenario: the image named in the history is downloaded
- **Key:** `comfy-transport:retrieval:downloads-image-named-in-history`
- **Layers:** unit
- **WHEN** a prompt's history record names a generated image
- **THEN** that image is fetched by the identifiers the record supplied
- **AND** its bytes are written to the run's output
