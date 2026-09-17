# Tasks — 0017 conjure

## Progress

- [ ] 1 — The one repair: the registry's contents stop being hard-coded
- [ ] 2 — `flows/conjure-v1/` — five files and the pin
- [ ] 3 — The verdict, measured rather than asserted
- [ ] 4 — ⚠️ **GPU · HALT** — the acceptance run

## The per-phase ritual

Every phase, without exception:

1. **There is no test-first step in this change, and that is the point.** It adds no logic: phase 1 edits
   one assertion, phase 2 writes five data files. Do not go looking for a unit to write first.
2. **Run each sub-task's stated verification — run it, never summarize it.** Paste real output.
3. **Gate green before the commit** — `make gate`, the five commands in `.minions/minions.toml`'s `gate`
   array, in order. **Never weaken the gate to pass**; halt and say so.
4. A `CHANGELOG.md` entry under `## [Unreleased]`, appended in that phase's own commit.
5. The phase's box ticked in `## Progress` above, in that phase's own commit.
6. **One commit per phase**, staged **by name**, carrying `Change: 0017-conjure` contiguous with the
   `Co-Authored-By:` line.

> **Every phase ends on a green gate, including the boundaries.** Phase 1 is one line and is green alone.
> Phase 2 writes the directory **and** its `PINNED` entry in the same phase, because a flow directory that
> exists without a pin fails `test_every_tracked_flow_is_pinned_at_all` — **there is no green state
> between those two edits, so they are one phase and one commit.** Stated here so it is not discovered.

> **This change's own subject is its diff**, so phase 3 records `git diff --stat` output into `design.md`
> rather than asserting anything. That is **recording a measurement, not revising a decision** — nothing
> in `design.md`'s `## Decisions` is reopened.

## The publisher's recommended configuration

**Read before phase 2, and do not re-derive it.** WAI-Illustrious-SDXL's own *"How to achieve optimal
results"*, at `https://illustriousxl.org/wai-illustrious-sdxl`. **Verbatim**, so a later reader can tell
what the publisher said from what this project measured:

| | the publisher | `conjure-v1` ships | standing |
|---|---|---|---|
| sampler | *"Euler a or K_EULER_ANCESTRAL"* | `euler_ancestral` | **exact** |
| steps | *"20-30"* | `28` | inside |
| CFG | *"between 5 and 7"* | `5` | inside, **at the floor** — and measured there on this graph |
| positive prefix | *"masterpiece, best quality, amazing quality, newest"* | the same string | **exact** |
| prompt form | *"List concepts using comma-separated tags"* | comma-joined Danbooru tags | **exact** |
| upscaler | *"R-ESRGAN 4x+ Anime6B"* | the same | **exact** |
| upscaler steps | *"20 steps"* | `20` | **exact** |
| hires denoise | *"0.35~0.5"* | `0.35` | inside, **at the floor** — see the note below |
| resolution | *"native 1536x1536 high-resolution"* | hires lands at 1536 on the long side | consistent |

**Three values the publisher does NOT specify, and each is inference rather than recommendation:**

- **clip skip `-2`** — **the weakest provenance in the manifest.** It rests on *every published WAI v17
  sample generating there, and none of its prose saying so.* Nothing on the publisher's page mentions
  clip skip. Keep it, because it is what every reference image was produced under and changing it makes
  this flow incomparable to `summon-v1` — but do not describe it as the publisher's.
- **scheduler `normal`** — unstated by the publisher.
- **VAE and base resolution** — the VAE comes from the checkpoint (graph node `1`, slot 2); the base
  resolution comes from the run's photograph header, not from a dial.

