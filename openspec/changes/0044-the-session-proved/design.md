# Design — 0044 the session proved

How the pod listing stops hanging, missing and over-matching, how a refused session leaves a listed pod alone, and
how a render boot and a stop boot prove v0.30's image as shipped. **Verdict: feasible** — laptop-side shell edits
held by stub tests, then one metered phase on the pinned digest.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut (`a76a5f5`):

- **`infra/pods.sh`** (`:1-21`): `isekai_pods` loops `while :` (`:9`), reads `.pagination.hasNextPage` (`:17-18`) and
  `.pagination.nextCursor` (`:19`), with no page cap and no check that the cursor moves. It selects
  `.name == "isekai" and ((.image // "") | startswith($image)) and .status != "TERMINATED"` (`:13-14`), with `$image`
  from `config/image.json`'s `.image`, `ghcr.io/alxb1t/isekai`. `up.sh` creates pods as `image@digest` (`:148`, `:198`).
- **`infra/up.sh`:** `lost()` (`:34-38`) prints and returns; the create loop runs `lost` for `201|5??|000|""` and then
  `exit 1` (`:220-223`), the same exit as every refusal. `check_no_pod` (`:69-77`) refuses a record, a failed listing
  and a listed pod.
- **`infra/render.sh`:** `bash ./infra/up.sh 2>&1 | tee -a "$log" "$up_out"` (`:96`) under `set -euo pipefail` (`:10`).
  `teardown()` (`:58-73`) runs `down.sh` on every trapped exit (`:68-70`). The record guard (`:42-43`) runs before the
  trap (`:75`).
- **`infra/down.sh`** sweeps every listed pod but the recorded one (`:56-77`).
- **`tests/test_infra.py`:**
  - `listed_pod` (`:2202-2209`) builds `image` as `<image>@sha256:0`, and `pod_pages` pages across a cursor.
  - `test_a_listed_pod_refuses_a_creation` (`:2281`) and `test_the_teardown_leaves_no_pod` (`:2381`) run the listing
    against stubbed pages.
  - `session_with_a_lost_create` (`:2771-2795`) stubs `up.sh` as `exit 1`, and
    `test_a_session_whose_create_is_lost_still_tears_down` (`:2808`) holds that such a session runs `down.sh`.
- **`README.md`:**
  - `:433-437` is the script table; its `start.sh` row says "authorize your key → start `sshd` → start ComfyUI".
  - `:448-478` is the provisioning diagram: step 0 is the volume read, `:463` says `exec ComfyUI`, and TEAR DOWN deletes
    one pod by id.
  - `:61-63` is the lifecycle line.
- **`CHANGELOG.md:12-25`:** `0.30.0` has bullets and no `###` heading, the only version without one.
  `tests/test_changelog.py`'s `format_problems` (`:54-80`) checks a `###` heading's name only when one is there;
  `test_the_format_check_reports_each_break` (`:132`) is parametrised by break.
- **v0.30's D9, deferred:** a render boot and a stop boot, planned at ~$0.20. The probe of 2026-09-29 read
  `RUNPOD_API_KEY` and `RUNPOD_POD_ID` from `/proc/1/environ`; an SSH shell carries neither. `tools/stop_pod.sh`
  refuses without them (`:15-16`).

## Goals / Non-Goals

**Goals:** a listing that fails rather than hangs, misses or over-matches; a refused session that deletes nothing;
docs that match the scripts; the changelog's sections checked; `v0.30-rc2` proved on a pod.

