## MODIFIED Requirements

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
A session gpunit refuses after it asks for a pod, rented or not, SHALL end its record failed with gpunit's reason,
and SHALL exit with gpunit's code.

The state of a session lives on disk, so a page, a second tab, a restarted surface and a render started in the
terminal all read the same truth; no price follows the quote. gpunit's code says its refusal's kind, so a caller tells
no card in stock from no card that fits without reading the log.

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

#### Scenario: a refused session exits with gpunit's code
- **Key:** `cli:render-session:a-refused-session-exits-with-gpunits-code`
- **Layers:** unit
- **WHEN** gpunit refuses a session for no card in stock
- **THEN** the verb exits 4
- **AND** its record ends failed with gpunit's reason
