# Tasks — 0020 readable caption

## Progress

- [x] 1 — The gate learns to see the browser, and the `tagging` extra
- [x] 2 — `run.py`: two layout names, two budget entries
- [x] 3 — `scripts/vocabulary.json`: the model pinned beside its own label index
- [x] 4 — `boundary/wd14.py`: the session, the label index, and the fake that keeps the suite offline
- [ ] 5 — `pipeline/tagging.py`: two functions, two seams, `constant_record()`
- [ ] 6 — `wiring` resolves a tagger per flow, and `caption` says three times
- [ ] 7 — `run_view.STAGES`: the two stages `show` would otherwise not see
- [ ] 8 — The surface: sentences, two chip lists, and the payload that feeds them
- [ ] 9 — The documents this version makes false
- [ ] 10 — ⚠️ **HUMAN · FREE** — the three artifacts end to end, on one synthetic portrait
- [ ] 11 — ⚠️ **HUMAN · FREE** — the acceptance, on fresh photographs

## The per-phase ritual

1. **Run each sub-task's stated verification — run it, never summarize it. Paste real output.**
2. **Gate green before the commit** — `make gate`, the commands in `.minions/minions.toml`'s `gate`
   array, in order. **Never weaken the gate to pass**; halt and say so.
3. A `CHANGELOG.md` entry under `## [Unreleased]`, appended in that phase's own commit.
4. The phase's box ticked in `## Progress` above, in that phase's own commit.
5. **One commit per phase**, staged **by name**, carrying `Change: 0020-readable-caption` contiguous
   with the `Co-Authored-By:` line.
6. **Every new test carries a binding** — `@pytest.mark.spec("<key>")` naming the scenario it proves,
   or `@pytest.mark.spec_exempt("<reason>")` if it is genuinely structural.

## Who builds which phase — read this before taking the first unticked box

**Nine of the eleven phases are the builder's, and they are free, offline and deterministic.** There
are no discovery phases: both build-time discoveries were run at the grilling and their results are in
`design.md` D1, D2, D11, D12 and D13. Do not re-run them to confirm; if a body disagrees with one, that
is a halt.

```
  1 - 9     BUILDER    free, offline, deterministic. The whole of the code
  10        HUMAN      needs Ollama up and both model files present. HALT and hand back
  11        HUMAN      the acceptance. Fresh photographs, the operator's judgement. HALT
```

**Two things that are a HALT, not a judgement call**

1. **If any file:line citation in `design.md` does not match the body it names**, that is `design.md`
   contradicting the code — a finding, not a divergence to work around. Every citation in it was
   verified against `main` at the cut; a mismatch means the tree has moved since.
2. **`design.md` is authoritative and the builder does not amend it.** Where the build disagrees with a
   decision it settled, stop and state the disagreement.

**No phase in this change spends money.** WD14 is a local ONNX pass, JoyCaption and Qwen are on
localhost, and the acceptance requires no render. If a phase appears to need a pod, that is a halt.

---

## 1 — The gate learns to see the browser, and the `tagging` extra

**Why first:** phase 8's whole product is browser code, and the Python gate cannot execute a line of it.
Adding the one check that can, before anything is built, is what makes every later browser phase run
under it (`design.md` D22).

- [x] 1.1 Add `npm run typecheck` to the `gate` array in `.minions/minions.toml` **and** to the `gate`
      target in `Makefile`, in the same position in both. It runs `vue-tsc --noEmit` from `ui/`, so it
      needs `ui/node_modules/`; make it refuse by name when that is absent rather than failing
      obscurely — `bundle.py`'s existing refusal is the shape to copy.
      **Verify:** `make gate` — every command exits 0, and the new one appears in the output.
- [x] 1.2 Add the `tagging` extra to `pyproject.toml`:
      `tagging = ["onnxruntime>=1.20", "numpy>=2.1", "Pillow>=11.0"]`, with a comment above it stating
      why it is not the `eval` extra (`design.md` D19). **`dependencies = []` does not move.**
      **Verify:** `uv lock && git diff --stat uv.lock` — commit the lockfile if it changed;
      then `uv sync --locked` exits 0.
