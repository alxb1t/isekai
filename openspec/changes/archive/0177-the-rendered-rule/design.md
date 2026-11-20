# The rendered rule — design

One rule says a seed is rendered when its image is a file in its group, and review's sites ask it. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

Review decides "is this seed rendered?" at several sites, each its own way. `refuse_revision` and `_refuse_unchanged` in `isekai/pipeline/review.py` ask for the record. `drafting_approval` asks for the record and the image. The paid stage's resume check, `rendered_seeds` in `isekai/foundation/layout.py`, asks for the image alone, and it is the one that spends money.

`Surface.rendered` in `isekai/interface/ui/surface.py` and `_revision` in `isekai/interface/ui/routes/reviewing.py` ask the image alone, spelled by hand. `copied_renders` and `_first_image` list a group by `is_seed(path.stem)`, which any file with a seed for its stem satisfies.

[D69](../../../docs/decisions.md#d69--a-render-groups-files-are-listed-in-foundationlayoutpy-and-a-module-above-the-pipeline-reads-the-listing-from-the-foundation) moved the listing and the name builders into `layout.py`, and says to reopen when one rule says a seed is rendered. The product writes a record beside its image and a delete removes both, so no folder it writes differs between the record's answer and the image's. A folder with one of them is a hand-made folder or a crashed write.

```
                           record only    image only    both
before  refuse_revision    written        refused       written
        _refuse_unchanged  reproduces     a change      reproduces
        drafting_approval  refused        refused       written
after   refuse_revision    refused        written       written
        _refuse_unchanged  a change       reproduces    reproduces
        drafting_approval  refused        written       written
the stage, as before       renders again  skips         skips
```

## Goals / Non-Goals

Goals:

- One function, `is_rendered`, that review's sites and the app's sites ask.
- Each changed answer carries a scenario and a case that fails before its site is switched.
- Behaviour on every folder the product writes is as before.

Non-goals are [the proposal's](proposal.md#not-in-this-change).

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `is_rendered(group, seed, suffix)` in `layout.py` is true when `render_image(group, seed, suffix)` is a file; a record alone is no render | the stage's resume check asks the image, and the spec reads a record with no image as unrendered | asking both files: a lone image would be unrendered to review and skipped by the stage |
| [D2](#d2) | `refuse_revision` and `_refuse_unchanged` ask it with `OUTPUT_SUFFIX` | review has a flow's name and no flow, so the suffix is its constant | a `Flow` parameter: it edits every caller, which `the-render-ref` rules out |
| [D3](#d3) | `drafting_approval` asks it in place of its test of the record and the image | a draft copies the image's bytes, and the record is not read | keeping both files: it refuses an image the draft can copy |
| [D4](#d4) | `copied_renders` and `_first_image` list by `rendered_seeds` and `OUTPUT_SUFFIX`; `Surface.rendered` and `_revision` ask the rule | one listing and one rule, with no answer changed on a folder the product writes | leaving the hand-built tests in the app: they are the third spelling of the rule |
| [D5](#d5) | `_holds_render`, `rendered_at`, `render_groups`' `str.isdigit`, review's `OUTPUT_SUFFIX` and `is_render` stand | a patch fixes behaviour only under an existing requirement, and none says what a stray folder answers | an `is_file` check in `is_render`: it makes a listing call the disk per name |
| [D6](#d6) | the delta adds scenarios under the review requirements [D6](#d6) names and changes no requirement's text | the patch rule lets a scenario be added under an existing requirement | a new requirement: a patch never adds one |
| [D7](#d7) | the next free decision, D71, records the rule and amends D69's *Accepts* | a home and a rule a later version reads | editing D69's body: it states the home, and D71 states the rule |

### D1

`is_rendered` sits after `render_record` in `isekai/foundation/layout.py` and is re-exported by `run.py`.

```python
def is_rendered(group: Path, seed: int, suffix: str) -> bool:
    """Return whether `seed` is rendered in `group`: its image is a file there."""
    return render_image(group, seed, suffix).is_file()
```

A missing `group` answers false, as `is_file` does. A group holding failure records alone answers false for every seed.

### D2

Each site replaces the hand-built path to the record with the rule. The refusals' texts do not change.

| site | before | after |
|---|---|---|
| `refuse_revision` | refuses a seed with no record | refuses a seed with no image |
| `_refuse_unchanged` | counts a seed with a record as made | counts a seed with an image as made |

### D3

`drafting_approval` refuses a `seed` when `not is_rendered(group, seed, OUTPUT_SUFFIX)`, with its text as before. A seed with a record and no image stays refused, so the lone record's case stands.

### D4

`copied_renders` reads `rendered_seeds(group, OUTPUT_SUFFIX)`, which is empty for a missing group. `_first_image` returns the least of `render_image(group, seed, OUTPUT_SUFFIX)` over those seeds, a `Path`, so it names the file it named.

The app's sites keep their answers and texts. `Surface.rendered` asks `is_rendered(image.parent, seed, one.output_suffix)` where it asked `image.is_file()`, and names the record by `render_record` where it asked for `{seed}{SIDECAR}`. `_revision` asks `is_rendered` for each listed seed of the approval's group.

### D5

Review reads `OUTPUT_SUFFIX` as it does today. The group-level rule `withdraw` applies, `_holds_render`, is the spec's and stays with its `failures_alone(group) is None`.

### D6

A MODIFIED block replaces its requirement whole, so each requirement below carries its text word for word and every scenario it has, then the new ones.

| requirement | new scenario |
|---|---|
| a revision is a draft from the approval that made the image | a seed with a record and no image is refused; a seed with an image and no record is revised |
| approval refuses a revision that would reproduce its images | a record with no image is a change; an image with no record is reproduced |
| a draft is written once from another flow's approval | an image with no record is drafted from |

### D7

D71 is the next free id once `the-render-ref` took D70. It states that a seed is rendered when its image is a file in its group, in `layout.py`, asked by review and the app. D69's *Accepts* drops the sites this change switches and keeps `_holds_render`, `rendered_at` and `render_groups`' `str.isdigit`.

## Tests

The change adds unit tests and no end-to-end test: every site is a function over a run's folder, so the lowest layer is the unit one ([T1](../../../CODING_STANDARDS.md)). It deletes and merges none, so no `I16` table is due.

| layer | tests added | where | counts before → after |
|---|---|---|---|
| unit | one test of the rule, a case for each folder below | `tests/test_generate.py` | 89 → 90, from `git grep -c -E "^def test_" -- tests/test_generate.py` |
| unit | one test for each new scenario | `tests/test_review.py` | 101 → 106, from `git grep -c -E "^def test_" -- tests/test_review.py` |

The rule's cases are a seed with both files, with an image alone, with a record alone and in a group of failure records alone. Each new scenario's test arranges its folder by deleting the record or the image `tests.stages.rendered_image` wrote, and is bound to its key by `pytest.mark.spec`.

Each new test fails on the code as it stands. The app's own sites change no answer, so the suite as it stands holds them, in `tests/test_ui_api.py`, with one arrangement moved: `test_a_revision_of_an_untracked_flow_is_refused_and_nothing_is_written` seeded a record with no image and wanted the tracked flow's seed revisable, which `refuse_revision` now refuses, so it seeds both files as a render writes them (task 2.5). A mutation run over each switched site's new lines is the proof that a case reaches them. `tools.mutate` refuses a range that holds no mutant, with exit 2, and a range that only assigns a path is held by the cases and the suite.

## Dependencies

None.

## Risks / Trade-offs

- `the-render-ref` is open beside this change and edits `layout.py`, `run.py` and `review.py`. A textual conflict is `mf-integrate`'s, and so is the decision id: both took D70 at this base, and `the-render-ref` keeps it, so this change's is D71.
- A hand-made folder with a record and no image was revisable and is refused now, and one with an image and no record was refused and is revisable. Its operator is told as before: the refusal names the seed and the command that lists the rendered seeds.
- `copied_renders` and `_first_image` listed any file whose stem is a seed, and list the flow's images alone now. The product writes no such file beside a render, so only a stray file in a hand-made folder is dropped.
- `_first_image` keeps its answer on purpose: the least path, not the least seed. A change to the least seed is a change to a remedy's text and is not asked for.

## Verdict

Ready to build in the phases of [tasks](tasks.md): the rule, the revision, the draft, the listings and the app's sites, the documents.
