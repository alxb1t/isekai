# Prototype summary — three flows, measured

**Branch `v0.13_prototype`. Closed 2026-09-07. 23 findings, 8 pod sessions, ≈$1.80.**
Full evidence in `../notes/FINDINGS.md`; this is the part worth carrying out.

---

## The three flows, side by side

`s1_control_blonde` — the subject with the most complete data across all three.

| | linework ↑ | posterisation ↑ | bg detail | hair ΔE ↓ | bg colour ΔE ↓ |
|---|---:|---:|---:|---:|---:|
| **the photograph** | 0.0299 | 0.266 | 1.000 | — | — |
| **ours** · `notile-d045` | **0.0136** | 0.272 | **0.525** | **3.41** | **1.98** |
| **Fotor** · *Anime* effect | 0.0404 | **0.460** | **1.008** | 20.95 | 8.60 |
| **Qwen** · `qwen-flatcel` | **0.0645** | 0.438 | **2.275** | 22.48 | 13.74 |

**Read the colour columns with F16's caveat**: colour distance to a photograph penalises *correct*
stylization, so it flatters whichever flow stylizes least — which is ours. Those columns rank
within a register, never across.

### What each flow is actually good and bad at

| | ours — Illustrious `notile-d045` | Fotor | Qwen `qwen-flatcel` |
|---|---|---|---|
| **register** | rendered anime illustration | flat cel | flat cel, **bolder lines** |
| **keeps** | garments, composition, pose | accessories, background, garment detail, layout | accessories, background, garment detail — **and tattoo placement** |
| **loses** | **all accessories**, background detail (0.525), eye colour | tattoo motifs, hair colour (ΔE 20.95) | occasionally an entire background; hair colour on some subjects |
| **failure shape** | **systematic and mild** — the same things every time | — | **occasional and dramatic** — usually keeps everything, then replaces a beach |
| **consistency** | linework spread ≈ 2× over 10 subjects | — | **4.09×**, and 4.80× with the native 8-step LoRA |
| **the operator's verdict** | **liked the style most** | best overall by eye | **disliked the style** — "bold lines" |

**The operator's preference split the two flows exactly against their measurements**: the style he
likes belongs to the flow that loses identity; the identity he wants belongs to the flow whose style he
does not like. That split is the prototype's real conclusion.

And "bold lines" is measurable: `qwen-flatcel` runs at **0.065 linework — 1.6× Fotor and 2.2× the
photograph.** The eye and the axis agreed.

---

## The eleven things worth carrying out

1. **The evaluator was built before the thing it judges, and came back a coin flip.** Every axis inside
   ±0.155 of chance over 40 blind labels. That ordering is what made everything below possible.
2. **The metrics were inverted, and we can say why.** The face axis rewards *not stylizing* (F4) — its
   optimum is the input photograph. Colour distance does the same on the colour axes (F16). One
   disease, two places.
3. **Only one side of the trade-off was instrumented.** Four axes measured similarity-to-photograph and
   **nothing measured style**, so a less-stylized render won by construction (F5).
4. **A style axis is buildable and takes two numbers** — posterisation and linework — calibrated on
   photo < ours < Fotor *before* any tuning (F7).
5. **Our renders were not under-stylized. They were off-axis** — as graduated as a photograph, with
   linework **60× below** it. Blur is a failure mode neither endpoint has (F7).
6. **Two dial changes fixed most of the identity loss**: tile ControlNet **off**, denoise **0.45**. The
   register and denoise had been doing each other's jobs — with nothing pushing toward flat anime,
   denoise was the only thing making a render non-photographic, and it buys style by destroying content
   (F9, F11).
7. **The two architectures occupy disjoint regions.** Ours spans linework 0.004–0.015 at background
   detail 0.06–0.60; Qwen spans 0.030–0.078 at 1.37–2.96. **No overlap** — a reachability result, not a
   trade-off, and reachability cannot be tuned around (F17).
8. **Fotor is stochastic** — two runs differ by 42× the JPEG floor. That killed the
   translation-network hypothesis and reframed its `background_detail` of 1.008 as *a target a
   generator can hit* rather than the signature of a preserving architecture (F20).
9. **Fotor's moat is a style library, not an architecture.** A catalogue of dozens of branded looks
   only ships as one base plus per-style LoRAs — and the Civitai search proved the gap directly: for
   Qwen-Image-Edit the community trains **anime→real** almost exclusively (F22).
