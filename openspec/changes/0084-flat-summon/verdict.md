# Verdict — 0084 flat summon

The operator's verdict on the prototype, per [D5](design.md#d5).

winner: summon-flat-a-anime-wai

| flow | photograph-level | person-level | no face found |
|---|---|---|---|
| `summon-anime-wai` | 14 / 15 | 10 / 15 | none |
| `summon-flat-a-anime-wai` | 1 / 13 | 4 / 13 | caprice-3, lily-1 |
| `summon-flat-b-anime-wai` | 2 / 13 | 2 / 13 | caprice-3, lily-1 |

Counts from `uv run python -m evaluation .data/flat-summon-prototype/runs --cohort .data/flat-summon-prototype/cohort`.

**Chosen by eye.** Both candidates are flat, and both keep the person. The count misses because the face encoder,
trained on photographs, does not read flat anime faces; D5's count rule is overruled for that reason.

**A over B.** B's hires pass on the plain checkpoint makes no visible difference: under 1% of pixels differ by more
than 32 grey levels. A differs from summon in fewer places.
