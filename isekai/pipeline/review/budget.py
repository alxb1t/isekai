"""The token budget of a sheet: what the text encoder will read from it.

Imports nothing of the front door.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from isekai.foundation.flow import Flow, Schema, assemble

# SDXL's text encoders read 77 tokens at a time; past that the prompt is chunked
# and the chunks are averaged, which is not the same prompt. Sheets already run
# well past it and nothing said so, so every one was being silently averaged.
ENCODER_WINDOW = 77


def estimate_tokens(fields: Mapping[str, Sequence[str]], schema: Schema) -> int:
    """Estimate what the text encoder will read from this sheet, in tokens.

    Deliberately crude and deliberately stated: one token per word plus one per
    tag separator, plus the two the encoder adds itself. It is an estimate for a
    warning, not a budget anything is enforced against -- the exact count depends
    on the tokenizer's merges, and a number that pretended otherwise would invite
    being trusted.
    """
    tags = [tag for name in schema.names for tag in fields.get(name, ())]
    words = sum(len(tag.split()) for tag in tags)
    separators = max(len(tags) - 1, 0)
    return words + separators + 2


@dataclass(frozen=True)
class TokenBudget:
    """What the text encoder will read from this sheet, and where it comes from.

    Three numbers from one rule, so they reconcile instead of disagreeing: the
    shares sum into the total and `overhead` is the remainder. The operator's
    question while correcting is never *how many tokens* but *which tag goes*,
    and a total with no breakdown cannot answer it.
    """

    total: int
    per_field: Mapping[str, int]
    overhead: int


def token_budget(
    fields: Mapping[str, Sequence[str]], schema: Schema, flow: Flow
) -> TokenBudget:
    """Count the assembled positive prompt, and split it into shares.

    `total` is taken over `assemble()`'s own output, so the flow's prefix, its
    trailer and the separators that join them fall out of one rule rather than
    being added back by hand. That is the whole point: counting the tags alone
    understates what the encoder reads by about nineteen tokens against a window
    of seventy-seven, so a sheet reported comfortably inside the budget is past it
    and silently chunked.

    `approve()` warns on `total` when it is given the flow, and on
    `estimate_tokens`, the tags alone, when it is not.

    A field absent from a mid-edit draft contributes nothing rather than raising,
    because the surface recomputes this on every keystroke.
    """
    separator = flow.prompt["separator"]
    positive, _ = assemble(fields, schema.names, flow)
    total = len(positive.split()) + positive.count(separator) + 2

    per_field: dict[str, int] = {}
    for name in schema.names:
        tags = list(fields.get(name, ()))
        per_field[name] = sum(len(tag.split()) for tag in tags) + len(tags)

    return TokenBudget(total, per_field, total - sum(per_field.values()))
