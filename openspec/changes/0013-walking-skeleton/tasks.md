# Tasks — the walking skeleton

## Progress

- [x] 1 — Foundations: `Refusal` moves, the derivation module is extracted, the vocabulary is pinned
- [x] 2 — The run directory, the new entry point, and the second stdlib guard
- [x] 3 — The vocabulary object, the mapping cascade, and the schema
- [x] 4 — ① `caption` — a photograph in, prose out
- [x] 5 — ② `sheet` — prose in, canonical fields out
- [x] 6 — ③ `review` and `approve`
- [x] 7 — ④ `generate`, the flow, and `show`
- [ ] 8 — Resume: run everything twice and assert nothing moved
- [ ] 9 — ⚠️ **GPU · HALT** — one session, five photographs, end to end
- [ ] 10 — The banner, the changelog, and the version line

## The per-phase ritual

Every phase, without exception:

1. **Test-first where there is logic.** Every phase here has it except 9 and 10. Red → green.
2. **Run each phase's stated verification — run it, never summarize it.** Paste real output.
3. **Gate green before the commit** — `make gate`, the five commands in `.minions/minions.toml`'s
   `gate` array, in order. **Never weaken the gate to pass**; halt and say so.
4. **A `CHANGELOG.md` entry** under `## [Unreleased]`, appended in that phase's own commit.
5. **Check the box** in `## Progress` above, in that phase's own commit. The first unchecked entry is
   the current phase.
6. **One commit per phase**, staged **by name**, carrying the trailer `Change: 0013-walking-skeleton`
   **contiguous** with `Co-Authored-By:` — no blank line between them.

**The existing path is not touched.** `convert.py`, `isekai/cli.py`, `isekai/workflow.py`,
`isekai/mutate.py`, `isekai/overrides.py`, `isekai/pipeline.py` and `workflows/pipeline.json` are read
and imported, never edited, in every phase. A version that replaced the proven path before proving the
new one would have nothing to fall back to. The only exception is `isekai/evaluate.py`, and only to
re-export a class that moved out of it.

**Every test carries `@pytest.mark.spec("<key>")`** naming the scenario it proves, or
`@pytest.mark.spec_exempt("<reason>")` if it is genuinely structural. The keys are in this change's
`specs/`.

---

## 1. Foundations

- [x] 1.1 Move `Refusal` from `isekai/evaluate.py` into `isekai/refusal.py` and re-export it from
  `isekai/evaluate.py`; verify `uv run pytest` is green with no test changed, and that both
  `evaluate.py` and `isekai/eval_backends.py` still import it by their existing paths
- [x] 1.2 Extract `scripts/manifest.py` carrying `Manifest`, `ManifestEntry`, `Source`,
  `published_digest`, `blob_digest` and the manifest writer; verify by importing it from a scratch
  interpreter and printing each name
- [x] 1.3 Repoint `scripts/derive_manifest.py` and `scripts/derive_eval_manifest.py` at the shared
  module, deleting the duplicated writer and the second `Spec` shape; verify by re-running both and
  asserting `git diff --exit-code scripts/models.json scripts/eval_models.json` is clean
  (`model-provisioning:derivation:entry-type-has-one-definition`,
  `model-provisioning:derivation:both-digest-strategies-are-shared`,
  `model-provisioning:derivation:rerun-is-byte-identical`)
- [x] 1.4 Add `scripts/derive_vocabulary.py` writing `scripts/vocabulary.json`, one entry for
  `wd14/selected_tags.csv`, its source **resolved to an immutable revision** and its digest obtained by
  fetching and hashing (it is 308 KB and publishes no large-file record); verify by running it twice
  and asserting the second run leaves the file byte-identical
  (`model-provisioning:vocabulary:manifest-is-its-own-file`,
  `model-provisioning:vocabulary:tagger-model-is-not-included`)
