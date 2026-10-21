# Design — 0065 revise

How a rendered image becomes a draft from the approval that made it, and how two versions of a seed are compared.
**Verdict: feasible** — `review` already copies an approval into a draft with its `renders`; revise names which one.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut, `main` at `abf4e5e` (`v0.39.1`):

- **`review(run, flow, *, new_version)`** copies the newest approval, carrying `renders`, its producer
  `{"implementation", "from": <approval>, "source": "review"}` (`isekai/pipeline/review.py:128-206`, the producer `:190`,
  `renders` `:203`). Approving renames the draft, so an approval keeps that producer; `approve` takes a `source` flow
  for `--from` copies (`:329-345`).
- **`renders`:** `Renders` and `renders_of` (`isekai/foundation/artifacts.py:249`, `:449`); `save_draft(…, renders=…)`
  (`review.py:223`).
- **Renders:** `read_renders`, `read_render`, `/image`, `/thumb` (`isekai/interface/ui/app.py:696-770`); the routes
  `/b/:batch/renders` and its large view (`ui/src/router.ts:18-20`); `ui/src/views/RenderLarge.vue` has no Revise and
  no Compare.
- **The verbs:** `review` takes `--new-version` (`isekai/interface/cli.py:236`).
- **The cards:** 0063·R19 — `tests/e2e/test_render.py:18-21` re-proves a disabled Render that
  `tests/test_ui_jobs.py:546` proves against the route; 0064·R4, R5 — the stream test at `tests/test_ui_api.py:1470-1500`
  hangs if its helper thread raises, and asserts an empty snapshot its timing does not guarantee.

| measured at the cut | value | command |
|---|---|---|
| tests in `tests/test_review.py` | 52 | `grep -c "def test_" tests/test_review.py` |
| tests in `tests/test_ui_api.py` | 54 | `grep -c "def test_" tests/test_ui_api.py` |
| tests in `tests/e2e/test_render.py` | 2 | `grep -c "def test_" tests/e2e/test_render.py` |

## Goals / Non-Goals

**Goals:** revise any rendered image from the sheet that made it; Compare a seed across versions; every write all or
nothing. **Non-Goals:** a new render grammar; revise from the hub; `control`.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `review.revise(run, flow, version, seed) -> Path`: the next draft, copied from approval `version`, producer naming it, `renders` `{count: 1, seeds: [seed]}`; refused while an unapproved draft waits | the image's own sheet; the same composition | always the newest approval |
| [D2](#d2) | `isekai revise <image.png> …`: each path parsed to run, flow, version, seed; every image checked first; all written, or none | the path is the whole address; a retry meets no half-written selection | a `<run> <flow>` form |
| [D3](#d3) | `review --discard --flow F <run>` deletes the highest draft only if unapproved | the waiting-draft refusal's way out | deleting approvals |
| [D4](#d4) | `approve` refuses a draft with its `producer.from` approval's fields whose every image is of a seed that approval lists or rendered, naming the images | an unchanged revision is paid for twice | a warning |
| [D5](#d5) | the header reads `producer.from`: a revision when fields differ, a re-roll when only `renders` do | the origin is on disk already | a `revision_of` field |
| [D6](#d6) | Compare pairs a seed with the newest older version holding it; it shows both images, the changed fields, the `renders` change and the tokens | the design's J5·8–J5·9 | ↵ opening compare |
| [D7](#d7) | routes and views: `POST /api/b/{batch}/revise`, `POST …/review/{digest}/{flow}/discard`, `GET …/renders/{digest}/{flow}/{version}/{seed}/compare`; Revise in `RenderLarge.vue` and `Renders.vue`; `Compare.vue` showing the pair; Review of a revision marking its fields, with a Discard that asks first | the design's J5, J6, 7a, 7b — less J5·9's ← → and Revise-again keys and J6's marking of ④'s changes, which no requirement asks for | |
| [D8](#d8) | drop `tests/e2e/test_render.py:18-21`; close the stream test's helper in a `finally`, re-raise its exception, and read the snapshot before uploading | the cards' fixes | |

### D1

```
image outputs/<v>/<seed>.png ──▶ review/<v>.approved.json ──copy──▶ review/<next>.draft.json
                                                         renders {count 1, seeds [seed]}
                                                         producer {from: v, source: "review"}
```

### D2

A path must sit under a run's `outputs/<NNN>/` and name a `<seed>.png` with its `.render.json`; anything else is
refused by name. The check runs over the whole selection before `revise` writes once.

### D6

```
versions of one source × flow holding seed s:  v1, v2, v3
large view of v3 ──▶ "Compare with v2  C" ──▶ …/v3/<s>/compare
```

## Tests

| layer | added | removed | where |
|---|---|---|---|
| unit | every `unit` scenario of the [review](specs/review/spec.md), [cli](specs/cli/spec.md) and [ui](specs/ui/spec.md) deltas | none | `tests/test_review.py`, `tests/test_ui_api.py` |
| e2e | `ui:revise:revise-opens-review-on-the-revision`, `ui:compare:compare-shows-the-pair-and-the-change`, one test each | the disabled-Render step of `test_confirming_the_dialog_opens_the_session` | `tests/e2e/test_render.py` |

**End-to-end runs added:** two tests, on Chromium, each on its own fixture batch — Revise, Review, Discard's ask,
Approve; and Compare on a seed rendered under two versions — each shown only by a browser (T1). They are not one
journey along J5, as first planned: a test carries one scenario's marker, so two e2e scenarios are two tests; the
server is shared by the session, so a test that approves a revision would move a batch another test reads; and a
journey reaching Compare would run a render on the fake session where the fixture writes the second version on disk.

| removed or merged | its assertions and scenario ids now carried by |
|---|---|
| the disabled-Render step in `test_confirming_the_dialog_opens_the_session` (`tests/e2e/test_render.py:18-21`) | `test_with_every_count_rendered_render_is_disabled_naming_why` (`tests/test_ui_jobs.py:546`), bound to `ui:render:nothing-short-disables-render` |

## Dependencies

None.

## Risks / Trade-offs

- **[Risk]** a revision of an old version after newer ones exist confuses the queue → the queue lists the drafts
  revise wrote, by run and flow.
- **[Trade-off]** the header compares two approvals on every read of Renders → both are small JSON files.

## Verdict

**Feasible.** `review` already copies an approval with its `renders`; revise names which approval and lists the seed.
