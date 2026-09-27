# Tasks — 0034 RunPod's REST v2

`up.sh` first, then `down.sh` and the docs, then one metered boot on v2 ([D7](design.md#d7)).

## Progress

- [x] 1 — `infra/up.sh` on v2
- [ ] 2 — `infra/down.sh` on v2, and the docs
- [ ] 3 — 🛑 **HUMAN · METERED · HALT** — one boot on v2, one render, teardown confirmed

Line numbers are `6e2475d`'s; find each site by the text it names.

## 1 — `infra/up.sh` on v2

- [x] 1.1 **HALT CHECK** — both scripts still call RunPod's REST v1.
  Verify: `cat infra/up.sh infra/down.sh | grep -c 'rest.runpod.io/v1'` prints `3`.
- [x] 1.2 In `infra/up.sh`, set `API` once, build the v2 body [D1](design.md#d1) maps, and post it once per type in `RUNPOD_GPU_TYPE`, in order: 201 is the pod, 400 moves to the next type, any other status stops and reports per [D4](design.md#d4).
  Verify: `grep -c 'rest.runpod.io' infra/up.sh` prints `0`, and `grep -c 'gpu: {' infra/up.sh` prints `1`.
- [x] 1.3 Rewrite `infra/up.sh`'s poll per [D2](design.md#d2): `GET "$API/pods/$pod_id"`, ready when `.ssh.direct.host` and `.ssh.direct.port` are set, and a failed read counted as not yet, so the 420 s teardown always runs.
  Verify: `grep -c 'ssh.direct' infra/up.sh` prints a number above `0`, and `grep -c -e 'publicIp' -e 'portMappings' infra/up.sh` prints `0`.
- [x] 1.4 Move `tests/test_infra.py`'s v1 names to v2 — `:108` and `:117` (the mount's `path`), `:306` (the line posting to `$API/pods`), `:413` (`disk:`), `:747` (`image: $image`) — and add `test_the_pod_is_asked_for_secure_cloud`, per [D5](design.md#d5).
  Verify: `grep -c -e 'volumeMountPath' -e 'containerDiskInGb' -e 'imageName' tests/test_infra.py` prints `0`, and `grep -c '^def test_the_pod_is_asked_for_secure_cloud' tests/test_infra.py` prints `1`.
- [x] 1.5 Name `disk: 30` in `start.sh`'s comment (`:46`), and say in `.env.example`'s comment that `RUNPOD_GPU_TYPE` is a comma list tried in order.
  Verify: `grep -c 'containerDiskInGb' start.sh` prints `0`, and `grep -c 'tried in order' .env.example` prints `1`.

## 2 — `infra/down.sh` on v2, and the docs

- [ ] 2.1 In `infra/down.sh`, set `API` and delete on `"$API/pods/$pod_id"`; keep the `"$code" = "204"` branch; a 404 asks for the RunPod MCP's confirmation and keeps the record files per [D3](design.md#d3); any other status prints its `problem+json` per [D4](design.md#d4).
  Verify: `grep -c 'rest.runpod.io' infra/down.sh` prints `0`, and `grep -c '"$code" = "404"' infra/down.sh` prints `1`.
- [ ] 2.2 Add `test_no_script_calls_the_retired_api` and its twin `test_the_retired_api_check_catches_a_v1_call` to `tests/test_infra.py`, `spec_exempt`, per [D5](design.md#d5).
  Verify: `grep -c -e '^def test_no_script_calls_the_retired_api' -e '^def test_the_retired_api_check_catches_a_v1_call' tests/test_infra.py` prints `2`.
- [ ] 2.3 Name v2's calls in `README.md`'s pod diagram (`:423`, `:436`, `:447`).
  Verify: `grep -c '/v1/pods' README.md` prints `0`.

## 3 — 🛑 **HUMAN · METERED · HALT** — one boot on v2, one render, teardown confirmed

**Ceiling: 45 minutes and ~$0.30; planned at about 10 minutes and ~$0.10.** The pod goes up only through
`infra/up.sh` and down through `infra/down.sh`, in the same session; the RunPod MCP confirms it gone. No
photograph: `conjure` only.

- [ ] 3.1 ⛔ **HALT.** Ask the operator for an explicit go that quotes the ceiling, and for an approved `conjure-anime-wai` run and its `--runs` root; record the go as the first line of `openspec/changes/0034-runpod-rest-v2/acceptance.md`, `Go: <date>`.
  Verify: `grep -c '^Go: ' openspec/changes/0034-runpod-rest-v2/acceptance.md` prints `1`.
- [ ] 3.2 ⚠️ **METERED.** `bash infra/up.sh`, the tunnel, `python -m isekai generate --flow conjure-anime-wai --count 1 --server http://127.0.0.1:8188 --runs <root> <run>`, then `bash infra/down.sh`, and the RunPod MCP confirms the pod gone. Record each command's output in `acceptance.md`, with no absolute path.
  Verify: `grep -c -e 'Port 22 mapped at' -e 'pod gone' openspec/changes/0034-runpod-rest-v2/acceptance.md` prints a number above `1`.