- [x] 1.5 Add a test asserting `scripts/vocabulary.json` declares a digest, a byte count and at least
  one source, and that no source resolves a mutable reference — the same rule the graph manifest is
  held to (`model-provisioning:vocabulary:entry-is-pinned-and-digested`)
- [x] 1.6 Add the vocabulary artifact's row to `eval_licences.md` — the terms, the URL they were read
  from, and the date; verify the file parses in the form the existing rows use
  (`model-provisioning:licences:vocabulary-terms-are-recorded`)

## 2. The run directory

- [x] 2.1 Add `isekai/__main__.py` with an argument parser carrying the six subcommands as no-ops;
  verify `python -m isekai --help` lists all six and an unknown verb exits non-zero
  (`cli:pipeline-surface:verbs-are-subcommands`, `cli:pipeline-surface:unknown-verb-is-refused`)
- [x] 2.2 Add a second stdlib guard beside the existing one, importing `isekai.__main__` under `-S`;
  verify both guards and the shared falsifiability twin pass
  (`cli:pipeline-surface:entry-point-is-stdlib-only`)
- [x] 2.3 Implement the data root at `.data/runs/<photo-id>/`, the photo-id — a SHA-256 prefix plus a
  sanitised stem — and the frame writer; verify the three identity scenarios and the three frame
  scenarios
  (`run-directory:identity:*`, `run-directory:frame:*`)
- [x] 2.4 Implement the atomic writer — temporary file on the same filesystem, then replace; verify an
  interrupted write leaves nothing at the final path (`run-directory:atomicity:*`)
- [x] 2.5 Implement per-directory numbering and the artifact envelope — `schema`, `producer`,
  `producer.from`; verify the provenance and numbering scenarios
  (`run-directory:provenance:*`, `run-directory:numbering:each-directory-counts-its-own`)
- [x] 2.6 Implement error records as siblings, with the attempt ordinal and kind in the filename, and
  the retry budgets (① 3 · ② 3 · ④a 1 · ④b 1); verify the failure and budget scenarios, including that
  a failed attempt does not consume the artifact's number (`run-directory:failure:*`,
  `run-directory:budget:*`)
- [x] 2.7 Implement schema refusal on an unknown version, naming the remedy; verify the two schema
  scenarios (`run-directory:schema:*`)
- [x] 2.8 Implement the completion tests as directory listings, with approval read from the filename;
  verify no completion decision opens a file (`run-directory:readdir:*`)

## 3. The vocabulary and the schema

- [x] 3.1 Add `isekai/vocabulary.py` with `Vocabulary` (name, revision, digest, tag→post-count mapping)
  and `load` reading the provisioned CSV with the stdlib `csv` module, keeping general tags only and
  normalising underscores; verify it loads 8,106 tags and that `count` and `search` return the expected
  ordering
- [x] 3.2 Port the four-pass cascade — exact, per-field suffix, curated span-consuming, containment —
  taking the suffixes as an argument rather than looking them up by field name; verify the five mapping
  scenarios (`sheet:mapping:*`)
- [x] 3.3 Add `schemas/identity.v1.json` — sixteen identifier-safe fields in prompt order, the seven
  scored flags, the per-field suffixes, and the vocabulary it is written against; verify the three
  schema scenarios including that every field name is a legal JSON-schema property key
  (`sheet:schema:*`)
- [x] 3.4 Implement sheet validation against the schema and the vocabulary — every field present, empty
  legal, no tag outside the vocabulary; verify the purity and output scenarios
  (`sheet:purity:*`, `sheet:output:empty-field-is-legal`)

## 4. Stage ① — caption

- [x] 4.1 Define the `Reader` interface and a `FakeReader` that counts calls; verify the stage writes a
  caption with no network reached (`caption:seam:offline-double-satisfies-the-interface`)
- [x] 4.2 Implement the `claude -p` adapter — `--safe-mode --strict-mcp-config --no-session-persistence
  --tools Read --add-dir <run> --permission-prompts none --output-format json`; verify against a fake
  subprocess that the argument vector carries every one of those flags
