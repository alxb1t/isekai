# Tasks — 0019 open models

## Progress

- [x] 1 — ⚠️ **OPERATOR** — the three build-time discoveries, before a line of adapter is written
- [x] 2 — `flow.py`: the `hosted` block parsed, and every unknown key refused
- [x] 3 — `boundary/ollama.py`: the transport, and nothing else
- [x] 4 — `OllamaReader`: a photograph in, prose out, no schema
- [x] 5 — `OllamaSorter`: prose and a shape in, the sixteen fields out
- [x] 6 — The registries, and the resolution moved inside the flow loop
- [x] 7 — `flows/summon-open-v1/`: the directory, both briefings, the pin
- [ ] 8 — The isolation proof, in the suite, non-vacuous
- [ ] 9 — The documents this version makes false
- [ ] 10 — ⚠️ **HUMAN · FREE** — the open flow end to end, stopping before the pod
- [ ] 11 — ⚠️ **HUMAN · METERED · GPU · HALT** — the acceptance render

## The per-phase ritual

1. **Run each sub-task's stated verification — run it, never summarize it. Paste real output.**
2. **Gate green before the commit** — `make gate`, the five commands in `.minions/minions.toml`'s `gate`
   array, in order. **Never weaken the gate to pass**; halt and say so.
3. A `CHANGELOG.md` entry under `## [Unreleased]`, appended in that phase's own commit.
4. The phase's box ticked in `## Progress` above, in that phase's own commit.
5. **One commit per phase**, staged **by name**, carrying `Change: 0019-open-models` contiguous with the
   `Co-Authored-By:` line.
6. **Every new test carries a binding** — `@pytest.mark.spec("<key>")` naming the scenario it proves, or
   `@pytest.mark.spec_exempt("<reason>")` if it is genuinely structural. An unregistered marker binds
   nothing while looking exactly like a binding.

## Who builds which phase — read this before taking the first unticked box

**Three of the eleven phases are the operator's and cannot be built by an agent.** They need a running
Ollama, two models created by hand, and the operator's own photographs on his own machine.

```
  1        OPERATOR   the three discoveries. HALT and hand back; do not attempt it
  2 - 9    BUILDER    free, offline, deterministic. The whole of the code
  10       OPERATOR   the open flow end to end, stopping before the pod. HALT
  11       OPERATOR   metered, GPU, and it halts for an explicit go
```

**So the build runs: operator does phase 1 and ticks its box → builder does 2 through 9 → operator does
10 and 11.** On reaching phase 1, 10 or 11 with the box unticked, **stop cleanly without committing and
say which phase is waiting on the operator.** An unticked box and a clean tree is the legible place to
resume from.

**Phase 1 comes first deliberately, and it is not merely setup: it decides D7**, which phase 4 is written
against. Phases 2 and 3 do not depend on its outcome, but the order is not negotiable — building phase 4
before D7 is decided is building against a guess.

### Two things that are a HALT, not a judgement call

1. **If phase 1.3 forces D7's fallback** — PIL as a function-local import — **that is a dependency
   decision and it is human-gated.** Stop and state it. **The builder does not amend `design.md`**; the
   decision is the operator's and the amendment is his, because `design.md` is authoritative and a builder
   that edits its own authority has none.
2. **If any file:line citation in `design.md` does not match the body it names**, that is
   `design.md` contradicting the code — a finding, not a divergence to work around. Every citation in it
   was verified against `main` at the cut; a mismatch means the tree has moved since.

### Two tests go red on purpose, and only one phase makes each green again

```
  tests/test_flow.py:430   assert sorted(PINNED) == tracked_flows()
                           RED the moment flows/summon-open-v1/ exists.  Green at 7.5.
                           The directory and its PINNED entry belong in ONE commit.

  the digest test          RED if any file in the new flow is edited after 7.5 pins it.
                           Author both briefings BEFORE taking 7.5, not after.
```

**Five existing tests loop over every tracked flow and all five pass for a copied flow** — the schema
document test, the stray-schema test, the models-pinned-by-digest test, the graph/manifest binding test
and the five-flat-files test. `models` is copied verbatim from `summon-v1`, so the digest test finds every
destination in `scripts/models.json` already. **Named here so a green result is understood rather than
trusted.**

---

**Phases 2–9 are free and offline.** Nothing in them contacts a host or spends money; every adapter test
runs through an injected transport, because the suite has no socket and is not gaining one.

> **Two phases are where this change can be found wrong rather than merely incomplete.** Phase 1, because
> a rejected request body invalidates D7 and its fallback has to be taken instead of assumed. Phase 10,
> because it is the first time the authored briefings meet the models they were written for, and
> `design.md`'s named risk is that an 8B fine-tune follows a 44-line briefing worse than the one-sentence
> prompt that was measured.

