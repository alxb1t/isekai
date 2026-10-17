# Tasks — 0060 the working window

The pin, the window, the pod's cards, the skill; then the image rebuilt by hand, and one metered window across pods,
per [design](design.md). Every new test carries `@pytest.mark.spec` with the key its task names.

## Progress

- [x] 1 — The pin
- [x] 2 — The window
- [ ] 3 — The pod's cards
- [ ] 4 — The skill and the protocol
- [ ] 5 — ⚠️ **HUMAN** — rebuild as v0.36-rc1, re-pin
- [ ] 6 — ⚠️ **HUMAN · METERED** — one window: volume up, a first and a second render, volume down

## 1 — The pin

- [x] 1.1 **HALT CHECK** — gpunit is pinned at `v0.2.0`, and the `Dockerfile` adds its `boot.sh` from that tag.
  Verify: `grep -c 'gpunit@v0.2.0' pyproject.toml` prints `1`, and `grep -c 'gpunit/v0.2.0/boot/boot.sh' Dockerfile` prints `1`.
- [x] 1.2 Move gpunit's tag in `pyproject.toml` to `v0.7.0` and run `uv lock`, per [D1](design.md#d1).
  Verify: `grep -c 'gpunit@v0.7.0' pyproject.toml` prints `1`, `grep -c 'gpunit?rev=v0.7.0' uv.lock` prints a number of at least `1`, and `uv run pytest -q tests/test_render.py` exits 0.
