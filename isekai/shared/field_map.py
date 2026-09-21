"""The authored tag-to-criterion table, read in two directions.

**One artifact, two indexes.** `scripts/field_map.json` assigns every tag it
carries a *primary* criterion -- the one field a router writes it to -- and any
further criteria it may be *browsed* under. The `tag -> field` direction fills a
sheet from a tagger's list with no language model in the path; the
`field -> tags` direction is what the cheatsheet shows. The second is **derived
here and never authored**, because two stored copies of one mapping is two
things to keep true.

**It is keyed by the vocabulary, not by a flow.** `twintails` answers *hair
silhouette* in every flow that declares that field, so the assignment belongs to
the tag list rather than to a schema -- and fixing one tag's criterion is one
edit here rather than three frozen flow directories.

**A tag has exactly one primary and may sit in several groups.** Single
assignment cannot serve both consumers: the operator's own approved sheets file
`navel` under clothes, pose *and* body shape, and `lips` is a declared field of
its own on `conjure-v1` while it is part of *expression* on `summon-v1`. Routing
needs one answer and browsing needs all of them (design.md D4).

**The loader raises all four checks, and the tests prove them.** The spec says
*loading it is refused*, so a check that lived only in a test would implement
nothing. Reading the tracked flows' schemas for the coverage check is not a new
layering edge -- `shared/fields.py` already imports `Schema` from
`foundation/flow.py`.

Stdlib only: `hashlib`, `json`, `pathlib`.
"""

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any

from isekai.foundation.flow import (
    FLOWS_DIR,
    SCHEMA_NAME,
    Schema,
    load_schema,
    tracked_flows,
)
from isekai.foundation.refusal import Refusal
from isekai.shared.vocabulary import Vocabulary

# Beside `scripts/vocabulary.json`, which the runtime already verifies against.
# The table is authored in this repository rather than fetched, so it is tracked
# and carries no digest of its own in a manifest -- its digest is of its bytes.
FIELD_MAP_PATH = (
    Path(__file__).resolve().parent.parent.parent / "scripts" / "field_map.json"
)

# The one command that writes the file, named here because a refusal that says a
# table is wrong without saying what regenerates it is half a refusal.
FIELD_MAP_REMEDY = "uv run python scripts/derive_field_map.py"


@dataclass(frozen=True)
class Group:
    """One criterion's tags: those it owns, and those it merely shows."""

    primary: tuple[str, ...]
    also: tuple[str, ...]

    @property
    def tags(self) -> tuple[str, ...]:
        """Return everything browsable under this criterion, owned tags first."""
        seen = dict.fromkeys(self.primary)
        seen.update(dict.fromkeys(self.also))
        return tuple(seen)


@dataclass(frozen=True)
class FieldMap:
    """The table, its pin, and the reverse index computed from it."""

    name: str
    revision: int
    digest: str
    fields: Mapping[str, Group]
    excluded: frozenset[str]

    @cached_property
    def _primary(self) -> Mapping[str, str]:
        """Return `tag -> field`, derived from the authored `field -> tags`."""
        return {
            tag: field for field, group in self.fields.items() for tag in group.primary
        }

    def primary_of(self, tag: str) -> str | None:
        """Return the one criterion `tag` routes to, or `None` if it routes nowhere.

        `None` rather than a refusal: a tag no criterion claims is dropped, and
        the excluded list is what says whether that absence was a decision.
        """
        return self._primary.get(tag)

    def group(self, field: str) -> tuple[str, ...]:
        """Return every tag browsable under `field`, refusing an unknown criterion."""
        if field not in self.fields:
            raise Refusal(
                f"{field!r} has no entry in {self.name}; the table declares "
                f"{', '.join(sorted(self.fields))} -- add an entry, empty if no "
                f"tag answers it, and re-run `{FIELD_MAP_REMEDY}`"
            )
        return self.fields[field].tags


def identity(field_map: FieldMap) -> dict[str, Any]:
    """Return the record a sheet carries to say which table routed it."""
    return {
        "name": field_map.name,
        "revision": field_map.revision,
        "sha256": field_map.digest,
    }


def declared_fields(flows_dir: Path | None = None) -> dict[str, tuple[str, ...]]:
    """Return each tracked flow's declared field names, read from its own schema.

    Read rather than declared as a constant: a hardcoded field list would stay
    green while a flow's schema moved underneath it, which is the whole failure
    the coverage check exists to catch.
    """
    root = FLOWS_DIR if flows_dir is None else flows_dir
    return {
        flow: load_schema(root / flow / SCHEMA_NAME).names
        for flow in tracked_flows(root)
    }


