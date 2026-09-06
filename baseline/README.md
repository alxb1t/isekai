# The v0.12 baseline — six subjects

The inputs to v0.12's metered session: six subjects, each chosen to break a metric rather than to
cover humanity (`design.md` D11). Thirty renders — six subjects × five seeds, **dials held** — are what
the evaluator is calibrated against.

**The pixels are not here.** This repository commits `run.json` artifacts and never inputs, and
committing derived faces into a project whose product is identity preservation invites a confusion the
README would then have to disclaim (`design.md` D14, D15). What is here is the recipe —
`build_subjects.py` — and the SHA-256 of every file it produces, so a re-run can be **checked** rather
than trusted. One version does not silently reverse a convention the previous one wrote down; this is
`probe/build_inputs.py`'s treatment, applied again.

## The recipe

```
python baseline/build_subjects.py --sources <synthetic portraits> --out <dir>
```

The sources are nine synthetic portraits, all 832×1216. Synthetic on purpose: no real person's
likeness enters the baseline, which makes the "do not commit derived faces" rule a matter of
convention here rather than of consequence.

## The six

| subject | stored | render target | slot | labelled |
|---|---|---|---|:---:|
| `s1_control_blonde` | 832×1216 | 1024×1472 | control — uniform blonde, frontal | ✅ |
| `s2_control_brunette` | 832×1216 | 1024×1472 | control — brunette close-up, a **different hair colour**, so the two controls are not one case counted twice | ✅ |
| `s3_multitone_balayage` | 832×1216 | 1024×1472 | multi-tone — dark roots into blonde ends, curly. The dominant-colour metric returns one mode and this hair has two | ✅ |
| `s4_multitone_bob` | 832×1216 | 1024×1472 | multi-tone — dark brown with caramel highlights, short bob. Multi-tone again, stressing a **different** thing: a small hair region rather than a large one | ✅ |
| `s5_small_face` | 832×1216 | 1024×1472 | refusal path — a full-length figure whose face is ~1.3% of the canvas. Exercises the guard and the absent-face field | ❌ |
| `s6_landscape` | **832×554** | **1536×1024** | refusal path — the only landscape input this project has ever rendered on a GPU | ❌ |

**Four are labelled, two are not.** 40 judgements is 4 subjects × 10 within-subject pairs (`design.md`
D10). `s5` and `s6` carry no labels: a subject whose axes are *expected* to refuse cannot calibrate
anything, and asking the operator to compare renders the scorer declined to score would be asking a
question with no answer on the other side.

### On `s6`, which is derived rather than generated

The source set is entirely portrait. `s6` is a crop, exactly as v0.11's landscape probe input was, and
it reuses that input's 832×554 geometry so a difference between the two versions' landscape cases is
not a difference in the crop. The crop origin is `y=150` rather than the centre, because a centred crop
of a standing figure is a crop of its chest, and a subject with no face in it measures the scale node
while proving nothing about the rest of the graph.

What the landscape case is *for* is the injector's short-side rounding on the **height** axis:
832×554 resolves to a 1536×1024 target, an aspect ratio this pipeline has never rendered and a gap
`CHANGELOG.md` v0.11 names explicitly. A crop exercises that identically to a natively-framed wide
shot.

### Sources deliberately unused

Recorded so the selection is reviewable rather than merely asserted:

- **`00060`** — the same person and the same shoot as `s5` (identical lace robe). Two slots filled by
  one subject would put one person's renders on both sides of a *different subject* comparison.
- **`00061`, `00072`** — further uniform-blonde frontal portraits. That is the case `s1` already
  covers, and a third control measures the same thing a third time.

## Digests

Every file `build_subjects.py` produced, from two consecutive runs that agreed byte for byte.
ImageMagick stamps a PNG with the time it wrote it, so the recipe strips profiles and excludes the
date chunks — without that, a recorded digest would verify nothing.

| file | stored | sha256 |
|---|---|---|
| `s1_control_blonde.png` | 832×1216 | `dede5477591b55ec8aacd2a2173d6b3b0139ecd601ce36a9671d34b628e88ba6` |
| `s2_control_brunette.png` | 832×1216 | `8eb8668b09c1b3e5271566c3a87416a93dda89589cbba4bb1b38321f235776b5` |
| `s3_multitone_balayage.png` | 832×1216 | `e4fb82b3e03801bafcce3e8485aa7287e4906e1647a548638676857c31d400c8` |
| `s4_multitone_bob.png` | 832×1216 | `12e0aa923fb05edda4c4ab873019627ac241cee4b94603937437fca6589643ed` |
| `s5_small_face.png` | 832×1216 | `a9d4e1da055b46f566eb8bf035d8f144df1dd95da59ff7f692a08eb0ceeb2f12` |
| `s6_landscape.png` | 832×554 | `756ab89deabe79d2ac6464b9a7647fb96aa5def5b6f2c52ebc2b117bad75fdc8` |

## What the scorer reads from them, before any render exists

Measured locally, on CPU, against the pinned artifacts. This is not a result — it is the confirmation
that all six subjects are legible to the instrument at all, taken before a pod was created.

| subject | face box | hair area | keypoints ≥ 0.3 |
|---|---|---|---|
| `s1_control_blonde` | (363,209)–(694,554) | 0.1190 | 100 / 133 |
| `s2_control_brunette` | (210,289)–(759,898) | 0.3104 | 84 / 133 |
| `s3_multitone_balayage` | (592,305)–(766,508) | 0.0374 | 133 / 133 |
| `s4_multitone_bob` | (361,208)–(725,605) | 0.0882 | 84 / 133 |
| `s5_small_face` | (500,84)–(628,236) | 0.0198 | 133 / 133 |
| `s6_landscape` | (404,0)–(750,399) | 0.1592 | 100 / 133 |

The hair areas span 0.0198 to 0.3104 — a factor of fifteen, all of it above the scorer's 0.005 floor,
so no subject refuses its region axes for lack of pixels before the renders even exist.

**`s5`'s face was found in the photograph.** That is worth stating plainly, because `s5` was chosen as
a refusal-path subject and its refusal has therefore **not** been demonstrated here. What is measured
above is the *anime* face detector run against a photograph; whether it locates a face in `s5`'s
**renders**, where the subject is small and stylized, is a phase-8 question and is not prejudged.

## Residual risk, stated rather than discovered later

**If the source photographs are lost, this baseline becomes unreproducible, and the labels are the only
surviving artifact.** The digests above would then prove that some file once existed and nothing about
what it contained. That is the accepted cost of not committing derived faces (`design.md` D15); there
is no mitigation beyond keeping the sources, and it is written here so the trade is visible rather than
implicit.
