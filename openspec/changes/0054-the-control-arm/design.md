# Design — 0054 the control arm

How the control flow is made and held equal, how an approval crosses flows, how a render reuses another flow's
seeds, and where each is recorded. **Verdict: feasible** — a directory and a test, one flag on `approve`, one on
`generate`, one grammar form in `render.sh`, each held by a test.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut (`04dfe26`):

- **The dials reach one node.** `isekai/pipeline/generate.py:385-390` patches the `identity` role with
  `ip_weight` and `identity_cn_strength`; `flow.py` checks a dial's presence (`:466-473`), never its value.
  `flows/summon-anime-wai/flow.json:26-27` holds `0.9` and `0.8`; `graph.json:174` holds
  `"filename_prefix": "summon-anime-wai"`, which names a file in the pod's memory only.
- **The freeze.** `manifest_digest` (`isekai/foundation/flow.py:516-530`) hashes every file's name and bytes;
  `load_flow` refuses a `"flow"` other than the directory name (`:436-440`). `tests/test_flow.py` — `PINNED`
  (`:36-56`), the digest test (`:531-538`), the changelog-digest test (`:541-566`), `tracked_flows` equality
  (`:569-571`); the fixture `flow` and `_scratch` (`:59-83`). Every enumerating test passes for a copy of `summon`:
  `tagger` true (`:876-880`), the model (`:727-736`), dials equal to the roles' reads (`:405-420`).
- **The approval.** `approve(run, flow, schema, vocabulary)` (`isekai/pipeline/review.py:308-389`) reads the
  draft, validates, computes `edited` through `_differs` (`:425-445`), writes `ReviewApproved`
  (`isekai/foundation/artifacts.py:254-265`: `schema`, `producer: ApprovedProducer` `:160-165`, `flow`, `sheet`,
  `vocabulary`, `fields`, optional `schema_document`, `field_map`) and refuses an existing approval (`:379-386`).
  `generate` reads only `fields`, `producer.edited` and `sheet` (`generate.py:193-197`); nothing reads `flow`
  back. The CLI builds `approve_flow` (`isekai/interface/cli.py:574-580`) per `--flow`.
- **The seeds.** `seeds_for` (`generate.py:116-133`) refuses a count beside explicit seeds and filters seeds
  already rendered; `render` (`:449`) takes `count` and `seeds`; `rendered_seeds` (`:284`) lists a group's seeds
  from filenames; `run_view.rendered(run, flows_dir, flows=…)` (`isekai/interface/run_view.py:175-197`) gives
  `(flow, group, seeds)` per group, groups ascending. The CLI's `--count` and `--seed` are one exclusive group
  (`cli.py:224-239`); `_generate` (`:590-647`) assembles every run through `prepare` before any client, then
  renders with `args.count` and `args.seeds`. `render.sh` accepts `<flow>=<count>` alone (`:27-30`), runs one free
  assemble pass (`:56`), then renders each spec with `--count` (`:139-145`).
- **The crossing rule.** `openspec/specs/run-directory/spec.md:367-412`, *input above, flow below*, with its
  four scenarios; D17 (`docs/decisions.md:225-230`). D15 and D31 close the *Flows* section (`:195-212`).
- **The docs.** `README.md:387` lists `flows/summon-anime-wai/` in the tree; `CLAUDE.md:5-7` says "Two flows";
  `evaluation/README.md` has `## Files` and `## Imported by` (`:15`, `:25`).
- **Tests the change touches:** `tests/test_flow.py` (a new flow fails `tracked_flows` equality until `PINNED`
  gains it, and the gate until a CHANGELOG bullet carries its digest); `tests/test_generate.py:384-400` (the
  parser's exclusive group); `tests/test_review.py` (every `approve(run, FLOW, schema, vocabulary)` call keeps
  its shape); `tests/golden/approved.json` and `render.json` (unchanged: the new keys are optional and absent on
  the old paths).

## Goals / Non-Goals

**Goals:** a third tracked flow equal to `summon` but for two dials; an approval copied across flows with its
origin recorded; a render on another flow's seeds, recorded; the crossing named in the spec and D38; the recipe.

