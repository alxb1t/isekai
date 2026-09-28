# Tasks — 0040 the pod image

The image and the start script with their tests; then the operator's rc build; then one metered session, per
[design](design.md).

## Progress

- [x] 1 — The image and the start script
- [x] 2 — 🛑 **HUMAN** — the rc build
- [ ] 3 — 🛑 **HUMAN · METERED** — one render session on the new image

Line numbers are `6a93516`'s. Every new test carries `@pytest.mark.spec` with the key its task names, and has a twin.

## 1 — The image and the start script

- [x] 1.1 **HALT CHECK** — the image keeps its baked keys, and ComfyUI writes to the container disk.
  Verify: `grep -c 'ssh_host_' Dockerfile` prints `0`, `grep -c 'ssh-keygen -A' start.sh` prints `1`, and `grep -c '/dev/shm' start.sh` prints `0`.
- [x] 1.2 Delete the host keys in `Dockerfile`'s install `RUN`, and move the image project's `COPY`, `ENV` and `uv sync` lines after `WORKDIR /opt/ComfyUI`, per [D1](design.md#d1) and [D4](design.md#d4).
  Verify: `grep -c 'rm -f /etc/ssh/ssh_host_' Dockerfile` prints `1`, and `test "$(grep -n 'RUN uv sync' Dockerfile | cut -d: -f1)" -lt "$(grep -n 'ComfyUI_InstantID.git' Dockerfile | cut -d: -f1)" && echo ok` prints `ok`.
- [x] 1.3 In `start.sh`, make the Ed25519 key, start `sshd` with it alone and print the fingerprint line, per [D1](design.md#d1).
  Verify: `grep -c 'ssh-keygen -A' start.sh` prints `0`, and `grep -c 'isekai host key: ' start.sh` prints `1`.
- [x] 1.4 In `start.sh`, add the timestamped step that makes the RAM directories and checks `/dev/shm`, and start ComfyUI with them and `--disable-metadata`, per [D2](design.md#d2) and [D3](design.md#d3); correct the 80 GB comment per [D4](design.md#d4).
  Verify: `grep -c -e '--input-directory /dev/shm/comfyui/input' -e '--disable-metadata' start.sh` prints `2`, and `grep -c '80 GB' start.sh` prints `0`.
- [x] 1.5 Add to `tests/test_infra.py`: `test_the_image_carries_no_host_key` (`pod-image:host-key:the-image-carries-none`), `test_each_boot_makes_and_prints_its_own_key` (`pod-image:host-key:each-boot-makes-and-prints-one`), `test_comfyui_writes_to_memory` (`pod-image:memory:comfyui-writes-to-memory`), `test_too_little_memory_holds_the_pod` (`pod-image:memory:too-little-memory-holds`) and `test_comfyui_writes_no_metadata` (`pod-image:render-metadata:none-is-written`); add the new step to the timestamped-steps check.
  Verify: `grep -c -e '^def test_the_image_carries_no_host_key' -e '^def test_each_boot_makes_and_prints_its_own_key' -e '^def test_comfyui_writes_to_memory' -e '^def test_too_little_memory_holds_the_pod' -e '^def test_comfyui_writes_no_metadata' tests/test_infra.py` prints `5`.
- [x] 1.6 Check the image files the way `CLAUDE.md` asks of an image phase.
  Verify: `bash -n start.sh && echo ok` prints `ok`, and `docker build --check .` exits `0`.

## 2 — 🛑 **HUMAN** — the rc build

- [x] 2.1 The operator pushes `v0.28_the_pod_image` and runs `gh workflow run build-image.yml --ref v0.28_the_pod_image -f tag=v0.28-rc1`, per [D5](design.md#d5); the job summary's digest and the tag go into `config/image.json`.
  Verify: `grep -c '"tag": "v0.28-rc1"' config/image.json` prints `1`.

## 3 — 🛑 **HUMAN · METERED** — one render session on the new image

**Ceiling: 45 minutes and ~$0.30; planned at about 10 minutes and ~$0.10.** The pod goes up and down only through
`infra/render.sh`; the RunPod MCP confirms it gone. Synthetic portraits only, per [D6](design.md#d6).

- [ ] 3.1 On the operator's go, run the session [D6](design.md#d6) describes, and read the pod's log through the RunPod MCP while it runs.
  Verify: `ls .data/v0.28/runs/*/summon-anime-wai/outputs/*.png .data/v0.28/runs/*/conjure-anime-wai/outputs/*.png` lists the renders, and `grep -c '^refused' .data/v0.28/log.txt` prints `0`.
- [ ] 3.2 Record the evidence in `openspec/changes/0040-the-pod-image/acceptance.md`, one line each, with no pod id, address or fingerprint value.
  Verify: `grep -c -e '^host key: generated at boot' -e '^fingerprint line: present' -e '^comfyui directories: /dev/shm/comfyui' -e '^rotated render: upright' -e '^png text chunks: 0' -e 'pods: \[\]' openspec/changes/0040-the-pod-image/acceptance.md` prints `6`.