- [x] 1.3 Prove the runtime rule still holds.
      **Verify:** the three existing guards, by name —
      `uv run pytest tests/test_pipeline_cli.py -k "site_packages_off_the_path or stdlib_guard" -v`
      (`test_the_pipeline_entry_point_imports_with_site_packages_off_the_path`,
      `test_the_run_directory_module_imports_with_site_packages_off_the_path`, and the falsification
      test that proves `-S` actually refuses).

**Gate green. Commit.**

## 2 — `run.py`: two layout names, two budget entries

**Why here:** phases 4 and 5 write into directories these constants name, and phase 7 reads them.

- [x] 2.1 `isekai/foundation/run.py`: add `TAGS = "tags"` and `WD14 = "wd14"` beside `CAPTIONS`,
      `SHEETS`, `REVIEW`, `PROMPTS`, `OUTPUTS` (`run.py:106-111`).
- [x] 2.2 `BUDGETS` (`run.py:128-133`) gains `"tags": 3` and `"wd14": 1`. **Three for the hosted
      tagger** — it is over HTTP and flaky, like `caption` and `sheet`. **One for the local tagger** —
      it is deterministic, so a second attempt cannot succeed where the first failed, exactly as
      `assemble` and `render` are one.
      **Verify:** a test asserting `check_budget` refuses by name for each new stage rather than
      raising `KeyError`, bound `@pytest.mark.spec("tagging:budget:each-tagger-has-its-own-budget")`.
      Run: `uv run pytest tests/test_run_directory.py -k budget -v`

**Gate green. Commit.**

## 3 — `scripts/vocabulary.json`: the model pinned beside its own label index

**Why here:** phase 4 verifies against this pin, so it must exist first.

- [x] 3.1 Add a second entry to `scripts/vocabulary.json` for `wd14/model.onnx`, same publisher and
      same revision as the CSV already there: sha256
      `e6774bff34d43bd49f75a47db4ef217dce701c9847b546523eb85ff6dbba1db1`, 467460978 bytes, source
      `https://huggingface.co/SmilingWolf/wd-swinv2-tagger-v3/resolve/627aef95638667ddcaa3ac8ae625e88ea5b02f51/model.onnx`.
      **Leave `lfs` at its default `True`** — `digest_of()` routes an LFS object through
      `published_digest()`, which reads the object id from the API, so this costs no download.
      **Verify:** `shasum -a 256 models/wd14/model.onnx` matches the digest the manifest now records.
- [x] 3.1a **Rewrite `derive_vocabulary.py`'s module docstring, which currently argues the opposite.**
      It says *"One entry, and deliberately one… the tagger is not here: this repository does not run
      it… a manifest that carried both would make swapping the vocabulary a decision about a model
      nobody loads."* **That premise is what this version falsifies**, and leaving it would put a
      tracked file in direct contradiction with `design.md` — a halt condition, not a stale comment.
      Replace it with D18's reason: the two files are **one artifact split in two**, row N of the CSV
      naming neuron N, so a manifest holding one without the other cannot detect the mismatch that
      matters. **Do not delete the paragraph silently**; the new text must say what changed and why.
- [x] 3.2 Re-derive and prove the derivation is stable.
      **Verify:** `uv run python scripts/derive_vocabulary.py && git diff --exit-code scripts/vocabulary.json`
      — exits 0, the file is byte-identical to what the script produces.
- [x] 3.3 A test asserting both entries carry the **same revision**, because row N of the CSV names
      neuron N and a mismatched pair mislabels every tag silently (`design.md` D18). Bound
      `@pytest.mark.spec("tagging:pin:the-label-index-and-the-model-are-verified-together")`.
      The manifest's existing home is `tests/test_vocabulary_manifest.py`, whose rules — an immutable
      revision, a digest and a byte count on every entry — the new entry must already satisfy.
      **Verify:** `uv run pytest tests/test_vocabulary_manifest.py -v`
