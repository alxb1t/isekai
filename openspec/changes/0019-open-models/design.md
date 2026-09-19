# 0019 · open models — design

**Verdict: `feasible-with-caveats`.** Three caveats, each named at its decision and carried into
`tasks.md` as a build-time check rather than an assumption: the photograph's request body is larger than
anything the prototype sent (D7), the reader's `ollama create` recipe has to be recovered from the
operator's live machine because it was never committed (D3), and the caption briefing is **authored
rather than ported** because the prompt that produced the measured captions is gitignored (D8).

**This design was settled by grilling against bodies, not against the record.** Roughly thirty assertions
about `main` were checked and **eleven did not survive** — including the key name this change was
originally going to use. Where a decision below overturns an earlier position, it says so and why.

See `proposal.md` — Why, for motivation. See `specs/` for the requirements.

---

## Context

```
  dependencies = []                     pyproject.toml:5, held by tests/test_pipeline_cli.py:82-98:
                                        `python -S -c "import isekai.__main__"` with site-packages
                                        off sys.path, PLUS a falsification test proving -S refuses
  ▶ the pipeline CANNOT load a model in-process. A socket or nothing.

  Reader / Sorter                       Protocols in pipeline/caption.py:74 and pipeline/sheet.py
  ClaudeReader / ClaudeSorter           the adapters, in the SAME files -- not in boundary/
  boundary/claude_cli.py                the TRANSPORT beneath them. There is no `argv` in it
  Reading / Sorting                     already carry implementation, models, pinned: bool = False
  output_shape(schema)   sheet.py:136   already emits the JSON Schema Ollama's `format` takes
  answers_from(...)      sheet.py:193   already falls back to json.loads(text)
  fill() -> map_phrase() sheet.py:82    canonicalises EVERY sorter's answers. Reader-agnostic
  tracked_flows()        flow.py:271    discovers flows by directory listing. No registry to edit
  REQUIRED               flow.py:63     eight keys, and `models` is one of them
  manifest_digest        flow.py:363    every regular file in the flow directory
```

Two facts from that list shape almost everything below. **`models` is already a required key** holding
twelve `{dest, sha256}` ComfyUI render weights, so the manifest addition needs a different name (D2).
**Both Claude adapters are pipeline modules**, so the open ones go beside them and the transport goes
beneath (D5).

## Goals / Non-Goals

**Goals:**

- One new flow runs `caption → sheet → review → approve → generate` on JoyCaption and Qwen3-8B and
  produces a PNG.
- **No code path from that flow reaches Claude**, proved behaviourally rather than argued structurally.
- **Nothing in the closed arm moves.** Both incumbent manifests and their committed digests are
  byte-identical; `claude_cli.py`, `run.py`, `review.py`, `generate.py` and `shared/*` are untouched.
- No runtime dependency is added.

**Non-Goals, at the design level:**

- **Provisioning, verification and pinning.** The manifest names models and checks no bytes.
- **Any claim about which arm is better.** No comparison is run; this change measures nothing.
- **Generality for a third implementation.** The registry's argument is the refusal, not extensibility —
  `modules/README.md`'s rule against anticipating a caller nobody has applies here as everywhere.
- **Renaming `CliFailure`.** See D13.

## Decisions

### D1 · The adapter is written against `/api/generate`, not the OpenAI-compatible endpoint

**This overturns the pre-grilling position.** The compatible endpoint was preferred for
provider-neutrality, before anyone checked what it cannot express.

```
  /api/generate        {model, prompt, images:[<b64>], format:<schema>, stream:false,
                        think:false, options:{temperature, seed, num_predict, repeat_penalty}}
                       THE MEASURED PATH -- both prototype call sites, stdlib urllib

  /v1/chat/completions messages[].content[].image_url.url = "data:image/jpeg;base64,..."
                       response_format:{type:"json_schema"} · max_tokens · seed · temperature
                       think  ABSENT       repeat_penalty  ABSENT
```

**Both missing fields are load-bearing by measurement, not by preference:**

| | what happened without it |
|---|---|
| `think: false` | Qwen3 is a hybrid reasoner and its thinking tokens come out of the answer's budget — **they truncated the JSON mid-string on the third subject** |
| `repeat_penalty: 1.15` | one field emitted `"white robe"` **forty times** until the output budget ran out. At temperature 0 there is no sampling noise to break a loop |

