# Design — 0073 sessions

How a render session becomes a record on disk, and how the app lists and shows it.
**Verdict: feasible** — the verb already reports every step as a JSON line and writes beside the runs root; the record
is those steps kept, and the screens read it.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut, `main` at `c52adb8` (`v0.45.0`):

- **The session lives in memory:** the job slot's `session` — started, limit, of, ended, steps, images
  (`isekai/interface/ui/jobs.py:244-277`); the child's `--progress json` lines feed it (`:451-480`); `/session`
  draws it (`ui/src/views/Session.vue`, `ui/src/router.ts:34`).
- **The verb:** `run_session` and `_session` (`isekai/interface/render.py:234`, `:526`); its log is
  `runs.parent / "log.txt"` (`:261`); image lines name step, number, run, flow (`:181`, `:211`); flags `--progress`,
  `--limit` (`isekai/interface/cli.py:243-249`, `:318`).
- **The contract:** each file kind is an `Artifact(name, version)` (`isekai/foundation/artifacts.py:350-360`);
  `write` writes a kind (`:382`).
- **The alert:** the band's *Resolve* opens `/session` (`ui/src/App.vue:130`); the way out is `Session.vue:152-160`.
- **Tiles:** `.session__tile` is 60×80 (`ui/src/app.css:322-324`); `--tile-width` × `--tile-height` is 96×128 (`:12-13`).
- **The cards:** `0063·R17` — `_run_render` marks `volume up` running and an `OSError` leaves it so (`jobs.py:413`,
  `:428`); `0070·R10` — `ImageViewer` fixes `last` once (`ui/src/components/ImageViewer.vue:25`); `0072·R4` —
  no test puts a render in the slot against `_rendering` and `post_cancel` (`isekai/interface/ui/app.py:755-759`,
  `:739`); `0072·R8` — `isekai/interface/README.md:28`; `0072·R9` — `README.md:240-241`; `0072·R11` — `README.md:312`
  and the living review requirement; `0072·R14` — `ui/design/spec.md:233-234`, the living ui SHALL,
  `ui/src/views/Review.vue:220-221`; `0072·R15` — `isekai/pipeline/review.py:313`.

| measured at the cut | value | command |
|---|---|---|
| tests in `tests/test_render.py` | 31 | `grep -c "def test_" tests/test_render.py` |
| tests in `tests/test_ui_jobs.py` | 21 | `grep -c "def test_" tests/test_ui_jobs.py` |
| e2e tests | 26 | `cat tests/e2e/test_*.py \| grep -c "def test_"` |

## Goals / Non-Goals

**Goals:** the session's state on disk; the UI from it; a finished session found again; a running one seen
everywhere. **Non-Goals:** a second job slot; money after the quote; a change to gpunit.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `SESSION_FILE = Artifact("session", 1)` in `artifacts.py`, a `SessionRecord` of `id`, `started`, `ended`, `limit`, `asked` (images per flow), `steps` (`pod`, `teardown`), `images` (`{digest, flow, version, seed}` in order), `outcome` (`running \| done \| stopped \| failed`), `message`; `artifacts.replace(path, kind, body)` writes it whole and atomically, again and again | the contract writes every file; a record is the one batch file kept current | a run file; an append-only log |
| [D2](#d2) | `_session` writes `runs.parent / "sessions" / f"{id}.json"` once the gpunit session is asked for, replaces it on each image and at the end; `id` is `--session`, else `datetime.now(UTC)` as `%Y%m%dT%H%M%SZ`; a refusal before the pod writes none | the verb is the one path; beside its log (D36) | written only at the end |
| [D3](#d3) | `library.sessions(folder)` reads every record, running first, then newest first; `GET /api/b/{batch}/sessions` and `GET /api/b/{batch}/sessions/{id}`, a missing id refused naming the list; the job passes `--session` to the verb and its slot holds the id, the volume steps and Stop | the record is the state; the slot adds only what the app runs | the slot as the source |
| [D4](#d4) | routes `/b/:batch/sessions` (`Sessions.vue`) and `/b/:batch/sessions/:id` (`SessionPage.vue`), the record polled through the batch store while running; a Sessions tab; `/session` and `Session.vue` gone; `/billing` (`Billing.vue`) holds the alert's way out, which the band's *Resolve* opens; the Render dialog's confirm opens the new session's page | the page names its batch; a pod may bill with no batch | keeping `/session` for the alert |
| [D5](#d5) | `App.vue` shows `● render 09:12` while the slot runs a render, linking to its session; `⇧S` goes there, else the open batch's sessions, and is not declared outside a batch | | |
| [D6](#d6) | a session page's images and the batch's sources (⑯) open in `ImageViewer`, tiles at `var(--tile-width)` × `var(--tile-height)`; `ImageViewer` reads `last` from its images on each step (`0070·R10`) | one viewer, one tile size | |
| [D7](#d7) | `0063·R17`: an `OSError` in `volume up` marks the step failed; `0072·R4`: a step with a render in the slot in `test_an_approved_sheet_carries_why_it_cannot_be_cancelled`, asserting the payload's reason and the cancel route's 409; `0072·R8` `POST …/cancel` in the interface README; `0072·R9` "`isekai revise` where an image exists, else `review --new-version`"; `0072·R11` "`--from` copies the source's newest approval again"; `0072·R14` "the draft open above what lies beneath, else the approval beneath, read-only"; `0072·R15` "and return what the flow is left on" | the cards' fixes | |

**Erratum, archived 0072:** `openspec/changes/archive/0072-cancel-approve/design.md`'s D3 says `--from` writes a copy
again, and its D5 says a copy's cancel opens the approval beneath, read-only; `--from` copies the source's newest
approval, and over a re-opened sheet the cancel opens the draft. The archive is frozen; this note and the corrected
SHALLs are the record (`0072·R11`, `0072·R14`).

## Tests

| layer | added | edited | where |
|---|---|---|---|
| unit · pytest | every `cli:render-session:` scenario; `ui:sessions:a-batch-lists-its-sessions`, `ui:sessions:a-session-reads-its-record`; `ui:render-job:an-opening-that-raises-fails-its-step` | `ui:review:the-sheet-says-why-it-cannot-be-cancelled` gains the render step (`0072·R4`) | `tests/test_render.py`, `tests/test_ui_api.py`, `tests/test_ui_jobs.py` |
| e2e | `ui:sessions:the-list-shows-a-finished-session` | `test_confirming_the_dialog_opens_the_session` lands on `/b/<batch>/sessions/<id>`; `tests/e2e/conftest.py` writes a finished record | `tests/e2e/test_render.py`, `tests/e2e/conftest.py` |

**End-to-end runs added:** one, on Chromium only (T4) — the tab and the list are a browser's (T1); the render test
reaches a live session, not a finished one in the list, so the list is its own test (T2). `0070·R10` adds no test:
the viewer has no unit layer, and its list changes only under a live rail.

**Removed or merged:** none.

## Dependencies

None.

## Risks / Trade-offs

- **[Risk]** a session killed outright leaves a record reading `running` → the list shows it running only while the
  slot holds a render; otherwise it reads as ended without an outcome.
- **[Trade-off]** the record is rewritten per image → one small JSON per image, atomically.

## Verdict

**Feasible.** The verb's own lines become a file; the screens read it.
