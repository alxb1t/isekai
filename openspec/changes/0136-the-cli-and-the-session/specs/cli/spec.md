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

#### Scenario: a count or a seed out of range is refused at parse time
- **Key:** `cli:generate-signature:a-count-or-seed-out-of-range-is-refused`
- **Layers:** unit
- **WHEN** a count below one, a seed outside the sampler's unsigned 64-bit range, or a count or seed that is no integer is given
- **THEN** the invocation is refused at parse time
- **AND** the message says what is out of range

### Requirement: A render session's limit is estimated from its work, at most the configured ceiling

The system SHALL bound a render session by a limit: the one `--limit` names, or else one boot plus the images it will
render, of every collection it names, each at the median duration of that flow's last recorded renders in that
collection or the configured time per image, whichever is higher, plus teardown, times the configured factor,
and never below the pod's provisioning hold plus five minutes. It SHALL refuse a limit above the ceiling `gpunit.toml`
names, and SHALL give the same estimate the surface quotes.

A fixed limit caps a batch at what fits in it; a limit from the work fits the work, and the ceiling still bounds the
spend. A median recorded on a fast card says nothing of a slow one, and gpunit takes whichever card is in stock, so
the configured time per image is the slowest card's
([D26](../../../docs/decisions.md#d26--renders-run-on-a-rented-gpu)). A pod held for diagnosis must stop after its
hold ends, not before. A source request's images are the seeds its source holds when it runs, so a line chaining two
source requests would be estimated short of its work: it is refused before the pod, and the second request names the
first's source instead, which renders the same seeds.

#### Scenario: the estimate comes from recorded durations
- **Key:** `cli:render-limit:the-estimate-comes-from-durations`
- **Layers:** unit
- **WHEN** four images will render at a recorded median of ninety seconds, above the configured time per image
- **THEN** the limit is boot plus four times ninety seconds plus teardown, times the factor

#### Scenario: a median below the configured figure takes the figure
- **Key:** `cli:render-limit:a-fast-median-takes-the-figure`
- **Layers:** unit
- **WHEN** a flow's last renders took a median below the configured time per image
- **THEN** the estimate uses the configured time per image

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

#### Scenario: a limit below the floor is refused
- **Key:** `cli:render-limit:below-the-floor-is-refused`
- **Layers:** unit
- **WHEN** a limit of one second or more, but below the hold plus five minutes, is given
- **THEN** the invocation is refused naming the floor
- **AND** no session is opened

#### Scenario: a limit below one second is refused at parse time
- **Key:** `cli:render-limit:below-one-second-is-refused-at-parse-time`
- **Layers:** unit
- **WHEN** a limit below one second, or one that is no integer, is given
- **THEN** the invocation is refused at parse time
- **AND** no session is opened

#### Scenario: a given limit is the session's limit
- **Key:** `cli:render-limit:a-given-limit-is-the-sessions`
- **Layers:** unit
- **WHEN** a limit from the floor to the ceiling is given
- **THEN** the session opens with that limit, and not with the estimate
- **AND** the session states that limit

#### Scenario: one boot for many collections
- **Key:** `cli:render-limit:one-boot-for-many-collections`
- **Layers:** unit
- **WHEN** the limit is estimated for two collections
- **THEN** it holds one boot and one teardown, and both collections' images

#### Scenario: a chained source is refused before the pod
- **Key:** `cli:render-limit:a-chained-source-is-refused-before-the-pod`
- **Layers:** unit
- **WHEN** a session's line holds a source request whose source is the flow of another source request
- **THEN** the invocation is refused naming both requests and the source request that renders the same seeds
- **AND** no session is opened
