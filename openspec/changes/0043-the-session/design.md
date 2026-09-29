# Design — 0043 the session

How `up.sh` places a pod only where it can render and refuses beside another, how `down.sh` leaves none, how the pod
stops itself and every hold ends in that stop, and how a render boot and a stop boot prove it — deferred to the
next version. **Verdict:
feasible** — shell edits held by text and stub tests; the key's stop was probed on a pod before the cut.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut (`2747163`):

- **`infra/up.sh`:**
  - `api()` is `:17-19`, `lost()` `:29-34` (it names the MCP's `list-pods`), `refuse()` `:36`, `check_volume` `:40-52`,
    `refuse_and_tear_down` `:56-61`, whose `bash ./infra/down.sh` at `:58` is the first non-echo line naming `down.sh`.
  - The GPU list is parsed at `:133-138`. The create body is `:143-158`, with `gpu: { id: $gpu, count: 1 }` at `:151`.
    The create loop is `:141-176`: a 400 tries the next type (`:170`), and `201|5??|000|""` runs `lost` (`:172-174`).
  - `.runpod_pod_id` is written at `:181` with nothing checked before it. The poll is `:211-234`; `verify_host_key`
    runs at `:237`.
- **`infra/down.sh`** (`:1-45`) deletes the recorded pod only. With no record it exits 0 (`:14-19`); a 204 removes the
  record files (`:27-29`), and a 404 or any other answer keeps them and exits 1 (`:30-45`).
- **`infra/render.sh:41-43`** refuses a recorded pod before its trap (`:75`), and no test binds it. `teardown()`
  (`:58-73`) runs `down.sh` only when a record exists.
- **`start.sh`:**
  - The first step, the SSH key, is `:9-14`, stamped at `:10`. `HOLD_SECONDS=900` is `:36`.
  - The provisioning hold (`:155`) and the memory step's type (`:170`), unread-figure (`:177`) and floor (`:184`)
    holds each end in `exec sleep "$HOLD_SECONDS"`.
  - ComfyUI starts at `:190-191`. PID 1 is `docker-init`, which runs `start.sh`.
- **The probe, 2026-09-29, on image `v0.29.1-rc1`:**
  - RunPod put `RUNPOD_API_KEY` and `RUNPOD_POD_ID` in PID 1's environment.
  - `POST /v2/pods/{id}/action {"action":"stop"}` with that key answered 200, `status: EXITED`; the MCP showed only
    `start` and `terminate` left, with `runtime.uptime` frozen.
  - The pod's `cost` still read the hourly rate. `DELETE` answered 204 on the EXITED pod.
  - The allocation reported `gpu.memory` 62 and `cudaVersion` 13.2.
- **REST v2:**
  - `CreateGpuConfig` takes `minRamPerGpu` (host GB) and `minCudaVersion` (`"major.minor"`), and refuses unknown fields.
  - `GET /v2/catalog/gpus/{id}` gives a card's `memory` (VRAM GB), or 404 for an unknown id.
  - `GET /v2/pods` has no filters. It pages by `nextCursor` and `hasNextPage`, and lists EXITED pods.
- **`tests/test_infra.py`** binds what this change moves:
  - The hold tests require `exec sleep "$HOLD_SECONDS"`: `:194-208`, `:211-224`, `:301-310`, and `memory_hold_faults`
    (`:992-1012`). `run_memory_step` (`:1092-1123`) stubs `sleep` on `PATH`.
  - `BOOT_STEPS` (`:785-792`) needs `date -u` on the line before each step. `unwarned_lost_create` (`:1377-1390`)
    needs `list-pods` in `up.sh`.
  - `unsafe_api_calls` (`:1344-1360`) scans `infra/` alone. The down.sh-after-cd rule is `:342-363`.
  - `removed_on_204` and `unrecorded_boot` (`:1275-1293`) read `down.sh`'s 204 line, and up.sh's unindented
    `echo "$pod_id" > .runpod_pod_id`.
- **The Dockerfile** copies `start.sh`, `tools/download_models.sh`, `config/models.json` and `provision.py`
  (`:82-85`), and makes the scripts executable at `:86`.
- **Prose:** `isekai/pipeline/generate.py:20-25` says the lifecycle lands with the second flow. `CLAUDE.md:223-225`
  names `down.sh` as the teardown, and `CLAUDE.md:239` puts renders on the pod's ephemeral disk. `docs/decisions.md`
  ends at D35 (`:343`).

## Goals / Non-Goals

**Goals:** no allocation that cannot render; no pod the tool cannot see; no pod that outlives its ceiling; no hold
that loops; no key in ComfyUI's environment; the session recorded.

**Non-Goals:** booting on intent; a Python `session()`; a session lock; an architecture gate; the rehash; the
volume's rent.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | the create carries `minRamPerGpu: 24` and `minCudaVersion: "12.8"`; a card under 24 GB of VRAM is skipped, named; an unknown card refuses | nothing that cannot render is placed; a typo is not a silent fallback | an architecture gate — no field reports one |
| [D2](#d2) | `up.sh` refuses on a record, then on any listed `isekai` pod, before the volume check; `lost()` names `down.sh` | the tool finds an orphan before it makes another | removing orphans in `up.sh` |
| [D3](#d3) | `down.sh` removes the recorded pod, then every other listed `isekai` pod; with no record, every listed one | one invariant: no `isekai` pod is left | the recorded pod only |
| [D4](#d4) | `tools/stop_pod.sh` stops the pod through v2 with RunPod's key, retrying until it succeeds, the wait doubling from 30 s to 5 minutes; `start.sh`'s first step arms it at 45 minutes, and a trap runs it however the boot ends | the probe proved the key; a laptop's watchdog dies with the laptop; an exit restarts the container, re-arming the ceiling | REST v1, which retires; an account key on the pod; a stop that gives up |
| [D5](#d5) | one `hold` function prints why, sleeps `HOLD_SECONDS`, then runs the stop; it replaces every `exec sleep "$HOLD_SECONDS"` | a restarted container would re-boot and hold forever | exiting, as today |
| [D6](#d6) | `start.sh` unsets `RUNPOD_API_KEY` before ComfyUI starts | least privilege: nothing ComfyUI's process prints can carry the key | leaving it in ComfyUI's environment |
| [D7](#d7) | D36 records `render.sh` as the session; `generate.py`, `CLAUDE.md` and `README.md` follow | the lifecycle is shell over an API the package never calls | a Python `session()` beside `up.sh` |
| [D8](#d8) | the operator builds `v0.30-rc1` on request, and `v0.30-rc2` once the boot's end changed | it publishes a public image | the agent dispatching it |
| [D9](#d9) | a render boot, then a stop boot, in one metered phase; deferred to the next version | the new digest renders; the stop and the refusal are live | a single boot |

### D1

**Placement.** `up.sh` gains `RAM_FLOOR_GB=24`, `VRAM_FLOOR_GB=24` and `CUDA_FLOOR="12.8"`. The body at `:151`
becomes:

```
gpu: { id: $gpu, count: 1, minRamPerGpu: $ram, minCudaVersion: $cuda },
```

with `--argjson ram` and `--arg cuda`. Before the create loop, each listed card is read from
`$API/catalog/gpus/<id>`, the id URL-encoded with `jq -rn --arg g "$gpu" '$g|@uri'`:

- **200** with `.memory` below `VRAM_FLOOR_GB`: `skipped: <card> has <n> GB, below 24`, and the card leaves the list.
- **404**: `refuse "RUNPOD_GPU_TYPE names <card>, which RunPod does not know; fix .env"`.
- **Anything else**: `refuse`, naming the card and the code.

A list that ends empty refuses, as `:135-138` does.

### D2

**`up.sh` refuses beside another pod.** A `check_no_pod` function, defined after `refuse_and_tear_down`, runs before
`check_volume` at `:126`:

- A record: `refuse "a pod is already recorded in .runpod_pod_id; run bash infra/down.sh"`.
- `isekai_pods` lists any pod: refuse naming each id and status, and `bash infra/down.sh`.
- The listing fails: refuse, naming the RunPod MCP's `list-pods`.

`lost()` says: "a pod named 'isekai' may exist and bill; run bash infra/down.sh — it finds and removes every
'isekai' pod — then re-run bash infra/up.sh". `unwarned_lost_create` needs `down.sh` in `lost()` in place of
`list-pods`.

**`infra/pods.sh`** holds `isekai_pods`, which `up.sh` and `down.sh` source after their `api()`. It walks
`$API/pods?limit=1000&cursor=…` while `hasNextPage` holds, and prints `<id> <status>` for each pod whose `name` is
`isekai` and whose `image` starts with `config/image.json`'s `.image`. A failed page returns non-zero.

### D3

**`down.sh` leaves no `isekai` pod.** The recorded path stays as `:20-45` has it, so its 204 line and 404 branch keep
their tests. After it, or with no record:

```
listed ──▶ none, and no record ──▶ "No pod to tear down."        exit 0
       ──▶ each id but the recorded one ──▶ DELETE ──▶ 204: "Removed <id> (<status>)"
                                                    └▶ else: report, failed=1
listing fails ──▶ "could not list pods; confirm with the RunPod MCP's list-pods"   exit 1
```

It exits 0 only when every removal answered 204. The no-record message of `:15-17` goes.

`render.sh`'s `teardown()` runs `down.sh` whether or not a record exists: a lost create records no pod, and
`down.sh` finds it by the listing.

### D4

**The pod stops itself.** `tools/stop_pod.sh`, copied to `/opt/isekai/tools/stop_pod.sh` and made executable:

```
wait_s=30
POST $API/pods/$RUNPOD_POD_ID/action {"action":"stop"}   curl --max-time 30, key via @<(printf …)
  200 ──▶ print the time, exit 0
  else ──▶ print the code, sleep wait_s, double it up to 300, try again
```

It never gives up: a stop that exited would leave ComfyUI billing, or end a hold's container, which restarts and
holds again.

`start.sh` gains a first step, before the SSH key, with its `date -u` line:

```
POD_CEILING_SECONDS=2700
STOP_POD=/opt/isekai/tools/stop_pod.sh
echo "$(date -u +%FT%TZ) step: the stop timer"
( sleep "$POD_CEILING_SECONDS"; exec bash "$STOP_POD" ) &
trap 'export RUNPOD_API_KEY; exec bash "$STOP_POD"' EXIT
```

The trap runs the stop however the script ends — ComfyUI exiting, with success or not, or a `set -e` step before
it — because an exit ends the container, RunPod restarts it, and the restart arms a fresh ceiling: a boot that died
before 45 minutes would never be stopped. A hold's `exec` replaces the shell, so the trap does not run twice.

The subshell copies the environment when it forks, so D6's `export -n` later leaves its key in place. `docker-init` reaps
it. `BOOT_STEPS` gains `( sleep "$POD_CEILING_SECONDS"`. `unsafe_api_calls`'s files gain `tools/stop_pod.sh`.

### D5

**Every hold ends in the stop.** Beside `HOLD_SECONDS`:

```
hold() {  # hold <line>...: say why, stay reachable HOLD_SECONDS, then stop the pod
    printf '%s\n' "$@" >&2
    echo "Holding ${HOLD_SECONDS}s, then stopping the pod." >&2
    sleep "$HOLD_SECONDS"
    exec bash "$STOP_POD"
}
```

Each hold's run of `echo … >&2` lines that ends in `exec sleep "$HOLD_SECONDS"` becomes one `hold` call carrying its
lines. The provisioning hold writes its marker first, as today. The tests that read `exec sleep "$HOLD_SECONDS"` read the `hold` calls and the function's
body; `run_memory_step` stubs `hold` beside `sleep`.

### D6

**ComfyUI starts without the key.** Before the ComfyUI step's `echo`, so the stamp stays on the line before
`python main.py`:

```
export -n RUNPOD_API_KEY
```

The key leaves the environment ComfyUI inherits and stays in the shell, whose trap re-exports it for the stop once
ComfyUI exits. ComfyUI runs as the script's child, not by `exec`, so the script outlives it. The timer's subshell,
forked at the first step, keeps its copy. A root process can still read `/proc/1/environ`
(D35's boundary); what this removes is the key in anything ComfyUI's process prints.

### D7

**The session is recorded.** In `docs/decisions.md`, after D35:

> ### D36 · A render session is `infra/render.sh`
>
> **It assembles every prompt before any pod exists, creates the pod through `up.sh`, tunnels to it strictly,
> renders, and tears it down on every exit.** Three bounds hold it: the laptop's watchdog; the pod's own stop at its
> ceiling; and `up.sh`, which refuses while any `isekai` pod is listed, with `down.sh` leaving none. One session runs
> at a time: a second started at once refuses, and its teardown removes the first's pod.
> - **Why:** the lifecycle is shell over a REST API the package never calls. A Python `session()` would be a second
>   creator of pods beside `up.sh`, which [D28](#d28--the-image-carries-code-the-volume-carries-weights) forbids,
>   and a pod the laptop can no longer reach must still stop.
> - **Made by:** `0035`, `0043`.

- **`isekai/pipeline/generate.py:20-25`:** `**No session lifecycle.** This stage talks to an endpoint somebody else
  brought up, … and no less.` → `**No session lifecycle.** This stage renders against the endpoint it is given;
  creating, tunnelling to and tearing down the pod is infra/render.sh's (docs/decisions.md D36).`
- **`CLAUDE.md:223`:** `` **Who tears it down** — `infra/down.sh`, which `render.sh`'s trap runs on every exit. `` →
  `` **Who tears it down** — `infra/down.sh`, which `render.sh`'s trap runs on every exit and which leaves no
  `isekai` pod; the pod also stops itself 45 minutes after it starts. ``
- **`CLAUDE.md:239`:** `**GPU renders live on the pod's ephemeral disk**` →
  `**GPU renders live in the pod's memory**`.
- **`README.md:395-398` and `:406-410`:** the tree gains `infra/pods.sh` and `tools/stop_pod.sh`, one line each.

### D8

**The rc build is the operator's.** Push `v0.30_the_session`, then
`gh workflow run build-image.yml --ref v0.30_the_session -f tag=v0.30-rc1`; the job summary's digest goes into
`config/image.json` with the tag `v0.30-rc1`.

**Rebuilt as `v0.30-rc2`.** The fix that ends every boot in the stop and makes the stop retry changed `start.sh` and
`tools/stop_pod.sh`, both baked into the image, after `v0.30-rc1` was built. The operator rebuilt from that tree
with `-f tag=v0.30-rc2`, and `config/image.json` pins it.

### D9

**A render boot and a stop boot prove it**, each inside 45 minutes and ~$0.30:

1. **A render session:** `render.sh` over a synthetic portrait, through `summon-anime-wai` and `conjure-anime-wai`.
   The create is accepted with the floors, and the MCP's `get-pod` shows `gpu.memory` of at least 24 while it runs.
2. **The stop:**
   - `up.sh`, then `bash /opt/isekai/tools/stop_pod.sh` over the `SSH:` line. The MCP shows the pod EXITED, with
     only `start` and `terminate` left.
   - A second `up.sh` refuses on the record. After 10 minutes stopped, `down.sh` removes the pod, and the MCP shows
     `pods: []`.
   - Once RunPod posts it, `list-pod-billing` for that pod shows whether the stopped minutes billed.

The record is `acceptance.md`, one line per piece of evidence, with no pod id, address or fingerprint. Planned at
~$0.20.

**Deferred, 2026-09-29, on the operator's ruling.** RunPod had no capacity for the listed cards, so both boots move
to the next version's metered phase, placed near its last phase. What the attempts proved and left open:

| session | what happened | proved |
|---|---|---|
| first | the create was accepted with the floors; the MCP read `gpu.memory` 30 and `cudaVersion` 13.0 on the `v0.30-rc1` digest; no `ssh.direct` came within 420 s, so `up.sh` tore the pod down and the MCP showed `pods: []` | the floors place a host that can render |
| second | no card was placed; no pod was created | — |

Open until then: that the image boots and renders, that the timer is armed, and the whole stop boot. The spend was
~$0.09, the first session's 7 minutes at $0.72/h. The next version proves this code on the image it pins.

## Dependencies

None.

## Risks / Trade-offs

- **EXITED may still bill** — the probe's pod kept its hourly `cost` → D9's deferred stop boot reads the billing. Either way the
  container and its memory are gone, and the next `up.sh` refuses until `down.sh` removes the pod.
- **The key's scope is unknown beyond stopping its own pod** → the key reaches only `start.sh`, the timer and
  `tools/stop_pod.sh`; a root process on the pod can still read it (D35).
- **A second session started at once** → the second refuses and its teardown removes the first's pod; D36 names it.
- **A catalogue id with a double space** — RunPod has some → ids come verbatim from `.env`, and a mismatch refuses
  (D1) rather than landing another card.
- **A new line naming `down.sh` ahead of `:58`** breaks the down.sh-after-cd rule → `check_no_pod` sits after
  `refuse_and_tear_down`, and `lost()`'s lines are `echo`s.

## Verdict

**feasible** — edits to the pod scripts and the image files, each held by a test; the stop's key proved on a pod.
The live acceptance is deferred to the next version ([D9](#d9)).