- [x] 1.3 In `Dockerfile`, `ADD` `boot.sh` from `v0.7.0` with the checksum [D1](design.md#d1) gives; re-derive `config/image.json`'s `files` with `uv run python -m tools.image_record`.
  Verify: `grep -c 'sha256:517ade6bf20d9869baeb1f1ff1ab45d9ab63c2fa477127ff11dac89611bec842' Dockerfile` prints `1`, and `uv run pytest -q tests/test_infra.py` exits 0.

## 2 — The window

- [x] 2.1 **HALT CHECK** — `gpunit.toml` names the kept volume.
  Verify: `grep -c '^volume = "db7sc8cild"$' gpunit.toml` prints `1`.
- [x] 2.2 In `gpunit.toml`, replace `volume` with `volume_gb = 50` and `volume_ceiling = "4h"` under a comment, per [D2](design.md#d2).
  Verify: `grep -c -E '^volume_gb = 50$|^volume_ceiling = "4h"$' gpunit.toml` prints `2`, and `uv run python -c 'from pathlib import Path; import gpunit; print(gpunit.load_spec(Path("gpunit.toml")).volume_gb)'` prints `50`.
- [x] 2.3 In `tests/test_infra.py`, replace `unnamed_volume` and its tests with `window_volume_faults`, its tests and their twin, binding `model-provisioning:reachability:provisioning-requires-the-network-volume` and `model-provisioning:reachability:the-window-volume-clears-the-floor`, per [D2](design.md#d2).
  Verify: `grep -c 'unnamed_volume' tests/test_infra.py` prints `0`, and `grep -c 'reachability:the-window-volume-clears-the-floor' tests/test_infra.py` prints a number of at least `1`.
- [x] 2.4 Describe the window in `README.md`, per [D3](design.md#d3).
  Verify: `grep -c 'gpunit volume up' README.md` prints a number of at least `3`, and `grep -c -E 'persistent RunPod|volume stays|3\.50/mo' README.md` prints `0`.
- [x] 2.5 Rewrite D27 in `docs/decisions.md` for the window and add the gpunit rebuild's order to `docs/pins.md`'s gpunit recipe, per [D3](design.md#d3).
  Verify: `grep -c 'volume_ceiling' docs/decisions.md` prints a number of at least `1`, `grep -c 'before any render' docs/pins.md` prints `1`, and `uv run pytest -q tests/test_docs.py` exits 0.

## 3 — The pod's cards

- [ ] 3.1 **HALT CHECK** — the cards still hold: the stale `(D2)`, the defaulted swap, the type read by text, and every `HTTPError` retried.
  Verify: `grep -c '(D2)' isekai/boundary/pod_start.py` prints `1`, `grep -c 'def can_swap(pod: Pod) -> bool:' isekai/boundary/pod_start.py` prints `1`, `grep -c 'fields\[1\] == str(pod.shm)' isekai/boundary/pod_start.py` prints `1`, and `grep -c 'except urllib.error.HTTPError' isekai/boundary/provision.py` prints `1`.
- [ ] 3.2 In `isekai/boundary/pod_start.py`, drop `(D2)` from `provision()`'s docstring (`0059·R8`) and report an unread swap table (`0059·R9`); add the test binding `pod-image:memory:an-unread-swap-is-reported` to `tests/test_pod_start.py`; per [D4](design.md#d4).
  Verify: `grep -c '(D2)' isekai/boundary/pod_start.py` prints `0`, `grep -c 'could not read whether the container can swap' isekai/boundary/pod_start.py` prints `1`, and `grep -c 'memory:an-unread-swap-is-reported' tests/test_pod_start.py` prints a number of at least `1`.
- [ ] 3.3 Read `/dev/shm`'s type from `mountinfo` by device in `isekai/boundary/pod_start.py` (`0059·S3`); move `tests/test_pod_start.py`'s fixture and memory tests onto it, binding `pod-image:memory:the-type-is-read-by-device`; add that test to `docs/principles.md`'s *Held by*; per [D4](design.md#d4).
  Verify: `grep -c 'fields\[1\] == str(pod.shm)' isekai/boundary/pod_start.py` prints `0`, `grep -c 'test_the_type_is_read_from_the_memory_directorys_device' docs/principles.md` prints `1`, and `uv run pytest -q tests/test_pod_start.py tests/test_principles.py` exits 0.
- [ ] 3.4 In `isekai/boundary/provision.py`, move on at once from a source that answers 4xx, and reword the comment above `ATTEMPTS` (`0059·R16`); give `FakeFetcher` in `tests/fakes.py` its `refuses`; bind `model-provisioning:source-fallback:a-refusing-source-is-not-tried-again` in `tests/test_provision.py`; per [D4](design.md#d4).
  Verify: `grep -c 'except urllib.error.HTTPError' isekai/boundary/provision.py` prints `2`, `grep -c 'source-fallback:a-refusing-source-is-not-tried-again' tests/test_provision.py` prints a number of at least `1`, and `uv run pytest -q tests/test_provision.py` exits 0.
- [ ] 3.5 Re-derive `config/image.json`'s `files`, since `pod_start.py` and `provision.py` changed, per [D4](design.md#d4).
  Verify: `uv run python -m tools.image_record | python3 -c 'import json,sys; r=json.load(sys.stdin); print(r == json.load(open("config/image.json"))["files"])'` prints `True`, and `grep -c -E 'c380d9c47cf1c9bb07a9d3a20f2af1c230e5562eaf3e46f7604d0f39e6b67a90|237a52eaa3c578ad23754a631925e4ad1f920ab30ad649a9b1b6370b147ae8fd' config/image.json` prints `0`.

## 4 — The skill and the protocol

- [ ] 4.1 In `.claude/skills/run-flows/SKILL.md`, write step 4's go, its `volume up` block and its outcomes, step 5's question and `volume down` block, and the *Never* line; name the window in `README.md`'s *The batch, run by an agent*; per [D5](design.md#d5).
  Verify: `grep -c 'gpunit volume up --yes' .claude/skills/run-flows/SKILL.md` prints a number of at least `1`, `grep -c 'list-network-volumes' .claude/skills/run-flows/SKILL.md` prints a number of at least `1`, and `uv run pytest -q tests/test_agent_skills.py` exits 0.
- [ ] 4.2 Add the volume lines to `CLAUDE.md`'s GPU protocol, per [D5](design.md#d5)'s table.
  Verify: `grep -c 'gpunit volume' CLAUDE.md` prints a number of at least `2`, and `grep -c 'list-network-volumes' CLAUDE.md` prints `1`.

## 5 — ⚠️ **HUMAN** — rebuild as v0.36-rc1, re-pin

- [ ] 5.1 **HUMAN** — push `v0.36_the_working_window`; run `gh workflow run build-image.yml --ref v0.36_the_working_window -f tag=v0.36-rc1`; check its build record equals `config/image.json`'s `files`; write the tag and digest into `config/image.json` and the digest into `gpunit.toml`; per [D6](design.md#d6).
  Verify: `grep -c '"tag": "v0.36-rc1"' config/image.json` prints `1`, and `uv run pytest -q tests/test_infra.py` exits 0.

## 6 — ⚠️ **HUMAN · METERED** — one window: volume up, a first and a second render, volume down

- [ ] 6.1 **HUMAN · METERED** — run `uv run --env-file .env gpunit volume up --yes`, then `uv run python -m isekai render` on a small approved batch; while it is open, write the pod's `saved (verified)` lines from the RunPod MCP's `stream-pod-logs` to `.minions/0060_window_first.txt`, no pod id; per [D7](design.md#d7).
  Verify: `grep -c 'saved (verified)' .minions/0060_window_first.txt` prints `12`.
- [ ] 6.2 **HUMAN · METERED** — run `uv run python -m isekai render` again on the same batch, a new pod; write its `skip (present, verified)` and `saved (verified)` lines to `.minions/0060_window_second.txt`, no pod id; per [D7](design.md#d7).
  Verify: `grep -c 'skip (present, verified)' .minions/0060_window_second.txt` prints `12`, and `grep -c 'saved (verified)' .minions/0060_window_second.txt` prints `0`.
- [ ] 6.3 **HUMAN · METERED** — run `uv run --env-file .env gpunit volume down`; record `no gpunit-isekai pod` and `no gpunit-isekai volume` from the RunPod MCP's `list-pods` and `list-network-volumes` in `.minions/0060_window_proof.txt`; per [D7](design.md#d7).
  Verify: `grep -c -E 'no gpunit-isekai pod|no gpunit-isekai volume' .minions/0060_window_proof.txt` prints `2`, and `test -e .gpunit/volume; echo $?` prints `1`.
