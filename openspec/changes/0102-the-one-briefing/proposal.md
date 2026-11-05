---
bump: minor
---

# 0102 — the one briefing

The caption briefing and the caption model leave the flows for `config/`, so one description serves every flow; the
flows are re-pinned, format only.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | each decision, and the tests it costs |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `caption`, `cli`, `image-generation`, `model-provisioning`, `run-directory`, `tagging` |

```
1 the config  config/caption.json and config/caption.briefing.md, their loader in foundation/;
              the reader and the hosted tagger read it; Flow.model and caption_briefing_path go
2 the flows   MANIFEST_VERSION 5; each flow.json drops "model"; each flow's briefing is deleted;
              SIBLINGS without it; every flow re-pinned, a digest each in CHANGELOG
3 the record  D14 and D6; README.md, docs/data-flow.md, isekai/pipeline/README.md
```

## Why

**Every flow carries the same briefing and names the same model.** Each `flows/*/caption.briefing.md` is the same
blob, and each `flow.json` says `"model": "joycaption-beta-one-q4k"`. A caption that several flows share needs one
description and one model, so both move out of the flows first.

## What Changes

- **`config/caption.json`**, new: `{"briefing": "caption.briefing.md", "model": "joycaption-beta-one-q4k"}`, read by
  a loader in `isekai/foundation/` ([D1](design.md#d1), [D2](design.md#d2)).
- **`config/caption.briefing.md`**, new: the flows' briefing, byte for byte. A caption records the same sha256 and
  is read under the same prompt; only the recorded path moves ([D1](design.md#d1)).
- **The reader and the hosted tagger** run the model `config/caption.json` names, for every flow
  ([D3](design.md#d3)).
- **BREAKING:** `MANIFEST_VERSION` moves to 5. A manifest declares no `model`, and a flow is `flow.json`,
  `graph.json` and `schema.json` ([D4](design.md#d4)).
- **Every flow is re-pinned in place, format only**, each new digest in `CHANGELOG.md` ([D5](design.md#d5)).
- **D14 and D6 are amended** in `docs/decisions.md` ([D6](design.md#d6)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `caption` — *The caption config names the reader's model and its briefing*: added, with its refusals.
- `caption` — *The flow names the model its reader runs*: removed.
- `caption` — *The reader takes a photograph and returns prose, for one flow*: removed; *The reader takes a
  photograph and its briefing, and returns prose for one flow* is added, the briefing from the caption config,
  re-keyed `caption:inputs:briefing-comes-from-the-config`.
- `caption` — *A hosted model that is not running or not installed is refused before any attempt is spent*: the
  unpinned-model scenario names the caption config, not a flow.
- `cli` — *Every per-flow seam is resolved per flow, on the model that flow names, for a flow that declares its
  stage*: removed; *Every per-flow seam is resolved per flow, for a flow that declares its stage* is added, every
  flow on the configured model, `cli:resolution:one-command-one-model`.
- `cli` — *A stage verb requires the flows it acts on, and takes more than one*: the flow supplies no briefing.
- `image-generation` — *Every flow declares the model its hosted stages run*: removed.
- `image-generation` — *An unrecognised manifest key is refused, naming what it carries*: removed; *An unrecognised
  or misspelled manifest key is refused, naming what it carries* is added, its example `taggr`, re-keyed
  `image-generation:manifest:a-misspelled-key-is-refused`.
- `image-generation` — *A flow is a flat directory of named files whose manifest declares and never computes*: no
  briefing and no model.
- `image-generation` — *A flow is pinned by equality; changing any file in it is an explicit act*: no briefing.
- `image-generation` — *A control flow equals its subject flow but for the dials it zeroes*: no briefing to compare.
- `image-generation` — *A flat flow is its subject with the face chain ending early and a flat style*: no briefing
  to compare.
- `image-generation` — *A semireal and a vivid flow are their subject's face chain ending early, in a style of
  their own*: no briefing to compare.
- `model-provisioning` — *The reader's files are provisioned from their own manifest, keyed by the model they
  build*: removed; *…keyed by the model the caption config names* is added, re-keyed
  `model-provisioning:reader:the-caption-model-is-pinned`.
- `run-directory` — *Every artifact declares its schema and what produced it*: instructions are a constant or a
  file, not a flow's.
- `run-directory` — *The run directory is input above, flow below, and every artifact is a flow's own*: a caption
  is written for a flow, not under its briefing.
- `tagging` — *Both taggers run for a flow that declares the tagger, and the hosted one runs on the model the flow
  names*: removed; *…the hosted one runs on the reader's model* is added, re-keyed
  `tagging:independence:the-hosted-tagger-runs-the-readers-model`.

## Impact

- New: `config/caption.json`, `config/caption.briefing.md`, `isekai/foundation/caption_config.py`.
- Code: `isekai/foundation/flow.py`, `isekai/interface/wiring.py`, `isekai/interface/cli.py`,
  `isekai/pipeline/caption.py`, `isekai/pipeline/tagging.py`, `isekai/boundary/wd14.py`, `isekai/boundary/ollama.py`'s
  refusal text, `tools/derive_reader.py`'s comment; each `flows/*/flow.json`;
  each `flows/*/caption.briefing.md` deleted.
- Tests: `tests/test_flow.py`, `tests/test_caption.py`, `tests/test_pipeline_cli.py`, `tests/test_tagging.py`,
  `tests/test_reader_manifest.py`, `tests/test_generate.py`, `tests/test_run_directory.py`, `tests/test_compare.py`,
  `tests/test_package_paths.py`, `tests/test_resume.py`, `tests/fakes.py`, `tests/stages.py`; the goldens `tests/golden/caption.json` (the briefing's path) and
  `prompt.json`, `render.json`, `sheet.json`, `sheet-empty.json` (`summon-anime-wai`'s digest).
- Docs: `docs/decisions.md`, `docs/pins.md`, `README.md`, `docs/data-flow.md`, `isekai/README.md`, `isekai/foundation/README.md`,
  `isekai/pipeline/README.md`.
- **No change to the product:** the same briefing bytes, the same prompt, the same caption for the same photograph.
- `isekai/boundary/provision.py`, `config/reader.json` and the `Dockerfile` are untouched; the pod image pins
  `provision.py` by digest.

## Not in this change

- A caption the flows share, its store, its readers and a migration of old runs: a later change, once the one
  briefing is on the default branch.
- A loader in `isekai/boundary/provision.py`: the pod image pins that file, so an edit there is an image rebuild.
- A new decision: D14 and D6 are amended, and D5 is read.
