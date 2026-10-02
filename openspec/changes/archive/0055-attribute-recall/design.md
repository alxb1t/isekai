# Design — 0055 attribute recall

How a render's tags are counted against the sheet it was made from, what reads them, the command that does it,
and the cards the change closes. **Verdict: feasible** — a pure count, a reader over a function the pipeline
already has, one entry point; the premise was probed at the cut and holds.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut (`73f45f4`):

- **The scored mark.** `Schema.scored` (`isekai/foundation/flow.py:200-203`) returns the names of the fields a
  measurement is taken over; no runtime code calls it. `tests/test_sheet_schema.py:50-58` pins `summon`'s:
  `hair_colour`, `hair_silhouette`, `eye_colour`, `marks`, `clothes`, `gaze`, `pose`.
- **The sheet.** `ReviewApproved.fields` (`isekai/foundation/artifacts.py:262-272`) maps a field to whole
  vocabulary tags, normalised. A render group `outputs/<NNN>` is the approval `review/<NNN>.approved.json`
  (`isekai/pipeline/generate.py:571-572`); `rendered(run, flows_dir, flows=…)`
  (`isekai/interface/run_view.py:180`) lists `(flow, group, seeds)`, groups ascending.
- **The tagger.** `wd14.scored(photo, session, labels, *, floor=FLOOR)` (`isekai/boundary/wd14.py:363-377`) returns
  the general tags at or above `FLOOR = 0.15` (`:107`); `open_session(models_dir)` (`:421-440`) verifies both
  files against `config/vocabulary.json` and returns a `LocalTagger` carrying its `pins`. `normalise`
  (`isekai/shared/vocabulary.py:68-70`) turns Danbooru's spelling into the sheet's. The suite's double is
  `fake_tagger` (`tests/stages.py:259-265`) over `INDEX` (`:212-216`).
- **The cohort evaluator.** `_rows` (`evaluation/__main__.py:103-154`) ranks `renders[0]`, the lowest group's
  first seed (`:129-140`). `_destination` (`:236-246`) refuses a record git can reach, ending in advice rather
  than a command (`:240-245`). `tests/test_evaluation_cli.py` builds its batch with `_batch` (`:38-56`).
- **The spec.** `openspec/specs/evaluation/spec.md` — *Purpose*, *Source*, *Tests* (`:3-11`); *Every render is a
  row* (`:155-232`), whose why says "a later change" (`:175`). `openspec/specs/image-generation/spec.md` —
  *A flow renders on another flow's seeds when the operator names it* (`:698-773`), whose
  `a-damaged-approval-record-is-refused` scenario (`:742-747`) proves nothing its SHALL states.
- **The docs.** `docs/decisions.md` — D37 closes *Models* (`:128-136`). `evaluation/README.md` — `## Files`
  (`:35`), `## Imported by` (`:45`). `isekai/boundary/README.md:33` — `provision.py`'s importers, without
  `tests/test_evaluation_cli.py`; `:34` — `wd14.py`'s. `README.md:19` — "both tracked flows name the same one".
  `tests/test_cohort.py:63` — `test_a_run_outside_the_cohort_is_listed_and_the_others_are_scored`.
- **The probe, run at the cut** over `.data/v0.30.1`'s four `summon-anime-wai` renders, each against its
  `review/001.approved.json`, at the tagger's floor:

  | run | hair_colour | hair_silhouette | eye_colour | clothes | gaze | pose | marks |
  |---|---|---|---|---|---|---|---|
  | `187ec7dce855` | 1 / 1 | 1 / 1 | 1 / 1 | 1 / 3, missed `shirt`, `black shirt` | 1 / 1 | 0 / 0 | 0 / 0 |
  | `28c3bb7ce031` | 1 / 1 | 1 / 1 | 1 / 1 | 4 / 4 | 1 / 1 | 1 / 1 | 0 / 0 |
  | `d2043248d6e1` | 1 / 1 | 1 / 1 | 1 / 1 | 9 / 9 | 1 / 1 | 1 / 1 | 0 / 0 |
  | `dff7c49cc66a` | 1 / 1 | 1 / 1 | 1 / 1 | 15 / 15 | 1 / 1 | 2 / 2 | 0 / 0 |

  Produced by `wd14.open_session()`, `wd14.scored(render, session, labels)` and `normalise`, one render per run.

## Goals / Non-Goals

**Goals:** a count per scored field per render, each miss named; a command that needs no cohort; the record
re-derivable; the cohort evaluator on the latest group; an empty backlog.