- [x] 3.4 **The `model-provisioning` spec delta the cut omitted** (`design.md` D24). The living spec's
      `model-provisioning:vocabulary:tagger-model-is-not-included` forbids 3.1 in as many words, and
      two tests are bound to it. The delta is authored at
      `specs/model-provisioning/spec.md`: the vocabulary requirement `REMOVED` whole and a successor
      `ADDED` — openspec cannot retire one scenario through `MODIFIED` — with four scenarios crossing
      under their **existing keys** and the fifth inverted into
      `model-provisioning:vocabulary:label-index-and-model-share-a-revision`.
      Rebind the two tests in `tests/test_vocabulary_manifest.py` that name the retired key — the one
      asserting no model weights and the one asserting no model source — to the new key, asserting the
      **positive** property: both entries resolve one revision of one publisher's repository. Do not
      delete either; a manifest naming two revisions must still fail.
      Two more tests in that file encode the one-entry premise and must widen rather than be dropped:
      `…answers_one_question` (asserts `entries == [csv]`) and the provisioner's
      `…plans_the_vocabulary_when_pointed_at_its_manifest` (asserts one planned target).
      **Verify:** `npx @fission-ai/openspec@1.11.0 validate 0020-readable-caption --strict`
- [x] 3.5 `scripts/eval_licences.md`: `wd14/model.onnx` gains a record, because
      `test_every_vocabulary_artifact_is_named_in_the_licence_record` walks every manifest entry. Same
      repository and the same Apache-2.0 grant the CSV's row already cites, **re-read and re-dated**
      rather than inherited. The section's existing paragraph *"The tagger it is published beside is
      not pinned and is not loaded"* is now false and must be rewritten, not left.
      **Verify:** `uv run pytest tests/test_vocabulary_manifest.py -k licence -v`
- [x] 3.6 **`scripts/manifest.py`: `digest_of_url()` gets two guards** (`design.md` D25). Twice during
      this phase a dropped connection left a short read that was hashed and written to the tracked
      manifest — 143049 and 64311 bytes of a 308468-byte file, each a well-formed wrong digest.
      **① Refuse a body shorter than the response's declared `Content-Length`**, naming the
      shortfall; `curl` exits 18 on exactly this and `urllib` returns it silently. **② Send
      `Accept-Encoding: identity`** — latent rather than observed, and not subsumed by ①, because a
      coded response declares its *coded* length so ① would pass over a hashed gzip stream.
      **Only `vocabulary.json` is re-derived in this version**; `models.json` and `eval_models.json`
      are not touched. Two tests, bound
      `@pytest.mark.spec("model-provisioning:derivation:a-truncated-fetch-is-refused")` and
      `@pytest.mark.spec("model-provisioning:derivation:fetched-digest-demands-identity-encoding")`,
      driven through a fake opener rather than the network — the suite is offline.
      **Verify:** `uv run pytest tests/test_derivation.py -v`

**Gate green. Commit.**

## 4 — `boundary/wd14.py`: the session, the label index, and the fake that keeps the suite offline

**The whole non-stdlib import lives here and nowhere else**, and it is function-local (`design.md` D9,
D19). This module must not be importable-with-side-effects: opening a 467 MB file at import time
defeats D14.

- [x] 4.1 A `Session` Protocol — one method taking a prepared array and returning a probability vector
      — with the real `onnxruntime.InferenceSession` behind a module function as its default, exactly
      as `ollama.Transport` has `ollama.post`.
- [x] 4.2 The preparation rule, pure and testable without the model: open, composite onto white, pad to
      a square, resize to the session's own input dimension with bicubic, convert to BGR float32,
      add a batch axis. **Do not hard-code 448** — read it from the session's declared input shape.
- [x] 4.3 The label index: parse `selected_tags.csv` into `(name, category)` in file order, **and
      assert the ordering is what indexes the output vector.** Category 0 is general; 4 is character
      and 9 is rating, and neither is returned.
- [x] 4.4 Verify both digests against `scripts/vocabulary.json` before the first inference, and refuse
      naming the fetch command when either is absent or wrong — the posture `require_binary()` and
      `READER_REMEDY` already take, applied to two files.
- [x] 4.5 A fake session returning a known vector over a known three-row label index.
      **Verify — all of it offline, no model file touched:**
      `uv run pytest tests/test_wd14.py -v`, with bindings
      `tagging:seam:offline-double-satisfies-the-interface` and
      `tagging:pin:the-label-index-and-the-model-are-verified-together`.
      **One of these tests must prove the label-index ordering**: a fake vector whose only high value
      is at index 1 yields the tag on CSV row 1 and no other.

