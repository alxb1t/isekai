## MODIFIED Requirements

### Requirement: A render session writes its record into the batch, from its start to its end

The system SHALL, once a render session asks for a pod, write its record to the batch's `sessions/` folder beside the
log, named by the session's id — the id `--session` gives, else the start in UTC as `20261024T091200Z` — and SHALL
replace the record whole as each image lands and as the session ends. The record SHALL hold the id, the start, the
end, the limit, what each flow was asked to render and what it plans for each photograph, the pod's and the
teardown's steps, each image as its run digest, flow, version and seed in order, and the outcome — running, done,
stopped or failed, with its message — and no price. A session refused before anything is rented SHALL write no
record. An existing id SHALL be refused without replacing its record or asking for a pod, including when concurrent
starts choose the same id.

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

