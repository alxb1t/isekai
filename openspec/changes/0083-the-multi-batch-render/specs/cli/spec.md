## MODIFIED Requirements

### Requirement: A render with no request renders every approval short of its count

The system SHALL, when the rendering verb names one or more collections' runs roots and no request, render in one
session, collection after collection in the order named, for every run of each and every flow its directory holds whose
newest approval holds fewer images than its count; SHALL skip a run that has no directory for a flow; and SHALL leave
out a flow a run holds without an approval, naming the run and the flow on standard error. A request
`<flow>=<count|source>` SHALL keep its meaning beside one runs root, and SHALL be refused beside a second.

The operator approves what to render, so the verb renders what is approved and not yet made. A source may hold only some
flows, and a draft still being corrected waits for its approval rather than holding up the rest. One boot serves every
collection named, so a second collection costs its images and no second pod.

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

### Requirement: A render session's limit is estimated from its work, at most the configured ceiling

The system SHALL bound a render session by a limit: the one `--limit` names, or else one boot plus the images it will
render, of every collection it names, times the median duration of that flow's last recorded renders in that
collection, plus teardown, times the configured factor,
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

#### Scenario: one boot for many collections
- **Key:** `cli:render-limit:one-boot-for-many-collections`
- **Layers:** unit
- **WHEN** the limit is estimated for two collections
- **THEN** it holds one boot and one teardown, and both collections' images

### Requirement: A render session writes its record into the collection, from its start to its end

The system SHALL, once a render session asks for a pod, write a record to each collection's `sessions/` folder it
renders, beside its log, every record holding the session's id and naming the other collections in `collections`, named
by the session's id — the id `--session` gives, else the start in UTC as `20261024T091200Z` — and SHALL replace a record
whole as each of its collection's images lands and as the session ends, the pod's and the teardown's steps in every
record; the session's log lines SHALL go to every collection's log, and every record SHALL name the complete
traversal in `collection_order`, including its own collection. The record SHALL hold the id, the start, the end,
the limit, what each flow was asked to render and what it plans for each photograph, the pod's and the teardown's steps,
each image as its run digest, flow, version and seed in order, and the outcome — running, done, stopped or failed, with
its message — and no price. A session refused before anything is rented SHALL write no record. An existing id SHALL be
refused without replacing its record or asking for a pod, including when concurrent starts choose the same id.

The state of a session lives on disk, so a page, a second tab, a restarted surface and a render started in the
terminal all read the same truth; no price follows the quote.

```
free checks ─▶ claim id + lifetime lock ─▶ running record ─▶ images ─▶ ended record ─▶ release lock
                    └ occupied ─▶ refuse without asking for a pod
```

#### Scenario: a session writes its record
- **Key:** `cli:render-session:a-session-writes-its-record`
- **Layers:** unit
- **WHEN** a session renders two images
- **THEN** its record names both images in order and the outcome done
- **AND** it holds no price

#### Scenario: the record follows each image
- **Key:** `cli:render-session:the-record-follows-each-image`
- **Layers:** unit
- **WHEN** a session has rendered its first of two images
- **THEN** its record reads running, with that one image

#### Scenario: the given id names the record
- **Key:** `cli:render-session:the-given-id-names-the-record`
- **Layers:** unit
- **WHEN** a session is run with `--session 20261024T091200Z`
- **THEN** its record is `sessions/20261024T091200Z.json`

#### Scenario: a refusal before renting writes no record
- **Key:** `cli:render-session:a-refusal-before-renting-writes-none`
- **Layers:** unit
- **WHEN** a session is refused before it asks for a pod
- **THEN** no record is written

#### Scenario: an owned id is refused
- **Key:** `cli:render-session:an-owned-id-is-refused`
- **Layers:** unit
- **WHEN** another session chooses an id whose record already exists, explicitly or automatically
- **THEN** it refuses before asking for a pod and leaves the existing record unchanged

#### Scenario: concurrent starts reserve one record
- **Key:** `cli:render-session:concurrent-starts-reserve-one-record`
- **Layers:** unit
- **WHEN** concurrent starts choose the same unused id
- **THEN** exactly one owns the complete record and the other refuses

#### Scenario: the record plans each photograph
- **Key:** `cli:render-session:the-record-plans-each-photograph`
- **Layers:** unit
- **WHEN** a session is asked for two images of one run and one of another
- **THEN** its record plans each run and flow with its number of images

#### Scenario: each collection holds its record
- **Key:** `cli:render-session:each-collection-holds-its-record`
- **Layers:** unit
- **WHEN** a session renders two collections
- **THEN** each collection's record holds the shared id, its own images and plan, and the complete collection order
- **AND** both records hold the pod's and the teardown's steps, and both logs the session's lines