**Gate green. Commit.**

## 5 — `pipeline/tagging.py`: two functions, two seams, `constant_record()`

- [ ] 5.1 `caption_wd14(run, flow, tagger, *, new_version=False) -> Path | None` — the guard is
      `caption()`'s, character for character (`caption.py:252-254`), against `run.directory(flow, WD14)`.
      Body: a list of `{tag, confidence}` above a **0.15** floor, sorted by confidence descending
      (`design.md` D13). Producer: `implementation: "wd14"`, the model name, **`pinned: true`**, and
      both digests (`design.md` D17).
- [ ] 5.2 `caption_tags(run, flow, tagger, *, new_version=False) -> Path | None` — the same guard
      against `run.directory(flow, TAGS)`. The prompt is a module constant,
      `"Write a long list of Booru tags for this image.\n"` (D11); `TAGGER_OPTIONS` is
      `{temperature: 0, seed: 1, num_predict: 1024, repeat_penalty: 1.15}` (D12). **Split at the
      adapter, store the list**; no canonicalisation, no vocabulary filtering, no re-ordering.
      Producer: `implementation: "ollama"`, the model, `pinned: false`, and the prompt's digest.
- [ ] 5.3 `constant_record(text: str) -> dict[str, str]` beside `instructions_record(path)` in
      `isekai/boundary/claude_cli.py` — digest only, **no `path` key**, because a constant has none
      (`design.md` D16).
- [ ] 5.4 A response containing **no comma** is a permanent `CliFailure`, recorded like any other
      (D15). Everything with at least one comma is stored exactly as it came.
- [ ] 5.5 `FakeTagger` counting its calls, so the idempotence assertion is provable.
      **Verify:** `uv run pytest tests/test_tagging.py -v` — bindings
      `tagging:inputs:only-the-photograph-is-passed`, `tagging:output:artifact-is-a-list-of-tags`,
      `tagging:output:the-list-is-stored-unnarrowed`,
      `tagging:failure:a-response-with-no-comma-is-permanent`,
      `tagging:independence:a-complete-tagger-makes-no-call`,
      `tagging:provenance:the-local-tagger-declares-its-pin`,
      `tagging:provenance:the-hosted-tagger-records-its-prompt-digest`.
- [ ] 5.6 **Prove `caption()` did not move.**
      **Verify:** `git diff main -- isekai/pipeline/caption.py` prints nothing.

**Gate green. Commit.**

## 6 — `wiring` resolves a tagger per flow, and `caption` says three times

- [ ] 6.1 `isekai/interface/wiring.py`: `tagger_for(flow)` and a hosted-tagger resolver, both
      `Callable[[Flow], …] | None` on `Wiring`, **constructing nothing until a flow asks**
      (`design.md` D14). The local tagger resolves for **every** flow; the hosted one resolves only
      where `flow.hosted` exists and is absent — not a refusal — where it does not (D3, D20).
- [ ] 6.2 `isekai/interface/cli.py`: the `caption` branch (`cli.py:362-380`) gains two `_say` calls
      **in this order and no other** — prose, then wd14, then tags (`design.md` D7). Inline the calls
      as the existing one is; bind no locals.
- [ ] 6.3 A test proving the ordering isolates failures: a hosted tagger rigged to fail leaves the
      caption and the wd14 artifact on disk and complete. Bound
      `@pytest.mark.spec("tagging:order:a-late-failure-leaves-the-earlier-artifacts-complete")`.
- [ ] 6.4 Tests for the two resolution scenarios: a flow with no `hosted` block gets a local tagger and
      no hosted one; two flows on two implementations each get their own.
      **Verify:** `uv run pytest tests/test_tagging.py tests/test_pipeline_cli.py -v` with bindings
      `tagging:independence:the-local-tagger-needs-no-manifest-key`,
      `tagging:independence:the-hosted-tagger-is-absent-without-a-hosted-block`,
      `cli:resolution:a-seam-without-a-manifest-key-resolves-for-every-flow`.
- [ ] 6.5 **Prove resume still holds across all three stages.**
      **Verify:** `uv run pytest -k second_pass_is_inert -v` — and the test must now assert that a
      second pass opens **no session** as well as making no network call.

