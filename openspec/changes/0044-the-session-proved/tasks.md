# Tasks — 0044 the session proved

The laptop side and its tests; then a metered render boot and stop boot on the pinned image, per
[design](design.md).

## Progress

- [ ] 1 — The laptop side
- [ ] 2 — 🛑 **HUMAN · METERED** — a render boot and a stop boot on `v0.30-rc2`

Line numbers are `a76a5f5`'s. Every new test carries `@pytest.mark.spec` with the key its task names, and has a twin.

## 1 — The laptop side

- [ ] 1.1 **HALT CHECK** — the listing matches by prefix, a lost create exits 1, and `0.30.0` has no section.
  Verify: `grep -c -F 'startswith($image))' infra/pods.sh` prints `1`, `grep -c 'LOST_CREATE_EXIT' infra/up.sh` prints `0`, and `sed -n 12,14p CHANGELOG.md | grep -c '^### '` prints `0`.
- [ ] 1.2 In `infra/pods.sh`, fail on a repeated cursor and on a named pod with no image, and match the image exactly, per [D1](design.md#d1).
  Verify: `grep -c -F 'startswith($image + "@")' infra/pods.sh` prints `1`, and `grep -c -F 'startswith($image))' infra/pods.sh` prints `0`.
- [ ] 1.3 In `infra/up.sh`, exit a lost create with `LOST_CREATE_EXIT`; in `infra/render.sh`, keep `up.sh`'s status and sweep without a record only on it, per [D2](design.md#d2).
  Verify: `grep -c '^LOST_CREATE_EXIT=3$' infra/up.sh` prints `1`, and `test "$(grep -c 'up_status' infra/render.sh)" -ge 2 && echo ok` prints `ok`.
- [ ] 1.4 Add to `tests/test_infra.py`: `test_a_repeated_cursor_fails_the_listing` (`pod-image:reconcile:a-repeated-cursor-fails`), `test_only_this_image_is_listed` (`pod-image:reconcile:only-this-image-is-listed`) and `test_a_pod_with_no_image_fails_the_listing` (`pod-image:reconcile:a-pod-with-no-image-fails`).
  Verify: `grep -c -e '^def test_a_repeated_cursor_fails_the_listing' -e '^def test_only_this_image_is_listed' -e '^def test_a_pod_with_no_image_fails_the_listing' tests/test_infra.py` prints `3`.
- [ ] 1.5 Add `test_a_refused_session_leaves_a_listed_pod` (`pod-image:reconcile:a-refused-session-leaves-a-listed-pod`) to `tests/test_infra.py`, and make `session_with_a_lost_create`'s `up.sh` stub exit 3.
  Verify: `grep -c '^def test_a_refused_session_leaves_a_listed_pod' tests/test_infra.py` prints `1`, and `grep -q -F 'exit 3' tests/test_infra.py && echo ok` prints `ok`.
- [ ] 1.6 In `README.md`, name the pod check, the catalogue read, the sweep and the stop timer in the script table, the provisioning diagram and the lifecycle line, per [D3](design.md#d3).
  Verify: `grep -c 'exec ComfyUI' README.md` prints `0`, and `test "$(grep -c 'stop timer' README.md)" -ge 2 && echo ok` prints `ok`.
- [ ] 1.7 In `CHANGELOG.md`, add `### Security` under `0.30.0`'s heading; in `tests/test_changelog.py`, report a bullet outside a section and add its case to `test_the_format_check_reports_each_break`, per [D4](design.md#d4).
  Verify: `sed -n 12,14p CHANGELOG.md | grep -c '^### Security$'` prints `1`, and `test "$(grep -c 'outside a section' tests/test_changelog.py)" -ge 2 && echo ok` prints `ok`.
- [ ] 1.8 Check the scripts parse.
  Verify: `bash -n infra/pods.sh && bash -n infra/up.sh && bash -n infra/render.sh && echo ok` prints `ok`.

## 2 — 🛑 **HUMAN · METERED** — a render boot and a stop boot on `v0.30-rc2`

**Ceiling: 45 minutes and ~$0.30 a boot; planned at ~$0.20 in all.** The pods go up only through `infra/render.sh`
and `infra/up.sh`, and down through `infra/down.sh`; the RunPod MCP confirms each gone. Synthetic portraits only, per
[D5](design.md#d5).

- [ ] 2.1 On the operator's go, run the render boot [D5](design.md#d5) describes, reading `gpu.memory` and the pod's log with the RunPod MCP while it runs.
  Verify: `ls .data/v0.30.1/runs/*/summon-anime-wai/outputs/*/*.png .data/v0.30.1/runs/*/conjure-anime-wai/outputs/*/*.png` lists the renders, and `grep -c '^refused' .data/v0.30.1/log.txt` prints `0`.
- [ ] 2.2 On the operator's go, run the stop boot [D5](design.md#d5) describes, and read the stopped pod's billing once RunPod posts it.
  Verify: `grep -c -e '^listing: ' -e '^key scope: ' -e '^refused key: ' -e '^stop: EXITED' -e '^signal path: ' -e '^billing while stopped: ' openspec/changes/0044-the-session-proved/acceptance.md` prints `6`.
- [ ] 2.3 Record the rest in `openspec/changes/0044-the-session-proved/acceptance.md`, one line each, with no pod id, address, fingerprint or key.
  Verify: `grep -c -e '^placement: gpu.memory ' -e '^stop timer: armed' -e '^renders: summon-anime-wai and conjure-anime-wai' -e 'pods: \[\]' openspec/changes/0044-the-session-proved/acceptance.md` prints `4`.
