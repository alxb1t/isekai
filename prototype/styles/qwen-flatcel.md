# Style preset: `qwen-flatcel` · Qwen-Image-Edit

**The second named style, and the first on a different architecture.** Chosen by the operator on
2026-09-07 from the T10d sheet (F17), as `c_light_8_cfg2`.

**Register:** flat cel anime — the register Fotor occupies, and the one **our own stack cannot reach at
any dial setting we have found** (F17). That is why this preset exists on a different base rather than
as another set of dials on the first.

## The setup

| | value |
|---|---|
| base | `qwen_image_edit_2511_fp8mixed` (Qwen-Image-Edit 2511, fp8) |
| text encoder | `qwen_2.5_vl_7b_fp8_scaled` — reads the **image and the instruction together** |
| vae | `qwen_image_vae` |
| lora | `Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16`, strength 1.0 |
| **steps / cfg** | **8 / 2.0** |
| denoise | **1.0** — and it stays there |
| scale | `ImageScaleToTotalPixels` 1.5 MP, *not* the injector's target |

**Instruction** (this is the prompt; there is no separate positive/negative register):

> *Turn this photo into an anime illustration. Anime style, cel shading, vibrant colors. Keep the
> person's face, hairstyle, clothing, accessories, and background exactly as they are.*

Graph: `qwen-flatcel.json`. Provisioning: `qwen_models.json` — four files, 28.89 GiB, each pinned to a
commit SHA and verified against a digest derived from Hugging Face before any pod existed.

**Why denoise is not a dial here.** An edit model conditions on the image through a vision-language
encoder, not through a partially-noised latent. There is no img2img trade-off to tune — which is the
whole architectural difference, and why "keep her necklace" is an instruction the model was trained to
obey rather than a conditioning strength to hope about.

**Why 8 steps and cfg 2.0.** F17 swept seven settings. 4-step Lightning overshoots into inked manga;
20-step full undershoots into a lightly retouched photograph. This sits between, and the operator picked
it by eye from the spread with the numbers attached.

## Style target

| | linework | posterisation | background detail |
|---|---:|---:|---:|
| the photograph (s1) | 0.030 | 0.266 | 1.000 |
| FOTOR | 0.040 | 0.460 | 1.008 |
| **this preset** | **0.065** | **0.438** | **2.275** |
| `notile-d045` (the other preset) | 0.014 | 0.272 | 0.525 |

**Read `background_detail` > 1 correctly**: it is not merely preserving the background, it is
**redrawing it with anime linework**, adding edges the photograph never had. Fotor's 1.008 is the number
that means *kept rather than embellished*.

**Hair ΔE is not usable to judge this preset** — F16: colour distance to a photograph penalises correct
stylization, and every stylized entrant here scores 21–26 while our least-stylized render scores 3.

## Baseline

Ten synthetic portraits at `60_qwen_gallery/`, plus the seven-setting sweep at `50_qwen_path/`.

**Known residuals.** Accessory retention is unmeasured (F14: the proxy did not validate) and it is one
of the things this preset visibly does best — the record has to say so in words rather than score it.
Hair-colour fidelity across subjects is unestablished for the same reason F16 gives.

**Not released.** Under the rule of 2026-09-07 — *a workflow exists only if it has a committed, scored
baseline and a stated style target* — it has both, in prototype. Promoting it is a change's job, and
that change also has to carry the provisioning: this preset needs a **grown volume** (80 GB) and
28.89 GiB the released manifest does not contain.
