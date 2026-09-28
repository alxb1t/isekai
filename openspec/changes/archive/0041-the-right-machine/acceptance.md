# Acceptance — 0041 the right machine

The evidence from the one metered session [D6](design.md#d6) names, one line each. It holds no pod id, address or
fingerprint value.

The session: 2026-09-28, EU-RO-1, one RTX PRO 4500 Blackwell, the image `config/image.json` pins, about 8 minutes.
Two runs, from the operator's photographs in `.data/v0.29/photos`, rendered through `summon-anime-wai` and
`conjure-anime-wai`: 4 renders, 0 refusals. The operator checked the comparison page and accepted it.

host key: verified — `up.sh` logged `Host key verified` once; the scanned key matched the fingerprint the pod printed.
tunnel: strict — `render.sh` tunnelled with `StrictHostKeyChecking=yes` against `.runpod_known_hosts`, and ComfyUI answered through it.
telemetry switches: set — the pod's `env`, read with the RunPod MCP while it ran, held `ORT_DISABLE_TELEMETRY`, `HF_HUB_DISABLE_TELEMETRY` and `DO_NOT_TRACK`, each `"1"`.
volume: beside it — the pod ran in the volume's data centre; `up.sh` refused nothing before the create.
renders: arrived — 4, written to the runs and shown on `.data/v0.29/compare.html`.
teardown: `render.sh` tore the pod down, no `.runpod_*` record file was left, and the RunPod MCP's `list-pods` returned pods: []
