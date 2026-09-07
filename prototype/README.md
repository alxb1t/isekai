# Prototype session — tuning the look, and the instrument that judges it

> **CLOSED 2026-09-07.** 23 findings, 8 pod sessions, ≈$1.80. **Read
> [`SUMMARY.md`](SUMMARY.md) first** — it carries the three-flow comparison, the eleven findings worth
> keeping, what was tried and failed, and what is parked. `FINDINGS.md` is the full evidence behind it.
> This file is the plan the session ran to, kept as the record of what was asked.

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
- [x] **T1 · style axis calibration** *($0)* — a candidate metric must order **photo < isekai < Fotor**
      on stylization, using files already on disk. Candidates: edge density, colour-count /
      posterisation, gradient smoothness, CLIP text-image against *"flat anime screencap"*.
      **If nothing separates those three, say so — that is a finding.**
- [x] **T2 · make the hair readout usable** *($0)* — the mode is invalid on a photograph (see
      `FINDINGS.md` F3). Needs to be trustworthy enough to use as a diagnostic while tuning, not
      necessarily production-correct.
- [x] **T3 · pod session 1 — the dial ladder** *(~20 min, ~$0.25)* — one subject (`s4_multitone_bob`,
      it lost the most), one seed, **one variable at a time**:

      | # | render | tests |
      |---|---|---|
      | 1 | current dials | the control |
      | 2 | negative + `realistic, photorealistic` | is the posterisation deficit the register? |
      | 3 | **lineart 0.2 → 0.6** | the 60× linework deficit is the larger, cleaner gap (F7) |
      | 4 | tile 0.2 → 0.9 | do accessories/colour come back? |
      | 5 | denoise 0.65 → 0.45 | identity↔style, **after** the register is right |

- [x] **T4 · read session 1** — done in-session; four rounds rather than one
- [x] ~~T4b~~ superseded by T6/T6b/T6c — the frontier is four points on ONE photograph. Re-run denoise 0.35/0.45/0.55 across all six subjects at 2–3 seeds before this is a setup rather than a candidate — by eye and with T1/T2. Decide session 2's variables.
- [x] **T5 · CHOOSE THE TARGET REGISTER** — **`notile`**, the rendered-illustration register. Chosen 2026-09-07.
- [x] ~~T5 (original)~~ *($0, operator)* — F10: the operator prefers `8_notile`
      (rendered anime illustration) over Fotor's flat cel. Until this is chosen, "better" is undefined
      and every dial search optimises toward whichever reference is on screen. **This gates T6 and T7.**
- [x] **T6 · pod session 2 — `notile` across all six subjects** *(~15 min)* — the operator's pick, run
      on every subject to see whether the register holds beyond `s4`. Its config is `tile 0.0` with
      everything else shipped (old register, denoise 0.65, lineart 0.2, pose 0.6); the run manifests
      are in `prototype/ladder/8_notile/`.
- [x] **T6b · the frontier, confirmed** — partly: six subjects, but 1 seed except s4 *(~20 min)* — F9's four points are ONE photograph at ONE seed.
      Re-run denoise 0.35 / 0.45 / 0.55 under the chosen register, all six subjects, 2–3 seeds, before
      it is a setup rather than a candidate.
- [x] **T6c · the register across ten diverse portraits** — F12. Generalises; the remaining failures are unmeasured ones
- [x] **T12 · the missing axes** — F14. `background_detail`, `background_colour`, `garment_colour` validate; `accessory_detail` did not
- [ ] **T8 · re-run the known-answer probe WITHIN one base** *($0)* — `notile d0.45` vs the shipped
      dials, all six, full evaluator. **Same base and same tool, so the face axes do not refuse** — this
      is a far better instrument test than the cross-base Fotor one, and the operator's eye already has
      an answer for it.
- [ ] *(deferred, notile closed)* **T9 · s5, the exception** — the only subject where shipped beats the candidate on hair, and the
      subject whose refusal path has never fired.
- [x] **T10a/T10b · provisioned + the instruction sweep** — F15: instruction is weak, the sampling path is strong, and 4-step / 20-step bracket the target
- [x] **T10d · sweep the SAMPLING PATH** — F17: the two architectures occupy DISJOINT regions; ours cannot reach Fotor's at any setting
- [x] **T10e · operator picked** `c_light_8_cfg2` → recorded as the `qwen-flatcel` preset from the sheet at `prototype/out/qwen_path_sheet.png` — Lightning (a/b/c, flat cel) vs full (d–g, painterly)
- [x] **T10f · all 10 portraits** — F18: register generalises; the two architectures fail in different shapes at the chosen setting, as `notile` got in T6c — steps x cfg x Lightning, the lever F15 identified. The target sits between two settings already run
- [ ] ~~T10 (original)~~ the instruction sweep — recover the Qwen path (`prototype/styles/qwen-image-edit.recovered.json`,
      from `e324699^`), grow the volume, and sweep the **instruction** rather than the architecture:
      F13 shows it overshot the register at 2x Fotor's linework because it was told "clean line art".
      Same six subjects, same axes.
- [ ] **T11 · the tattoo question** — Qwen kept the subject's chest ink. `xor` is a claim about global
      ControlNet and stands; this asks whether the project's largest parked feature is a *base* problem.
- [x] **T7 · style presets** — `notile-d045` recorded in `prototype/styles/`; the rule is *a workflow exists only if it has a committed scored baseline and a stated style target* — the operator wants several named setups rather than one. `notile`,
      `flat-cel`, and the shipped register are three candidates that already exist as run manifests.
      Note this is [backlog] `style menu`, previously held out of the arc and now evidence-backed.
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
