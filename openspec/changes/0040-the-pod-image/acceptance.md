# Acceptance — 0040 the pod image

The evidence from the one metered session [D6](design.md#d6) names, one line each. It holds no pod id, address or
fingerprint value.

The session: 2026-09-28, EU-RO-1, one RTX 4090, image `v0.28-rc1`. Four runs — three synthetic portraits and a copy of
one turned 90° and tagged orientation 6 — rendered through `summon-anime-wai` and `conjure-anime-wai`: 8 renders,
0 refusals.

host key: generated at boot — the image ships none, and the key step ran at boot, before provisioning.
fingerprint line: present — `isekai host key: SHA256:<fingerprint>` in the pod log, right after `step: sshd`.
comfyui directories: /dev/shm/comfyui — ComfyUI logged its input, output, temp and user directories there; `/dev/shm` had about 28 GiB free.
rotated render: upright — the orientation-6 copy renders upright in both flows, checked by eye on the comparison page.
png text chunks: 0 — every render holds only `IHDR`, `IDAT` and `IEND`.
teardown: `render.sh` logged the pod terminated, and the RunPod MCP's `list-pods` returned pods: []