---

## 1. ⚠️ OPERATOR — the three build-time discoveries

**Not buildable by an agent. Halt and hand back.** Needs Ollama running, both models created by hand,
and one of the operator's own photographs.

**Nothing is committed here except the Modelfile.** Throwaway scripts go in `/tmp`, not in the tree.
`design.md` D3, D7, and the Risks table.

- [x] 1.1 Recover the reader's recipe from the operator's live model — `ollama show --modelfile
      <reader>` — and commit it as `scripts/joycaption.Modelfile`, verifying that `ollama create` from
      the committed file reproduces a model that answers. **The original was never committed and the
      two-`FROM` projector pairing is undocumented; any `TEMPLATE` or `PARAMETER` line it carries is
      load-bearing and recoverable only this way.**
- [x] 1.2 Confirm the reader can see, by `ollama show` listing `vision` under Capabilities **and** a
      projector block, plus one eye-colour question about one photograph whose answer the operator can
      check. **A LLaVA-family model with no projector loads, answers fluently and describes nothing** —
      verify sight before anything is built on it.
- [x] 1.3 **Decide D7.** Send one of the operator's own full-size photographs to `/api/generate` as
      unresized base64 from a throwaway stdlib script, and record the body size, the wall-clock time and
      whether the host accepted it. **If it is rejected or unworkably slow, D7's fallback is taken** —
      PIL as a function-local import with a refusal naming the install — **and that is a dependency
      decision the operator makes and amends `design.md` D7 with, before phase 4 starts.** Verify by
      pasting the real body size, the real timing and the first line of the caption.
- [x] 1.4 Record in `scripts/joycaption.Modelfile`'s header comment, or beside it, the exact
      `ollama create` and `ollama pull` commands for both models, verified by running them from a state
      where neither model exists.

## 2. `flow.py` — the `hosted` block, and the allowlist

`specs/image-generation/spec.md`. `design.md` D2, D12.

- [x] 2.1 Add a frozen `Hosted` value carrying `implementation`, `reader` and `sorter`, and parse the
      optional `hosted` key into `Flow.hosted: Hosted | None`. Verify with a test that a manifest
      declaring the block loads it verbatim and one declaring none yields `None` without a refusal —
      keys `image-generation:hosted:flow-declares-its-hosted-models` and
      `image-generation:hosted:absent-block-means-the-default`.
- [x] 2.2 Refuse any top-level manifest key not in `REQUIRED + ("hosted",)`, naming it, without
      executing the flow. Verify with a test injecting an unrecognised key and one injecting a near-miss
      spelling of `hosted` — keys `image-generation:manifest:unknown-key-is-refused` and
      `image-generation:manifest:misspelled-hosted-block-is-refused`.
- [x] 2.3 Verify `MANIFEST_VERSION` is still `2` and both incumbent `PINNED` digests are unchanged, by
      running `tests/test_flow.py` and showing the immutability tests green — key
      `image-generation:hosted:incumbent-flows-are-unchanged`.

## 3. `boundary/ollama.py` — the transport

`design.md` D1, D4, D9, D10, D11. **No adapter class in this file.**

- [x] 3.1 Add the module with `HOST` as a module constant, a `Transport` Protocol, and a `post` default
      that speaks stdlib `urllib` and nothing else. Verify it imports under
      `python -S -c "import isekai.boundary.ollama"` with site-packages off the path.
- [x] 3.2 Implement the classification of D9 — `HTTPError` **caught before** `URLError`, 404 and an
      unreachable host as refusals naming the fixing command, 5xx and `TimeoutError` as transient,
      unparseable or answerless bodies and `done_reason == "length"` as permanent with `done_reason` in
      the detail. Verify with unit tests per row through an injected transport.
- [x] 3.3 Verify the module imports no name from `boundary/claude_cli.py`, by `git grep claude_cli
      isekai/boundary/ollama.py` returning nothing.

## 4. `OllamaReader` — in `pipeline/caption.py`

`specs/caption/spec.md`. `design.md` D5, D7, D8, D10.

- [x] 4.1 Add `OllamaReader` beside `ClaudeReader` and `FakeReader`, with `implementation = "ollama"`,
      an injectable `transport`, and a `body()` method the way `ClaudeReader.argv()` is a method — so the
      request is assertable without a call. Verify with a test asserting the body carries the
      photograph's base64, `stream: false`, the options of D10, **and no `format` and no schema**.
