# Design — 0063 render

How the render moves into the browser: the approval says how many images, `render` renders what is short within a
limit fitted to the work, a job opens and closes the volume around it, and the images come back into a Renders view.
**Verdict: feasible-with-caveats** — gpunit takes a `Spec` per session and records what it creates; the caveats are
the provisioning hold, which sets a floor under the limit, and one metered proof.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut, `main` at `7a9a698` (`v0.38.0`):

- **The session:** `isekai/interface/render.py` — `CEILING_S = 2640` (`:37-38`), its watchdog (`:247-260`), `Lost` and
  `TeardownFailed` handled (`:307-321`), `REQUEST` (`:45`); `Seams` holds `open_session`, `connect`, `kill`,
  `ceiling_s` with defaults (`:165-177`) and is not built from `Wiring`, so `ISEKAI_WIRING` cannot reach a render
  child. `gpu.open_session` passes a path to `gpunit.session` (`isekai/boundary/gpu.py:44`).
- **gpunit `0.7.0`:** `session(spec)` takes a `Spec` (`gpunit/library.py:73`); its `ceiling_s` becomes the pod's
  `GPUNIT_CEILING`, where `boot.sh` stops the pod; a session is refused when the window ends within
  `ceiling + timeout` (`gpunit/lifecycle.py:267-271`); records in `.gpunit/` — `pod`, `pending`, `volume` (`ends`),
  `volume.pending` (`gpunit/state.py:22-60`); `status`, `volume up`, `volume down` are CLI verbs, exit `3` a lost create.
- **`gpunit.toml`:** `ceiling = "45m"` (`:17`), `timeout = 420` (`:18`), `volume_ceiling = "4h"` (`:24`), the cards
  in `gpus` (`:5-11`), no `max_hourly`.
- **Prices**, RunPod secure, read at the cut through the RunPod MCP's `list-gpu-types`: RTX PRO 4500 Blackwell $0.72,
  L4 $0.59, RTX 4090 $0.89, A40 $0.59, RTX PRO 6000 Blackwell WK $2.59 per hour.
- **The hold:** a provisioning failure holds the pod reachable for `HOLD_SECONDS = 900`
  (`isekai/boundary/pod_start.py:23`), which the `model-provisioning` spec requires to end before the session's ceiling.
- **Rendering:** `render(run, flow, client, *, count, seeds, …)` (`isekai/pipeline/generate.py:504-517`); `draw_seeds`
  (`:95`), `seeds_for` (`:114`), `_submit` polls history to a deadline (`:640-653`); the record's fields
  (`isekai/foundation/artifacts.py:288-309`), new ones `NotRequired` under their version (D32).
- **Review:** `approve` (`isekai/pipeline/review.py:312`); the draft `PUT` and approve routes
  (`isekai/interface/ui/app.py:540`); `ui/src/views/Review.vue`.
- **Jobs:** `Jobs.prepare`, `stop`, `shutdown` and the child-line reader (`isekai/interface/ui/jobs.py:98-260`); the
  `/events` stream (`app.py:385`).
- **Tests holding the old ceiling:** `SESSION_CEILING_SECONDS = 45 * 60` (`tests/conftest.py:48`), used by
  `tests/test_infra.py:1032` (`pod-image:stop:armed-at-boot`) and `tests/test_pod_start.py:445`;
  `assert render.CEILING_S == spec.ceiling_s - 60` (`tests/test_render.py:604`).

| measured at the cut | value | command |
|---|---|---|
| tests in `tests/test_render.py` | 21 | `grep -c "def test_" tests/test_render.py` |
| tests in `tests/test_generate.py` | 82 | `grep -c "def test_" tests/test_generate.py` |
| tests in `tests/test_review.py` | 49 | `grep -c "def test_" tests/test_review.py` |
| tests in `tests/test_ui_jobs.py` | 6 | `grep -c "def test_" tests/test_ui_jobs.py` |

## Goals / Non-Goals

**Goals:** render from the browser behind a quote; a limit that fits the work; the volume opened and closed by the
job; billing read from gpunit; the images in a Renders view; one proof on a pod.

