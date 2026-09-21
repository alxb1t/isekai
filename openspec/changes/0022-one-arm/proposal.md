---
version: v0.22
---

## Why

**The stack is JoyCaption and WD14, and nothing else decides anything.** Two flows out of three still
reach Anthropic's `claude` CLI to read a photograph, and the manifest key that selects an arm still
names a model — `qwen3:8b` — that no stage has called since v0.21. The repository claims, in its
README banner and in `CLAUDE.md`'s system-dependency list, that it needs a subscription it does not
need for anything the operator actually runs.

**A grilling was run against `main` at `44e5a2d` before this change was cut, and it overturned nine of
the twenty-one decisions the brief had settled.** The four that decide the version:

**① The `hosted` block does not shrink — it goes.** The brief settled that `hosted` collapses to one
live key, `reader`. But `hosted` was a name for *"a model reached over a network to a third party"* as
against *"a socket to this machine"* (`openspec/specs/caption/spec.md:169-172`), and after this change
only the second exists. A block whose name no longer distinguishes anything, holding one key, is what
`CLAUDE.md:208-210` already calls not a declaration. It becomes a **required top-level `model` key**,
and that is what carries `MANIFEST_VERSION` to 3. It also dissolves a decision: the brief wanted a key
allowlist *inside* `hosted` to close the misspelling path, and flattening closes it for free with the
top-level allowlist that already exists at `flow.py:350-357`.

**② The five-phase order cannot be built.** `isekai/interface/wiring.py:176` is the only line in the
package that selects an arm, and it reads `flow.hosted` — the key the flow-and-loader phase deletes,
one phase before the arm is removed. That phase would end with `ty check` red and
`import isekai.__main__` broken. The reverse order fails too: delete the arm first and `summon-v1` and
`conjure-v1`, still tracked and still declaring no block, resolve to a `DEFAULT_IMPLEMENTATION` that no
longer exists — and re-pinning them to fix it is what `tests/test_flow.py:430-438` forbids by design.
**The flow set, the loader and the arm are one phase.** Four phases, not five.

**③ `eyelashes` stays in `conjure-anime-wai`'s schema, and the brief's reason for dropping it was
backwards.** The brief settled the drop on *"a new flow's schema is authored fresh, so it costs
nothing."* Measured, it is the most expensive thing in the version and none of the cost is about Claude
or Qwen. `scripts/derive_field_map.py:628` reads its criterion list from the tracked flows' own
schemas, then unconditionally indexes three criterion-keyed constants into it — so an undeclared
`eyelashes` raises `KeyError` inside `claims()` before the deriver emits anything. Repairing that means
editing `SUFFIXES:98`, `BRIEFING:181` and `PRECEDENCE:361`, regenerating `scripts/field_map.json`,
bumping its `revision` — which the sheet's producer records — and moving two assertions in
`tests/test_field_map.py`. Keeping the field costs nothing at runtime: it is `scored: false`, the
operator fills it by hand, and an empty field is already legal. **The flow-set change is five
artifacts, not seven.**

**④ Two requirements retire that the brief's casualty list does not name, and one scenario goes
unbound.** `caption:refusal:absent-reader-names-the-fix` is not rewritten for the surviving arm — it is
removed, because `boundary/ollama.py` is HTTP to localhost with no binary to be absent, and both of its
real failures already have scenarios under `caption:reachability:*`. And
`caption:selection:no-path-reaches-another-implementation` has exactly two bindings, both in
`tests/test_isolation.py`, which this change deletes whole; nothing in the gate would notice, because
this repository has no spec↔test binding checker.

---

## What Changes

**Three flow directories out, two in.** A flow is never edited, only deleted and created, so this is
one act on five artifacts: three directories, `tests/test_flow.py`'s `PINNED`, and the session fixtures
that name a flow at module scope.

```
  flows/summon-v1/        ──▶ DELETED   the claude arm by absence of a block
  flows/conjure-v1/       ──▶ DELETED   the claude arm by absence of a block
  flows/summon-open-v1/   ──▶ RENAMED   to summon-anime-wai, minus sheet.briefing.md,
                                        graph and schema carried verbatim
  flows/conjure-anime-wai/ ──▶ NEW      conjure-v1's graph and schema unchanged,
                                        minus sheet.briefing.md, caption.briefing.md
                                        a byte-identical copy of summon-anime-wai's
```