- [x] 4.2 Verify the reader ignores the `workspace` argument and reads the photograph's bytes itself,
      with a test that passes a workspace the photograph is not inside and still gets a caption.
- [x] 4.3 Verify the refusals with tests through the injected transport: an unreachable host and a 404
      each refuse naming their command **and record no attempt** — assert the error-record directory is
      empty, not merely that a refusal was raised. Keys
      `caption:reachability:unreachable-host-refuses-without-an-attempt`,
      `caption:reachability:absent-model-names-how-to-create-it`.
- [x] 4.4 Verify the artifact records the implementation that ran, with a test asserting the caption's
      `producer.implementation` is `"ollama"` — key
      `caption:selection:the-flow-names-the-implementation`.

## 5. `OllamaSorter` — in `pipeline/sheet.py`

`specs/sheet/spec.md`. `design.md` D1, D10.

- [x] 5.1 Add `OllamaSorter` beside `ClaudeSorter` and `FakeSorter`, sending `format =
      output_shape(schema)`, `think: false`, and `repeat_penalty` with the rest of D10's options. Verify
      with a test asserting the body's `format` **equals** `output_shape(schema)` rather than merely
      resembling it — key `sheet:selection:structure-is-required-of-every-implementation`.
- [x] 5.2 Verify the answer is read from the response body, with a test whose transport returns the
      sixteen fields as the body's answer string and no separate structured field — key
      `sheet:selection:answer-in-the-body-is-read`. **`answers_from()` already does this; the test is
      what stops a later edit from breaking it.**
- [x] 5.3 Verify `done_reason == "length"` is permanent and distinguishable, with a test asserting the
      failure record carries `done_reason` — key `sheet:selection:truncation-is-permanent-and-named`.
- [x] 5.4 Verify the artifact records the implementation that ran, with a test asserting the sheet's
      `producer.implementation` is `"ollama"` — key `sheet:selection:the-flow-names-the-implementation`.
- [x] 5.5 Verify the cascade and the validation are untouched, by a test that an absence clause in the
      sorter's answer produces an empty field and a non-vocabulary tag is refused — reusing the existing
      keys, and showing `shared/vocabulary.py` and `shared/fields.py` unmodified in the diff.

## 6. The registries, and the resolution moved inside the loop

`specs/cli/spec.md`. `design.md` D6.

- [x] 6.1 Add `READERS` and `SORTERS` to `wiring.py`, keyed by the implementation string, and change
      `Wiring.reader` / `Wiring.sorter` to `Callable[[Flow], …] | None`. Verify with a test that an
      unknown implementation refuses **naming the implementations this build carries** — keys
      `caption:selection:unknown-implementation-is-refused`,
      `sheet:selection:unknown-implementation-is-refused`.
- [x] 6.2 Move the resolution inside `cli.py`'s per-flow loop at both sites, leaving `_seam` unchanged.
      Verify with a test that one stage verb given two flows on two implementations writes two artifacts
      each naming its own — key `cli:resolution:one-command-two-implementations`.
- [x] 6.3 Update the five call sites that construct `Wiring` directly — `test_ui.py`, `test_ui_api.py`,
      `test_generate.py`, `test_resume.py`, `test_pipeline_cli.py`. **The two that pass `None` stay
      `None`**, and verify the uncomposed case still refuses by name — key
      `cli:resolution:uncomposed-seam-refuses-by-name`.
- [x] 6.4 Add the test that holds each registry's keys **equal** to the strings the artifacts record, so
      the duplication cannot drift — key `caption:selection:the-flow-names-the-implementation`. Verify
      by changing one string locally and seeing the test go red, then reverting.
- [x] 6.5 Verify nothing is constructed until a flow asks, with a test that composes a wiring, performs
      no stage, and asserts no host was contacted and no binary looked up — key
      `caption:reachability:the-check-fires-at-first-call`.

## 7. `flows/summon-open-v1/` — the directory and the pin

`design.md` D2, D8. **Exactly five files, as every tracked flow is.**

- [x] 7.1 Create the directory with `graph.json` and `schema.json` as **byte-identical copies** of
      `summon-v1`'s, verified by `cmp` on both.
- [x] 7.2 Write `flow.json` as `summon-v1`'s with `"flow"` changed and one `hosted` block added, and
      verify by diffing the two manifests that **those are the only two differences**.
- [x] 7.3 Author `caption.briefing.md`, carrying `summon-v1`'s absence-licence paragraph **verbatim** —
      verify by `grep` that the licence text matches byte for byte — and written for the open reader
      otherwise. **The prototype's measured prompt is not in git; this is authored, not ported.**
