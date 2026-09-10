# `standing_turn` — criteria sheet

Drafted by a reader from `prototype/inputs/synthetic/pose/standing_turn.png`, 2026-09-10. **Not reviewed.** ✓ marks a scored
criterion. Edit the table, then run `sheet.py build standing_turn` to regenerate the prompt.

| field | value |
|---|---|
| 1 · count | 1girl, solo |
| 2 · age band | *(none)* |
| 3 · skin / ancestry | *(none)* |
| 4 · hair colour ✓ | brown hair |
| 5 · hair silhouette ✓ | long hair, straight hair |
| 6 · eye colour ✓ | brown eyes |
| 7 · eyebrows | *(none)* |
| 8 · marks ✓ | *(none)* |
| 9 · clothes ✓ | red shirt, long sleeves, shirt, blue pants, denim, white footwear |
| 10 · accessories | earrings |
| 11 · expression | closed mouth |
| 12 · gaze ✓ | looking at viewer |
| 13 · pose ✓ | standing, from side, looking back, hand on own hip |
| 14 · framing | full body |
| 15 · body shape | medium breasts |
| 16 · background | simple background, grey background |

### The positive prompt, assembled

```
masterpiece, best quality, amazing quality, newest, 1girl, solo, brown hair, long hair, straight hair, brown eyes, red shirt, long sleeves, shirt, blue pants, denim, white footwear, earrings, closed mouth, looking at viewer, standing, from side, looking back, hand on own hip, full body, medium breasts, simple background, grey background, anime screencap, detailed eyes, soft lighting
```

### The positive prompt — pose tags dropped

**Flow `A`'s ablation arm (N25).** The same table with field 13 omitted, on the
hypothesis that OpenPose's skeleton already carries the geometry. Flow `D` never
uses this block: it has no skeleton, so for `D` the tags are the only thing
placing the body.

```
masterpiece, best quality, amazing quality, newest, 1girl, solo, brown hair, long hair, straight hair, brown eyes, red shirt, long sleeves, shirt, blue pants, denim, white footwear, earrings, closed mouth, looking at viewer, full body, medium breasts, simple background, grey background, anime screencap, detailed eyes, soft lighting
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
