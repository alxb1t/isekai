Go: 2026-09-27 — the operator: "run the generate prompt and run the GPU on that one synthetic photo", on
the run under `.data/v0.23/runs`, approving its conjure draft. Ceiling 45 minutes and ~$0.30.

# Acceptance — 0034 RunPod's REST v2

The evidence phase 3 closes on. Paths are repository-relative; `<pod>` and `<host>` stand for the pod id
and its address.

## 3 — one boot on v2, one render, teardown confirmed

**One departure, the agent's, restored after.** The catalog, read through the RunPod MCP before creating,
showed neither configured type in stock in `EU-RO-1`, which had the RTX 4090 and B200 only. For this
session `.env`'s `RUNPOD_GPU_TYPE` gained `NVIDIA GeForce RTX 4090` as a third choice; the file was restored
byte for byte after teardown. The first type was placed anyway, so the fallback was not exercised live.

### The free half

```
uv run python -m isekai approve --runs .data/v0.23/runs --flow conjure-anime-wai <run>
  <run>: approve wrote 001.approved.json
uv run python -m isekai generate --runs .data/v0.23/runs --flow conjure-anime-wai --count 1 <run>
  <run>: assembled conjure-anime-wai/001.json
```

The RunPod MCP's `list-pods` returned `"pods": []` before the boot.

### The metered half — one pod session

```
bash infra/up.sh
  Creating pod in EU-RO-1 ...
    image: ghcr.io/alxb1t/isekai@sha256:d6f12d02b1fb6b0d2c4c6d0505c70193202c647d57c27b7e1235845427dbb500
  Trying 'NVIDIA RTX PRO 4500 Blackwell' ...
  Pod <pod> created at 2026-09-27T10:17:33Z. Waiting for SSH ...
  Port 22 mapped at 2026-09-27T10:21:54Z.
ssh -N -L 8188:localhost:8188 root@<host> -p <port>
  ComfyUI 0.34.0 answering at 10:23:00Z, on "NVIDIA RTX PRO 4500 Blackwell"
uv run python -m isekai generate --flow conjure-anime-wai --count 1 --server http://127.0.0.1:8188 \
    --runs .data/v0.23/runs <run>
  <run>: assembled conjure-anime-wai/001.json
  <run>: rendered conjure-anime-wai/15409833285332472070.png            (10:24:08Z)
bash infra/down.sh
  Terminating pod <pod> ...
  Pod terminated. Billing stopped. (Network volume kept.)   (10:24:19Z; both record files removed)
```

The render's record: `image` the digest above, `pinned: true`, `runtime` ComfyUI `0.34.0` / PyTorch
`2.8.0+cu128`, `flow_digest` `f2bd3202…`, `sheet: 1`. Checked by eye: a clean anime render.

### Teardown confirmed — pod gone

The RunPod MCP, after `down.sh`: `get-pod <pod>` → `404 Not Found`, `"detail": "pod not found"`;
`list-pods` → `"pods": []`. The pod is gone.

**Time and cost:** created 10:17:33Z, terminated 10:24:19Z — 6 min 46 s at $0.72/hr Secure, about $0.08,
under the 45-minute and ~$0.30 ceiling.
