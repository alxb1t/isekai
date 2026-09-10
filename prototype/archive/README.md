# Archive — what is finished

**Records, not tools.** Round 1's runners, the graphs they drove, and two notes whose questions are
closed. Every script here drove a pod session that is finished; its result is written up
in `../notes/FINDINGS.md` and `../SUMMARY.md`. They are kept because a finding without the code that produced
it is an assertion, and because two of them recover deleted graphs from git history that would otherwise
have to be rediscovered.

They still import (`prototype.archive.<name>`) and would still run, but nothing in round 2 needs them.

| script | drove | finding |
|---|---|---|
| `ladder.py` | the first dial ladder — negative, lineart, tile, denoise | F9 |
| `notile.py` | the chosen register across six subjects and its denoise frontier | F11 |
| `gallery.py` | `notile-d045` across ten portraits, plus the contact sheet | F12 |
| `external_eval.py` | scoring a render this pipeline did not produce — the Fotor seam | F1, F2 |
| `qwen_graph.py` | **flattens the recovered Qwen-Image-Edit graph** from `e324699^` into two runnable variants | F15 |
| `qwen_sweep.py` | six instructions × two subjects | F15 |
| `qwen_path.py` | the sampling-path sweep that answered the architecture thesis | F17 |
| `qwen_gallery.py` | `qwen-flatcel` across ten portraits | F18 |
| `qwen_lora.py` | the `raena` style-LoRA sweep | F19 |
| `lightning8.py` | the 8-step-native Lightning test | F21 |
| `tattoo_test.py` | three presets on four real photographs | F23 |

**The two worth reading before writing anything new:** `qwen_graph.py`, for how a deleted ComfyUI
subgraph export was recovered and flattened into something submittable over the API — round 2 has to do
the same for `workflows/animagine.json`; and `external_eval.py`, for how a foreign render is scored
without fabricating provenance.

## Round 1's measurement

Moved here 2026-09-10. It still runs, and its **findings** are worth carrying; its **numbers** are not.

| script | what it measured | why it is here |
|---|---|---|
| `hair_colour.py` | the colour machinery, plus the known-answer test that indicted the mode in favour of the mean | **F8**. Usable within one register only |
| `retention.py` | background detail · background colour · garment colour, and the `accessory_detail` proxy that **did not validate** | **F14**. Every axis is referenced to the photograph |
| `thesis.py` | retention plotted against stylization | the plot that showed the two architectures occupy **disjoint regions**, **F17** |

**All three are photograph-referenced, which is F16's disease**: a colour or edge distance to a
photograph rewards *not stylizing*, so its optimum is the input. That is precisely what N27 exists to
replace, and it is why these are records rather than instruments. `style_axis.py` stayed at `../`
because it is the one axis that is **absolute** — it describes the render alone.

## Round 2's finished arms

| script | drove | finding |
|---|---|---|
| `n4_measure.py` | four flows on six subjects — the run that **cleared the style bar** | F24 |
| `prompt_arms.py` | five prompt arms; **all four documented changes made the render worse** | F32 |

## `SUMMARY.md` — round 1's close

The eleven things worth carrying, and **what was tried and did not work**. Still the answer to *has this
been tried*, which is why `README.md` still sends a new thread here before it spends anything.

## The graphs, at `styles/`

Round 1's presets and every manifest only they need. Moved here 2026-09-10; `prototype/styles/` now
holds exactly the three files the live flows read -- `fromnoise-v1.json`, `wd14_models.json` and
`upscaler_models.json` -- so what is current is legible from `ls` rather than from memory.

| file | what it is |
|---|---|
| `notile-d045.{json,md}` | round 1's img2img preset, **rejected as soft** (F7) |
| `qwen-flatcel.{json,md}` | round 1's Qwen preset, **rejected on style** (F15, F17, F18) |
| `qwen-lightning.json` · `qwen-full.json` | the two flattenings `qwen_graph.py` produces |
| `qwen-image-edit.recovered.json` | the subgraph export recovered from `e324699^` |
| `qwen_models.json` | **28.89 GiB of pinned digests** — this is what makes freeing the Qwen space on the volume reversible, so it is archived and never deleted |
| `lightning8_models.json` · `flux_kontext_models.json` | the 8-step Lightning test (F21); Flux.1 Kontext, parked on its gated VAE |
| `raena_lora.json` | round 1's style-LoRA sweep (F19). **N20 was dropped on 2026-09-10** — no style LoRA is trained in this prototype — so this is a record only |

The runners here were repointed at `prototype/archive/styles/` in the same move, so each still runs.

## Two closed notes

| file | why it is here |
|---|---|
| `GPU.md` | the card question, **settled**: keep it, and a render's cost is not where the money goes |
| `SYNTHETIC_PORTRAITS_FIX.md` | the sibling repo's blocker, **fixed** — the portfolio portraits generated |

## `galleries/` — round 1's contact images

`gallery_notile_d045.png`, `gallery_qwen_c_light_8_cfg2.png` and `qwen_path_sheet.png` — the ten-portrait
galleries of both **rejected** round 1 flows (F12, F18) and the sampling-path sheet behind F17. Moved here
2026-09-10 with the flows they depict; `gallery.py` and `qwen_gallery.py` now write here rather than into
the working `derived/` tree.

## `fotor/` — round 1's lighthouse, retired 2026-09-10

Six renders from a commercial stylizer, their nine canvas resamples under `canvas/`, and the two
external-eval score files from F1/F2. Gitignored; digests are in `../notes/FINDINGS.md` F0.

**It earned its place and then stopped being useful.** It calibrated the style axis when nothing in this
project knew what "flat enough" meant (**F7**), it was the third point in a three-way ordering whose
sequence was not in dispute, and two findings came out of interrogating it directly: it is **stochastic**,
two runs differing by 42x the JPEG floor (**F20**), which killed the translation-network hypothesis; and
its moat is **a style library, not an architecture** (**F22**), which is what redirected round 1 toward a
trained style adapter.

**What retired it was reaching the register.** Round 2's flows are what the operator wants, and at that
point a number he had passed was still being reported as a 19% deficit. A reference you have passed is a
rearview mirror. The bar is now each flow's own last measured number — `README.md` § *The style bar,
restated* — which is possible only because both style axes are **absolute**: they describe the render and
need no foreign image to be read.

`archive/retention.py` and `archive/thesis.py` read `canvas/` and still run. Nothing at `prototype/`'s
root reads any of it.