**Alternative considered — the compatible endpoint with the losses absorbed.** Rejected: it converts a
port into a re-measurement, and the two things being re-measured are the two known failure modes of the
model this change is adopting. **Alternative considered — a router in front of both.** Rejected on four
counts recorded in the design notes, the load-bearing one being that its headline feature is fallback,
which `caption.py`'s standing rule forbids outright.

**What is given up, named:** swapping Ollama for another runtime means writing another adapter rather than
repointing a URL. Accepted — one adapter per runtime is what the registry already assumes, and no such
runtime is scheduled.

### D2 · The manifest key is `hosted`, because `models` is taken

```
  models:   [ {dest: "annotator_ckpts/.../yolox_l.onnx", sha256: "7860ae..."}, x12 ]
            REQUIRED on every flow · what a rented GPU loads · pinned by digest

  hosted:   {implementation: "ollama", reader: "<name>", sorter: "<name>"}
            OPTIONAL · what stages (1) and (2) call · no digest in this version
```

`flow.py:63` makes `models` required and `flow.py:186` parses it into `tuple[Model, ...]`. The original
proposal would have collided with it.

**The name splits the manifest along a boundary the architecture already draws** — the hosted-model tier
is *"an API **or a local runtime**, per call"*. `open` was rejected: it names the arm rather than the
thing, and a later local runtime is equally open. `reader`/`sorter` as two separate keys was rejected
because one key makes *"this flow is wholly one implementation"* a property of the document rather than of
two lookups that happen to agree.

**Optional, so `MANIFEST_VERSION` stays `2`.** Required keys plus a version bump was this change's first
shape and it was wrong: it forced an edit to two frozen directories in a change whose whole point is to
add one and touch nothing.

> **The accepted asymmetry, stated so it is not discovered later.** `models` pairs every name with a
> digest. `hosted` pairs neither with one. In the same document, that reads as an omission — and it is a
> deferral, recorded as one.

### D3 · Literal model names in the flow; the `ollama create` recipe is committed to `scripts/`

**The two names are not the same kind of name**, which is why nothing indirects them:

| | what it is | how it comes to exist |
|---|---|---|
| the reader's name | **a machine-local alias** | `ollama create` from a **two-`FROM` Modelfile** pairing the quantised weights with the vision projector |
| the sorter's name | **a public registry tag** | one `ollama pull` |

A lookup table would be exactly as machine-local as the alias it hid, and `isekai provision` already owns
this problem properly. **What makes the name mean something is the recipe**, so the recipe is committed —
`scripts/joycaption.Modelfile`, beside `models.json` and `download_models.sh`, which is where provisioning
artifacts already live. **The release notes state the one command.**

**It does not go in the flow directory**, though the freeze semantics would be right there:
`tests/test_flow.py:171` asserts every tracked flow's directory is **exactly** its manifest plus four
siblings, and `manifest_digest` covers every regular file. A sixth file means modifying a structural
requirement and its test to house a file nothing reads. **Not worth it in this change.**

> ⚠ **Build-time recovery, unavoidable.** `models/` is gitignored and the original Modelfile was never
> committed. The two-`FROM` projector pairing is **undocumented in Ollama's own import and modelfile
> docs**, and any `TEMPLATE`, `SYSTEM` or `PARAMETER` line it carried is recorded nowhere. Since the
> prototype sent no system message and relied on the model's own chat template, **whatever that template
> was is load-bearing.** The committed file is reconstructed from the operator's live model — `ollama
> show --modelfile` — not from the repository.

### D4 · `HOST` is a module constant. No flag, no environment variable

```python
# boundary/ollama.py
HOST = "http://127.0.0.1:11434"
```

1. **The runtime reads no environment variables at all** — one `os.environ` hit repository-wide and it is
   in a test. An env-var default would be the first of its kind on this path.
2. **A module constant is the house precedent for a fixed local address** —
   `interface/ui/__init__.py:31` and `interface/cli.py:75`. **`--server`'s deliberate no-default exists
   because rendering costs money**; a free loopback call does not inherit that reason.
3. **It is what makes this change have no security surface.** A flag or an environment variable makes the
   photograph's destination operator-controlled, which is `_check_run_root`'s concern pointed outward.
   **The version that makes the address configurable owns that guard.** This one cannot express an address
   at all, and that is the point.

### D5 · The transport goes in `boundary/`; the adapters go beside their twins in `pipeline/`

**The pre-grilling put `OllamaReader` in `boundary/ollama.py`. Its twin is not there.**

```
  boundary/claude_cli.py    BINARY BASE_FLAGS Runner spawn require_binary invoke Envelope
                            CliFailure classify classify_text detail models_that_ran
                            briefing_text refusal_for instructions_record
                            ...the TRANSPORT. No `argv` -- there never was one.

  pipeline/caption.py:105   ClaudeReader   argv() at :116   --tools Read --add-dir
  pipeline/sheet.py :159    ClaudeSorter   argv() at :170   --tools "" --json-schema

  SO:
  boundary/ollama.py        NEW. HOST · post · Transport · the classification. Transport only.
  pipeline/caption.py       + OllamaReader    three Reader implementations, one file
  pipeline/sheet.py         + OllamaSorter    three Sorter implementations, one file
