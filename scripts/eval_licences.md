# The evaluator's model licences — read, quoted, and what each one costs

The tracked note that sits beside `scripts/eval_models.json`, the way that manifest sits beside
`scripts/models.json`. Every artifact the scorer loads is listed here with the licence it ships
under, the URL that licence was read at, and the date it was read.

**Every licence below was read on 2026-09-06, and none of them forbids this use.** That was checked
before a line of scorer code was written, because a licence that forbids the use should kill a model
before an axis is built on it (`openspec/changes/0012-identity-evaluator/design.md`, D16, D18).

This repository is **Apache-2.0** (`LICENSE`), it is public, and it distributes **no model weights** —
`README.md` already says model weights are licensed separately by their publishers. That last fact is
what every row but the detector turns on.

---

## The four non-commercial artifacts — recorded deviations

Each is carried in the manner `README.md` already carries the tile ControlNet's *"no comic, animation
application are promised"* disclaimer: a restriction that is real, recorded, and does not bind this
project's actual use of the model.

**Read the standing cost first.** All four are non-commercial-research licences and this project is a
personal learning exercise. **If this project ever became commercial, all four would bite at once, and
retroactively — against a baseline already committed to git.** There is no mitigation for that beyond
knowing it. It is stated here rather than discovered later.

### StyleID — the primary face axis

- **Licence:** non-commercial research use. The Hugging Face card declares `license: other`.
- **Read at:** <https://github.com/kwanyun/StyleID> and <https://huggingface.co/kwanY/styleid>, 2026-09-06.

The repository's README says, verbatim:

> StyleID is released for non-commercial research use.

and

> Do not use FFHQ-derived data for biometric human recognition

The Hugging Face model card says the same thing in shorter form, verbatim:

> Open for non-commercial research. Do not use FFHQ for biometric human recognition

**On the FFHQ clause: it does not bind this use.** It governs the *dataset* — FFHQ-derived data — not
the encoder trained on it. This project runs the encoder over its own photographs and derives no
FFHQ data. It is recorded because it is adjacent to what the scorer does, not because it applies.

**On the website-versus-model-card conflict: there is no conflict.** The project page carries, in its
footer:

> This website is licensed under a [Creative Commons Attribution-ShareAlike 4.0 International License](https://creativecommons.org/licenses/by-sa/4.0/).

That is a notice about **the website**, and it is boilerplate from the Academic Project Page Template
it is built on — it appears immediately after the credit to that template. The repository and the
model card agree with each other, and they are what govern the model. Read at
<https://kwanyun.github.io/StyleID_page/>, 2026-09-06. This change was cut believing the two
disagreed; they do not.

### `segformer_b2_clothes` — the region parser

- **Licence:** NVIDIA Source Code License, inherited from SegFormer. The Hugging Face card declares
  `license: other` and points at NVlabs.
- **Read at:** <https://huggingface.co/mattmdjaga/segformer_b2_clothes> and
  <https://github.com/NVlabs/SegFormer/blob/master/LICENSE>, 2026-09-06.

The model card says, verbatim:

> The license for this model can be found [here](https://github.com/NVlabs/SegFormer/blob/master/LICENSE).

That licence, §3.3, says verbatim:

> The Work and any derivative works thereof only may be used or intended for use non-commercially.
> Notwithstanding the foregoing, NVIDIA and its affiliates may use the Work and any derivative works
> commercially. As used herein, "non-commercially" means for research or evaluation purposes only.

### `glintr100` / antelopev2 — the sanity recognizer

- **Licence:** non-commercial research. InsightFace's *library* is MIT; its **weights are not**.
- **Read at:** <https://github.com/deepinsight/insightface>, 2026-09-06.

The project README states the split in two consecutive sentences, verbatim:

> The code of InsightFace is released under the MIT License. There is no limitation for both academic
> and commercial usage.

> The training data containing the annotation (and the models trained with these data) are available
> for non-commercial research purposes only.

`glintr100` is a model trained with that data, so it falls under the second sentence and not the
first. Its README also, as of 2025-11-24, directs licensing enquiries for its open-source recognition
models to `recognition-oss-pack@insightface.ai` — noted because it is the route that exists if this
project's use ever stops being non-commercial research.

**This one is not new.** It is the same artifact `scripts/models.json` has pinned and this project has
been shipping since v0.9, because it is the encoder the generator itself injects identity with. The
restriction was already being carried; recording it here is what makes that deliberate rather than
inherited by accident.

### DWPose — the pose axis

- **Licence:** **Apache-2.0.** Permissive; nothing to record beyond the fact.
- **Read at:** <https://github.com/IDEA-Research/DWPose/blob/onnx/LICENSE>, 2026-09-06.

**This was the one entry design.md left open, and it closes clean.** The file is the Apache License,
Version 2.0, verbatim from its first line. The pose axis is therefore unthreatened, and D9's
contingency — the pose axis reporting its own absence rather than a zero — is not needed on licence
grounds.

Like `glintr100`, both DWPose artifacts are already pinned in `scripts/models.json` and are reused
here byte for byte.

---

## The rule that survives all four

**A model whose licence is restrictive may not be the sole carrier of an axis.**

StyleID ships beside ArcFace or not at all. This is the load-bearing half of the original decision and
it stands whatever the licences turned out to say: it is what stops a single restricted artifact from
being the only thing standing between this project and a working face axis.

---

## The copyleft artifact — a different problem, and its resolution

### The anime-face detector

AGPL is **not** a use restriction. It restricts *distribution*, and it is copyleft. Importing an
AGPL-licensed Python package into this Apache-2.0 public repository would, on the standard reading,
combine the two and force the whole work to AGPL. Every licence above is safe precisely because no
weights are distributed; that argument does not rescue this one, because with a package it is **code**
that would be combined.

The resolution is to load a detector's weights through **`onnxruntime`** — MIT, already in the image
(`Dockerfile`) — and never to import the training framework. Loading weights is not linking code.

**The artifact this resolution names had to change, and here is exactly why.**

`design.md` D19 names `Fuyucchi/yolov8_animeface` (**AGPL-3.0**, `library_name: ultralytics`) and says
it will be loaded through `onnxruntime` with `ultralytics` never imported. Checked on 2026-09-06:

- its Hugging Face tree at revision `b0841ce930453c0f23ceb8086d6554c17de5fe4a` contains exactly one
  weight file, `yolov8x6_animeface.pt`;
- its sole GitHub release, `v1`, carries exactly the same one file.

**It publishes no ONNX export at all**, so D19's stated mechanism had no artifact to point at. The
three ways out were: export the `.pt` ourselves (rejected — the export needs `ultralytics` installed,
and the result is an artifact we produced, with no upstream revision to pin, which breaks D18's rule
that a branch name is not a pin); drop the detector and guard on landmark-centroid alignment alone
(D19's own stated reserve, at the cost of collapsing D9's two-way comparison to one method); or find a
published ONNX detector.

**Resolved 2026-09-06 in favour of the third.** `scripts/eval_models.json` pins:

- **`deepghs/anime_face_detection`**, `face_detect_v1.4_s`, revision
  `784dc4c0bb692351ddcdbe6131a050b17d3025d5`.
- **Licence: MIT.** Read at <https://huggingface.co/deepghs/anime_face_detection>, 2026-09-06; the
  model card's frontmatter declares `license: mit`.

This does not route around the AGPL problem — it **dissolves** it, and it keeps D9's guard measurable
both ways rather than one. The mechanism D19 argued for is unchanged and still enforced: the detector
is an ONNX file loaded through `onnxruntime`, and `ultralytics` is absent from the `[eval]` extra and
from the scorer's import graph, asserted by a test (phase 4), because a licence review nobody runs is
not a control.

**Recorded residual:** deepghs's MIT tag is deepghs's own declaration over weights trained with
YOLOv8/`ultralytics` tooling, and Ultralytics asserts AGPL over models trained with its code. That
assertion is about **weights**, and this repository distributes none and links no AGPL code — the same
weights-are-not-code reading D19 already rests on. It is written down here rather than relied on
silently.

---

## Summary

| artifact | licence | reading | pinned in |
|---|---|---|---|
| StyleID (`kwanY/styleid`) | non-commercial research | recorded deviation | `eval_models.json` |
| `segformer_b2_clothes` | NVIDIA Source Code License — non-commercial | recorded deviation | `eval_models.json` |
| `glintr100` / antelopev2 | non-commercial research; weights not MIT | recorded deviation, **shipping since v0.9** | both manifests, byte-identical |
| DWPose (`yolox_l`, `dw-ll_ucoco_384_bs5`) | **Apache-2.0** | permissive; the open entry, now closed | both manifests, byte-identical |
| `deepghs/anime_face_detection` | **MIT** | permissive; replaces D19's AGPL artifact | `eval_models.json` |