10. **`xor` survives contact with a commercial product.** Fotor keeps tattoo *presence* — coverage,
    placement, palette — and loses the motifs. Qwen only kept specific ink at the setting where it
    barely stylized. Ink fidelity is **coupled to how little the image is transformed** (F23).
11. **Consistency is Qwen's, not ours.** The 8-step-native LoRA did not narrow the spread; it widened it
    to 4.80×. A prediction recorded before the render, resolved on its second branch (F21).

---

## What the instrument can and cannot say

**Validated and usable:** `background_detail` (with a denominator floor — it refuses on flat backdrops,
2 of 6 subjects), posterisation, linework, pose PCK, the composition guard (box IoU, chosen by
measurement, 30/30).

**Usable within one register only:** hair colour, garment colour, background colour — all mean-based
after the mode was indicted by a known-answer test (F8).

**Not measurable today:** **accessory retention** — the proxy did not validate (F14), and it is the
single thing that most separates the three flows. Also unmeasured: eye-colour drift, and the
idealisation of body proportions that F12 found in 4 of 10 renders.

**Two axes are known-broken and unfixed:** `hair_mask_area` reports the photograph's own area, so every
within-subject pair is a tie. `0012:R3` — four eval artifacts pinned, verified and never read, with a
published detector threshold of 0.307 against a hardcoded 0.25.

---

## The two presets

| | `notile-d045` | `qwen-flatcel` |
|---|---|---|
| base | WAI-illustrious-SDXL v17.0 | Qwen-Image-Edit 2511 fp8 |
| the change | tile ControlNet **0.0**, denoise **0.45** | Lightning 4-step LoRA, **8 steps, cfg 2.0**, denoise 1.0 |
| provisioning | the released 16.51 GiB manifest | **+28.89 GiB**, needs the 80 GB volume |
| baseline | 6 adversarial subjects + 10 portraits × 2 seeds | 7-setting sweep + 10 portraits |
| recorded at | `prototype/styles/notile-d045.{json,md}` | `prototype/styles/qwen-flatcel.{json,md}` |

Both satisfy the rule agreed 2026-09-07: **a workflow exists only if it has a committed, scored
baseline and a stated style target.** Neither is released; promoting one is a change's job.

---

## What was tried and did not work

Recorded so it is not re-tried.

- **lineart ControlNet 0.2 → 0.6** made linework *worse* (F9).
- **tile ControlNet at its card's recommended 0.9** crushed linework to 0.0002 — tile is a
  *de-stylizing* force for this product (F9).
- **Six instructions on Qwen** spanned linework 0.057–0.078; dropping the phrase blamed for the
  overshoot changed almost nothing (F15).
- **The 8-step-native Lightning LoRA** widened the spread rather than narrowing it (F21).
- **`raena` style LoRA** applies and works, but pushes *away* from flat cel. It does improve colour
  fidelity when stacked under Lightning (F19).
- **`flat_fraction`** as a style measure conflates cel flatness with blur; **`unique_ratio`** does not
  order the calibration set at all (F7).
- **`accessory_detail`** as a proxy — defeated by a bob falling into the ear zones (F14).
- **AnimeGAN-class translation networks** — ruled out as Fotor's architecture by the determinism test
  before any was installed (F20).

---

## Parked, with reasons

- **Train a photo→anime style LoRA.** F22's redirect and the strongest remaining lever. F19 shows a
  Qwen-*Image* t2i LoRA transfers to Qwen-Image-*Edit*, so it needs only **unpaired** style images — no
  paired-data problem. **Do not train it on our own renders**: F7 measured that style as soft and
  under-drawn, so the corpus would teach the deficiency. Validate any candidate corpus against the style
  axis *before* spending GPU hours.
- **Flux.1 Kontext dev.** Three of four components fetch; the **VAE is gated** behind BFL's licence and
  every mirror returns 401/404. Needs an HF token with the licence accepted. ~17 GiB, and there is room.
- **Tattoo placement.** F23 says no general-purpose stylizer carries specific ink through a strong
  style transfer. Untested: whether a **subject-trained** LoRA carrying the ink vocabulary escapes it.
- **The within-base known-answer probe (T8).** $0, never run: `notile d0.45` against the shipped dials,
  same base and same tool, so the face axes would *not* refuse. The cleanest remaining test of whether
  the scoreboard can see an improvement the eye can.
