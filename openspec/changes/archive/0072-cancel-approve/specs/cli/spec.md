## ADDED Requirements

### Requirement: The approve verb cancels an approval with `--cancel`

The system SHALL take `--cancel` on `isekai approve`, cancelling each named run's approval in each named flow through
the review stage, SHALL answer each run on its own so one refusal stops no other, and SHALL refuse `--cancel` beside
`--from`.

A cancel is the review stage's act, so the verb composes it and decides nothing; a batch is many runs, and one refused
run must not cost the rest.

#### Scenario: each run is cancelled on its own
- **Key:** `cli:approve-cancel:each-run-on-its-own`
- **Layers:** unit
- **WHEN** `approve --cancel` names a cancellable run and a run with a prompt
- **THEN** the first is a draft again and the second is refused naming its prompt

#### Scenario: cancel beside from is refused
- **Key:** `cli:approve-cancel:not-beside-from`
- **Layers:** unit
- **WHEN** `approve` is given `--cancel` and `--from`
- **THEN** it is refused before any run is read