**Gate green. Commit.**

## 7 — `run_view.STAGES`: the two stages `show` would otherwise not see

- [ ] 7.1 `isekai/interface/run_view.py:40` — `STAGES` gains `WD14` and `TAGS`, in the order a run
      passes through them: `(CAPTIONS, WD14, TAGS, SHEETS, REVIEW, PROMPTS)`.
- [ ] 7.2 A test asserting `show` reports both new stages for a run that has them, and does not refuse
      for a run that does not. Bound `@pytest.mark.spec("run-directory:layout:stage-artifacts-live-under-the-flow")`.
- [ ] 7.3 A test asserting `show` prints a WD14 artifact **without** the word `unpinned` — it is the
      first producer in this repository that can honestly claim a pin (`design.md` D17,
      `run_view.py:66`). Bound `@pytest.mark.spec("tagging:provenance:the-local-tagger-declares-its-pin")`.
      **Verify:** `uv run pytest tests/test_run_view.py -v`

**Gate green. Commit.**

## 8 — The surface: sentences, two chip lists, and the payload that feeds them

**This is the phase whose product the Python gate cannot execute.** `npm run typecheck` from phase 1
checks that it compiles and that its props typecheck; nothing mechanical checks that it renders or that
a sentence broke in the right place. That is phase 10 and phase 11's job, and it is stated here so
nobody reads a green gate as proof of more.

- [ ] 8.1 `isekai/interface/ui/batch.py`: two resolvers beside `caption_path()` — `tags_path(held)` and
      `wd14_path(held)`, each `latest_artifact(held.run.directory(self.flow.id, …))`. **An absent one
      returns `None` and is never a refusal** (`design.md` D20). Startup's refusal order does not
      change: no new thing may block the port being bound.