```

Two implementations of one Protocol in two different layers is what this avoids. The Protocol, its
offline double and its adapters live together, which is already why `FakeReader` sits in production code
rather than in `tests/`.

**And it retargets the isolation law onto the edge that exists.** *"`boundary/ollama.py` must not import
`boundary/claude_cli.py`"* names an edge that would never have existed. **The edge that exists is
`pipeline/caption.py:30-40` — nine names — and every flow traverses it.** So the law is about the **call
graph**: `OllamaReader.read` and `OllamaSorter.sort` reach no name from `claude_cli`. D11 is how that is
proved.

### D6 · `Wiring.reader` becomes `Callable[[Flow], Reader] | None`, resolved inside the flow loop

**The resolution is currently hoisted above the loop** (`cli.py:363`), so one invocation naming flows on
both arms would resolve one reader and hand it to both.

```python
  wiring.py    reader: Callable[[Flow], Reader] | None    # the shape `vocabulary` already has, :59
               sorter: Callable[[Flow], Sorter] | None
               READERS: Mapping[str, Callable[[Hosted | None], Reader]]
               SORTERS: Mapping[str, Callable[[Hosted | None], Sorter]]

  cli.py       for name, flow in flows.items():
                   reader = _seam(wired.reader, "reader", "reads the photograph")(flow)
```

**`| None` is not decoration.** `isekai ui` composes a wiring with no reader at all — `_seam`'s own docstring (`cli.py:322`): *"a front end that serves stage (3) alone reaches no hosted model and would otherwise fabricate
doubles it never calls."* **`_seam` is unchanged; only the call site moves.**

**Alternative considered — keep `Wiring.reader` a value and have `wiring()` read `args.flow`.** Rejected:
it duplicates `_flows_for`'s loading inside the composition root and breaks outright on two flows.

**Registry over a two-branch conditional**, and the argument is the refusal: a conditional gives an
unrecognised implementation the default one, producing a working run on the wrong models with the
artifact's provenance disagreeing with the manifest. A table makes that a refusal by construction, in the
house style `load_flow` already uses. **A test holds the registry's keys equal to the strings
`Reading.implementation` records** — the pattern `Model`'s own docstring establishes.

### D7 · The photograph is sent as its own bytes, base64, unresized

**The prototype's encoder cannot be ported.** It imports PIL to downscale to a 1024 long side and
re-encode JPEG q92; Pillow is in the `eval` extra, the adapter is reachable from `isekai.__main__`, and
`shared/image.py` reads headers and decodes no pixels.

**So `base64.b64encode(photo.read_bytes())`.** The operator's requirement — **no quality lost** — holds by
construction: nothing is resampled, and the vision tower encodes at patch14-384 regardless of what it is
handed.

> ⚠ **The caveat behind the verdict.** The prototype's photographs ran 21–28 MB, so the worst case is a
> ~37 MB POST. **Untested — the prototype always downscaled first.** If a real photograph is rejected or
> the request is unworkably slow, **PIL moves in as a function-local import inside the adapter's method**,
> which is the pattern `cli.py:236-245` already documents for the UI and which the `-S` guard does not
> see, carrying a refusal that names the install. **In `tasks.md` as a contingency with an explicit check,
> not built speculatively.**

### D8 · The open caption briefing licenses absence, and is authored rather than ported

**The premise that the two arms disagreed about absence does not survive.** The prototype string that
forbids absence is JoyCaption's own stock *Straightforward* mode, quoted verbatim from its README — **and
it is not the mode that fed the router.** The measured captions came from *Descriptive*, whose entire
prompt is *"Write a long detailed description for this image."* — silent on absence.

**And on this branch absence dies in code, not in a briefing:** `shared/vocabulary.py:57`'s regex →
`:137`'s predicate → `:301`, at the **head** of `map_phrase()`, before every mapping pass. One production
caller — `sheet.py:82` inside `fill()` — which runs on every sorter's answers. **Reader-agnostic and
already shipped**, which is why stage ② changes least of anything here.

**So the open briefing carries the incumbent's licence paragraph verbatim.** Licensing absence is what
stopped a reader confabulating nineteen identity marks across seven of ten subjects and dropping its score
from 0.518 to 0.307.

> ⚠ **The second caveat behind the verdict.** The prompt that produced the measured captions is
> **gitignored and not on the branch**, and carried an identity-coverage block no committed constant
> holds. **The briefing is authored, not ported** — and the instruction load is heavier than what was
> measured: 44 lines of structured prose where the winning prototype prompt was one sentence.
> **Instruction-following on an 8B fine-tune is the untested variable of this change**, and the release
> notes must say the operator reads the first caption against the photograph — which is also the only
> detector for a reader whose vision projector is missing.

### D9 · Failure classification, and a missing model refuses rather than spending an attempt

```
  HTTPError 404      model not created / not pulled   ▶ REFUSAL, no attempt
  URLError           nothing listening on the port    ▶ REFUSAL, no attempt
  HTTPError 5xx      load failure, eviction           ▶ transient
  TimeoutError       the ceiling hit                  ▶ transient
  body not JSON · no answer field                     ▶ permanent
  done_reason == "length"                             ▶ permanent, and the record says so
  the answer is not the schema's fields               ▶ permanent   answers_from() already
