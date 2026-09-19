## ADDED Requirements

### Requirement: The flow selects the sorter implementation, and the shape constraint travels with it

The system SHALL select the sorter implementation from the string the flow's manifest declares, SHALL
refuse — naming the implementations the build carries — when a flow declares one it does not have, and
SHALL constrain every implementation's output to the schema's field structure regardless of how that
constraint is expressed to the model. A sorter's answer SHALL be read whether it arrives as a separate
structured field or as the body of the response.

The shape constraint is what keeps a malformed answer classified as permanent rather than transient: the
structure was stated in the request, so a response that does not carry it will not carry it on the next
attempt either, and another attempt would spend for nothing. That classification is a property of the
constraint being enforced server-side, not of which transport carries it — an implementation that merely
asked politely for the right shape would flip that row to transient and quietly turn a wasted attempt
into three. Reading the answer from either place is what lets one stage serve implementations that differ
in nothing the stage cares about: the cascade that canonicalises the phrases, the validation that refuses
a non-vocabulary tag, and the rule that an empty field is a legal answer are all downstream of this seam
and all unchanged by which implementation filled it.

#### Scenario: the declared implementation is the one that runs
- **Key:** `sheet:selection:the-flow-names-the-implementation`
- **Layers:** unit
- **WHEN** a flow declaring an implementation is sorted
- **THEN** the sheet's producer names that implementation
- **AND** no other implementation was constructed

#### Scenario: an implementation this build does not carry is refused naming the ones it does
- **Key:** `sheet:selection:unknown-implementation-is-refused`
- **Layers:** unit
- **WHEN** a flow declares a sorter implementation the build does not carry
- **THEN** the command refuses naming the implementations it does carry
- **AND** no sheet is written and no attempt is recorded

#### Scenario: the field structure is required of every implementation
- **Key:** `sheet:selection:structure-is-required-of-every-implementation`
- **Layers:** unit
- **WHEN** any implementation is called
- **THEN** it is required to return exactly the schema's fields
- **AND** the requirement is expressed to the model rather than checked only after the fact

#### Scenario: an answer carried in the response body is read
- **Key:** `sheet:selection:answer-in-the-body-is-read`
- **Layers:** unit
- **WHEN** an implementation returns the schema's fields as the body of its response rather than as a
  separate structured field
- **THEN** the sheet is filled from it
- **AND** the stage does not record a failure for the difference

#### Scenario: a truncated answer is permanent and says why
- **Key:** `sheet:selection:truncation-is-permanent-and-named`
- **Layers:** unit
- **WHEN** an implementation's answer is cut short before the fields are complete and the host reports
  that it ran out of output budget
- **THEN** the failure is recorded as permanent
- **AND** the record distinguishes it from an answer that was malformed for another reason