- [x] 4.3 Write `briefings/caption.md` — prose only, licensed to state absence, no schema and no field
  list; verify a test asserts the briefing names no schema field
  (`caption:inputs:only-the-photograph-is-passed`)
- [x] 4.4 Implement `isekai caption`, writing prose, the producer with the briefing digest and the
  models that actually ran; verify the output, absence, reuse and producer scenarios
  (`caption:output:*`, `caption:absence:*`, `caption:seam:producer-names-the-implementation`)
- [x] 4.5 Implement envelope-based failure classification and the absent-binary refusal; verify the
  four failure and refusal scenarios (`caption:failure:*`, `caption:refusal:absent-reader-names-the-fix`)

## 5. Stage ② — sheet

- [x] 5.1 Define the sorting model interface and its fake; verify a sheet is written with no network
  (`sheet:seam:offline-double-satisfies-the-interface`)
- [x] 5.2 Write `schemas/identity.v1.briefing.md` — the routing rules and the two worked examples, using
  the **same identifier-safe field names** the schema declares; verify a test asserts every field name
  the briefing mentions exists in the schema
- [x] 5.3 Implement the `claude -p` adapter for this stage — `--tools ""`, the schema's field structure
  passed as the required output shape, wording unconstrained; verify the structure-constrained scenario
  and that a structurally wrong response is a permanent failure
  (`sheet:seam:structure-constrained-content-free`, `sheet:failure:structural-mismatch-is-permanent`)
- [x] 5.4 Implement `isekai sheet` — fill, map through the cascade, write fields only with the
  vocabulary's identity recorded; verify the output scenarios (`sheet:output:*`)
- [x] 5.5 Implement the once-per-(schema, vocabulary) rule, writing the result to every flow declaring
  that pair; verify with two flows sharing a pair that one fill serves both
  (`sheet:sharing:one-fill-serves-every-matching-flow`)

## 6. Stage ③ — review and approve

- [x] 6.1 Implement `isekai review` — copy the highest sheet into `review/<flow>/` as a draft, recording
  the source version; verify the three copy scenarios (`review:copy:*`)
- [x] 6.2 Implement `isekai approve` — validate, then rename; verify the three approval scenarios
  including that the bytes are unchanged (`review:approval:*`)
- [x] 6.3 Implement tag validation at approval with the honest message — not in the vocabulary's
  prediction set — and the missing-field refusal; verify the three validation scenarios
  (`review:validation:*`)
- [x] 6.4 Implement the token-window warning against the encoder's 77-token window; verify an over-long
  prompt warns and still approves (`review:budget:over-window-warns-not-refuses`)
- [x] 6.5 Record `edited` on the approved artifact by comparing it to its source sheet; verify both
  provenance scenarios (`review:provenance:*`)
- [x] 6.6 Ensure this stage writes no error record and consumes no budget; verify a refusal leaves the
  run directory unchanged (`review:refusal:no-error-record-is-written`)

## 7. Stage ④ — generate, the flow, and show

- [x] 7.1 Add `flows/summon-v1/` with its manifest declaring inputs, schema, vocabulary and the
  **measured** dials from design.md D12 — not the graph file's; verify the manifest parses and its
  schema and vocabulary resolve (`image-generation:manifest:*`)
- [x] 7.2 Add the flow-immutability test holding every tracked manifest against a committed digest;
  verify by editing a dial in a scratch copy and asserting the test fails naming the flow
  (`image-generation:immutability:flow-manifest-is-pinned-by-equality`)
- [x] 7.3 Implement `assemble` — pure, local, from the approved artifact and the flow's dials, in the
  schema's field order; verify the three assembly scenarios with no endpoint contacted
  (`image-generation:assembly:*`)
- [x] 7.4 Implement seed handling — a count drawing from an injected source, explicit seeds rendering
  exactly those, the two mutually exclusive; verify the four seed scenarios and the two parse-time CLI
  scenarios (`image-generation:seeds:*`, `cli:generate-signature:*`)