- [ ] 8.2 `isekai/interface/ui/app.py`: `read_input`'s payload gains `tags: [{tag, in_vocabulary,
      posts}] | null` and `wd14: [{tag, confidence}] | null`. **Membership is marked server-side**
      (`design.md` D6 of the grilling record — `/api/tags` answers a fragment query and there is no
      membership endpoint; marking N tags must not mean N round trips). No new endpoint.
- [ ] 8.3 `ui/src/types.ts`: the two new payload types. `ui/src/api.ts`: nothing new — the data rides
      on `inputDetail()`.
- [ ] 8.4 `ui/src/caption.ts`: `sentencesOf(prose)`, beside `paragraphsOf()`. Split on sentence-ending
      punctuation followed by whitespace; the naive-against-abbreviations edge is known and accepted
      (`design.md` D2, and phase 11 looks for it).
- [ ] 8.5 `ui/src/components/CaptionPanel.vue`: render one sentence to a block. `SourcePanel.vue`: two
      `TagChip` lists stacked below the prose, **always visible, read-only, in this order — WD14 first,
      JoyCaption second**, matching the order the pipeline produces them and putting the usable list
      nearer the prose. WD14 chips carry the confidence; JoyCaption chips carry the post count where
      the tag is in the vocabulary and nothing where it is not — a chip with no count reads as the
      model's word rather than Danbooru's, which is the scepticism that defuses the anchoring risk.
      **No new component, colour, spacing or type step** (`design.md` D21). If one proves necessary,
      that is a halt and a finding.
- [ ] 8.6 **Verify:** `uv run pytest tests/test_ui_api.py -v` with bindings
      `ui:source:both-tag-lists-are-shown-raw-and-read-only`,
      `ui:source:vocabulary-membership-is-marked-by-the-server`,
      `ui:source:an-absent-tag-artifact-is-silent` — the last asserting the payload carries `null` and
      the surface still serves, for an input with neither artifact.
      Then: `cd ui && npm run typecheck` exits 0.

**Gate green. Commit.**

## 9 — The documents this version makes false

- [ ] 9.1 `README.md` and `CLAUDE.md`: the `caption` verb produces three artifacts;
      `isekai/boundary/wd14.py` and `isekai/pipeline/tagging.py` join the layout paragraph; the
      `tagging` extra joins the extras; `models/wd14/model.onnx` is named as a pinned artifact the
      operator fetches. Each group directory's `README.md` names its new file and who imports it.
- [ ] 9.2 **Three specific lines, found by a sweep at the cut, so they are fixed rather than
      rediscovered:**
      - **`CLAUDE.md:132` says *"nine capabilities"* and there are already TEN** — `caption`, `cli`,
        `comfy-transport`, `evaluation`, `image-generation`, `model-provisioning`, `review`,
        `run-directory`, `sheet`, `ui`. It was stale before this version. **Write `eleven`**, and count
        `openspec/specs/*/` rather than trusting either number.
      - **`CLAUDE.md:167` and `README.md:251` describe `pipeline/` as *"the four staged verbs"***. That
        stays true — v0.20 adds no verb — but `pipeline/` now holds a fifth module that is **not** a
        verb. Say so rather than making the count wrong in the other direction.
      - **`CLAUDE.md:237`'s *"driven in four staged verbs"*** is unchanged and correct. Leave it.
      **Verify:** `ls openspec/specs/ | wc -l` agrees with the number `CLAUDE.md` states.
- [ ] 9.3 `CLAUDE.md`'s gate paragraph gains the sixth command.
      **Verify:** `git grep -n "nine capabilities\|ten capabilities"` returns nothing stale; then
      `make gate` — six commands now, all exiting 0.

**Gate green. Commit.**

## 10 — ⚠️ **HUMAN · FREE** — the three artifacts end to end, on one synthetic portrait

**Stop here and hand back.** This needs Ollama running, `joycaption-beta-one-q4k` and
`models/wd14/model.onnx` present, and `uv sync --extra tagging`. An agent must not assume any of them.

- [ ] 10.1 Pick **one or two** images from `.data/inputs/synthetic/` — synthetic portraits, not
      personal photographs — and a throwaway `--runs` root. **Do not write into `.data/v0.19/runs/`**:
      those directories are the recorded evidence of the last release's acceptance.
- [ ] 10.2 `python -m isekai caption <input> --flow summon-open-v1 --runs <throwaway>` — expect three
      lines. Then `python -m isekai sheet` and `python -m isekai ui` for the same input.
      **Verify:** paste all three `caption` lines; paste `python -m isekai show`'s output showing
      `captions`, `wd14` and `tags`, with the wd14 line **not** marked `unpinned`.
- [ ] 10.3 Re-run `caption` unchanged. **Verify:** three *already complete* lines, and not one byte of
      the run directory differs — `git status` is not the check here; diff the tree or compare mtimes.
- [ ] 10.4 Open the surface and confirm the three panes render: sentences one to a block, the WD14 list
      with confidences, the JoyCaption list with post counts on the in-vocabulary ones only.
- [ ] 10.5 Run the same input under `--flow summon-v1`. **Verify:** a `wd14` directory appears and a
      `tags` directory does not, and the surface shows one list rather than two — `design.md` D3.

**Gate green. Commit.**

## 11 — ⚠️ **HUMAN · FREE** — the acceptance, on fresh photographs

**Stop here and hand back.** No pod, no render, no metered call. Fresh photographs, not the three in
`.data/v0.19/runs/` — the claim is about reading a caption for the first time, and it cannot be tested
on captions already read.

- [ ] 11.1 Run the batch through `caption` → `sheet` → `ui` on the open flow and review it.
- [ ] 11.2 **Record ③ and ④ separately. They can fail independently, and a no is a finding.**

      > **④** *Reading the caption one sentence to a block made it easier to keep my place than reading
      > paragraphs did.* — and, mechanically: **was any sentence split in the wrong place?**
      >
      > **③a — WD14** *The scored list surfaced at least one tag I would not otherwise have reached,
      > and the confidences made the wrong ones dismissible at a glance.*
      >
      > **③b — JoyCaption** *The raw list surfaced at least one tag I would not otherwise have reached,
      > and the vocabulary marking made the unusable ones obvious.*

- [ ] 11.3 Write the verdict into `CHANGELOG.md` under `## [Unreleased]`, in the shape v0.18's and
      v0.19's acceptance entries take. **A no is recorded as a no**, with what it was.

**Gate green. Commit. Hand back to `mf-converge`.**
