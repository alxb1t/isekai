## MODIFIED Requirements

### Requirement: A failure is recorded as the kind it was, and one flow's failure is its own

The system SHALL record a failure to reach an endpoint as transient rather than permanent, and SHALL
assemble each selected flow independently, so that one flow whose sheet cannot be assembled does not
prevent another from being assembled or rendered.

The kinds separate what will fail again from what might not, and a transport error is the clearest case
of the second: a transient record tells the operator that trying again may succeed. At the rendering
stage the kind does not change what the next invocation does. That stage's budget is one attempt, so a
record of either kind refuses the next render until the operator deletes it — a paid stage is never
retried on its own.

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
- **AND** a later invocation of that stage refuses on the record, naming it, until the record is deleted

#### Scenario: one flow's malformed sheet does not cost its siblings their assembly
- **Key:** `image-generation:assembly:a-bad-sheet-is-per-flow`
- **Layers:** unit
- **WHEN** an invocation selects more than one flow and one flow's approved sheet cannot be assembled
- **THEN** the other selected flows are still assembled
- **AND** the failure is reported naming the flow it belongs to
