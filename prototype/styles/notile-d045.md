# Style preset: `notile-d045` · Illustrious

**The first named style this project has.** Chosen by the operator on 2026-09-07 (T5) as the target
register, and given its denoise by measurement (F11).

**Register:** rendered anime illustration — polished, shaded, clean edges. **Not** a flat cel TV
screencap; that is a different target and this preset is not a failed attempt at it (F10).

## The setup

| | value | change from shipped |
|---|---|---|
| base | `waiIllustriousSDXL_v170` | — |
| **tile ControlNet** | **0.0** | was 0.2 — **off** |
| **denoise** | **0.45** | was 0.65 |
| OpenPose ControlNet | 0.6 | — |
| MistoLine (lineart) | 0.2 | — |
| `ip_weight` / `cn_strength` | 0.9 / 0.5 | — |
| positive / negative | as shipped | — |

Graph: `notile-d045.json`. Two changes, both discovered rather than assumed.

**Why tile off.** TTPlanet's tile ControlNet conditions on the photograph's local colour and continuous
tone, so it continuously drags the render back toward looking photographic. At 0.9 it crushed linework
to 0.0002; at 0.0 the base is free to render (F9).

**Why denoise down, not up.** With no register pushing toward flat anime, denoise was the only thing
making a render look non-photographic — and denoise buys style by destroying content. Turning tile off
lets the base supply the style, which frees denoise to preserve identity. That is why the fix runs
*opposite* to the intuition (F9).

## Style target — the coordinate, not a maximum

| | posterisation | linework |
|---|---|---|
| the photograph | ≈ its own | ≈ its own |
| **this preset** | **≈ the photograph's** | **≈ the photograph's, ±2×** |
| flat-cel (Fotor) | ~2× the photograph | ~1.5–3× |
| inked line-art (Qwen, as recovered) | ~2.5× | **~5×** — overshoot |

## Baseline

Six adversarial subjects at `21_notile_d045/`, ten diverse portraits × 2 seeds at `30_gallery/`.
Hair ΔE beats the shipped dials on **5 of 6** baseline subjects (F11) and the register holds across all
ten portraits (F12).

**Known residuals**, none of them measured by any current axis: eye colour drifts, body proportions are
idealised on ~4 of 10, faces converge toward one anime face, backgrounds simplify. `s5` (face ~1.3% of
canvas) is the one subject where the shipped dials still win on hair.

**This preset is not released.** Under the rule agreed 2026-09-07 — *a workflow exists only if it has a
committed, scored baseline and a stated style target* — it has both, in prototype. Promoting it is a
change's job.
