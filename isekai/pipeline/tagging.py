"""Stage (1), twice more: a photograph in, a list of Danbooru tags out.

**Two functions and two seams, deliberately not one Protocol with two
implementations.** A Protocol earns its name when the thing behind it is
interchangeable, and these are not. `caption_tags` reaches a model over HTTP, on
the alias the flow's manifest names in its `model` key; `caption_wd14` opens a
digest-verified file on disk and resolves through **nothing at all** -- there is
no manifest key it reads and no flow for which it would be wrong. A Protocol
whose two implementations resolve through different mechanisms is a shared name
rather than a seam (design.md D3).

**Neither narrows anything, and that is the product.** Stage (2) is where a tag
list is filtered down to a sheet; seeing *behind* that filter is the whole reason
these two artifacts exist. So nothing here canonicalises, maps to the vocabulary,
deduplicates or re-orders on anything but confidence. The hosted tagger's list is
known to be roughly three-quarters unusable -- it is stock-photo keywording, and
it contradicts its own prose on the same photograph -- and it ships anyway, marked
for what is committable, because the panel is advisory and a wrong tag costs a
glance (design.md D1, D15).

**`caption()` is not modified and is byte-identical in the diff.** It is the one
function in this change whose behaviour has to be provably unchanged, and a
function with no edit is provably unchanged by `git diff`. These two sit beside
it and the CLI says three times.

**The two artifacts resume independently**, which is why each has its own
directory, its own `latest()` check and its own `BUDGETS` entry. WD14 is
deterministic and free; the hosted tagger is over HTTP with a retry budget.
Coupling their idempotence would spend a model call to retry a matrix multiply
(design.md D4).

Stdlib only. `wd14.Session` and `ollama.Transport` are the seams, and their
doubles are what keep the suite offline.
"""

import base64
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from isekai.boundary import ollama, wd14
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    TAGS,
    WD14,
    Run,
    StageFailure,
    artifact_name,
    check_budget,
    constant_record,
    envelope,
    latest,
    next_version,
    record_failure,
    refusal_for,
    write_json,
)

# The verb a refusal tells the operator to run again, and it is `caption` rather
# than either stage name above: one verb produces all three artifacts, so there
# is no `python -m isekai tags` to name (design.md D8). Written out rather than
# imported from `caption.py` -- no stage imports another.
VERB = "caption"

# The whole of what the hosted tagger is told. **"Long" is the lever**: it takes
# the answer from 34-40 tags to 45-51, and in-vocabulary yield from 11-23% to
# 24%. Measured on three real photographs across four prompt variants.
#
# Unframed, and that is a decision rather than an omission. The llama-3 chat
# framing adds five tags across three photographs and is refused: the Modelfile
# pins `TEMPLATE {{ .Prompt }}`, the shipped prose briefing goes through it
# unframed, and hand-building chat markup here would make two calls to the same
# model use different framing -- and would double-apply the day that TEMPLATE
# gains one (design.md D11).
TAG_PROMPT = "Write a long list of Booru tags for this image.\n"

# What the hosted tagger is sampled at. `repeat_penalty` is the sorter's, kept on
# the sorter's own precedent rather than on a budget argument: at temperature 0
# there is no sampling noise to break a loop, one field came back `"white robe"`
# forty times, and **a comma-separated list is that loop with more surface**.
#
# `num_predict` is the reader's 1024 and is *not* the constraint -- eight runs,
# every one `done_reason: stop`, the longest 200 tokens. Stated rather than
# inherited, so nobody later reads the number as evidence of a measurement it did
# not come from (design.md D12).
TAGGER_OPTIONS: Mapping[str, Any] = {
    "temperature": 0,
    "seed": 1,
    "num_predict": 1024,
    "repeat_penalty": 1.15,
}

# The one command that turns an absent hosted tagger into a present one. The same
# alias the reader uses, built from the same committed recipe -- one model answers
# both prompts, which is exactly why `TAG_PROMPT` above must not be framed
# differently from the briefing.
TAGGER_REMEDY = "ollama create {model} -f scripts/joycaption.Modelfile"

