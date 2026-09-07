# Prototype session — tuning the look, and the instrument that judges it

**Not a version. This branch (`v0.13_prototype`) does not merge.** It exists to answer empirical
questions cheaply, in practice rather than on paper. When the answers are in, they are written up
and a proper change is cut from them — the branch is the workshop, `FINDINGS.md` is the product.

**Tuning by eye is allowed here and nowhere else.** The rule that dials are settled by numbers
binds *versions*. A branch that never merges settles nothing; it produces candidates the eventual
change re-measures.

---

## The problem, in one line

Our renders are **semi-realistic and blurry** where a commercial tool (Fotor) produces **flat cel
anime that keeps far more of the subject** — and our own evaluator, asked which is better, picks
ours on every axis.

## Questions we are trying to answer

| | question | how it gets answered |
|---|---|---|
| **Q1** | Is the semi-realistic look a **register** problem (prompt/negative) or a **conditioning** problem (dials)? | pod, one variable at a time |
| **Q2** | Does **tile at 0.9** (its card's own recommendation, we run 0.2) bring back accessories, garment colour and background? | pod |
| **Q3** | Can a **style axis** be built at all — one that orders photo < ours < Fotor correctly? | $0, files already on disk |
| **Q4** | Is `hair_colour_delta_e` fixable, or is dominant-colour the wrong idea on a photograph? | $0 |
| **Q5** | After tuning, does the gap to Fotor close — or is this **architecture** (instruction-edit vs img2img+ControlNet)? | the whole point |

**Q5 is the one that matters.** Everything else is in service of answering it honestly.

## Findings we are hunting

- a dial set that produces **flat anime with identity kept**, written down exactly
- whether a style metric is buildable, and what it is made of
- a defensible answer to *dials or architecture*
- the residuals: what tuning cannot fix

---

## Tasks

Order matters. **T1 before T3** — building the style metric *after* tuning means building one that
agrees with what we already picked.

- [x] **T0 · external-render seam** — score a render this pipeline did not produce. `b0dac41`
- [ ] **T1 · style axis calibration** *($0)* — a candidate metric must order **photo < isekai < Fotor**
      on stylization, using files already on disk. Candidates: edge density, colour-count /
      posterisation, gradient smoothness, CLIP text-image against *"flat anime screencap"*.
      **If nothing separates those three, say so — that is a finding.**
- [ ] **T2 · make the hair readout usable** *($0)* — the mode is invalid on a photograph (see
      `FINDINGS.md` F3). Needs to be trustworthy enough to use as a diagnostic while tuning, not
      necessarily production-correct.
- [ ] **T3 · pod session 1 — the dial ladder** *(~20 min, ~$0.25)* — one subject (`s4_multitone_bob`,
      it lost the most), one seed, **one variable at a time**:

      | # | render | tests |
      |---|---|---|
      | 1 | current dials | the control |
      | 2 | negative + `realistic, photorealistic` | is the blur the register? |
      | 3 | tile 0.2 → 0.9 | do accessories/colour come back? |
      | 4 | lineart 0.2 → 0.6 | does flat linework need the edge leg? |
      | 5 | denoise 0.65 → 0.45 | identity↔style, **after** the register is right |

- [ ] **T4 · read session 1** — by eye and with T1/T2. Decide session 2's variables.
- [ ] **T5 · pod session 2** — combinations of whatever won, plus `cn_strength` (never searched).
- [ ] **T6 · re-probe against Fotor** — repaired axes, all six subjects. Does the instrument now
      agree with the eye?
- [ ] **T7 · answer Q5** — dials or architecture, with the evidence for it.
- [ ] **T8 · write it up** — lessons, the exact working setup, then cut a real change.

---

## Blockers

| | blocker | owner |
|---|---|---|
| **B1** | Fotor outputs for `s3`, `s4`, `s5`, `s6` — same effect, clean export, no watermark | **human** |
| **B2** | The Fotor **effect name** is not recorded. Filenames say `ai-art-effects`, which is the family | **human** |
| **B3** | `0012:R3` — four eval artifacts are pinned, verified and **never read**, and the pinned anime-face `threshold.json` publishes **0.307** where the code hardcodes **0.25**. Upstream of every region number. Not blocking eye-tuning; blocking any re-scored table | agent |
| **B4** | T3–T5 need a pod. Standing authority: **45 min / ~$0.30 per session**, no approval needed, teardown confirmed via MCP and recorded | agent |

## Human TODO

- [ ] download `s3`, `s4`, `s5`, `s6` from Fotor — **same effect as s1/s2**, clean, native size
- [ ] write the exact effect name into `FINDINGS.md` under F0
- [ ] note whether Fotor **resized or cropped** the upload

---

## Resuming in a fresh thread

Everything needed to pick this up cold:

```bash
git checkout v0.13_prototype          # never merges
uv sync --extra eval                  # torch/transformers/onnxruntime, ~3 GB

# score a render this pipeline did not produce
PYTHONPATH=. uv run --extra eval python prototype/external_eval.py \
  --photo inputs/baseline/s1_control_blonde.png \
  --render <fotor.jpg> --subject s1_control_blonde --tool "fotor:<effect>"
# add --force-embeddings to suppress the cross-base refusal (output tagged EXPLORATORY)
```

| what | where |
|---|---|
| six subject photos | `inputs/baseline/*.png` — digests in `baseline/README.md` |
| 30 isekai renders + their scores | `outputs/baseline/<subject>/{0..4}.png`, `*.eval.json` |
| pinned eval models (2.3 GB) | `models/` |
| Fotor outputs | not in the repo — operator's `~/Downloads/fotor/` |
| what we have learned | `prototype/FINDINGS.md` ← **read this first** |
| resampled canvases | `prototype/out/` (gitignored) |

**Read `FINDINGS.md` before doing anything.** It carries why the plan is shaped this way, and
several of the tasks above only make sense against it.
