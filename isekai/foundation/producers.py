"""The stage record: each stage a run passes through, declared once.

A row names a stage's key, the folder its artifacts sit in, whether that folder is
under `photo/` or under a flow, the verb that runs it and the attempts it may spend.
`names.py` and `failures.py` read their tables from it, and `run.py` re-exports each
name (D62).

Imports nothing of `isekai`: stdlib only, and on `python -m isekai`'s import graph.
"""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Producer:
    """One stage: its key, its folder, where the folder sits, its verb and its budget.

    The key is the budget's key and the `stage` field of a failure record on disk, so
    it never changes. A budget of None is a stage with no attempt to spend.
    """

    key: str
    folder: str
    scope: Literal["photo", "flow"]
    verb: str
    budget: int | None


# What each stage may spend before it costs a person's attention instead. Reading
# and sorting are cheap and flaky, so they get three; assembling and rendering get
# one, because a render that has failed once should be looked at rather than paid
# for again. `review` calls no model and records no failure, so it has no budget.
#
# The two taggers are split on the same axis rather than sharing a number.
# `tags` is a hosted model over HTTP, so it is flaky in exactly the way `caption`
# is and gets its three. `wd14` is a local pass over a
# digest-verified graph, and what can still fail there is **this photograph's own
# bytes** -- a header no decoder can read. That is permanent by construction, so
# one attempt is the whole budget, exactly as `assemble` and `render` are one.
#
# The two file conditions that would fail identically for every input -- an
# absent model, bytes that disagree with the pin -- are deliberately **not**
# counted here. They are conditions about this build rather than about a
# photograph, so the tagger is opened before the stage's `try` and refuses the
# batch once instead of writing one error record per input for a single fix.
#
# **`sheet` is one for `wd14`'s reason.** It reached a hosted model once and had
# three; it is now a dictionary lookup over an artifact already on disk, so there
# is no transient failure left for a second attempt to catch -- which is exactly
# what the `wd14` row already records for the other local producer. The stage
# records every failure as permanent, so a second attempt waits on a deletion.
#
# In the order a run passes through the stages.
PRODUCERS: tuple[Producer, ...] = (
    Producer("caption", "captions", "photo", "caption", 3),
    Producer("wd14", "wd14", "photo", "tag", 1),
    Producer("tags", "tags", "photo", "tag", 3),
    Producer("sheet", "sheets", "flow", "sheet", 1),
    Producer("review", "review", "flow", "review", None),
    Producer("assemble", "prompts", "flow", "generate", 1),
    Producer("render", "outputs", "flow", "generate", 1),
)


def producer_for(key: str) -> Producer:
    """Return the row of the stage `key` names, or raise `KeyError`.

    e.g. "wd14" -> Producer("wd14", "wd14", "photo", "tag", 1)
    """
    for producer in PRODUCERS:
        if producer.key == key:
            return producer
    raise KeyError(key)