**Non-Goals:** revise, compare, the before and after; recording spend; more than one batch per session; a change to
the image.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `renders: {count, seeds}` in the draft and the approval, `NotRequired`; `render` takes an approval's seeds first and draws the rest; a typed seed is used as it is | one number, one image; old drafts read as count 1 | hashing a short seed; a version bump |
| [D2](#d2) | `render <runs>` with no request: every approval short of its count; a run without the flow skipped; an unapproved flow left out, named on stderr | render what is approved and not made; a draft waits for its approval | rendering every tracked flow; refusing the batch for one draft |
| [D3](#d3) | the limit: `--limit`, or the estimate — boot + images × the median of the flow's last 20 durations + teardown, × 1.5 — floored at `HOLD_SECONDS` + 300 s, capped by `gpunit.toml`'s `ceiling = "3h"`; passed to gpunit as `ceiling_s` and run by isekai's timer | a limit from the work; the hold must end before the pod stops | a fixed 45 minutes; shortening the hold in the image |
| [D4](#d4) | `max_hourly = 0.90` in `gpunit.toml`; the quote is the limit at that rate plus the volume at `config/render.json`'s rate | gpunit refuses a dearer card, so the price is a bound | a `pod_rate` guess; `2.60` |
| [D5](#d5) | `render --progress json`: `volume`, `pod`, `image n of N`, `teardown`, each with its state | the session view reads the verb's report | parsing `log.txt` |
| [D6](#d6) | `Wiring` gains `session` — the render `Seams` — and `volume` — up, down, status — so a render child and the job run on doubles | `ISEKAI_WIRING` reaches them | patching in tests |
| [D7](#d7) | `isekai/interface/ui/billing.py` reads `.gpunit/`: pod alert, volume item and band; `gpunit status --json` on start, every 30 s while needed, on Check again | gpunit's records are the truth | a log of alerts |
| [D8](#d8) | the job: `volume up --yes` → `render --limit … --progress json <runs>` → `volume down` unless kept; the quote, render, stop and check routes; `/session` | the volume is the job's to open and close | the operator closing it |
| [D9](#d9) | the Renders view and the large view; thumbnails in `~/isekai/.cache/` | the images back where sheets are decided | full-size images in a grid |
| [D10](#d10) | `CLAUDE.md`'s cost rule and D26, D36 follow the quoted limit | a decision lives where it is in force | |
| [D11](#d11) | **HUMAN · METERED** — two images rendered from the UI | only a pod proves the ceiling, the window and the durations | |

### D1

```json
"renders": {"count": 3, "seeds": [1]}
```

`ReviewDraft` and `ReviewApproved` gain `renders: NotRequired[Renders]`; a missing block reads as count 1, no seeds.
The draft `PUT` carries it; `approve` refuses a count below `len(seeds)` or a seed outside `0…2**64-1`, naming the
field. `render` takes `seeds_for` the approval: its seeds not yet rendered, then `draw_seeds` for the rest of the count.
`Review.vue` gains the ④ block per the design spec's J3·2.

### D2

```
for each run under <runs>, each flow its directory holds:
  no approval ──▶ left out, named on stderr
  newest approval has n images, count c, n < c ──▶ render c − n, its seeds first
```

`F=N` and `F=<source>` keep their meaning; a run without `F`'s directory is skipped silently.

### D3

```
estimate = boot + Σ images × median(last 20 durations of that flow, else per_image) + teardown
limit    = min(ceiling, max(HOLD_SECONDS + 300, estimate × limit_factor))
```

`config/render.json`:

```json
{ "boot_s": 180, "per_image_s": 60, "teardown_s": 120, "limit_factor": 1.5, "volume_rate": 0.005 }
```

`gpu.open_session` takes the limit and passes `dataclasses.replace(gpunit.load_spec(path), ceiling_s=limit)`.
`CEILING_S` goes; the watchdog runs at the limit, and the session prints `session limit <seconds>s` on stderr as it
opens. Each render records `duration` in seconds, from `_submit` to the
image's arrival. `gpunit.toml`: `ceiling = "3h"`, `max_hourly = 0.90`; a test holds `ceiling + timeout <
volume_ceiling`.

### D4

`quote(limit) = limit × max_hourly + limit × volume_rate`, the volume line on its own when *keep open* adds the 4-hour
window. The dialog shows the estimate's price as *about* and the limit's as *at most*.

### D5

```
{"step": "volume", "state": "up"} · {"step": "pod", "state": "ready"}
{"step": "image", "of": 4, "n": 2, "run": "…", "flow": "…", "state": "done"} · {"step": "teardown", "state": "done"}
```

### D6

`Wiring.session: Seams` and `Wiring.volume: Volume` — `up()`, `down()`, `status()` — default to the real gpunit;
`tests/e2e/wiring.py`'s `fake` sets a `FakeSession`-backed `Seams` and a recording `Volume`.

### D7

```
.gpunit/pod or pending, no session running ──▶ pod alert; Render disabled; Check again → gpunit status --json
.gpunit/volume, ends in the future        ──▶ quiet item, a timer to `ends`
.gpunit/volume, ends past · volume.pending ──▶ the band
```

### D8

```
POST /api/b/{batch}/render/quote    → per flow, left out, estimate, limit, price at most
POST /api/b/{batch}/render          {keep_open} → the job; /session opens
POST /api/job/stop                  → SIGINT to the render child
POST /api/billing/check             → gpunit status
```

`Jobs.render` reuses the slot; a volume `up` exit 3 raises the volume alert and stops the job. The dialog, the session
view and the alerts follow the design spec's J4, J8b and J8c.

### D9

`GET /api/b/{batch}/renders`, `…/renders/{digest}/{flow}/{version}/{seed}` and its `thumb`. A thumbnail is a JPEG of
at most 512 px on its long side, written once under `~/isekai/.cache/<digest>/…`; sources' thumbnails take the same
path. Views: `ui/src/views/Renders.vue`, `ui/src/views/RenderLarge.vue`, `ui/src/views/Session.vue`.

### D10

`CLAUDE.md`'s *"The ceiling is 45 minutes and ~$0.30 for a single pod session"* → *"a session's limit and price are
its quote's, at most `gpunit.toml`'s `ceiling` and `max_hourly`"*; D26 and D36 in `docs/decisions.md` likewise.

### D11

One batch of two images, rendered from the UI on the operator's go, quoted first. Its evidence: the session's
`ceiling_s` on the pod's environment in the log, both renders' `duration`, and the RunPod MCP listing no
`gpunit-isekai` pod or volume after.

## Tests

| layer | added | removed | where |
|---|---|---|---|
| unit, pytest | every `unit` scenario of the [review](specs/review/spec.md), [image-generation](specs/image-generation/spec.md), [cli](specs/cli/spec.md), [pod-image](specs/pod-image/spec.md) and [ui](specs/ui/spec.md) deltas | none | `tests/test_review.py`, `tests/test_generate.py`, `tests/test_render.py`, `tests/test_infra.py`, `tests/test_ui_billing.py`, `tests/test_ui_jobs.py`, `tests/test_ui_api.py` |
| e2e, Playwright | `ui:render:the-confirmation-starts-the-render`, `ui:renders:the-large-view-shows-its-sheet` | none | `tests/e2e/test_render.py` |

**End-to-end runs added:** the two above, once each, on Chromium: a confirmation that opens `/session`, and a large
view opened from the grid — both only a browser shows (T1). The large view is a step after the session's end in the
same test (T2).

`tests/test_render.py:604`'s assertion on `CEILING_S` is rewritten to the limit, still bound to its key.

## Dependencies

None.

## Risks / Trade-offs

- **[Risk]** a card's price rises above `max_hourly` → gpunit refuses that card and tries the next; if all are
  dearer, Render refuses before anything bills, naming `max_hourly`.
- **[Trade-off]** the floor makes a short session's *at most* about $0.30 though it costs about $0.09.
- **[Risk]** a median skewed by a slow first image → the factor 1.5 and the hold's floor leave room; the cap stays.
- **[Risk]** the metered proof spends → it is quoted, and runs on the operator's go only.

## Verdict

**Feasible with caveats:** the floor under the limit, and the proof phase that rents.
