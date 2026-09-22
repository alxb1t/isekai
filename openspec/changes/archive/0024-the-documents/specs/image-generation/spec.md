## ADDED Requirements

### Requirement: A failure is recorded as the kind it was, and one flow's failure is its own

The system SHALL record a failure to reach an endpoint as transient rather than permanent, and SHALL
assemble each selected flow independently, so that one flow whose sheet cannot be assembled does not
prevent another from being assembled or rendered.

A permanent record is never retried, so classifying a closed tunnel as one turns a network blip into a
stage that refuses forever and can only be cleared by deleting an error record by hand. The kinds exist
to separate what will fail again from what might not, and a transport error is the clearest case of the
second.

Assembling every selected flow in one expression makes the first failure the invocation's failure. The
batch-over-photographs rule already collects one refusal per photograph and carries on; a flow is the
same kind of unit and gets the same treatment. Without it, a malformed sheet for one flow leaves a
second flow unrenderable until the first is repaired, and the permanent record written before the raise
means repairing it is not enough.

#### Scenario: an unreachable endpoint is recorded transient
- **Key:** `image-generation:failure:an-unreachable-endpoint-is-transient`
- **Layers:** unit
- **WHEN** a render fails because the endpoint cannot be reached
- **THEN** the failure record names the failure as transient
- **AND** a later invocation of that stage attempts the work rather than refusing on the record

#### Scenario: one flow's malformed sheet does not cost its siblings their assembly
- **Key:** `image-generation:assembly:a-bad-sheet-is-per-flow`
- **Layers:** unit
- **WHEN** an invocation selects more than one flow and one flow's approved sheet cannot be assembled
- **THEN** the other selected flows are still assembled
- **AND** the failure is reported naming the flow it belongs to
