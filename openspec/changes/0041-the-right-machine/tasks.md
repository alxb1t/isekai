# Tasks — 0041 the right machine

The volume and the telemetry switches, then the host-key check and the strict tunnel, then the docs, then one
metered boot, per [design](design.md).

## Progress

- [ ] 1 — The volume and the telemetry switches
- [ ] 2 — The host-key check and the strict tunnel
- [ ] 3 — The privacy rules in `docs/`
- [ ] 4 — 🛑 **HUMAN · METERED** — one boot, checked

Line numbers are `88cac24`'s. Every new test carries `@pytest.mark.spec` with the key its task names, and has a twin.

## 1 — The volume and the telemetry switches

- [ ] 1.1 **HALT CHECK** — `up.sh` reads no volume, checks no host key and sets no telemetry switch, and v0.28's pod prints its fingerprint.
  Verify: `grep -c -e 'network-volumes' -e 'ssh-keyscan' -e 'ORT_DISABLE_TELEMETRY' infra/up.sh` prints `0`, and `grep -c 'isekai host key: ' start.sh` prints `1`.
- [ ] 1.2 In `infra/up.sh`, read the volume before the create and refuse per [D3](design.md#d3); add `test_another_data_centre_is_refused` (`pod-image:volume:another-data-centre-is-refused`) and `test_a_volume_too_small_is_refused` (`pod-image:volume:a-volume-too-small-is-refused`) to `tests/test_infra.py`.
  Verify: `grep -c 'network-volumes/' infra/up.sh` prints `1`, and `grep -c -e '^def test_another_data_centre_is_refused' -e '^def test_a_volume_too_small_is_refused' tests/test_infra.py` prints `2`.
- [ ] 1.3 Add the telemetry switches to the create body's `env` per [D4](design.md#d4); add `test_the_pod_is_created_with_telemetry_off` (`pod-image:telemetry:the-switches-are-off`).
  Verify: `grep -c -e 'ORT_DISABLE_TELEMETRY: "1"' -e 'HF_HUB_DISABLE_TELEMETRY: "1"' -e 'DO_NOT_TRACK: "1"' infra/up.sh` prints `3`, and `grep -c '^def test_the_pod_is_created_with_telemetry_off' tests/test_infra.py` prints `1`.

## 2 — The host-key check and the strict tunnel

- [ ] 2.1 In `infra/up.sh`, read the printed fingerprint, scan and compare, keep the key in `.runpod_known_hosts`, refuse and tear down per [D1](design.md#d1) and [D2](design.md#d2), and name the file in the printed lines.
  Verify: `grep -c 'ssh-keyscan' infra/up.sh` prints `1`, `grep -c 'Host key verified' infra/up.sh` prints `1`, and `grep -c 'UserKnownHostsFile=.runpod_known_hosts' infra/up.sh` prints `2`.
- [ ] 2.2 In `infra/render.sh`, drop `known_hosts=$(mktemp)` and tunnel with strict checking against `.runpod_known_hosts`; in `infra/down.sh`, `.gitignore` and `CLAUDE.md`'s pod rule, add `.runpod_known_hosts` beside the other record files, per [D1](design.md#d1).
  Verify: `grep -cF 'known_hosts=$(mktemp)' infra/render.sh` prints `0`, `grep -c 'StrictHostKeyChecking=yes' infra/render.sh` prints `1`, and `test "$(cat infra/down.sh .gitignore CLAUDE.md | grep -c 'runpod_known_hosts')" -ge 5 && echo ok` prints `ok`.
- [ ] 2.3 Rewrite `tests/test_infra.py`'s `test_a_sessions_host_keys_are_its_own` and its helper `shared_host_keys` for the per-pod checked file, and add `test_a_matching_key_is_kept` (`pod-image:host-key:a-matching-key-is-kept`), `test_a_mismatch_is_refused` (`pod-image:host-key:a-mismatch-is-refused`) and `test_no_fingerprint_is_refused` (`pod-image:host-key:no-fingerprint-is-refused`), the refusals against stubbed answers.
  Verify: `grep -cF 'known_hosts=$(mktemp)' tests/test_infra.py` prints `0`, and `grep -c -e '^def test_a_matching_key_is_kept' -e '^def test_a_mismatch_is_refused' -e '^def test_no_fingerprint_is_refused' tests/test_infra.py` prints `3`.

## 3 — The privacy rules in `docs/`

- [ ] 3.1 Add `## Privacy` with its principles to `docs/principles.md`, per [D5](design.md#d5).
  Verify: `grep -c '^## Privacy' docs/principles.md` prints `1`, and `grep -c -e 'Privacy is ensured as far as is in our hands' -e 'carries only its pixels' -e 'proves who it is before it receives anything' docs/principles.md` prints `3`.
- [ ] 3.2 Add D34 and D35 to `docs/decisions.md`, extend D27, and remove the serverless preamble line, per [D5](design.md#d5).
  Verify: `grep -c -e '^### D34 · Renders stay on a pod' -e '^### D35 · ' docs/decisions.md` prints `2`, and `grep -c 'serverless rendering, which is being researched' docs/decisions.md` prints `0`.

## 4 — 🛑 **HUMAN · METERED** — one boot, checked

**Ceiling: 45 minutes and ~$0.30; planned at about 10 minutes and ~$0.10.** The pod goes up and down only through
`infra/render.sh`; the RunPod MCP confirms it gone. A synthetic portrait only, per [D6](design.md#d6).

- [ ] 4.1 On the operator's go, run the session [D6](design.md#d6) describes, and read the pod's `env` back through the API while it runs.
  Verify: `grep -c 'Host key verified' .data/v0.29/log.txt` prints `1`, and `grep -c '^refused' .data/v0.29/log.txt` prints `0`.
- [ ] 4.2 Record the evidence in `openspec/changes/0041-the-right-machine/acceptance.md`, one line each, with no pod id, address or fingerprint value.
  Verify: `grep -c -e '^host key: verified' -e '^tunnel: strict' -e '^telemetry switches: set' -e '^renders: arrived' -e 'pods: \[\]' openspec/changes/0041-the-right-machine/acceptance.md` prints `5`.