# What separates *wrong* from *not a list at all*. The operator asked for the raw
# list knowing it is wrong, so wrongness is not the failure being guarded here. A
# model that answers in prose yields one element no chip can render, and that is
# detectable and should be -- one comma is the whole test, and it touches no
# content. Anything richer starts filtering, which is what this stage exists not
# to do (design.md D15).
SEPARATOR = ","


@dataclass(frozen=True)
class Tagging:
    """What a hosted tagger returned: the tags, and what actually produced them."""

    tags: tuple[str, ...]
    implementation: str
    models: tuple[str, ...] = ()
    pinned: bool = False


class Tagger(Protocol):
    """The hosted tagger seam. One implementation ships; the double keeps it dry."""

    def tag(self, photo: Path) -> Tagging:
        """Return the tags a hosted model offers for `photo`."""
        ...


@dataclass(frozen=True)
class FakeTagger:
    """An offline stand-in that counts its calls.

    It is what makes the idempotence assertion provable: showing that a completed
    stage makes **no** call needs something that counts calls. `FakeReader` is
    the precedent and this is the same shape.
    """

    tags: tuple[str, ...] = ("1girl", "solo", "looking at viewer")
    implementation: str = "fake-tagger"
    models: tuple[str, ...] = ("fake-model",)
    calls: list[Path] = field(default_factory=list)

    def tag(self, photo: Path) -> Tagging:
        """Record the call and return the fixed tags."""
        self.calls.append(photo)
        return Tagging(self.tags, self.implementation, self.models)


@dataclass(frozen=True)
class OllamaTagger:
    """The Ollama adapter: the photograph's own bytes and one fixed prompt.

    **No briefing and no schema.** Unlike the reader, this one is told nothing
    that varies by flow -- the prompt is a module constant, which is precisely
    why its provenance is recorded with `constant_record` and carries no path
    (design.md D16).

    The photograph goes as its own bytes, unresized, for the reader's reason: the
    resampler lives in a wheel a module on the entry point's import graph may not
    import, and the vision tower encodes whatever it is handed.
    """

    model: str
    transport: ollama.Transport = ollama.post
    implementation: str = "ollama"

    def body(self, photo: Path) -> dict[str, Any]:
        """Return the exact request this tagger is invoked with.

        A method rather than a local, so the request is assertable without a
        call -- the property `OllamaReader.body()` has, for the same reason.
        """
        return {
            "model": self.model,
            "prompt": TAG_PROMPT,
            "images": [base64.b64encode(photo.read_bytes()).decode()],
            "stream": False,
            "options": dict(TAGGER_OPTIONS),
        }

    def tag(self, photo: Path) -> Tagging:
        """Send the photograph and return the tags, or raise.

        **Split at the adapter, stored as a list.** The split happens here rather
        than in the stage because it is this implementation's business that the
        answer arrives as one comma-separated string; a different hosted tagger
        might answer in another shape. Nothing beyond the split and a strip
        happens to any element.
        """
        try:
            answer = ollama.ask(
                self.body(photo),
                remedy=TAGGER_REMEDY.format(model=self.model),
                transport=self.transport,
            )
        except ollama.OllamaFailure as failed:
            raise StageFailure(failed.kind, failed.detail) from failed

        if SEPARATOR not in answer:
            raise StageFailure(
                "permanent",
                f"{self.model} answered without a single {SEPARATOR!r}, so it "
                "returned prose rather than a tag list; the prompt asks for a "
                "list and a model that will not give one cannot be retried into "
                "it",
            )
        tags = tuple(
            stripped for part in answer.split(SEPARATOR) if (stripped := part.strip())
        )
        return Tagging(tags, self.implementation, (self.model,))


