# Tasks — 0043 the session

The gates and the reconciler; the pod's stop; the docs; then the operator's rc build, per [design](design.md). The
metered render boot and stop boot are deferred to the next version ([D9](design.md#d9)).

## Progress

- [x] 1 — The gates and the reconciler
- [x] 2 — The pod's stop
- [x] 3 — The docs
- [x] 4 — 🛑 **HUMAN** — the rc build

Line numbers are `2747163`'s. Every new test carries `@pytest.mark.spec` with the key its task names, and has a twin.

## 1 — The gates and the reconciler

- [x] 1.1 **HALT CHECK** — nothing lists pods, the create carries no floor, and every hold exits.
  Verify: `grep -c -e 'minRamPerGpu' -e 'isekai_pods' infra/up.sh` prints `0`, `ls infra/pods.sh tools/stop_pod.sh` fails, and `grep -c -F 'exec sleep "$HOLD_SECONDS"' start.sh` prints `4`.
- [x] 1.2 Write `infra/pods.sh` with `isekai_pods`, per [D2](design.md#d2).
  Verify: `grep -c '^isekai_pods()' infra/pods.sh` prints `1`, and `grep -q hasNextPage infra/pods.sh && echo ok` prints `ok`.
- [x] 1.3 In `infra/up.sh`, add the floors to the create and the catalogue's VRAM skip and unknown-card refusal, per [D1](design.md#d1).
  Verify: `grep -c -F 'minRamPerGpu: $ram, minCudaVersion: $cuda' infra/up.sh` prints `1`, and `grep -q 'catalog/gpus/' infra/up.sh && echo ok` prints `ok`.
- [x] 1.4 In `infra/up.sh`, add `check_no_pod` before `check_volume`, and make `lost()` name `down.sh`, per [D2](design.md#d2).
  Verify: `grep -c '^check_no_pod$' infra/up.sh` prints `1`, and `sed -n '/^lost()/,/^}/p' infra/up.sh | grep -c 'list-pods'` prints `0`.
- [x] 1.5 In `infra/down.sh`, remove every other listed `isekai` pod after the recorded one, per [D3](design.md#d3).
  Verify: `grep -c 'source ./infra/pods.sh' infra/down.sh` prints `1`, and `grep -c 'No .runpod_pod_id — nothing to tear down' infra/down.sh` prints `0`.
- [x] 1.6 Add to `tests/test_infra.py`: `test_the_create_carries_the_floors` (`pod-image:placement:the-create-carries-the-floors`), `test_a_card_short_of_memory_is_skipped` (`pod-image:placement:a-card-short-of-memory-is-skipped`) and `test_an_unknown_card_is_refused` (`pod-image:placement:an-unknown-card-is-refused`).
  Verify: `grep -c -e '^def test_the_create_carries_the_floors' -e '^def test_a_card_short_of_memory_is_skipped' -e '^def test_an_unknown_card_is_refused' tests/test_infra.py` prints `3`.
- [x] 1.7 Add to `tests/test_infra.py`: `test_a_recorded_pod_refuses_a_creation` (`pod-image:reconcile:a-recorded-pod-refuses`), `test_a_listed_pod_refuses_a_creation` (`pod-image:reconcile:a-listed-pod-refuses`) and `test_the_teardown_leaves_no_pod` (`pod-image:reconcile:the-teardown-leaves-none`).
  Verify: `grep -c -e '^def test_a_recorded_pod_refuses_a_creation' -e '^def test_a_listed_pod_refuses_a_creation' -e '^def test_the_teardown_leaves_no_pod' tests/test_infra.py` prints `3`.
- [x] 1.8 Add `test_a_session_refuses_a_recorded_pod` (`pod-image:reconcile:a-session-refuses-a-recorded-pod`) to `tests/test_infra.py`, and bind `unwarned_lost_create` to `lost()` naming `down.sh` under `pod-image:reconcile:a-lost-create-names-the-teardown`.
  Verify: `grep -c '^def test_a_session_refuses_a_recorded_pod' tests/test_infra.py` prints `1`, and `grep -c 'pod-image:reconcile:a-lost-create-names-the-teardown' tests/test_infra.py` prints `1`.

## 2 — The pod's stop

- [x] 2.1 Write `tools/stop_pod.sh`, per [D4](design.md#d4), and add it to the `Dockerfile`'s copies and its `chmod`.
  Verify: `grep -q -F '{"action":"stop"}' tools/stop_pod.sh && echo ok` prints `ok`, and `grep -c 'tools/stop_pod.sh' Dockerfile` prints `2`.
- [x] 2.2 In `start.sh`, add the stop timer as the first step, per [D4](design.md#d4).
  Verify: `grep -c -F '( sleep "$POD_CEILING_SECONDS"; exec bash "$STOP_POD" ) &' start.sh` prints `1`, and `grep -c '^POD_CEILING_SECONDS=2700$' start.sh` prints `1`.
- [x] 2.3 In `start.sh`, add `hold` and make every hold call it, per [D5](design.md#d5).
  Verify: `grep -c -F 'exec sleep "$HOLD_SECONDS"' start.sh` prints `0`, and `grep -c '^hold()' start.sh` prints `1`.
- [x] 2.4 In `start.sh`, unset `RUNPOD_API_KEY` before the ComfyUI step, per [D6](design.md#d6).
  Verify: `grep -c '^unset RUNPOD_API_KEY$' start.sh` prints `1`.
- [x] 2.5 Add to `tests/test_infra.py`: `test_the_pod_arms_its_stop_first` (`pod-image:stop:armed-at-boot`), `test_every_hold_ends_in_the_stop` (`pod-image:stop:a-hold-ends-in-the-stop`) and `test_a_failed_stop_is_retried_then_given_up` (`pod-image:stop:a-failed-stop-is-retried`).
  Verify: `grep -c -e '^def test_the_pod_arms_its_stop_first' -e '^def test_every_hold_ends_in_the_stop' -e '^def test_a_failed_stop_is_retried_then_given_up' tests/test_infra.py` prints `3`.
- [x] 2.6 Add `test_comfyui_starts_without_the_key` (`pod-image:stop:comfyui-holds-no-key`) to `tests/test_infra.py`; rebind the hold tests at `:194-224`, `:301-310`, `memory_hold_faults` and `run_memory_step` to `hold`, and add `tools/stop_pod.sh` to `unsafe_api_calls`'s files.
  Verify: `grep -c '^def test_comfyui_starts_without_the_key' tests/test_infra.py` prints `1`, and `grep -q -F 'tools/stop_pod.sh' tests/test_infra.py && echo ok` prints `ok`.
- [x] 2.7 Check the image files the way `CLAUDE.md` asks of an image phase.
  Verify: `bash -n start.sh && bash -n tools/stop_pod.sh && echo ok` prints `ok`, and `docker build --check .` exits `0`.

## 3 — The docs

- [x] 3.1 Add D36 to `docs/decisions.md`, per [D7](design.md#d7).
  Verify: `grep -c '^### D36 · A render session is ' docs/decisions.md` prints `1`.
- [x] 3.2 Rewrite `isekai/pipeline/generate.py`'s session paragraph, per [D7](design.md#d7).
  Verify: `grep -c 'land with the version that adds a second flow' isekai/pipeline/generate.py` prints `0`, and `grep -c 'D36' isekai/pipeline/generate.py` prints `1`.
- [x] 3.3 In `CLAUDE.md`, name `down.sh`'s sweep and the pod's own stop in the teardown rule, and put renders in the pod's memory, per [D7](design.md#d7).
  Verify: `grep -c 'leaves no' CLAUDE.md` prints `1`, and `grep -c "the pod's ephemeral disk" CLAUDE.md` prints `0`.
- [x] 3.4 Add `infra/pods.sh` and `tools/stop_pod.sh` to `README.md`'s tree, per [D7](design.md#d7).
  Verify: `grep -c -e '── pods.sh' -e '── stop_pod.sh' README.md` prints `2`.

## 4 — 🛑 **HUMAN** — the rc build

- [x] 4.1 The operator pushes `v0.30_the_session` and runs `gh workflow run build-image.yml --ref v0.30_the_session -f tag=v0.30-rc1`, per [D8](design.md#d8); the job summary's digest and the tag go into `config/image.json`.
  Verify: `grep -c '"tag": "v0.30-rc1"' config/image.json` prints `1`.

## Deferred — the acceptance

RunPod had no capacity on 2026-09-29, so the render boot and the stop boot move to the next version's metered
phase, near its last phase, per [D9](design.md#d9). That version runs these checks against the image it pins:

- The render session over `summon-anime-wai` and `conjure-anime-wai` leaves renders for both, and no line of the
  batch's log starts with `refused`.
- The stop boot: the pod reaches EXITED, a second `up.sh` refuses, and the stopped pod's billing is read.
- The evidence is one line each in that change's `acceptance.md`, with no pod id, address or fingerprint.
