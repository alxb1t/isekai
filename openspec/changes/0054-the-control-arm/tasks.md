# Tasks — 0054 the control arm

The flow, the approval, the seeds, then the records, per [design](design.md). The deltas hold every new
scenario; each task below adds the tests that bind them.

## Progress

- [ ] 1 — The flow
- [ ] 2 — The approval
- [ ] 3 — The seeds
- [ ] 4 — The records

Line numbers are `04dfe26`'s. Every new test carries `@pytest.mark.spec` with the key its task names. The flow
phase's changelog bullet names the control's full digest, which the changelog-digest test requires.

## 1 — The flow

- [ ] 1.1 **HALT CHECK** — `summon` is pinned at the digest the brief read, its face dials are `0.9` and `0.8`, and no control flow exists.
  Verify: `grep -c '96c605821e68a8ac2f1c7a60807cfcfb4c3658ae4112cc84d21a00bf39f3e698' tests/test_flow.py` prints `1`, `grep -c '"ip_weight": 0.9,\|"identity_cn_strength": 0.8,' flows/summon-anime-wai/flow.json` prints `2`, and `test ! -e flows/control-anime-wai && echo none` prints `none`.
- [ ] 1.2 Copy `flows/summon-anime-wai/` to `flows/control-anime-wai/` and edit `flow.json`'s `flow`, `ip_weight` and `identity_cn_strength` per [D1](design.md#d1); add the control's digest to `PINNED` in `tests/test_flow.py`.
  Verify: `cmp flows/summon-anime-wai/graph.json flows/control-anime-wai/graph.json && cmp flows/summon-anime-wai/schema.json flows/control-anime-wai/schema.json && cmp flows/summon-anime-wai/caption.briefing.md flows/control-anime-wai/caption.briefing.md && echo same` prints `same`, `grep -c '"flow": "control-anime-wai"\|"ip_weight": 0,\|"identity_cn_strength": 0,' flows/control-anime-wai/flow.json` prints `3`, and `grep -c '"control-anime-wai":' tests/test_flow.py` prints `1`.
- [ ] 1.3 Add `CONTROLS` and the equality test to `tests/test_flow.py`, binding `image-generation:control:files-equal-the-subject` and `image-generation:control:manifest-differs-only-in-the-face-dials`.
  Verify: `grep -c '^CONTROLS' tests/test_flow.py` prints `1`, and `grep -c 'image-generation:control:' tests/test_flow.py` prints `2`.

## 2 — The approval

- [ ] 2.1 In `isekai/foundation/artifacts.py`, add `CopiedFrom` and `ApprovedProducer.copied_from`; in `isekai/pipeline/review.py`, give `approve` the `source` keyword per [D2](design.md#d2).
  Verify: `grep -c '^class CopiedFrom\|copied_from: NotRequired\[CopiedFrom\]' isekai/foundation/artifacts.py` prints `2`, and `grep -c 'source: str | None = None' isekai/pipeline/review.py` prints `1`.
- [ ] 2.2 In `isekai/interface/cli.py`, add `--from` to `approve` with `dest="source"`, refuse a source among the `--flow` names in `dispatch`, and pass it through `approve_flow`.
  Verify: `grep -c '"--from"' isekai/interface/cli.py` prints `1`, and `grep -c 'source=args.source' isekai/interface/cli.py` prints `1`.
- [ ] 2.3 Add to `tests/test_review.py` tests binding `review:copy-from:fields-are-copied-and-validated`, `review:copy-from:the-origin-is-recorded`, `review:copy-from:no-source-approval-is-refused`, `review:copy-from:an-approved-target-writes-nothing` and `run-directory:layout:a-named-source-is-recorded`; add to `tests/test_pipeline_cli.py` a test that `approve --from X --flow X` is refused naming `X`.
  Verify: `grep -c 'review:copy-from:' tests/test_review.py` prints `4`, `grep -c 'run-directory:layout:a-named-source-is-recorded' tests/test_review.py` prints `1`, and `grep -c '"--from"' tests/test_pipeline_cli.py` prints a number above `0`.

## 3 — The seeds

- [ ] 3.1 In `isekai/foundation/artifacts.py`, add `Render.seeds_from`; in `isekai/pipeline/generate.py`, add `source_seeds` and the `seeds_from` keyword on `render` that writes it into the sidecar, per [D3](design.md#d3).
  Verify: `grep -c 'seeds_from: NotRequired\[str\]' isekai/foundation/artifacts.py` prints `1`, and `grep -c '^def source_seeds(' isekai/pipeline/generate.py` prints `1`.
- [ ] 3.2 In `isekai/interface/cli.py`, add `--seeds-from` to `generate`'s exclusive group, refuse a source among the `--flow` names, and call `source_seeds` in `assemble_one` with its refusal collected in `broken`.
  Verify: `grep -c '"--seeds-from"' isekai/interface/cli.py` prints `1`, and `grep -c 'source_seeds(' isekai/interface/cli.py` prints `1`.
- [ ] 3.3 Add to `tests/test_generate.py` tests binding `image-generation:seeds-from:one-render-per-source-seed`, `image-generation:seeds-from:no-source-render-is-refused-first`, `image-generation:seeds-from:a-flow-is-not-its-own-source` and `image-generation:seeds-from:excludes-count-and-seeds`, the last on the parser beside `test_the_parser_refuses_a_count_and_a_seed_together` (`:384`).
  Verify: `grep -c 'image-generation:seeds-from:' tests/test_generate.py` prints `4`.
- [ ] 3.4 In `infra/render.sh`, widen the spec regex, add the free pass per named source before `up.sh`, and choose `--count` or `--seeds-from` in the render loop, per [D3](design.md#d3); restate the usage comment with both forms.
  Verify: `bash -n infra/render.sh && echo ok` prints `ok`, `grep -c -- '--seeds-from' infra/render.sh` prints `2`, and `grep -c 'control-anime-wai=summon-anime-wai' infra/render.sh` prints `1`.

## 4 — The records

- [ ] 4.1 In `docs/decisions.md`, add D38 after D31 per [D4](design.md#d4).
  Verify: `grep -c '^### D38 · A control flow is its subject with the face chain at zero' docs/decisions.md` prints `1`.
- [ ] 4.2 In `evaluation/README.md`, add `## The control arm` with the four commands and the floor line; in `README.md:387`'s tree, add the control's line; in `CLAUDE.md:5-7`, name the third flow.
  Verify: `grep -c '^## The control arm' evaluation/README.md` prints `1`, `grep -c 'control-anime-wai=summon-anime-wai' evaluation/README.md` prints `1`, `grep -c 'flows/control-anime-wai/' README.md` prints `1`, and `grep -c 'control-anime-wai' CLAUDE.md` prints `1`.
