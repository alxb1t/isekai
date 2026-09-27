## ADDED Requirements

### Requirement: A damaged run file or a malformed draft update is refused, never failed

The system SHALL answer a request that reads a run file lacking a key it needs, or holding one in the wrong shape,
with a refusal naming the file and the command that rewrites it. It SHALL refuse a draft update whose fields are not
an object of lists of strings, naming the field, and SHALL NOT store a value it did not accept. It SHALL NOT answer
either with a server error.

The stages already refuse the same damage by name. A server error names nothing and offers no remedy, and a string
saved as its letters corrupts a draft without a word.

#### Scenario: a damaged file is refused by name
- **Key:** `ui:damage:a-damaged-file-is-refused-by-name`
- **Layers:** unit
- **WHEN** a draft, an approved sheet, a caption or a tag list the surface reads lacks a key it needs or holds it in
  the wrong shape
- **THEN** the request is refused naming the file and the command that rewrites it
- **AND** the surface keeps serving

#### Scenario: a malformed draft update is refused naming the field
- **Key:** `ui:damage:a-malformed-update-is-refused-naming-the-field`
- **Layers:** unit
- **WHEN** a draft update sends a field whose value is not a list of strings
- **THEN** the update is refused naming the field
- **AND** the draft on disk is unchanged