> **`hires_denoise` ships at 0.35 — the only value proved on this graph — and its reason is NARROWER
> than `summon`'s, which must be written into the manifest's comment rather than assumed.** F39 moved `A` from 0.50 to 0.35 on the grounds that
> *"0.50 wins one axis by 0.014 and loses three"* — the three being linework, **face identification** and
> **pose**. **`conjure` has no identity claim and no OpenPose**, so two of those three columns do not
> apply to it and the tally is **1–1**, not 3–1. It still ships 0.35 because that is the value the
> sheet-only flow was directly measured at, gaining **+0.025 posterisation and +47% linework** over the
> same flow without hires. **The value is right; the argument is smaller.** F39's own sentence is the
> rule — *a settled value is settled against the axes that existed when it was set* — and for a flow it
> becomes **the axes the flow has.** **And the direction differs between the flows**: for `A`, 0.35
> *lost* posterisation; for the sheet-only flow it *gained*.
>
> **Do not "try 0.50" during the build.** There is no dial override — the CLI has no dial flags and
> `build_graph` patches from `flow.dials` alone — so a different denoise is a different digest and
> therefore **`conjure-v2`**, which the append-only registry keeps forever. 0.50 is deferred with a
> trigger, and its delta can be settled later **with no pod**: six sheet-only renders at 0.50 already
> exist on disk, seed-matched against six without hires, and have never been scored.

---

---

## 1. The one repair: the registry's contents stop being hard-coded

**This phase is green on its own and touches no flow.** It lands first deliberately: the defect is
independent of `conjure-v1`, and isolating it in its own commit is what makes the change's verdict
legible in `git log`.

- [ ] 1.1 In `tests/test_flow.py`, `test_every_tracked_flow_parses` opens with
      `assert tracked_flows() == ["summon-v1"]`. That line is a vacuity guard wearing a registry
      assertion's clothes — it exists so the loop below it cannot pass empty. **Replace it with
      `assert tracked_flows()`**, which keeps the guard and drops the assumption. Change nothing else in
      the function. Verify:
      `uv run pytest tests/test_flow.py -q` exits 0, and
      `grep -n 'tracked_flows() == \[' tests/test_flow.py; test $? -eq 1` exits 0 — no list literal
      naming a flow survives.
- [ ] 1.2 Full gate green. Verify: `make gate` exits 0.

## 2. `flows/conjure-v1/` — five files and the pin

**Read `## The publisher's recommended configuration` above before writing `flow.json`.**

- [ ] 2.1 Create `flows/conjure-v1/graph.json` from `flows/summon-v1/graph.json` by deleting nodes
      `2`, `5`, `6`, `7`, `8`, `16`, `17`, `18`, `22`; repointing `10` and `34`'s `model` to `["1", 0]`,
      `positive` to `["3", 0]` and `negative` to `["4", 0]`; and setting `12`'s `filename_prefix` to
      `conjure-v1`. Verify — this one command checks the count, every edge and the prefix at once:
      ```
      uv run python -c "
      import json; g=json.load(open('flows/conjure-v1/graph.json'))
      dangling=[(n,k,v) for n,d in g.items() for k,v in d['inputs'].items()
                if isinstance(v,list) and v and v[0] not in g]
      print('nodes:',len(g)); print('dangling:',dangling)
      print('prefix:',g['12']['inputs']['filename_prefix'])
      assert len(g)==14 and not dangling and g['12']['inputs']['filename_prefix']=='conjure-v1'"
      ```
- [ ] 2.2 Create `flows/conjure-v1/flow.json`: the eight required keys, `flow: "conjure-v1"`,
      `manifest_version: 2`, `inputs: ["sheet"]`, **no `photo` key in `nodes`**, the seven surviving
      roles, the vocabulary pin copied unchanged, **two** models (the base checkpoint and the upscaler)
      with their digests copied from `summon-v1`, and dials minus `ip_weight`, `identity_cn_strength`
      and `openpose_strength`. **Add no key the eight do not include** — `load_flow` tolerates extras
      and the record does not: a declaration nothing reads is one that goes stale and then lies.
      Verify:
      ```
      uv run python -c "
      from isekai.foundation.flow import load_flow
      f=load_flow('conjure-v1')
      print('inputs:',f.inputs); print('roles:',sorted(f.nodes))
      print('models:',[m.dest for m in f.models]); print('dials:',sorted(f.dials))
      assert list(f.inputs)==['sheet'] and 'photo' not in f.nodes and len(f.models)==2"
      ```