def parse(body: str, declared: Mapping[str, Sequence[str]]) -> FieldMap:
    """Build the table from its bytes, refusing every way it can be wrong but one.

    The vocabulary check is not here, because it needs an artifact this function
    is not given; `load` runs it. Everything decidable from the document alone --
    one primary per tag, disjointness from the excluded list, an entry per
    declared criterion -- is decided before a `FieldMap` exists, so no partial
    table is ever returned.
    """
    document: Any = json.loads(body)
    fields = {
        name: Group(
            primary=tuple(entry.get("primary", ())),
            also=tuple(entry.get("also", ())),
        )
        for name, entry in document["fields"].items()
    }
    excluded = frozenset(document.get("excluded", ()))
    name = str(document["name"])

    owners: dict[str, list[str]] = {}
    for field, group in fields.items():
        for tag in group.primary:
            owners.setdefault(tag, []).append(field)
    shared = sorted(tag for tag, claims in owners.items() if len(claims) > 1)
    if shared:
        listed = ", ".join(f"{tag!r} in {', '.join(owners[tag])}" for tag in shared)
        raise Refusal(
            f"{name}: {listed} -- a tag has exactly one primary criterion, "
            "because that is the one a router writes it to; keep the primary in "
            "the criterion it answers and list the others under `also`"
        )
    browsable = {tag for group in fields.values() for tag in group.tags}
    both = sorted(excluded & browsable)
    if both:
        raise Refusal(
            f"{name}: {', '.join(repr(tag) for tag in both)} is in the excluded "
            "list and in a criterion's group; the excluded list says no criterion "
            "can hold a tag, so one entry contradicts the other -- delete the "
            "one that is wrong"
        )

    absent = sorted(
        (field, flow)
        for flow, names in declared.items()
        for field in names
        if field not in fields
    )
    if absent:
        listed = ", ".join(f"{field!r} declared by {flow}" for field, flow in absent)
        raise Refusal(
            f"{name}: {listed} has no entry; every criterion a tracked flow "
            "declares carries one, empty if no tag in the vocabulary answers it "
            "-- an absent entry and an empty one are not the same statement"
        )

    return FieldMap(
        name=name,
        revision=int(document["revision"]),
        digest=hashlib.sha256(body.encode()).hexdigest(),
        fields=fields,
        excluded=excluded,
    )


def load(
    vocabulary: Vocabulary | None = None,
    path: Path = FIELD_MAP_PATH,
    declared: Mapping[str, Sequence[str]] | None = None,
) -> FieldMap:
    """Read the authored table and hold it against the pinned vocabulary.

    An authored artifact held against nothing rots in the worst direction: a tag
    that no longer exists routes nothing and shows nothing, and both failures are
    silent. The vocabulary is already provisioned by digest, so the check is free.
    """
    if vocabulary is None:
        from isekai.shared.vocabulary import load as load_vocabulary

        vocabulary = load_vocabulary()
    body = path.read_text()
    field_map = parse(body, declared_fields() if declared is None else declared)

    outside = sorted(
        {
            tag
            for group in field_map.fields.values()
            for tag in group.tags
            if tag not in vocabulary
        }
        | {tag for tag in field_map.excluded if tag not in vocabulary}
    )
    if outside:
        listed = ", ".join(repr(tag) for tag in outside)
        raise Refusal(
            f"{field_map.name}: {listed} is not in {vocabulary.name}'s prediction "
            "set, so it can never be routed to a field or shown as a candidate; "
            f"delete the entry, or re-run `{FIELD_MAP_REMEDY}` against the "
            "vocabulary the flows pin"
        )
    return field_map


def route(
    tags: Sequence[str], field_map: FieldMap, schema: Schema
) -> dict[str, list[str]]:
    """Place each tag in its primary criterion, dropping what the flow does not ask.

    **It is a dictionary lookup and it reaches nothing.** No model, no network, no
    free-text cascade -- the tagger's output layer *is* the vocabulary, so the
    tags arrive canonical and nothing has to be completed, corrected or
    substituted on the way. That property is what allows the sheet's author to
    change at all.

    Dropping by declared field is what lets one table serve every flow: a
    criterion five of twenty-one tags answer exists whether the acting flow asked
    for it or not, and a tag routed to a criterion the flow does not declare has
    nowhere legal to go. The tagger's order survives inside each criterion because
    it is the operator's deletion aid -- a Danbooru hierarchy arrives
    general-form-first, and the general forms are what he deletes.
    """
    routed: dict[str, list[str]] = {name: [] for name in schema.names}
    for tag in tags:
        field = field_map.primary_of(tag)
        if field in routed and tag not in routed[field]:
            routed[field].append(tag)
    return routed
