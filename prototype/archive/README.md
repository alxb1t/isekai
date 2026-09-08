# Archive — round 1's runners

**Records, not tools.** Every script here drove a pod session that is finished; its result is written up
in `../FINDINGS.md` and `../SUMMARY.md`. They are kept because a finding without the code that produced
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

## Still live, at `../`

`style_axis.py` · `hair_colour.py` · `retention.py` · `thesis.py` — the measurement, which round 2 needs
and which round 2's bar is stated in.