- [x] 7.4 Author `sheet.briefing.md` for the open sorter, porting the two worked examples and the rules
      from `summon-v1`'s. Verify the file exists, the flow loads, and the briefing names every one of the
      schema's sixteen fields.
- [x] 7.5 Add the `PINNED` entry to `tests/test_flow.py` and verify the whole-directory digest test is
      green — the designed cost of adding a flow. **Take this only after 7.1–7.4 are final**:
      `test_flow.py:430` asserts `sorted(PINNED) == tracked_flows()`, so the gate is red from the moment
      the directory exists until this lands, and the digest goes stale again if any of the five files is
      edited afterwards. **The directory and its pin belong in one commit.**
- [x] 7.6 Add the assertion that closes the last hole —
      `load_flow("summon-open-v1").hosted.implementation == "ollama"` — and verify it goes red if the
      block is removed locally, then revert. **`design.md` D12 ③: an absent block has no key to refuse.**

## 8. The isolation proof, in the suite

`specs/caption/spec.md`, `design.md` D11. **The whole point is that it cannot pass vacuously.**

- [ ] 8.1 Add a test that runs the open flow's caption and sheet with `claude_cli.spawn` **and**
      `claude_cli.require_binary` monkeypatched to raise `AssertionError("Claude was reached")`. Verify
      it is non-vacuous by pointing the same test at `summon-v1` and seeing it go red, then reverting —
      key `caption:selection:no-path-reaches-another-implementation`.
- [ ] 8.2 Verify no fallback exists on the failure path, with a test where the open reader's transport
      fails permanently and no other implementation is entered — reusing
      `caption:failure:decline-is-permanent`'s no-substitution assertion.

## 9. The documents this version makes false

- [ ] 9.1 `README.md` and `CLAUDE.md`: Ollama named as the third system dependency beside `claude` and
      `node`, with the two `ollama create` / `ollama pull` commands and the `scripts/joycaption.Modelfile`
      path. Verify by following the written instructions on a machine where neither model exists.
- [ ] 9.2 The release notes state the two things this version does **not** check and hands to the
      operator: **read the first caption against the photograph** — the only detector for a reader whose
      projector is missing — and **pass an explicit `--seed`** for any run meant to be compared, because
      each flow otherwise draws its own even at `--count 1`.
- [ ] 9.3 Strike the roadmap's `v0.19` claims this version does not deliver — *"both readers pinned"* and
      `--model`/`--effort` for the Claude arm — naming where each went. Verify by `grep` that no document
      still claims either.
- [ ] 9.4 Correct *"both stdlib over HTTPS"* wherever it appears: it is **HTTP to localhost**, and there
      is no TLS and should not be.

## 10. ⚠️ HUMAN · FREE — the open flow end to end, stopping before the pod

**Free: ①② run on localhost. The operator's own photograph, on his own machine.**

- [ ] 10.1 `caption --flow summon-open-v1 <photo>` and **read the prose against the photograph.** Verify
      the caption describes what is actually there — this is the projector check and the briefing check
      at once, and it is the first time the authored briefing meets the model.
- [ ] 10.2 `sheet --flow summon-open-v1` and verify the sixteen fields are canonical, no absence clause
      survived, and no tag is outside the vocabulary — by `approve` refusing, or not, on its own.
- [ ] 10.3 `review --flow summon-open-v1` through the v0.18 UI and `approve` **unedited**, verifying the
      surface needs no change because it is already flow-aware.
- [ ] 10.4 Re-run all three verbs and verify each reports already-complete and makes no call, which is
      the whole of resume at these stages.
- [ ] 10.5 **Halt and report** before phase 11: the caption, the sheet, what the briefings got wrong, and
      the wall-clock cost of each stage including the cold reload between them.

## 11. ⚠️ HUMAN · METERED · GPU · HALT — the acceptance render

**Do not start this phase on phase 10's success. The operator confirms the spend and says go.**
Ceiling **45 minutes and ~$0.30**.

- [ ] 11.1 `generate --flow summon-open-v1 --seed N --server <tunnel>` and verify a PNG lands under the
      flow's own `outputs/`.
- [ ] 11.2 **The same five verbs again with `claude` absent from `PATH`**, and verify the run completes
      unchanged. **This is the only evidence that no path reaches Claude** — phase 8 proves it offline,
      this proves it in the real invocation.
- [ ] 11.3 Verify every artifact's `producer` names `ollama` and both model names, by `isekai show`, and
      that `pinned` is `false` throughout — which is what this version deliberately does not deliver.
- [ ] 11.4 Report the render, the cost against the ceiling, and **no claim about which arm is better** —
      that is v0.20's, and this version measures nothing.
