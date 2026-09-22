## ADDED Requirements

### Requirement: A flow manifest is refused at load when its declarations do not resolve

The system SHALL refuse a flow manifest that names a node role whose id is absent from that flow's own
graph, and SHALL refuse one that omits a dial the roles it declares require. Both refusals SHALL happen
at load, before any endpoint is contacted and before any input is transferred.

A manifest is validated at load or it is validated by a render. The second costs a rented GPU and an
uploaded photograph to discover a typo, and it fails as a bare lookup error rather than a refusal — so
nothing collects it, no failure record is written, and the rest of the batch dies with it. Refusing at
load moves the same discovery into a test run.

**The dial check is conditional on the roles a flow declares, not on a fixed list.** Flows differ in what
they render: one that declares no identity leg legitimately declares none of that leg's dials, and a flat
list would refuse it for being what it is. What must hold is narrower and true of every flow — that every
dial the declared roles read is present.

#### Scenario: a role naming a node the graph does not carry is refused
- **Key:** `cli:manifest:a-dangling-node-id-is-refused-at-load`
- **Layers:** unit
- **WHEN** a flow manifest names a node role whose id is absent from that flow's graph
- **THEN** loading it is refused naming the role and the id
- **AND** no endpoint is contacted and no input is transferred

#### Scenario: every role a tracked flow names resolves in its own graph
- **Key:** `cli:manifest:every-tracked-role-resolves`
- **Layers:** unit
- **WHEN** each tracked flow is loaded
- **THEN** every node id its roles name is present in that flow's graph

#### Scenario: every dial a tracked flow declares is one its roles read
- **Key:** `cli:manifest:every-tracked-dial-is-read`
- **Layers:** unit
- **WHEN** each tracked flow is loaded
- **THEN** every dial the roles it declares require is present in its manifest