- [ ] 2.3 Create `flows/conjure-v1/schema.json`: `summon-v1`'s sixteen fields in order, plus `bangs`
      (suffix `bangs`) after `hair_silhouette`; `eyelashes` (suffix `eyelashes`) after `eyebrows`; and
      `nose` (suffix `nose`), `lips` (suffix `lips`), `facial_hair` (suffix `null`) before `marks`. All
      five `scored: false`; `name` stays `"identity"`. Verify:
      ```
      uv run python -c "
      from isekai.foundation.flow import load_flow
      c,s=load_flow('conjure-v1').schema,load_flow('summon-v1').schema
      new=[f.name for f in c.fields if f.name not in {x.name for x in s.fields}]
      print('fields:',len(c.fields)); print('added:',new); print('scored:',c.scored)
      assert len(c.fields)==21 and c.scored==s.scored
      assert sorted(new)==['bangs','eyelashes','facial_hair','lips','nose']"
      ```
- [ ] 2.4 Create `flows/conjure-v1/caption.briefing.md` from `summon-v1`'s: richer on the face, **naming
      all 21 attributes** including the three `summon` omits (skin ancestry, eyebrows, marks); inference
      licensed for **expression and the scene's light only**; *"do not interpret"* kept and scoped to
      marks, hair, eyes, skin and build; the absence licence kept **verbatim**; gaze kept surface.
      Verify — **this checks the clauses are PRESENT, not that they are good**; the quality judgement is
      task 4.4, where a human is already reading renders:
      ```
      uv run python -c "
      import pathlib,re
      b=pathlib.Path('flows/conjure-v1/caption.briefing.md').read_text().lower()
      need=['eyebrow','skin','mark','expression','light','do not interpret','not visible']
      missing=[w for w in need if w not in b]
      print('missing clauses:',missing); assert not missing"
      ```
- [ ] 2.5 Create `flows/conjure-v1/sheet.briefing.md` from `summon-v1`'s, adding the five new fields to
      `## The fields` **and to both worked examples**. Verify:
      ```
      uv run python -c "
      import json,pathlib
      names=[f['name'] for f in json.load(open('flows/conjure-v1/schema.json'))['fields']]
      b=pathlib.Path('flows/conjure-v1/sheet.briefing.md').read_text()
      missing=[n for n in names if b.count(n)<3]
      print('fields:',len(names)); print('appearing fewer than 3 times:',missing)
      assert not missing"
      ```
- [ ] 2.6 ⚠️ **ABORT CHECK — this is the one task that can change the version's verdict.** For each new
      field, map an English phrase a reader would actually write and confirm it reaches a canonical tag
      through the suffix or containment pass alone. **If any returns `[]` and would need a `CURATED`
      entry, HALT** — `CURATED` (`isekai/shared/vocabulary.py`) is a module constant shared by every
      flow, so that is a code change and `design.md`'s verdict must be rewritten before building on.
      Verify:
      ```
      uv run python -c "
      from isekai.shared.vocabulary import load, map_phrase
      v=load()
      cases=[('thick','lips'),('long','nose'),('blunt','bangs'),('long','eyelashes'),
             ('a short beard',None)]
      out={p:map_phrase(p,v,s) for p,s in cases}
      for k,r in out.items(): print(k,'->',r)
      assert all(out.values()), 'a field needs a CURATED span -- HALT'"
      ```
      **All five were dry-run at the grilling and every one mapped** — `thick`+`lips` → `thick lips`,
      `long`+`nose` → `long nose`, `blunt`+`bangs` → `blunt bangs`, `long`+`eyelashes` →
      `long eyelashes`, `a short beard` → `beard` by containment. **Run it anyway**: the phrases the
      briefing actually elicits may differ from these, and this is the task that can change the verdict.
- [ ] 2.7 Write the dial provenance table into `design.md` under a new `## Dial provenance` heading:
      each dial, what the publisher's page says, and its standing — **the publisher's**, **inside the
      publisher's range**, or **inference**. Name `clip_skip`, `scheduler` and the VAE/base resolution as
      inference. **Do not put it in `flow.json`** — the manifest carries eight keys and JSON has no
      comments. Verify: every key in `flow.json`'s `dials` appears in the new table:
      ```
      uv run python -c "
      import json,pathlib
      d=json.load(open('flows/conjure-v1/flow.json'))['dials']
      t=pathlib.Path('openspec/changes/0017-conjure/design.md').read_text()
      body=t[t.index('## Dial provenance'):]
      missing=[k for k in d if k not in body]
      print('dials:',sorted(d)); print('absent from the table:',missing); assert not missing"
      ```
