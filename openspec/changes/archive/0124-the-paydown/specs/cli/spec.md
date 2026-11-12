## MODIFIED Requirements

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
