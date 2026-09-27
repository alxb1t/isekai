## ADDED Requirements

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