**Non-Goals:** a rebuild; any change to `start.sh` or `tools/stop_pod.sh`; a session lock.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | the listing fails on a repeated cursor and on a named pod with no image, and matches `image`, `image@…` or `image:…` | a fault refuses instead of hanging or missing; a look-alike image is not this project's | a page cap alone, which still loops the pages under it |
| [D2](#d2) | `lost` exits 3; `render.sh` reads `up.sh`'s status and, with no record, runs `down.sh` only on 3 | `up.sh` names a listed pod; removing it is `down.sh`'s act, on the operator's word | sweeping after any failure, as v0.30 does |
| [D3](#d3) | `README.md`'s table, diagram and lifecycle line name the pod check, the catalogue, the sweep and the stop | the docs contradict the scripts | — |
| [D4](#d4) | `0.30.0` gains `### Security`, a stated exception to append-only; `format_problems` refuses a bullet outside a section | the format's rule, now checked | a new bullet |
| [D5](#d5) | a render boot and a stop boot on `v0.30-rc2`, as v0.30's D9 planned, with the stop boot reading the listing, the key's scope and the signal path | the digest `main` pins is proved; what converge left open is read | a rebuild first |

### D1

**The listing.** In `isekai_pods`:

- **The match:** `.image == $image or (.image | startswith($image + "@")) or (.image | startswith($image + ":"))`.
- **No image:** a pod whose `name` is `isekai` and whose `image` is missing or empty makes the function return non-zero,
  naming the pod on stderr.
- **The cursor:** the loop keeps the cursor it asked with. A `nextCursor` equal to it, with `hasNextPage` true, returns
  non-zero, naming the repeat on stderr.

Each failure reaches `check_no_pod` and `down.sh` as the failed listing they already refuse on.

### D2

**A refused session leaves a listed pod.**

- **`infra/up.sh`:** `LOST_CREATE_EXIT=3`; the create loop's `lost` case exits with it. Every other failure keeps 1.
- **`infra/render.sh`:** the `up.sh` line becomes
  `bash ./infra/up.sh 2>&1 | tee -a "$log" "$up_out" || { up_status=${PIPESTATUS[0]}; exit "$up_status"; }`.
  `teardown()` runs `down.sh` when `.runpod_pod_id` exists, when `.runpod_pod_pending` exists, or when `up_status` is
  3; otherwise it prints that no pod was made. `up_status` is not preset before `up.sh` runs, so an interrupt during
  `up.sh`'s pre-create checks sweeps nothing. A `.runpod_pod_pending` left by an earlier session refuses before the
  trap is set, naming `down.sh`.
- **The pending-create marker:** `up.sh` writes `.runpod_pod_pending` (gitignored) just before its first create and
  removes it once `.runpod_pod_id` and `.runpod_pod_image` are written, or when every create was definitely refused. A
  lost create, an interrupt mid-create, or a failed record write leaves it, so the session still sweeps: the
  spend-safe side. `down.sh` removes it once its sweep leaves no pod.

`session_with_a_lost_create` stubs `up.sh` as `exit 3`. A second stub, a refusal with `exit 1`, must leave `down.sh`
unrun. `session_interrupted` signals the session from `up.sh`: before the marker it must leave `down.sh` unrun, after
it it must run it. D36 needs no edit. Its "a second started at once refuses, and its teardown removes the first's pod" stays true
within one checkout, whose record the second session sees. A refused session in another checkout now removes
nothing.

### D3

**The README follows the scripts.**

- **The table, `README.md:435-437`:**
  - `start.sh`: "arm the stop timer → authorize your key → start `sshd` → start ComfyUI; every way out
    stops the pod".
  - `infra/up.sh`: gains "refuses beside a recorded or listed `isekai` pod, reads each card from the catalogue".
  - `infra/down.sh`: "`DELETE`s the recorded pod and every other listed `isekai` pod".
- **The diagram, `:448-478`:**
  - Step 0 gains the pod check and the catalogue read.
  - Step 4 gains the stop timer, and `exec ComfyUI` becomes `run ComfyUI`.
  - TEAR DOWN names the sweep, and the pod's own stop at 45 minutes.
- **The lifecycle line, `:61-63`:** names the sweep and the pod's own stop.

### D4

**The changelog.** `### Security` goes between `CHANGELOG.md:12`'s heading and its first bullet. This version's own
bullet names the exception. `format_problems` gains: a `- ` bullet after a `## [X.Y.Z]` heading and before any `###`
heading is a problem. `test_the_format_check_reports_each_break` gains that case.

### D5

**A render boot and a stop boot on `v0.30-rc2`**, each inside 45 minutes and ~$0.30, planned at ~$0.20:

1. **The render boot:** `render.sh` over a synthetic portrait, through `summon-anime-wai` and `conjure-anime-wai`.
   The MCP's `get-pod` reads `gpu.memory` at least 24; the pod's log, through the MCP's `stream-pod-logs`, shows
   `step: the stop timer`.
2. **The stop boot:** `up.sh`, then over the `SSH:` line:
   - **The listing:** a second `up.sh` refuses, naming the pod.
   - **The key's scope:** a read-only `GET /v2/pods` with the pod's key answers.
   - **A refused key:** `stop_pod.sh` run with a bogus key under `timeout 40` prints what a 401 prints.
   - **The stop:** `stop_pod.sh` run with the key and pod id read from `/proc/1/environ`, never printed. The MCP shows
     the pod EXITED, and its log after the stop shows the signal path.
   - **The end:** 10 minutes EXITED, then `down.sh`; the MCP shows `pods: []`. The stopped minutes' billing is read
     once RunPod posts it.

The record is `acceptance.md`, one line per piece of evidence, with no pod id, address, fingerprint or key. What the
refused key and the signal path show becomes cards for the next rebuild.

## Dependencies

None.

## Risks / Trade-offs

- **RunPod has no capacity again** → the phase waits for the operator's go; no code depends on it.
- **The live listing names the image another way** → D1 fails closed, and the stop boot's second `up.sh` shows it.
- **A stopped pod bills** → read at the end of the stop boot; `down.sh` ends it either way.
- **`teardown()` now prints instead of sweeping after a refusal** → a pod left by a lost create in an earlier session
  is still named by `up.sh`'s refusal, and `down.sh` removes it on the operator's word.

## Verdict

**feasible** — laptop-side edits held by stub tests; the image proved on the pod it pins.
