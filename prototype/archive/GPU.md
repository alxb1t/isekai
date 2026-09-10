# Which GPU, and is ours the right one

**Researched 2026-09-08**, after EU-RO-1 stopped issuing public IPs and the question came up: are we
paying for the right card? Data is from RunPod's live catalogue (`get-gpu-type`, `list-gpu-types`) and
from **this repository's own session timings**, not from datasheets.

**Short answer: the card is fine, and it is not where the money goes.** Our cost is dominated by
*session overhead*, not by render throughput, so a cheaper-per-hour card would save almost nothing and
cost wall-clock. The real finding is a different one — **the pinned card exists in only two
datacenters**, which is a fragility worth fixing regardless of price.

---

## 1. What we actually pay, measured

| session | minutes | renders | cost | $/render |
|---|---:|---:|---:|---:|
| N3 | 10 | 6 | $0.120 | 0.0200 |
| N6 | 9 | 21 | $0.108 | 0.0051 |
| N8 | 3 | 6 | $0.036 | 0.0060 |
| N9 | 15 | 24 | $0.180 | 0.0075 |
| N12 | 5 | 12 | $0.060 | 0.0050 |
| **total** | **42** | **69** | **$0.504** | **0.0073** |

At `RTX PRO 4500 Blackwell`, $0.72/hr secure, a render takes **~22 s** — about **$0.0044** of GPU time.

**Boot and ComfyUI start cost 2–4 minutes of every session, roughly $0.036 — eight times the cost of one
render.** N3's $0.020/render and N12's $0.005/render differ by 4x for exactly that reason: one amortised
the boot over 6 renders and the other over 12.

> **The lever that matters is fewer, larger sessions — not a cheaper card.** Halving $/hr saves ~$0.25 per
> day at our volume. Merging two sessions into one saves as much and costs nothing.

---

## 2. What the graph needs, estimated — and not yet measured

Flow `A`, at the 1024×1472 working resolution, fp16:

| component | approx. VRAM |
|---|---:|
| SDXL UNet | ~5.0 GB |
| two CLIP text encoders | ~1.4 GB |
| VAE | ~0.2 GB |
| InstantID — IP-adapter + its ControlNet | ~3.2 GB |
| OpenPose ControlNet | ~2.5 GB |
| DWPose preprocessor (yolox_l + dw-ll) | ~0.4 GB |
| latent, attention and working buffers | ~2–4 GB |
| **peak, flow `A`** | **~15–17 GB** |
| **peak, flow `D`** (no InstantID, no OpenPose) | **~8–10 GB** |

**InsightFace runs on CPU** — the graph sets `provider: "CPU"` on node 6 — so it costs no VRAM.

**This is an estimate and nothing here has measured it.** The measurement is free and takes one line
during any future session:

```bash
nvidia-smi --query-gpu=memory.used --format=csv -l 2   # while a render runs
```

Until that is run, **16 GB should be treated as unproven for flow `A`** and 24 GB as the safe floor.

---

## 3. The fragility that actually bit us

`get-gpu-type NVIDIA RTX PRO 4500 Blackwell`:

| datacenter | availability | network volumes |
|---|---|---|
| **EU-RO-1** | MEDIUM | STANDARD — our 80 GB volume lives here |
| **EUR-IS-1** | LOW | STANDARD |
| *everywhere else* | **none** | — |

**Two datacenters. That is the single point of failure**, and nothing in this repository recorded it
until F31. Network volumes are datacenter-bound, so the volume pins the location and the card pins the
datacenter — a mutual lock.

### And most cheap cards are in datacenters that cannot hold a volume

| card | VRAM | $/hr secure | where | volumes there? |
|---|---:|---:|---|---|
| RTX A4000 | 16 | **$0.25** | EUR-IS-1 | ✅ STANDARD |
| RTX A6000 | 48 | $0.53 | EU-SE-1 | ❌ **none** |
| A40 | 48 | $0.49 | EU-SE-1, CA-MTL-1 | ❌ **none** |
| L4 | 24 | $0.49 | **EU-RO-1**, EUR-IS-1, EUR-IS-2, US-MO-2 | ✅ STANDARD |
| RTX A4500 | 20 | $0.25 | *no secure DC currently* | — |
| **RTX PRO 4500 Blackwell** | **32** | **$0.72** | EU-RO-1, EUR-IS-1 | ✅ STANDARD |

A6000 at $0.53 and A40 at $0.49 look attractive and are **unusable**: `EU-SE-1` reports
`networkVolumeTypes: []`, so the models could not persist there and every session would re-download
16.5 GiB.

---

## 4. Cheaper per hour is not cheaper per render

The two viable alternatives, against ours:

| card | $/hr | VRAM | rough speed vs ours | est. $/render | verdict |
|---|---:|---:|---|---:|---|
| **RTX PRO 4500 Blackwell** | $0.72 | 32 | 1.0× (22 s) | **$0.0044** | the baseline |
| **L4** | $0.49 | 24 | ~0.4× — 72 W, inference-tuned, no NVLink | ~$0.0075 | **worse**, and slower |
| **RTX A4000** | $0.25 | 16 | ~0.35× (Ampere, 140 W) | ~$0.0044 | **a wash**, at 3× the wall-clock and unproven VRAM |

**Both estimates are throughput guesses and are flagged as such.** But the direction is not close: a card
at a third of the price that is a third as fast costs the same per render *and* triples the session
length — which, per §1, is where the actual money is.

**Only a measurement would overturn this**, and it is cheap: one identical arm on an A4000, timed. If it
turns out only 1.5× slower rather than 3×, it becomes genuinely cheaper and the conclusion flips.

---

## 5. What was changed, and what is worth doing

**Done, 2026-09-08** (prototype branch only):

- **`RUNPOD_GPU_TYPE` accepts a comma-separated preference list**, sent as `gpuTypeIds`. RunPod places on
  whichever is free. A single hardcoded card in a two-datacenter pool was a single point of failure.
- **Every entry must be cu128-compatible.** cu128 covers sm_80 → sm_120, so Ampere and Ada qualify.
  `CLAUDE.md`'s constraint is that **cu124 fails on Blackwell**, not that the image is Blackwell-only —
  the list is safe.

**Worth doing:**

1. **Add `NVIDIA L4` to the preference list for EU-RO-1.** Not for the price — it is worse per render —
   but because it is a **different host pool in the same datacenter**, and the failure that blocked this
   session was per-host, not per-datacenter. It is a free second chance at a public IP.
2. **Measure VRAM** (§2). One command, no extra spend, settles whether 16 GB cards are even eligible.
3. **Merge sessions.** §1 says this is worth more than any card change available to us.
4. **Do not chase A6000 or A40.** They are cheap and in datacenters that cannot persist our models.

---

## Sources

RunPod live catalogue via the MCP, read 2026-09-08: `get-gpu-type` per card for per-datacenter
availability, `list-gpu-types` for the priced catalogue, `list-data-centers` for `networkVolumeTypes`.
Prices are **secure cloud**; community cloud is roughly half but carries no availability guarantee and is
not used here. Timings in §1 are this repository's own session records, not benchmarks.