**Non-Goals:** rendering; the evaluator; the skill; pairing beyond the seed; a significance test.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `flows/control-anime-wai/` is `summon`'s files; `flow.json` differs in `flow`, `ip_weight` 0, `identity_cn_strength` 0; a test holds the equality; `PINNED` gains the digest | one graph, two numbers; a byte comparison cannot be argued with | nodes removed from the graph; a control-named `filename_prefix` |
| [D2](#d2) | `approve --from <flow>`: the source's latest approval's fields, validated against the target's schema, written as the target's next approval with `producer.copied_from` | a `cp` carries the wrong identifier; a second review lets the prompts drift | a verb of its own; copying the draft |
| [D3](#d3) | `generate --seeds-from <flow>`: the source's latest group's seeds, from filenames, checked in the free pass; the sidecar records `seeds_from`; `render.sh` takes `<flow>=<flow>` | same noise makes the pair an ablation; the check before the pod costs nothing | `--seed` per run by hand; pairing by a record |
| [D5](#d5) | the target is in step when its latest approval is a copy of the source's latest; otherwise `approve --from` copies again under the next number; `generate --seeds-from` refuses a copy made from another approval than the source's latest renders | a source approved again after the copy left the control on the old sheet and the new seeds, silently | a warning alone; refusing every re-copy |
| [D6](#d6) | `render.sh` defers the pre-pod seeds check for a source an earlier spec renders by count in the same session, and refuses a source spec placed after its dependent | a fresh batch is one command and one boot | two sessions always |
| [D4](#d4) | D38 under *Flows*; `run-directory` MODIFIED with the named-source crossing; the recipe in `evaluation/README.md`; `README.md` and `CLAUDE.md` name the third flow | the crossing is the operator's act, stated once | a new capability for the control |

### D1

**The flow.** `cp -r flows/summon-anime-wai flows/control-anime-wai`, then three edits in `flow.json`: `"flow":
"control-anime-wai"`, `"ip_weight": 0`, `"identity_cn_strength": 0`. `PINNED` gains `"control-anime-wai"` with
`manifest_digest("control-anime-wai")`. The phase's CHANGELOG bullet names that digest in full, as the
changelog-digest test requires of a new flow.

The equality test, in `tests/test_flow.py`, keyed `image-generation:control:files-equal-the-subject` and
`image-generation:control:manifest-differs-only-in-the-face-dials`: for each of `SIBLINGS`, the control's bytes
equal `summon`'s; the two manifests, parsed, equal after popping `flow` and the two dials from each; the control's
two dials are `0`. The pair is a module constant `CONTROLS = {"control-anime-wai": "summon-anime-wai"}`, so a
second control is one line.

### D2

**The copy.** `approve` gains `source: str | None = None`. With a source:

```
approve(run, flow, schema, vocabulary, source=S)
   S's review/ has no approval ──▶ Refusal: "run `python -m isekai approve --flow S <run>` first"
   flow's review/ has an approval ──▶ (None, [])
   read S's latest approval; validate(fields, schema, vocabulary)   ← the target's schema
   write flow/review/<next>.approved.json:
      producer = S's producer + "copied_from": {"flow": S, "approval": <S's version>}
      flow = flow · sheet = S's sheet · vocabulary, fields, schema_document, field_map = S's
```

`ApprovedProducer` gains `copied_from: NotRequired[CopiedFrom]`, `CopiedFrom = TypedDict({"flow": str,
"approval": int})`: a key added under the kind's version, optional to every reader (D32). The CLI adds `--from
FLOW` to `approve` (`dest="source"`), refuses a source among the `--flow` names before any run opens, and passes
it to `approve_flow`. The refusal for a missing source approval is `_unapproved(run, [source])`'s wording.

### D3

**The seeds.** `generate` gains `--seeds-from FLOW` in the exclusive group beside `--count` and `--seed`, so the
parser refuses the pairs. `dispatch` refuses a source among the `--flow` names. In `_generate`, after `prepare`,
`assemble_one` calls `source_seeds(run, source, flows_dir) -> list[int]`: the last group of
`rendered(run, flows_dir, flows=(source,))`, or a `Refusal` naming the run, the source and
`bash infra/render.sh <runs> <source>=1`, collected as `broken` is. The free pass therefore refuses before any
pod. `render_one` passes those seeds as `seeds=` and `seeds_from=source`; `render` writes `"seeds_from": source`
into the sidecar when given. `Render` gains `seeds_from: NotRequired[str]`.

`render.sh`: the spec regex becomes `^[a-z0-9-]+=([1-9][0-9]*|[a-z0-9-]+)$`; in the render loop a numeric value
is `--count`, a name is `--seeds-from`; before `up.sh`, every spec with a name runs one more free pass,
`generate --flow <flow> --seeds-from <name> --runs "$runs" "${ids[@]}"`, so a missing source render refuses
before the pod. The usage comment shows both forms.

### D4

**The records.** `docs/decisions.md`, after D31:

```
### D38 · A control flow is its subject with the face chain at zero

**`control-anime-wai` is `summon-anime-wai`'s directory with `ip_weight` and `identity_cn_strength` at 0, held
equal to it by a test; its approval is copied from `summon`'s and its renders take `summon`'s seeds, each
recording the source. A stage reads another flow only when the operator names it as a source.**

- **Why:** the count's floor is the same sheet and the same noise with the face mechanism off; the comparison
  is sound only while the two differ in exactly that. D17 forbids a flow reaching into another on its own, and
  an operator's named source is not that.
- **Made by:** `0054`.
```

`evaluation/README.md` gains `## The control arm`: the four commands, `approve --flow control-anime-wai --from
summon-anime-wai <run>` for every run, `bash infra/render.sh <runs> control-anime-wai=summon-anime-wai`,
`python -m evaluation <runs> --cohort <cohort>`, `python -m isekai compare <batch>`, and one line: the control
row is the floor, the difference is the face mechanism's share. `README.md:387` gains the control's line in the
tree; `CLAUDE.md:5-7` names the third flow in its paragraph.

### D5

**In step.** What holds after the first four phases (`34feabf`): `_copy_approval`
(`isekai/pipeline/review.py:398`) returns `None` for any approved target (`:417-418`); `source_seeds`
(`isekai/pipeline/generate.py:310`) returns the seeds of the source's latest render group, whose directory name
is the source approval those renders came from; `assemble_one` (`isekai/interface/cli.py:664-669`) stores them.

```
approve --from S, target T
   T has no approval ───────────────────────────────▶ copy as T's next number
   T's latest is a copy of S's latest ──────────────▶ nothing written
   anything else (an older copy, a hand approval) ──▶ copy S's latest as T's next number

generate --seeds-from S, flow T, S's latest render group G
   T's approval has no copied_from naming S ────────▶ no check
   copied_from.approval == G ───────────────────────▶ render
   copied_from.approval <  G ───────────────────────▶ refuse: `approve --flow T --from S <run>`
   copied_from.approval >  G ───────────────────────▶ refuse: render S first, `render.sh <runs> S=1`
```

`_copy_approval` reads the target's latest approval when one exists and returns `None` only when its
`producer.copied_from` equals `{"flow": source, "approval": <source's latest>}`. `source_seeds` returns
`(group, seeds)`, `group` the latest render group's number. `refuse_out_of_step(run, flow, source, group)` in
`generate.py` reads `flow`'s latest approval through `approved_artifact` and raises the refusals drawn, each naming
both approval numbers. `assemble_one` calls it for every flow assembled, inside the same collection as
`source_seeds`, so it refuses in the free pass.

The CLI guard tests at `tests/test_pipeline_cli.py:572` and `:589` bind
`review:copy-from:the-source-is-another-tracked-flow` in place of their exemption.

### D6

**One session.** What holds (`34feabf`): `infra/render.sh` parses each spec into `names`, `modes`, `values`
(`:28-35`), runs the free seeds pass for every `--seeds-from` spec before `up.sh` (`:62-66`), and renders the specs
in order (`:150-154`). With `summon-anime-wai=1 control-anime-wai=summon-anime-wai` the free pass refuses: the
source has no render yet.

After the parse loop, for each `--seeds-from` spec: a spec naming its source with a count *later* in the line is
refused, `'<spec>' comes before its source '<source>=<count>'; put the source first`; one naming its source with a
count *earlier* is marked deferred. The free seeds pass skips a deferred spec; its checks then run at its turn in
the render loop, after the source has rendered. `evaluation/README.md`'s recipe gains the one-session line for a
fresh batch beside the two-step form.

## Dependencies

None.

## Risks / Trade-offs

- **The dials at zero still run InsightFace on the photograph** → the cohort's photographs all hold a face; a
  faceless one refuses `summon` the same way. The first control render is checked by eye for a face unlike the
  photograph.
- **`render.sh`'s grammar is held by `bash -n` and review, not a test** → the Python side it calls is tested;
  the script's own tests read it for teardown and ceiling only.
- **The CHANGELOG bullet must carry the digest or the gate is red at the end of the flow phase** → stated in
  [D1](#d1); the gate names the flow.
- **A deferred seeds check refuses on a paid pod** → only when the source's own render failed in that session,
  which the log already shows; the control's renders are skipped, nothing else is lost.
- **`refuse_out_of_step` checks only a copy naming the source** → a flow rendered on another's seeds under its own
  hand approval is a different experiment, and is not refused.
- **A copied approval names a sheet version under another flow** → `sheet` is provenance only; `copied_from`
  says where to look.

## Verdict

**feasible** — a directory, two flags, one grammar form, each with its test and its record.
