## MODIFIED Requirements

### Requirement: A render with no request renders every approval short of its count

The system SHALL, when the rendering verb names one or more collections' runs roots and no request, render in one
session, collection after collection in the order named, for every run of each and every flow its directory holds whose
newest approval holds fewer images than its count; SHALL skip a run that has no directory for a flow; and SHALL leave
out a flow a run holds without an approval, naming the run and the flow on standard error. A request
`<flow>=<count|source>` SHALL keep its meaning beside one runs root, and SHALL be refused beside a second. Each
`--without <runs>/<run-id>/<flow>` SHALL take that run's flow out of what renders, and a damaged approval it names SHALL
be refused all the same; a `--without` under no runs root the verb names, one naming no run's flow, and one beside a
request SHALL be refused before anything is rented. The command the session's limit names for the rest SHALL carry
each `--without`.

The operator approves what to render, so the verb renders what is approved and not yet made. A source may hold only some
flows, and a draft still being corrected waits for its approval rather than holding up the rest. One boot serves every
collection named, so a second collection costs its images and no second pod. A photograph taken out of a session is the
operator's choice for that session alone, so it is a flag and not an edit of the approval; the Render dialog's removal
is this flag ([D3](../../../docs/decisions.md#d3--the-hand-path-stays)).

#### Scenario: what is short is rendered
- **Key:** `cli:render-short:what-is-short-is-rendered`
- **Layers:** unit
- **WHEN** a runs root holds an approval of count two with one image and another with its two
- **THEN** one image is rendered, for the first
- **AND** nothing is rendered for the second

#### Scenario: a run without the flow is skipped
- **Key:** `cli:render-short:a-run-without-the-flow-is-skipped`
- **Layers:** unit
- **WHEN** a run holds no directory for a flow another run is approved in
- **THEN** that run is not rendered for the flow and is not refused

#### Scenario: an unapproved flow is left out
- **Key:** `cli:render-short:an-unapproved-flow-is-left-out`
- **Layers:** unit
- **WHEN** a run holds a flow's directory and no approval for it, and another run's approval is short
- **THEN** the other run is rendered and the first is not
- **AND** standard error names the run and the flow left out

#### Scenario: many collections render in one session
- **Key:** `cli:render-short:many-collections-render-in-one-session`
- **Layers:** unit
- **WHEN** the verb names two collections' runs roots, each short of an image
- **THEN** one session renders both, the first collection's lines before the second's
- **AND** a request beside the two runs roots is refused before anything is rented

#### Scenario: a flow named by --without is not rendered
- **Key:** `cli:render-short:a-flow-named-without-is-not-rendered`
- **Layers:** unit
- **WHEN** two runs' approvals are short and `--without` names the second's flow
- **THEN** the first is rendered and the second is not
- **AND** the quote over the runs root counts the first's images alone

#### Scenario: a --without naming nothing in the session is refused
- **Key:** `cli:render-short:a-without-naming-nothing-is-refused`
- **Layers:** unit
- **WHEN** a `--without` sits under a runs root the verb does not name, or names no run's flow
- **THEN** the verb is refused, naming the `--without`
- **AND** nothing is rented

#### Scenario: a --without beside a request is refused
- **Key:** `cli:render-short:a-without-beside-a-request-is-refused`
- **Layers:** unit
- **WHEN** the verb names a request and a `--without`
- **THEN** the verb is refused before anything is rented

#### Scenario: a damaged approval taken out is still refused
- **Key:** `cli:render-short:a-damaged-approval-taken-out-is-refused`
- **Layers:** unit
- **WHEN** a `--without` names a run's flow whose approval holds a count no render takes
- **THEN** the session is refused, naming the approval
- **AND** nothing is rented

#### Scenario: the retry the limit names keeps each --without
- **Key:** `cli:render-short:the-retry-keeps-without`
- **Layers:** unit
- **WHEN** a session given a `--without` reaches its limit
- **THEN** the command it names for the rest carries the same `--without`