```

**A retry budget counts models tried and failed; neither of the first two is that.** Both are the
operator's one-command fix, and spending an attempt leaves a run whose error records must be deleted by
hand before it resumes — the same reasoning `require_binary()` already embodies for a missing binary.

⚠ **Catch `HTTPError` before `URLError` — it is a subclass.** The prototype has one handler and mislabels
every 5xx as *"did not answer"*. **Porting the body verbatim is not porting the handler verbatim.**

**Read `done_reason` into the detail.** It is the host's own answer to *truncated or malformed*, and
without it the two are indistinguishable while only one is fixed by raising the output budget.

### D10 · One timeout — 900 s — for both stages; output budgets port verbatim

```
  timeout       900     BOTH stages          (the prototype used 300 and 900)
  num_predict  1024     (1) the caption
               2048     (2) the sheet
  temperature 0 · seed 1 · repeat_penalty 1.15 at (2)
```

**Why one number.** The prototype ran many reader calls in a row, so only the first was a cold load. This
pipeline alternates `caption` → `sheet`, and **the two models do not co-reside in 16 GiB** — so every
stage transition evicts the other and the next call is cold. A timeout is a ceiling on a hang, not a
budget; two of them is a knob with no measurement behind it.

### D11 · An injectable `Transport`, and an isolation test that cannot pass vacuously

The suite has **no HTTP server, no bound socket, and never imports `unittest.mock`**. Doubles are
hand-written frozen dataclasses. The precedent is one line away — `ClaudeReader.runner: Runner = spawn`,
which is what makes `argv()` assertable.

```python
class Transport(Protocol):  # boundary/ollama.py
    def __call__(self, path: str, body: bytes) -> tuple[int, bytes]: ...


# OllamaReader(transport: Transport = post)
```

**This makes the request body itself the thing asserted** — that ① carries the image and **no schema**,
that ② carries `format` and `think: false`.

> ⚠ **The isolation test, corrected.** The obvious form — monkeypatch `shutil.which` to `None`, as
> `tests/test_caption.py:408` does — **passes vacuously here.** It only fires if `require_binary` is
> called, so a run that touches no Claude path is green *for the wrong reason*, which is precisely the
> thing being tested for.
>
> **Instead: monkeypatch `claude_cli.spawn` and `claude_cli.require_binary` to raise
> `AssertionError("Claude was reached")`, and run the open flow through it.** Non-vacuous, offline, and
> **strictly stronger than the PATH removal it stands in for.** The operator's `claude`-off-`PATH` run
> remains the acceptance evidence; this is its CI-resident twin.

### D12 · The strict key allowlist, and the one hole it does not close

`load_flow` currently checks for **missing** keys only; an extra top-level key is silently ignored. The
allowlist becomes `REQUIRED + ("hosted",)`, and any other key is a refusal naming it.

```
  (1) hosted.implementation = "vllm"   wrong VALUE  ▶ REFUSAL   the registry has no entry     D6
  (2) `hostd:` · `Hosted:` · a typo    wrong KEY    ▶ REFUSAL   the allowlist                 D12
  (3) the block ABSENT ENTIRELY        ⚠ no key to refuse  ▶ would run the DEFAULT, silently
  (4) ollama down · 404 · 5xx          failed call  ▶ REFUSAL / ModelFailure                  D9
  (5) the registry picking wrong                    ▶ a test holds its keys == the artifact's D11
