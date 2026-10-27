## MODIFIED Requirements

### Requirement: A comparison page shows every run's photograph beside its renders

The system SHALL offer a verb that, given a collection directory holding a `runs/` directory, writes one HTML page into
that collection directory showing, for each run, the run's photograph and every render of each flow's latest approval,
each render labelled by its flow and seed and carrying the positive prompt it came from, with each flow's caption
and a run without a render marked. The page SHALL link every image by a path relative to itself and SHALL embed
none. The verb SHALL print only the page's path, and SHALL refuse, naming the directory, a collection directory that
holds no `runs/`.

A batch ends in a question a person answers by eye: which flow kept whom. The page answers it without an agent
reading the run directories. Linking keeps the page small and every image where the run put it; printing only the
path lets an agent hand the page over unread.

#### Scenario: the page links each photograph to its renders
- **Key:** `cli:compare:the-page-links-photographs-to-renders`
- **Layers:** unit
- **WHEN** the verb is run on a collection whose runs hold renders from more than one flow
- **THEN** the page holds one entry per run, with its photograph and each flow's renders labelled by flow and seed
- **AND** every image is linked by a relative path and none is embedded

#### Scenario: a run with no render is marked
- **Key:** `cli:compare:a-run-without-a-render-is-marked`
- **Layers:** unit
- **WHEN** a run in the collection has no render for a flow
- **THEN** its entry says so for that flow
- **AND** the page is still written

#### Scenario: the verb prints only the page's path
- **Key:** `cli:compare:only-the-path-is-printed`
- **Layers:** unit
- **WHEN** the verb writes the page
- **THEN** its standard output is the page's path and nothing else

#### Scenario: a batch with no runs is refused
- **Key:** `cli:compare:a-batch-without-runs-is-refused`
- **Layers:** unit
- **WHEN** the verb is given a directory that holds no `runs/`
- **THEN** it refuses naming the directory
- **AND** nothing is written

### Requirement: A stage verb requires the flows it acts on, and takes more than one

The system SHALL require a flow selection on every stage verb — reading, tagging, filling a sheet, reviewing,
approving and rendering — SHALL accept the selection more than once in a single invocation, and SHALL refuse an
invocation that names none, naming the flows that are tracked. It SHALL NOT fall back to every tracked
flow. It SHALL refuse a flow that is not tracked, at the point of selection, naming the flows that are.

The flow supplies what a stage reads — its briefing, its schema, its graph and its dials — so a stage cannot act
without one, and every tracked flow is an unbounded default that spends at the last verb. The selection repeats
because flows batch: every flow named in one rendering invocation shares one boot. The serving verb is not a stage
verb: it serves the flows its configuration offers, of every collection, and its page selects one.

#### Scenario: a stage verb without a flow is refused
- **Key:** `cli:flow-selection:a-stage-verb-requires-a-flow`
- **Layers:** unit
- **WHEN** a stage verb is invoked with no flow named
- **THEN** the invocation is refused
- **AND** the message lists the tracked flows

#### Scenario: the selection repeats
- **Key:** `cli:flow-selection:the-flag-is-repeatable`
- **Layers:** unit
- **WHEN** a stage verb is given more than one flow
- **THEN** every named flow is acted on in that one invocation
- **AND** no named flow is silently dropped

#### Scenario: every stage verb accepts it
- **Key:** `cli:flow-selection:every-stage-verb-accepts-it`
- **Layers:** unit
- **WHEN** each stage verb — `caption`, `tag`, `sheet`, `review`, `approve` and `generate` — is invoked
  with a flow named
- **THEN** none of them rejects the flag as unrecognised
- **AND** the inspection verb is the only one that does not take it

#### Scenario: an untracked flow is refused at selection
- **Key:** `cli:flow-selection:an-untracked-flow-is-refused`
- **Layers:** unit
- **WHEN** a stage verb names a flow that is not tracked
- **THEN** the invocation is refused naming that flow
- **AND** the message lists the flows that are tracked

#### Scenario: one flow's refusal leaves the input's other flows
- **Key:** `cli:flow-selection:one-flows-refusal-leaves-the-others`
- **Layers:** unit
- **WHEN** a stage verb names more than one flow, and one of them refuses for an input
- **THEN** the input's other named flows are still acted on
- **AND** every refusal is reported together at the end

### Requirement: The approve verb cancels an approval with `--cancel`

The system SHALL take `--cancel` on `isekai approve`, cancelling each named run's approval in each named flow through
the review stage, SHALL answer each run on its own so one refusal stops no other, and SHALL refuse `--cancel` beside
`--from`.

A cancel is the review stage's act, so the verb composes it and decides nothing; a collection is many runs, and one
refused run must not cost the rest.

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

## REMOVED Requirements

### Requirement: A render session writes its record into the batch, from its start to its end

**Reason**: a library folder is a collection; the requirement is renamed in that word.

**Migration**: the requirement holds, unchanged but for the word, under its new title, *A render session writes its record into the collection, from its start to its end*.

## ADDED Requirements

### Requirement: A render session writes its record into the collection, from its start to its end

The system SHALL, once a render session asks for a pod, write its record to the collection's `sessions/` folder beside
the log, named by the session's id — the id `--session` gives, else the start in UTC as `20261024T091200Z` — and SHALL
replace the record whole as each image lands and as the session ends. The record SHALL hold the id, the start, the end,
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
