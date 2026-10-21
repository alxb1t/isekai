## ADDED Requirements

### Requirement: A render with no request renders every approval short of its count

The system SHALL, when the rendering verb names a runs root and no request, render for every run and every flow its
directory holds whose newest approval holds fewer images than its count; SHALL skip a run that has no directory for a
flow; and SHALL leave out a flow a run holds without an approval, naming the run and the flow on standard error. A
request `<flow>=<count|source>` SHALL keep its meaning.

The operator approves what to render, so the verb renders what is approved and not yet made. A source may hold only
some flows, and a draft still being corrected waits for its approval rather than holding up the rest.

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

### Requirement: A render session's limit is estimated from its work, at most the configured ceiling

The system SHALL bound a render session by a limit: the one `--limit` names, or else boot plus the images it will
render times the median duration of that flow's last recorded renders, plus teardown, times the configured factor,
with configured figures where nothing is recorded, and never below the pod's provisioning hold plus five minutes. It
SHALL refuse a limit above the ceiling `gpunit.toml` names, and SHALL give the same estimate the surface quotes.

A fixed limit caps a batch at what fits in it; a limit from the work fits the work, and the ceiling still bounds the
spend. A pod held for diagnosis must stop after its hold ends, not before.

#### Scenario: the estimate comes from recorded durations
- **Key:** `cli:render-limit:the-estimate-comes-from-durations`
- **Layers:** unit
- **WHEN** a flow's last renders took a median of ninety seconds and four images will render
- **THEN** the limit is boot plus four times ninety seconds plus teardown, times the factor

#### Scenario: with nothing recorded the configured figure is used
- **Key:** `cli:render-limit:the-configured-figure-without-records`
- **Layers:** unit
- **WHEN** no render of a flow carries a duration
- **THEN** the estimate uses the configured time per image

#### Scenario: a short session's limit is the floor
- **Key:** `cli:render-limit:a-short-session-takes-the-floor`
- **Layers:** unit
- **WHEN** the estimate for one image is shorter than the hold plus five minutes
- **THEN** the limit is the hold plus five minutes

#### Scenario: a limit above the ceiling is refused
- **Key:** `cli:render-limit:above-the-ceiling-is-refused`
- **Layers:** unit
- **WHEN** a limit above `gpunit.toml`'s ceiling is given
- **THEN** the invocation is refused naming the ceiling
- **AND** no session is opened

### Requirement: A render session reports its steps as JSON lines when asked

The system SHALL, when the rendering verb is given `--progress json`, print one JSON object per line on standard
output as the session opens its pod, renders each image and tears its pod down, each naming its step, its state and,
for an image, its number of the total; it SHALL print its human lines on standard error instead.

The surface shows a session as the verb reports it.

#### Scenario: a session reports each image of the total
- **Key:** `cli:render-progress:each-image-of-the-total`
- **Layers:** unit
- **WHEN** a session renders two images with `--progress json`
- **THEN** standard output holds a line for image one of two and image two of two
- **AND** a line for the teardown's end

## MODIFIED Requirements

### Requirement: The rendering verb takes many photographs and either a count or explicit seeds

The system SHALL accept several run identifiers in one rendering invocation, SHALL accept either a
count of renders per photograph or an explicit list of seeds but not both, and SHALL default to the
count each photograph's newest approval states, one where it states none.

Rendering is where the money is, and a boot costs more than a render, so one photograph per invocation is mostly
overhead. Many identifiers let one boot serve a batch. With nothing asked for, the approval says how many, because
that is the number a person agreed to; one is the default where it says nothing, because the cheap option is what
happens then.

#### Scenario: several photographs render in one invocation
- **Key:** `cli:generate-signature:accepts-many-identifiers`
- **Layers:** unit
- **WHEN** several run identifiers are given
- **THEN** all of them are prepared and rendered in one invocation
- **AND** the endpoint is acquired once

#### Scenario: the count defaults to one
- **Key:** `cli:generate-signature:count-defaults-to-one`
- **Layers:** unit
- **WHEN** no count and no seed is given for a photograph whose approval states no count
- **THEN** one render is produced for it per approved flow
- **AND** its seed is drawn rather than fixed

#### Scenario: the count defaults to the approval's
- **Key:** `cli:generate-signature:count-defaults-to-the-approvals`
- **Layers:** unit
- **WHEN** no count and no seed is given for a photograph whose approval states a count of three
- **THEN** three renders are produced for it
- **AND** their seeds are drawn rather than fixed

#### Scenario: a count and explicit seeds cannot be combined
- **Key:** `cli:generate-signature:count-and-seed-are-exclusive`
- **Layers:** unit
- **WHEN** both a count and one or more seeds are given
- **THEN** the invocation is refused at parse time
- **AND** the message states that the two are alternatives
