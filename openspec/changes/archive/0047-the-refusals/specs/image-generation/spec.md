## MODIFIED Requirements

### Requirement: Only an approved sheet is rendered

The system SHALL render from an approved artifact only, and SHALL refuse a flow that has none, naming
the commands that would produce one.

A person's correction is what the render is for
([D33](../../../docs/decisions.md#d33--the-operator-decides-what-is-rendered)). Rendering an unapproved draft spends
money on the result the correction exists to improve, and leaves the two indistinguishable afterwards.

#### Scenario: an unapproved flow is refused
- **Key:** `image-generation:inputs:unapproved-flow-is-refused`
- **Layers:** unit
- **WHEN** a run has no approved artifact for a flow
- **THEN** rendering is refused naming that flow
- **AND** the message names the commands that would produce one

#### Scenario: every flow with an approved artifact renders
- **Key:** `image-generation:inputs:every-approved-flow-renders`
- **Layers:** unit
- **WHEN** a run has approved artifacts for more than one flow, and the invocation names them
- **THEN** each of them is rendered
- **AND** an approved flow the invocation does not name is not rendered
