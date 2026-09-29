# Tasks — 0042 the rebuild

The image files and their tests; the docs; then the operator's rc build; then one metered session, per
[design](design.md).

## Progress

- [ ] 1 — The image, the start script and `up.sh`
- [ ] 2 — The docs
- [ ] 3 — 🛑 **HUMAN** — the rc build
- [ ] 4 — 🛑 **HUMAN · METERED** — one render session on the new image

Line numbers are `ad27f67`'s. Every new test carries `@pytest.mark.spec` with the key its task names, and has a twin.

## 1 — The image, the start script and `up.sh`

- [ ] 1.1 **HALT CHECK** — the image is on the devel base with `onnxruntime-gpu`, no `TMPDIR`, and the switches in `up.sh` alone.
  Verify: `grep -c '^FROM nvidia/cuda:12.4.1-devel' Dockerfile` prints `1`, `grep -c '"onnxruntime-gpu"' image/pyproject.toml` prints `1`, `grep -c 'TMPDIR' start.sh` prints `0`, and `grep -c 'ORT_DISABLE_TELEMETRY' Dockerfile` prints `0`.
- [ ] 1.2 In `Dockerfile`, move to the `ubuntu:22.04` base, replace apt's Python with `build-essential` and `ca-certificates`, add the `NVIDIA_*` `ENV`, and rewrite line 1's comment, per [D1](design.md#d1).
  Verify: `grep -c '^FROM ubuntu:22.04@sha256:' Dockerfile` prints `1`, `grep -c 'python3' Dockerfile` prints `0`, and `test "$(grep -o -e build-essential -e ca-certificates -e NVIDIA_VISIBLE_DEVICES=all -e NVIDIA_DRIVER_CAPABILITIES=compute,utility Dockerfile | wc -l)" -ge 4 && echo ok` prints `ok`.
- [ ] 1.3 Add the switches' `ENV` to `Dockerfile`, and remove them and the comment above the body from `infra/up.sh`, per [D3](design.md#d3).
  Verify: `grep -c '^ENV ORT_DISABLE_TELEMETRY=1 HF_HUB_DISABLE_TELEMETRY=1 DO_NOT_TRACK=1 NO_ALBUMENTATIONS_UPDATE=1$' Dockerfile` prints `1`, and `grep -c -e ORT_DISABLE_TELEMETRY -e HF_HUB_DISABLE_TELEMETRY -e DO_NOT_TRACK -e NO_ALBUMENTATIONS_UPDATE infra/up.sh` prints `0`.
- [ ] 1.4 In `tools/derive_image_project.py`, pin `onnxruntime`, drop `onnxruntime-gpu` and hash the build constraints; run it and read `git diff --stat -- image/`, per [D4](design.md#d4) and [D5](design.md#d5).
  Verify: `grep -c '"onnxruntime-gpu"' image/pyproject.toml` prints `0`, `grep -c '"onnxruntime==1.30.0"' image/pyproject.toml` prints `1`, `grep -c 'hashes = \["sha256:' image/pyproject.toml` prints `3`, and `grep -c '^name = "onnxruntime-gpu"' image/uv.lock` prints `0`.
- [ ] 1.5 In `start.sh`'s memory step, make the `tmp` directory and export `TMPDIR`, check the type, and hold on an unreadable figure, per [D2](design.md#d2).
  Verify: `grep -c '^export TMPDIR=/dev/shm/comfyui/tmp$' start.sh` prints `1`, `grep -c 'stat -f -c %T /dev/shm' start.sh` prints `1`, `grep -c "could not read /dev/shm" start.sh` prints `1`, and `grep -c 'free_kib=0' start.sh` prints `0`.
- [ ] 1.6 Add to `tests/test_infra.py`: `test_comfyui_spools_uploads_to_memory` (`pod-image:memory:uploads-spool-to-memory`), `test_a_shm_that_is_not_memory_holds_the_pod` (`pod-image:memory:a-disk-backed-shm-holds`) and `test_an_unread_figure_holds_the_pod` (`pod-image:memory:an-unread-figure-holds`).
  Verify: `grep -c -e '^def test_comfyui_spools_uploads_to_memory' -e '^def test_a_shm_that_is_not_memory_holds_the_pod' -e '^def test_an_unread_figure_holds_the_pod' tests/test_infra.py` prints `3`.
- [ ] 1.7 Add `test_the_build_tools_are_checked_by_hash` (`pod-image:build:the-build-tools-are-hashed`) to `tests/test_infra.py`, and point `telemetry_left_on` at the `Dockerfile`'s `ENV` and `up.sh`, per [D3](design.md#d3).
  Verify: `grep -c '^def test_the_build_tools_are_checked_by_hash' tests/test_infra.py` prints `1`, and `test "$(sed -n '/^def telemetry_left_on/,/^$/p' tests/test_infra.py | grep -c -i dockerfile)" -ge 1 && echo ok` prints `ok`.
- [ ] 1.8 Check the image files the way `CLAUDE.md` asks of an image phase.
  Verify: `bash -n start.sh && echo ok` prints `ok`, and `docker build --check .` exits `0`.

## 2 — The docs

- [ ] 2.1 In `docs/pins.md`, say the sdist builds' tools are pinned by hash, and remove their *Not pinned* row, per [D5](design.md#d5).
  Verify: `grep -c "the sdist builds' tools by hash" docs/pins.md` prints `1`, and `grep -c 'the build tools of the image' docs/pins.md` prints `0`.
- [ ] 2.2 Add the tests from 1.6 to the *Held by* list of *The rented machine is proved, and forgets* in `docs/principles.md`.
  Verify: `grep -c -e 'test_comfyui_spools_uploads_to_memory' -e 'test_a_shm_that_is_not_memory_holds_the_pod' -e 'test_an_unread_figure_holds_the_pod' docs/principles.md` prints `3`.
- [ ] 2.3 In `CHANGELOG.md`, make 0.26.1's first bullet name the append-only exception, per [D6](design.md#d6).
  Verify: `grep -c 'the one stated exception to append-only' CHANGELOG.md` prints `1`.

## 3 — 🛑 **HUMAN** — the rc build

- [ ] 3.1 The operator pushes `v0.29.1_the_rebuild` and runs `gh workflow run build-image.yml --ref v0.29.1_the_rebuild -f tag=v0.29.1-rc1`, per [D7](design.md#d7); the job summary's digest and the tag go into `config/image.json`.
  Verify: `grep -c '"tag": "v0.29.1-rc1"' config/image.json` prints `1`.

## 4 — 🛑 **HUMAN · METERED** — one render session on the new image

**Ceiling: 45 minutes and ~$0.30; planned at about 10 minutes and ~$0.10.** The pod goes up and down only through
`infra/render.sh`; the RunPod MCP confirms it gone. Synthetic portraits only, per [D8](design.md#d8).

- [ ] 4.1 On the operator's go, run the session [D8](design.md#d8) describes; read the pod's environment over SSH and its log through the RunPod MCP while it runs.
  Verify: `ls .data/v0.29.1/runs/*/summon-anime-wai/outputs/*/*.png .data/v0.29.1/runs/*/conjure-anime-wai/outputs/*/*.png` lists the renders, and `grep -c '^refused' .data/v0.29.1/log.txt` prints `0`.
- [ ] 4.2 Record the evidence in `openspec/changes/0042-the-rebuild/acceptance.md`, one line each, with no pod id, address or fingerprint.
  Verify: `grep -c -e '^tmpdir: /dev/shm/comfyui/tmp' -e '^shm: tmpfs' -e '^telemetry switches: from the image' -e '^boot: created to port 22 in ' -e '^renders: summon-anime-wai and conjure-anime-wai' -e 'pods: \[\]' openspec/changes/0042-the-rebuild/acceptance.md` prints `6`.