```

**③ is real and the allowlist cannot close it**, because *absent means the default* is deliberate — it is
what keeps both incumbent manifests unedited. `manifest_digest` freezes the bytes once committed, but the
first commit is exactly where this mistake lives and a digest cannot tell a correct manifest from a wrong
one. **It costs one assertion, and it is the last hole:**

```python
assert load_flow("summon-open-v1").hosted.implementation == "ollama"
```

### D13 · What is deliberately not here, and the one item removed after it was settled

Twelve deferrals, each held to one test — **does it block running the open flow end to end?** None does.
Provisioning · digest verification · `pinned: true` · the blind-model check · the CWD-relative models root
· Claude's `--model`/`--effort` · seed matching across flows · decline detection at ② · the licence read ·
the comparison campaign · a second open flow · briefing tuning.

**And one was removed from this change after being settled**, by applying that same test to it:

> **The `CliFailure` → `ModelFailure` rename is deferred.** It was argued as *forced* by the isolation
> law, on the grounds that an open adapter raising it would name a Claude module. **Under D5 the open
> adapter lives in `pipeline/caption.py`, which already imports `claude_cli` for `ClaudeReader`** — so the
> import edge exists either way and the rename buys a **name**, not a behaviour. No Claude code executes
> regardless, and D11 proves that independently of what the exception is called.
>
> **Deferring keeps `claude_cli.py`, `foundation/run.py`, both offline doubles and two test files
> completely untouched** — a phase of pure refactor, ~60 lines, zero new behaviour. **The type stays
> misnamed**, and it travels with the provisioning work, which opens that file anyway.

## Risks / Trade-offs

| risk | mitigation |
|---|---|
| **A ~37 MB request body is rejected or unworkably slow** — never tested, because the prototype always downscaled | D7's contingency: PIL as a **function-local** import, which the `-S` guard does not see, plus a refusal naming the install. A `tasks.md` check on a real photograph before anything downstream is built |
| **The reader's Modelfile `TEMPLATE` is lost**, and the model relies on its own chat template | Recovered at build time with `ollama show --modelfile` against the operator's live model, and committed. **A build-time discovery, not a design unknown** |
| **The reader's vision projector may be absent and the failure is silent** — it loads, answers fluently and describes nothing; two of three published repositories ship none | Not detected in this change. **The operator reads the first caption against the photograph**, and the release notes must say so — an undocumented check is an assumption |
| **An authored briefing on an 8B model may follow instructions worse than the one-sentence prompt that was measured** | Accepted and out of scope. ③ is the only stage that absorbs a reader regression, and the review UI shipped the version before this one |
| **A malformed `hosted` block silently running the default implementation** | Three mechanisms, and D12 names which closes which. The residual — an entirely absent block — is closed by one assertion on the shipped flow |
| **The flow declares a model name and nothing checks the bytes behind it** | Accepted. The pipeline trusts the operator's own machine, which is the trust `models/` already runs on. Verification travels with provisioning |
| **`conjure-v1` has no open twin**, so a second briefing is never written against these models | Accepted. One open flow proves the registry, the adapter, the isolation, the manifest key and the freeze; the second would prove only that a second briefing can be written |

## Migration Plan

**Nothing to migrate.** No artifact shape changes, no manifest is rewritten, no run directory is
restructured, and both incumbent flows keep their committed digests. A clone that never declares a
`hosted` block behaves exactly as it does today.

**Rollback is deleting one directory and one module.** The only edits outside new files are additive: two
registries and a type change in `wiring.py`, a parsed key and an allowlist in `flow.py`, a moved call site
in `cli.py`, one adapter class each in `caption.py` and `sheet.py`.

**A new system dependency, and it refuses rather than assuming.** Ollama is the repository's third, after
`claude` and `node`. The operator installs it and creates both models by hand; an unreachable host or an
absent model is a refusal naming the command (D9), which is the posture `require_binary()` already sets.

## Open Questions

**None that affect the specs, the approach or the task breakdown.** The three build-time discoveries — the
recovered Modelfile (D3), whether the unresized body is accepted (D7), and whether the host exposes a
capability field that would catch a missing projector for about five lines — are checks inside phases, and
each has its fallback written down. *Taking the capability check if it turns out to exist is cheaper than
scheduling it; it is not planned for.*