**Non-Goals:** a base line; a split by `edited`; the sheet against the photograph; pose geometry; a new model.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | per scored field, tags read back over tags asked; each miss named; a field with no tag counts nothing | a field showing three of four tags is not a failed render, and the miss is the finding | all-or-nothing per render; any-tag per render |
| [D2](#d2) | the pipeline's tagger through `wd14.open_session` and `wd14.scored` at `wd14.FLOOR`; D39 records it | the sheet's vocabulary is its label set; the same floor asks whether the render would put the tag on its own sheet | a second tagger and a tag mapping; a stricter floor |
| [D3](#d3) | `python -m evaluation.recall <runs> [<run>…]`: every render of every group and seed, each against its group's approval; `<batch>/recall.json`; a table per flow | each output is read alone; an older pair is still a true pair | a block in the cohort command; the latest group only |
| [D4](#d4) | the cohort evaluator ranks the first seed of the latest group | the render the operator last made, and the one a control's seeds come from | leaving it; ranking every group |
| [D5](#d5) | the six fixable cards are fixed where this change already edits; 0054·R8 is retired | the backlog is empty after the release | a paydown of its own |

### D1

**The count.** `recall.py`, stdlib and `isekai.shared.vocabulary.normalise` alone in its pure half:

```
FieldRecall = {"asked": list[str], "missed": list[str]}
count(fields, scored, seen) -> dict[str, FieldRecall]
    for name in scored:  asked = fields.get(name, []);  missed = [t for t in asked if normalise(t) not in seen]
Row = {"run", "flow", "group", "seed", "outcome": "read" | "unreadable" | "no approval", "fields": {…}}
totals(rows) -> {flow: {field: {"read_back": int, "asked": int}}}      over the rows whose outcome is "read"
record(rows, tagger, floor) -> {"tagger": {dest: sha256}, "floor": float, "rows": […], "totals": {…}}
table(record) -> str
```

`table` prints one block per flow, flows sorted: a header of the flow's scored fields in schema order, a row per
render — the run id's first twelve characters, the group, the seed, then `read back / asked` per field, `-` where
nothing was asked — a `missed:` line under any row with a miss, `field: tag, tag · field: tag`, then a `total`
row. A row not `read` prints its outcome in place of its cells.

### D2

**The reader.** `Read = Callable[[Path], set[str]]`: the normalised tags seen in an image. The real one, built in
`recall.py`'s `_reader(models)`:

```
tagger = wd14.open_session(models)                              # verifies both pins, D7
read   = lambda path: {normalise(one.tag) for one in wd14.scored(path, tagger.session, tagger.labels)}
```

An image that does not decode raises `OSError` from the tagger's preparation; `_reader` turns it into a `Refusal`
naming the file, which the command makes an `unreadable` row. The record's `tagger` is `tagger.pins`, each
destination with its digest, and `floor` is `wd14.FLOOR`.

**D39 in `docs/decisions.md`**, after D37:

```
### D39 · Attribute recall uses the sheet's tagger

**Attribute recall reads each render with WD14, the tagger whose tags fill the sheet, at the same floor, and
counts the approved sheet's scored tags it reads back.**

- **Why:** the sheet's vocabulary is that tagger's label set, so only it answers in the sheet's own words, and
  the same floor asks whether the render would put the tag on its own sheet. The generator is not trained to
  satisfy it, so this is not the case D37 guards against.
- **Accepts:** its blind spots are on both sides: a tag it cannot see is neither asked well nor read well.
  Reopen when a tag set a second tagger shares with the vocabulary exists.
- **Made by:** `0055`.
```

### D3

**The command.** `python -m evaluation.recall <runs> [<run>…]`, with `--models` and `--flows` as the cohort
command has them.

```
destination(runs, "recall.json")            refuses where git can reach, before anything is read
named runs not under <runs> ──▶ Refusal naming each, before anything is read
for run in the runs named, or every */run.json:
  for flow in run.flows:        load_flow → schema.scored, output_suffix     (unloadable → a note, as the cohort's)
    for (group, seeds) in rendered(run, flows_dir, flows=(flow,)):
      approval = <flow>/review/<group>.approved.json     absent or refused ──▶ row "no approval"
      for seed in seeds:  read(render)  ──▶ row "read" with count(…)   |   Refusal ──▶ row "unreadable"
write recall.json; print table(record)
```

`evaluation/record.py` holds `destination(runs, name) -> Path`, the cohort command's `_destination` moved and
given a name, with the refusal 0053·R15 asks for: `…; move <batch> under .data/, then this command again with
its new runs path`. `evaluation/__main__.py` calls it with `"evaluation.json"`.

`tests/recall/recall.json` and `recall.txt` are a committed pair the re-derive test holds equal.

### D4

**The latest group.** In `_rows`, the row ranks the first seed of the last group `rendered` returns;
`also_rendered` lists every other seed, as now. `tests/test_evaluation_cli.py` gains a run with renders under
`outputs/001` and `outputs/002` and asserts the row's seed is the later group's first.

### D5

**The cards.**

| card | fix | where |
|---|---|---|
| 0053·R15 | the refusal ends in the move and "then this command again" | `evaluation/record.py`, [D3](#d3) |
| 0053·R16 | the test is `test_a_run_outside_the_cohort_is_counted_and_the_others_are_scored` | `tests/test_cohort.py:63` |
| 0053·R17 | "the record — the file a batch publishes —" | the `evaluation` delta's MODIFIED block |
| 0053·R18 | `tests/test_evaluation_cli.py` among `provision.py`'s outside importers | `isekai/boundary/README.md:33` |
| 0054·R4 | "every tracked flow names the same one" | `README.md:19` |
| 0054·R9 | the SHALL gains "It SHALL refuse, naming its file, an approval whose record of its producer or origin is damaged." | the `image-generation` delta's MODIFIED block |
| 0054·R8 | retired: it names the control arm's archived `design.md`, which is frozen | none |

`isekai/boundary/README.md:34` also gains `evaluation/recall.py` among `wd14.py`'s outside importers, and
`evaluation/README.md` gains the recall command, `recall.py` and `record.py` in *Files* and *Imported by*. The
living spec's header lines (`openspec/specs/evaluation/spec.md:3-11`) gain recall in *Purpose*, `recall.py` and
`record.py` in *Source*, and the recall tests in *Tests*.

## Dependencies

None.

## Risks / Trade-offs

- **High counts by construction** → the model is told the tags it is then checked for; the value is in the
  misses, which the table names.
- **The same tagger on both sides** → accepted in D39, with its reopen trigger.
- **`marks` is empty unless a person fills it** → an empty field counts nothing and prints `-`.
- **A flow whose schema scores other fields** → each flow's block has its own header.
- **The MODIFIED blocks copy two long requirements** → each was copied whole from the living spec at the cut;
  the binding checker fails a dropped key.

## Verdict

**feasible** — the count is a set difference, the reader is one call the pipeline already makes, and the probe
at the cut found a real miss on a real render.
