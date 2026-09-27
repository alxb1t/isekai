# Design — 0034 RunPod's REST v2

How `infra/up.sh` and `infra/down.sh` move to RunPod's REST v2 and keep every behaviour they have today.
**Verdict: `feasible`.** Every line below was re-checked at `main` `6e2475d`; the v2 facts are from RunPod's
v2 reference and its OpenAPI spec, `https://api.runpod.io/v2/openapi.json`.

## Context

- **v1 retires on 2026-11-15.** v2's base is `https://api.runpod.io/v2`, with the same bearer key.
- **`infra/up.sh`:** builds a v1 body with `jq` (`:42-59`), posts it once to `https://rest.runpod.io/v1/pods`
  (`:61-64`), reads `.id` (`:66`), writes `.runpod_pod_id` and `.runpod_pod_image` (`:71-73`), then polls the v1
  list endpoint (`?id=`) every 5 s for `publicIp` and `portMappings."22"` (`:101-122`), running `down.sh` at the
  420 s deadline. `RUNPOD_GPU_TYPE` is a comma list turned into `gpuTypeIds`, and v1 "picks the first with
  capacity" (`:36-41`).
- **`infra/down.sh`:** one `DELETE /v1/pods/{id}` (`:14-16`); 204 removes both record files (`:18-20`); any other
  code prints "check the console" and exits 1.
- **A defect in the poll:** `curl -s` checks no status, and under `set -euo pipefail` a transport error or a
  non-JSON body makes `jq` abort the script after `.runpod_pod_id` is written — skipping the deadline teardown.
- **The tests are static** (`tests/test_infra.py`): `:108` and `:117` read `volumeMountPath`, `:306` finds the line
  holding `POST https://rest.runpod.io`, `:413` reads `containerDiskInGb`, `:747` wants `imageName: $image,`, and
  `:795` keys on `"$code" = "204"`. No test runs either script.

## Goals / Non-Goals

**Goals**

- Both scripts speak v2 only, before 2026-11-15.
- Every behaviour survives: the pinned digest, the GPU fallback, the bounded poll and its teardown, the record
  files, the timestamps.

**Non-Goals**

- Anything the [proposal](proposal.md#not-in-this-change) sets out.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | try each `RUNPOD_GPU_TYPE` in order; a 400 moves on, anything else stops | v2 places one type; v1 fell back server-side | the first type only; a catalog read first |
| [D2](#d2) | poll `.ssh.direct`; a failed read is *not yet* | keeps today's contract, which `set -e` broke by accident | leaving the abort |
| [D3](#d3) | only 204 tears down; a 404 asks for the MCP | a 404 is also a wrong key, and a false *gone* bills | treating 404 as gone |
| [D4](#d4) | every call reads its status and prints `problem+json` | a missing `.id` told the operator nothing | retries |
| [D5](#d5) | the static tests move to v2, and guard against v1 and for Secure Cloud | the suite is the only one these scripts have | a test that runs the scripts |
| [D6](#d6) | a patch, with no spec delta | the product and every requirement are unchanged | a minor |
| [D7](#d7) | one metered boot proves it | only a live call shows v2 accepts the body | trusting the static tests |

### D1

**The create call, and the GPU fallback.**

| v1 | v2 |
|---|---|
| `imageName: $image` | `image: $image` |
| `gpuTypeIds: [...]`, `gpuCount: 1` | `gpu: {id: $gpu, count: 1}` — one type per call |
| `networkVolumeId: $vol`, `volumeMountPath: "/runpod-volume"` | `mounts: {network: [{volumeId: $vol, path: "/runpod-volume"}]}` |
| `containerDiskInGb: 30` | `disk: 30` |
| `cloudType: "SECURE"` | `cloud: "SECURE"`, still explicit |
| `ports`, `dataCenterIds`, `env`, `name` | unchanged |

- Each script sets `API="https://api.runpod.io/v2"` once and calls `"$API/pods"`.
- `up.sh` splits `RUNPOD_GPU_TYPE` on commas and posts once per type, in order: a **201** is the pod; a **400**
  (no capacity, or a rule broken) moves to the next type; any other status — 402, 403, 422, 5xx — stops and
  reports ([D4](#d4)). The comment at `:36-41` says why the list exists, and that v2 no longer walks it for us.

### D2

**The poll keeps its contract.** `GET "$API/pods/$pod_id"` every 5 s; ready when `.ssh.direct.host` and
`.ssh.direct.port` are both set — v2 leaves `ssh.direct` null until the public port is assigned, which is the v1
condition. **A read that fails** — a transport error, a non-2xx status, a body that is not JSON — **counts as not
ready yet**, so the loop always reaches its 420 s deadline and runs `down.sh`. "Port 22 mapped at" stays, and the
comment on RunPod's SSH proxy (`:76-100`) stays true of `ssh.proxy`.

### D3

**Teardown.** `DELETE "$API/pods/$pod_id"`; the `if [ "$code" = "204" ]` branch and its `rm -f` stay. A **404**
prints that the API does not know the pod — it may be gone, or the key may be wrong — and asks for the RunPod MCP's
confirmation, then exits 1 with the record files kept. Any other status prints its `problem+json` and exits 1.

### D4

**Errors by name.** Each call captures the body and `curl -w "%{http_code}"`. A failure prints the status and
the body's `title` and `detail` when it is `problem+json`, and the raw body otherwise. No retries: the GPU list is
the only one, and the poll already repeats.

### D5

**The tests.** `tests/test_infra.py:108` and `:117` read the mount's `path`; `:306` finds the line that posts to
`$API/pods`; `:413` reads `disk:`; `:747` wants `image: $image`; `:795` is unchanged. New:
`test_no_script_calls_the_retired_api` — no file under `infra/` names `rest.runpod.io` — with its twin, and
`test_the_pod_is_asked_for_secure_cloud` — `cloud: "SECURE"` stays explicit — each `spec_exempt`, since no requirement names either.

### D6

**A patch, with no spec delta.** No format version moves, no verb or flag is deprecated, and the product is
unchanged. No requirement names the API version, and the ones the scripts hold — `pod-image`'s boot and record
requirements, and `model-provisioning`'s volume refused before a pod is created — stay true word for word. D2 is
the port keeping an existing contract, not a new behaviour.

### D7

**The proof: one metered boot.** `up.sh` on v2 — its create, its poll, its record files — then SSH, the tunnel,
one `conjure` render with `--count 1` (no photograph), `down.sh`, and the RunPod MCP confirming the pod gone. About
5 to 10 minutes and ~$0.10, under the standing ceiling.

## Dependencies

None.

## Risks / Trade-offs

- [v2's 400 covers a broken rule as well as no capacity] → the loop tries every type, then reports the last
  `problem+json`; a broken rule fails every type the same way.
- [A 404 right after creation, before the pod is readable] → a failed read is *not yet* ([D2](#d2)).
- [The static tests cannot prove v2 accepts the body] → [D7](#d7).

## Verdict

`feasible`.
