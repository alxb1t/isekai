## ADDED Requirements

### Requirement: Inspection reads the flows root it was given, and refuses before it prints

The system SHALL resolve a run's flows through the flows root the invocation supplies rather than a
default, and SHALL refuse a run holding a directory no flow answers for before any line of the report is
printed.

A verb that takes an injected root and then reads a different one is a seam that is not a seam: the
double it is given in a test is not the one it uses, and a run captured under another root cannot be
inspected at all. Inspection is the one verb whose whole job is reading a run in whatever state it is
in, which is what makes the bypass matter here rather than being a tidiness point.

Refusing after output has begun is worse than refusing: the report streams, so a reader sees a partial
account and then an error, with no way to tell which lines were complete. What is printed must be
decided before anything is.

#### Scenario: inspection reads the flows root it is given
- **Key:** `run-directory:inspection:the-injected-flows-root-is-used`
- **Layers:** unit
- **WHEN** a run is inspected with a flows root supplied by the invocation
- **THEN** the flows it reports are resolved through that root

#### Scenario: a directory no flow answers for refuses before any line is printed
- **Key:** `run-directory:inspection:an-unanswerable-directory-refuses-first`
- **Layers:** unit
- **WHEN** a run holds a directory no tracked flow answers for
- **THEN** the invocation is refused
- **AND** no line of the report has been printed