**The manifest.** `hosted` is deleted; a required top-level `model` names the one alias two seams run —
`OllamaReader` and `OllamaTagger`, which have shared it since v0.19 (`wiring.py:131-139`).
`MANIFEST_VERSION` 2 → 3. `Hosted` and `REQUIRED_HOSTED` are deleted.

**The arm.** `isekai/boundary/claude_cli.py` is deleted. Five names rehome to `foundation/run.py`:
`CliFailure` (renamed `StageFailure`), `refusal_for` (widened from a `CliFailure` to `(kind, detail)`),
`instructions_record`, `constant_record`. `briefing_text` is inlined at its one caller and deleted;
`ROOT` is deleted, because `foundation/run.py`'s `DATA_ROOT.parent` is the same path and
`wiring.py:237` already spells it.

**The structural rule stops counting.** *"A flow is five flat files"* becomes *a flow is flat, and its
files are the manifest and its siblings* — named rather than tallied, because the count has now changed
once and a spec key carrying a numeral is a key that goes stale. `len(SIBLINGS)` gains the assertion it
has never had.

**The documents.** `claude` and `qwen` leave the source and the live documents; they stay in
`openspec/changes/archive/`, `CHANGELOG.md`'s released sections, git history, `ui/design/`,
`CLAUDE.md`'s filename and the `Co-Authored-By` trailers. The test is *does this sentence claim
something untrue of the running system*, not *does the word appear*.

## Capabilities

### Modified Capabilities

- **`caption`** — two requirements removed (the reader-implementation selection block, and the absent-
  reader remedy), two scenarios narrowed where they assert a property a one-armed system cannot fail,
  and one narrowed to name the **model** a flow reads through rather than the implementation.
- **`cli`** — `cli:resolution:one-command-two-implementations` removed; it is premised on there being
  two, and v0.21 already modified it once.
- **`image-generation`** — the whole `hosted` requirement removed with its four scenarios, replaced by
  a required top-level `model`; the five-flat-files requirement replaced by one that names the files.
- **`tagging`** — the hosted tagger's absence case removed; it is unrepresentable once every tracked
  flow declares a model, and replaced by one asserting it runs the model the flow names.

**`run-directory` needs no delta, and that was checked rather than assumed.** None of its scenarios is
arm-specific: `run-directory:provenance:unpinned-producer-is-declared` says *"a hosted service that
exposes no immutable revision"*, which is still true of Ollama — v0.19 shipped selection and not
pinning, and every artifact this arm writes still records `pinned: false`.

### Unchanged, deliberately

`field-map`, `sheet`, `review`, `ui`, `comfy-transport`, `evaluation`, `model-provisioning`,
`run-directory`. **The tag table, the deriver and the router are not touched** — see ③ above.

## Impact

| | |
|---|---|
| **Source deleted** | `isekai/boundary/claude_cli.py` (291 lines), `tests/test_isolation.py` (140 lines) |
| **Flows** | 3 directories deleted, 2 created, `PINNED` rewritten |
| **Manifest format** | version 2 → 3; `hosted` → required top-level `model` |
| **Spec delta** | **4** capabilities — `caption`, `cli`, `image-generation`, `tagging`; 5 requirements removed, 4 re-added, 2 modified in place |
| **Scenarios retired** | 6 outright, of which `caption:selection:no-path-reaches-another-implementation` would otherwise be left bound to nothing; 7 more renamed onto the model |
| **Tests** | 1 file deleted; ~14 rewritten; ~11 deleted; 6 files re-imported |
| **Metered cost** | **zero on phases 1–3.** Phase 4 is one attended acceptance; v0.21's comparable run was 21m36s and ≈$0.30 |
| **Not touched** | `scripts/field_map.json` (revision stays 3), `scripts/derive_field_map.py`, the tagger, `tests/test_field_map.py` |
