## MODIFIED Requirements

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

#### Scenario: a sheet inside the window by its tags and past it assembled warns
- **Key:** `review:budget:a-sheet-past-the-window-only-assembled-warns`
- **Layers:** unit
- **WHEN** a sheet's tags alone fit the encoder's window and the flow's prefix and trailer carry the prompt past it
- **THEN** a warning states the assembled count and the window
- **AND** approval still succeeds
