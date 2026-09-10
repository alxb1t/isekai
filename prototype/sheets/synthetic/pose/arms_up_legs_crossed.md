# `arms_up_legs_crossed` — criteria sheet

Drafted by a reader from `prototype/inputs/synthetic/pose/arms_up_legs_crossed.png`, 2026-09-10. **Not reviewed.** ✓ marks a scored
criterion. Edit the table, then run `sheet.py build arms_up_legs_crossed` to regenerate the prompt.

| field | value |
|---|---|
| 1 · count | 1girl, solo |
| 2 · age band | *(none)* |
| 3 · skin / ancestry | *(none)* |
| 4 · hair colour ✓ | brown hair |
| 5 · hair silhouette ✓ | long hair |
| 6 · eye colour ✓ | brown eyes |
| 7 · eyebrows | *(none)* |
| 8 · marks ✓ | *(none)* |
| 9 · clothes ✓ | tank top, grey shirt, black pants, leggings, barefoot |
| 10 · accessories | *(none)* |
| 11 · expression | smile, closed mouth |
| 12 · gaze ✓ | looking at viewer |
| 13 · pose ✓ | standing, arms up, own hands clasped, crossed legs |
| 14 · framing | full body |
| 15 · body shape | medium breasts |
| 16 · background | simple background, grey background |

### The positive prompt, assembled

```
masterpiece, best quality, amazing quality, newest, 1girl, solo, brown hair, long hair, brown eyes, tank top, grey shirt, black pants, leggings, barefoot, smile, closed mouth, looking at viewer, standing, arms up, own hands clasped, crossed legs, full body, medium breasts, simple background, grey background, anime screencap, detailed eyes, soft lighting
```

### The positive prompt — pose tags dropped

**Flow `A`'s ablation arm (N25).** The same table with field 13 omitted, on the
hypothesis that OpenPose's skeleton already carries the geometry. Flow `D` never
uses this block: it has no skeleton, so for `D` the tags are the only thing
placing the body.

```
masterpiece, best quality, amazing quality, newest, 1girl, solo, brown hair, long hair, brown eyes, tank top, grey shirt, black pants, leggings, barefoot, smile, closed mouth, looking at viewer, full body, medium breasts, simple background, grey background, anime screencap, detailed eyes, soft lighting
```

### The negative prompt

```
bad quality, worst quality, sketch, censor, nsfw, lens flare, light particles, dust
```

### Verdict — filled in after the render, by eye

| scored criterion | survived? | note |
|---|:-:|---|
| pose *(mandatory)* | | |
| gaze | | |
| hair silhouette *(mandatory)* | | |
| hair colour | | |
| eye colour | | |
| clothes | | |
| marks | | |

**Bar: 6 of 7, and both mandatory ones.**