- [ ] 2.8 Compute the digest and add `conjure-v1` to `PINNED` in `tests/test_flow.py`, with a comment
      naming this change. **This is designed bookkeeping, not a defect** — the pin list is what makes
      adding or removing a flow deliberate. Verify:
      ```
      uv run python -c "
      from isekai.foundation.flow import manifest_digest; print(manifest_digest('conjure-v1'))"
      uv run pytest tests/test_flow.py -q
      ```
- [ ] 2.9 Full gate green, and the registry now holds two flows. Verify: `make gate` exits 0, and
      ```
      uv run python -c "
      from isekai.foundation.flow import tracked_flows; print(tracked_flows())"
      ```

## 3. The verdict, measured rather than asserted

**Nothing here changes code.** Each task records a measurement into `design.md`. **If a measurement
disagrees with the verdict `design.md` states, that is the change's finding — write it down exactly as
it is and HALT for the operator rather than adjusting either.**

- [ ] 3.1 Run and record **verbatim**, under a new `## Verdict, measured` heading in `design.md`:
      ```
      git diff --stat v0.16.0..HEAD -- isekai/ scripts/ Dockerfile start.sh infra/ \
        Makefile pyproject.toml .github/ openspec/specs/
      ```
      **Expected: empty output.** Non-empty is the finding, not a failure to hide.
- [ ] 3.2 Run and record **verbatim** beneath it: `git diff --stat v0.16.0..HEAD -- tests/`.
      **Expected: `tests/test_flow.py` only, two lines changed.**
- [ ] 3.3 Write the three-bucket classification against what actually landed — the flow · the designed
      pin · the undesigned assumption. **If a fourth bucket appeared, name it and state what it means
      for v0.16's completeness.** Verify: the section names all three buckets and cites 3.1 and 3.2.
- [ ] 3.4 Verify: `openspec validate 0017-conjure --strict` exits 0.

## 4. ⚠️ **GPU · HALT** — the acceptance run

**The only metered phase.** Announce before `infra/up.sh`, tear down with `infra/down.sh` in the same
session, and confirm the account is empty through the RunPod MCP, recording what it returned. **Ceiling:
45 minutes and ~$0.30.** This run is planned at **three photographs × two flows × one seed = six renders
— $0.036 boot plus 6 × ~$0.01 ≈ $0.10**, about 15–25 minutes boot to teardown. **Exceeding the ceiling
is a halt, not a judgement call.**

- [ ] 4.1 Locally and for free, before anything is rented: `caption` → `sheet` → `review` → edit →
      `approve` for three photographs with `--flow summon-v1 --flow conjure-v1`, then `generate`
      **without** `--server`. Verify: six approved sheets and six assembled prompt artifacts exist, no
      endpoint was contacted, and `conjure-v1`'s sheets carry non-empty values in at least two of the
      five new fields across the three subjects.
- [ ] 4.2 ⚠️ **GPU** — one session: bring the pod up, open the tunnel, then
      ```
      python -m isekai generate <run…> --flow summon-v1 --flow conjure-v1 \
        --seed <N> --server <addr>
      ```
      **`--seed` is not optional.** Without it the two flows draw different seeds from one shared
      `Random` and the pair stops being comparable — the one cheap piece of evidence this session can
      produce. Download the outputs before teardown, tear down, confirm the account is empty.
      Verify: six renders from **one** boot, and `<N>.png` present under **both**
      `runs/<id>/summon-v1/outputs/<v>/` and `runs/<id>/conjure-v1/outputs/<v>/`.
- [ ] 4.3 Verify `show` survives two flows — **never run before this change**:
      `python -m isekai show <run>` prints two flow subtrees, refuses nothing, and exits 0.
- [ ] 4.4 **By eye**, and this is the version's product judgement: `conjure-v1` rendered a recognisable
      anime character from the sheet alone, at a flatness the operator accepts. **If it reads as
      insufficiently flat, that is parked entry P9's trigger — `hires_denoise` 0.50 as `conjure-v2`, not
      an edit to this flow.** Record the session's duration and actual cost in `CHANGELOG.md`.
