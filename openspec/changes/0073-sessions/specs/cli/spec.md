## ADDED Requirements

### Requirement: A render session writes its record into the batch, from its start to its end

The system SHALL, once a render session asks for a pod, write its record to the batch's `sessions/` folder beside the
log, named by the session's id — the id `--session` gives, else the start in UTC as `20261024T091200Z` — and SHALL
replace the record whole as each image lands and as the session ends. The record SHALL hold the id, the start, the
end, the limit, what each flow was asked to render, the pod's and the teardown's steps, each image as its run digest,
flow, version and seed in order, and the outcome — running, done, stopped or failed, with its message — and no price.
A session refused before anything is rented SHALL write no record.

The state of a session lives on disk, so a page, a second tab, a restarted surface and a render started in the
terminal all read the same truth; no price follows the quote.

```
start ─▶ sessions/<id>.json {outcome: running, images: []} ─▶ each image: replaced ─▶ end: replaced {outcome}
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
