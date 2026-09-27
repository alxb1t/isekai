Image: ghcr.io/alxb1t/isekai:v0.24-rc1@sha256:d6f12d02b1fb6b0d2c4c6d0505c70193202c647d57c27b7e1235845427dbb500

# Acceptance — 0033 pin and record

The evidence each HUMAN phase closes on. Paths are repository-relative.

## 3 — the rc build

- `gh workflow run build-image.yml --ref v0.24_pin_and_record -f tag=v0.24-rc1`, at `42da914`: run
  `36298537985`, `success`.
- The digest the build step reported and the one `docker buildx imagetools inspect
  ghcr.io/alxb1t/isekai:v0.24-rc1` reads agree: `sha256:d6f12d02b1fb6b0d2c4c6d0505c70193202c647d57c27b7e1235845427dbb500`.
- A first dispatch at `09e3111` was refused: `build-image.yml` did not parse. Fixed in `42da914`.

## 8 — the whole flow, both flows, every pin in place

Go: 2026-09-27 — the operator: "Please take it from here, run the GPU on those photos", then chose one
render per photograph per flow. Six photographs, two flows, runs under a batch root in `.data/`.

**Two departures from the plan, both the operator's call.** One render per photograph per flow
(`--count 1`, twelve renders) instead of conjure ×2 and summon ×1 on one portrait. The volume was **not
grown**: `isekai-models` stayed at **20 GB**, which the RunPod MCP (`list-network-volumes`) reported, and it
passed — see *the volume*, below.

### The free half — run by the operator

```
bash tools/download_models.sh config/reader.json
uv run python -m isekai tag     --runs <R> --flow summon-anime-wai --flow conjure-anime-wai <photos>
uv run python -m isekai caption --runs <R> --flow summon-anime-wai --flow conjure-anime-wai <photos>
uv run python -m isekai sheet   --runs <R> --flow summon-anime-wai --flow conjure-anime-wai <photos>
uv run python -m isekai ui --runs <R> --flow summon-anime-wai  <run ids>
uv run python -m isekai ui --runs <R> --flow conjure-anime-wai <run ids>
```

`tag` first refused once, naming `ollama serve`: the Ollama app was not yet running. It passed once the
app was up, spending no attempt. Every record, read back from the files, six runs × two flows:

| artifact | record | runs |
|---|---|---|
| caption | `pinned: true`, both GGUF digests, `options` | 12/12 |
| tags | `pinned: true`, both GGUF digests, `options` | 12/12 |
| wd14 | `floor: 0.15` | 12/12 |
| sheet | `floor: 0.15`, `flow_digest` | 12/12 |
| approval | `schema_document`, `field_map` | 12/12 |
| prompt | `flow_digest`, `sheet: 1` | 12/12 |
| render | `image`, `pinned: true`, `runtime`, `flow_digest`, `sheet: 1` | 12/12 |

### The metered half — one pod session

```
bash infra/up.sh
  image: ghcr.io/alxb1t/isekai@sha256:d6f12d02b1fb6b0d2c4c6d0505c70193202c647d57c27b7e1235845427dbb500
  Pod <pod> created at 2026-09-27T08:46:17Z. Waiting for SSH ...
  Port 22 mapped at 2026-09-27T08:50:50Z.
uv run python -m isekai generate --runs <R> --flow summon-anime-wai --flow conjure-anime-wai --count 1 \
    --server http://127.0.0.1:8188 <run ids>
  12 × assembled, 12 × rendered, exit 0 at 09:04:02
bash infra/down.sh
  Pod terminated. Billing stopped. (Network volume kept.)
```

- **Boot:** created 08:46:17, port 22 mapped 08:50:50 (4 m 33 s, the image pull), ComfyUI answering
  `/system_stats` at 08:51:26. No failure marker at `/opt/isekai/provisioning-failed`.
- **Renders:** twelve, ~67 s each, every one written locally beside its sidecar. One, verbatim:

  ```json
  {
    "flow": "summon-anime-wai",
    "flow_digest": "039a1a80f2b43069e8e1bffcc4e1665417c4aa73e1c2f40fca783379c351669b",
    "sheet": 1,
    "image": "ghcr.io/alxb1t/isekai@sha256:d6f12d02b1fb6b0d2c4c6d0505c70193202c647d57c27b7e1235845427dbb500",
    "pinned": true,
    "runtime": {"comfyui_version": "0.34.0", "python_version": "3.12.14", "pytorch_version": "2.8.0+cu128"}
  }
  ```

- **Teardown:** `down.sh` answered 204 at 09:04:14; the RunPod MCP's `list-pods` returned no pods —
  pod gone.
- **Cost:** 17 m 58 s at the RTX PRO 4500 Blackwell's $0.72/hr, **≈ $0.22** — inside the 45-minute,
  ~$0.30 ceiling.
- **By eye:** the operator compared all twelve renders against their photographs in a side-by-side
  page and judged the run a success: "All works as expected."

### The volume

`df -k --output=size /runpod-volume` on the pod read **2399613600768 KiB** (≈ 2.2 PiB): a network volume
reports its storage cluster's capacity, not its own 20 GB quota. So the 40 GiB floor in `start.sh` does
not measure the volume — it tells a mounted network volume from the pod's own 18.6 GiB and 27.9 GiB
disks, which is the guard's job. D27's known break, *the floor is larger than the real volume*, was
never true; it is closed in `docs/decisions.md`. A floor on the volume's own size is the next version's.
