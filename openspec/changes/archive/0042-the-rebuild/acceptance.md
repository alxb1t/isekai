# Acceptance — 0042 the rebuild

The evidence from the one metered session [D8](design.md#d8) names, one line each. It holds no pod id, address or
fingerprint value.

The session: 2026-09-29, one RTX PRO 4500 Blackwell, image `v0.29.1-rc1` as `config/image.json` pins it, about
7 minutes from the create to the teardown. Two runs, from the operator's synthetic portraits in
`.data/v0.29.1/photos`, rendered through `summon-anime-wai` and `conjure-anime-wai`: 4 renders, 0 refusals. The operator checked the comparison page and accepted it.

tmpdir: /dev/shm/comfyui/tmp — read over SSH from the ComfyUI process's environment. PID 1 is `docker-init`, which runs `start.sh`, so `/proc/1/environ` cannot carry what `start.sh` exports; the process that spools the upload does.
shm: tmpfs — `stat -f -c %T /dev/shm` over SSH, and the pod's log, read with the RunPod MCP, printed `/dev/shm is tmpfs`; `tmp` sat beside `input`, `output` and `user`.
telemetry switches: from the image — the ComfyUI process held `ORT_DISABLE_TELEMETRY`, `HF_HUB_DISABLE_TELEMETRY`, `DO_NOT_TRACK` and `NO_ALBUMENTATIONS_UPDATE`, each `1`, and `up.sh` sent none of them.
boot: created to port 22 in 4 m 23 s, against 0033's 4 m 33 s; the container's first step began 19 s before port 22, so the pull and scheduling hold the rest.
gpu: on the plain base — torch `2.8.0+cu128` saw `cuda:0`, and ComfyUI rendered on it; the platform set `NVIDIA_VISIBLE_DEVICES=void` in the environment and mounted the driver regardless.
onnxruntime: the CPU package — InstantID's face analysis applied `CPUExecutionProvider`; DWPose, finding no GPU provider, ran its box detector through OpenCV on the CPU, where `onnxruntime-gpu` had run it through onnxruntime; the operator accepted OpenCV, pending an evaluation on more photographs.
renders: summon-anime-wai and conjure-anime-wai — 4, written to the runs and shown on `.data/v0.29.1/compare.html`.
teardown: `render.sh` tore the pod down, no `.runpod_*` record file was left, and the RunPod MCP's `list-pods` returned pods: []