- [x] 7.5 Implement `render` over the existing `ComfyTransport`, writing outputs named by seed under the
  approved artifact's number, with provenance carrying flow, seed, version and graph digest; verify
  through the existing fake with no GPU and no network
  (`image-generation:transport:offline-double-drives-the-stage`,
  `image-generation:immutability:output-records-the-graph-digest`)
- [x] 7.6 Implement the approved-only rule and the absent-models preflight refusal; verify the inputs
  and preflight scenarios (`image-generation:inputs:*`, `image-generation:preflight:absent-models-refuse-early`)
- [x] 7.7 Implement per-image idempotence — an existing seed is skipped, a raised count renders only the
  shortfall; verify both scenarios (`image-generation:idempotence:*`)
- [x] 7.8 Implement `isekai show`; verify it marks the active version per stage and reports each
  artifact's producer (`cli:show:*`)

## 8. Resume

- [ ] 8.1 Write the resume test: run all six commands against a temporary run with every fake in place,
  snapshot the directory, run all six again, and assert **not one byte changed and not one call was
  made**; verify it is offline, needs no GPU and passes (`cli:resume:second-pass-is-inert`)
- [ ] 8.2 Verify the explicit-version flag against it — the flag writes the next number, the repeat
  invocation without it does nothing (`cli:explicit-versions:*`,
  `run-directory:idempotence:rerun-is-a-no-op`,
  `run-directory:idempotence:new-version-must-be-asked-for`)
- [ ] 8.3 Audit every refusal added in phases 2–7 for a remedy that this build can actually perform, and
  a non-zero exit; verify both refusal scenarios (`cli:refusals:*`)

## 9. ⚠️ **GPU · HALT** — the acceptance run

**This is the only metered phase.** Announce before `infra/up.sh`, tear down with `infra/down.sh` in the
same session, confirm the account is empty through the RunPod MCP and record what it returned. The
ceiling on this branch is **45 minutes and ~$0.30** per pod session; this run is planned at
**five photographs, one render each — $0.036 boot plus 5 × $0.0044 ≈ $0.058** — and about 15–25 minutes
boot to teardown. Exceeding the ceiling is a halt, not a judgement call.

- [ ] 9.1 Locally and for free, before anything is rented: `caption` → `sheet` → `review` → edit →
  `approve` for five photographs, then `generate` assembling every prompt; verify five assembled prompt
  artifacts exist and no endpoint was contacted
- [ ] 9.2 ⚠️ **GPU** — one session on the release-candidate image: bring the pod up, open the tunnel,
  render the five approved artifacts, download the outputs before teardown, tear down, confirm empty
- [ ] 9.3 Verify by eye that flow `summon-v1` rendered a recognisable anime image of each subject from a
  photograph nobody hand-captioned — the seam this whole version exists to cross — and record the
  session's duration and cost in `CHANGELOG.md`

## 10. Release preparation

- [ ] 10.1 Add the layout rule to `CLAUDE.md` — everything a run produces or consumes lives under
  `.data/`, which is gitignored, and `models/` stays separate because it is provisioned from a pinned
  manifest and is re-derivable byte-for-byte; verify `.gitignore` covers `.data` and that no tracked
  file writes outside it
- [ ] 10.2 Add the work-in-progress banner to `README.md`, once, stating that stages ① and ② need the
  `claude` binary and a subscription and that the open-model replacements are the next version; verify
  it renders and that no other README section was changed
- [ ] 10.3 Cut `CHANGELOG.md`'s `## [Unreleased]` entries into `## [0.13.0]`; verify the heading form
  matches the existing ones
- [ ] 10.4 Set the version line in all four places — `proposal.md`'s frontmatter, `CHANGELOG.md`'s
  heading, `pyproject.toml`'s `version`, and the annotated tag; verify all four read `0.13.0` and that
  `openspec validate 0013-walking-skeleton --strict` passes
