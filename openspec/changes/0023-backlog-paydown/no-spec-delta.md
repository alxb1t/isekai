# No spec delta

**This change alters no requirement and no scenario, and the omission is deliberate rather than
incidental.** `v0.22.2` is scheduled for the openspec prose and the living `docs/`, so behaviour and the
sentence describing it land together there rather than half here. That version also owns the ten false
self-claims the repository currently makes about itself, which a docs pass rewrites anyway.

## Four entries make an already-written assertion true

These are not deltas — they are the opposite. Each names a scenario whose `THEN` is **false today**, and
the fix is what makes it hold:

| entry | scenario | why it is false today |
|---|---|---|
| `v0.18 review/R7` | `ui:startup:refusals-are-reported-together` | with two unreadable photographs **neither** is named: `image_dimensions()` raises `SystemExit` and `across()` catches only `Refusal` |
| `v0.16 review/R5` | `image-generation:inputs:unapproved-flow-is-refused` | *"the message names the commands that would produce one"* — both printed commands are refused by the parser for lacking `--flow` |
| `v0.16 review/R8` *(dials half)* | `image-generation:manifest:invalid-manifest-names-the-field` | the parent requirement says the manifest declares *"every dial the render uses"*, and a manifest with an empty `dials` block loads clean |
| `v0.18 review/R6` | `ui:approval:approved-input-refuses-a-draft-update` | see below — the `PUT` already succeeds |

## One scenario is false because two capabilities contradict each other

```
ui/spec.md      "SHALL ... refuse a draft update against [an approved] input"
review/spec.md  "reviewing again appends a new numbered draft from the approved one"
                 └── both live, and they cannot both hold
```

`ui:approval:approved-input-refuses-a-draft-update`'s `WHEN` carries **no `and no draft` guard** — its
sibling scenario does — so it matches the state `review --flow F --new-version` produces. In code,
`save_draft` refuses on *no draft* and never on *approved*, while `put_draft` has **no approval gate at
all**. **The `PUT` already succeeds there; the scenario is already false.**

This change closes the contradiction in `ui`'s favour, which is a bug fix rather than new behaviour and is
therefore the only version of the fix that needs no delta. **Whether an approved input *should* be
re-openable — that is, which capability is right — is a design question and is `v0.22.2`'s.** A third rail
status is explicitly out of scope here.

## Three entries need no test at all

`v0.18 review/R11` and `v0.15 review/R7` are dead-code deletions with no behaviour change. `v0.19
review/R7` *is* a test fix and keeps the `spec_exempt` marker it already carries.

## Eleven carry `spec_exempt`, and the cost is stated rather than hidden

The remaining eleven change behaviour the living spec does not describe, so there is nothing to bind to.
They carry `@pytest.mark.spec_exempt("behaviour; the scenario lands in 0024")`.

> ⚠️ **This borrows `spec_exempt` past its documented meaning for one version.** The marker means
> *genuinely structural*, and these are behaviour. It is borrowed deliberately because the alternatives are
> worse: an unmarked test hides the debt behind a gap the repository already knows about
> (`CLAUDE.md:176-179` — there is no binding checker, so nothing would catch it), and a third marker is new
> tooling in a patch release.
>
> **The `0024` in the reason string is load-bearing.** `grep spec_exempt tests/ | grep 0024` is the
> worklist `v0.22.2` opens with, and it is the only thing that makes this debt countable.

## What no spec describes at all

**`openspec/specs/ui/spec.md` is the only one of twelve with no `Source:` and no `Tests:` line.**
`grep -L '\*\*Source:\*\*' openspec/specs/*/spec.md` returns exactly that file. Nine of this change's
eighteen entries live in `isekai/interface/ui/` or `ui/src/` — modules that spec would name if it had the
line. Recorded here so `v0.22.2` does not have to rediscover it.