def caption_wd14(
    run: Run,
    flow: str,
    open_tagger: Callable[[], wd14.LocalTagger],
    *,
    new_version: bool = False,
) -> Path | None:
    """Score `run`'s photograph against the local tagger, or do nothing.

    The guard is `caption()`'s, against this stage's own directory: a stage that
    has already written is a stage that does nothing the second time, with no
    special mode and no state machine.

    **`open_tagger` is a thunk, and the laziness is the point.** Opening the
    tagger hashes 467 MB and loads a graph; a run whose list is already complete
    must not pay for that to return `None`, and on a machine that has since
    deleted `models/` a completed run must still resume. `Wiring.vocabulary` is
    a thunk for the same reason, stated the same way: an eager read made a verb
    impossible on a clone that had not provisioned the file it never used.

    It is called **after** the guard and **outside** the `try` below, which is
    what keeps the two kinds of failure apart. An absent or corrupt model is a
    condition about this *build*, identical for every photograph in the batch,
    so it refuses without accruing one error record per input; what the `try`
    catches is this *photograph* -- a header no decoder can read -- which is
    per-input, permanent, and exactly what a budget of one is for.

    **This is the first producer in this repository that can honestly claim a
    pin.** Every artifact in the tree records `pinned: false` and `show` prints
    *"unpinned"* over all of them; a local file with a digest is not the hosted
    service that field was written for, so it records `true` and carries **both**
    digests -- the ones the session was actually verified against, not the ones
    the manifest happens to hold at write time (design.md D17).

    Returns the artifact's path when one is written, and None when the stage was
    already complete.
    """
    directory = run.directory(flow, WD14)
    if latest(directory) is not None and not new_version:
        return None

    version = next_version(directory)
    check_budget(WD14, directory, version, run.id)

    tagger = open_tagger()
    try:
        found = wd14.scored(run.photo, tagger.session, tagger.labels)
    except (Refusal, OSError) as failed:
        # Permanent, always. Nothing here is transient: the session is open and
        # the index is read, so what is left to fail is this photograph's own
        # bytes, and a second pass over them decodes exactly as badly.
        record = record_failure(
            directory,
            version,
            "permanent",
            {"stage": WD14, "detail": str(failed)},
        )
        raise refusal_for(
            "tagger",
            run.id,
            "permanent",
            str(failed),
            record,
            f"{flow}/{WD14}/",
            VERB,
            flow,
        ) from failed

    path = directory / artifact_name(version)
    write_json(
        path,
        envelope(
            WD14,
            {
                "implementation": "wd14",
                "models": [wd14.MODEL_DEST],
                "pinned": True,
                "artifacts": dict(tagger.pins),
            },
            {"tags": [{"tag": one.tag, "confidence": one.confidence} for one in found]},
        ),
    )
    return path


def caption_tags(
    run: Run,
    flow: str,
    tagger: Tagger,
    *,
    new_version: bool = False,
) -> Path | None:
    """Ask the hosted tagger for `run`'s photograph, or do nothing.

    The guard is `caption()`'s again, against this stage's **own** directory. The
    three artifacts resume independently, so a complete caption and a complete
    WD14 list beside a failed hosted one is an ordinary, resumable state rather
    than a stuck one.

    **The list is stored exactly as it came**, minus the split and a strip. No
    canonicalisation, no vocabulary filtering, no re-ordering: narrowing is stage
    (2)'s job and seeing behind it is why this artifact exists.

    `pinned` is `false` and the prompt's digest is recorded with no path, because
    the prompt is a module constant and a record that invented a path would
    assert a location that does not exist.
    """
    directory = run.directory(flow, TAGS)
    if latest(directory) is not None and not new_version:
        return None

    version = next_version(directory)
    check_budget(TAGS, directory, version, run.id)

    try:
        tagging = tagger.tag(run.photo)
    except StageFailure as failed:
        record = record_failure(
            directory,
            version,
            failed.kind,
            {"stage": TAGS, "detail": failed.detail},
        )
        raise refusal_for(
            "tagger",
            run.id,
            failed.kind,
            failed.detail,
            record,
            f"{flow}/{TAGS}/",
            VERB,
            flow,
        ) from failed

    path = directory / artifact_name(version)
    write_json(
        path,
        envelope(
            TAGS,
            {
                "implementation": tagging.implementation,
                "models": list(tagging.models),
                "pinned": tagging.pinned,
                "prompt": constant_record(TAG_PROMPT),
            },
            {"tags": list(tagging.tags)},
        ),
    )
    return path


__all__: Sequence[str] = (
    "SEPARATOR",
    "TAGGER_OPTIONS",
    "TAGGER_REMEDY",
    "TAG_PROMPT",
    "FakeTagger",
    "OllamaTagger",
    "Tagger",
    "Tagging",
    "caption_tags",
    "caption_wd14",
)
