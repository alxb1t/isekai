"""A flow: a directory whose manifest declares, and never computes.

**Declaration, not computation, is the whole point.** A manifest with no derived
value is fully checkable without executing anything, which is what lets a broken
flow be caught by the suite rather than after a pod boot and several minutes of
waiting. That property is also the standing argument against anyone later adding
a computed field.

**A flow is flat, and its files are the manifest and its siblings.** The manifest
names none of them -- a key that can only ever hold one value is not a
declaration -- and they all sit directly in the directory, because the digest that
freezes a flow covers regular files only. The rule names its files rather than
tallying them: the count has changed once already, and a rule carrying a numeral
is a rule that goes stale (design.md D10).

**A flow is immutable.** Changing a dial, a prompt fragment, the graph, the schema
or the briefing does not edit this flow -- it creates a new identifier. A tuned
dial is not a variant of a flow, it is an untested flow, and an output's path
identifies a configuration only if a flow identifier never silently means
something else. The suite holds each tracked directory against a committed digest,
the same mechanism this repository already uses to pin its committed prompts.

**The dials are the measured ones, not the graph file's.** `summon-anime-wai`'s
graph carries a guidance scale of 7 and an identity control strength of 0.5, and every
measured run overrode them to 5 and 0.8. A manifest transcribed from the graph
would ship a configuration nothing measured (design.md D12), so the two disagree
on purpose and a test says so.

Stdlib only.
"""

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any

from isekai.boundary.comfy_types import Workflow
from isekai.foundation.refusal import Refusal

FLOWS_DIR = Path(__file__).resolve().parent.parent.parent / "flows"

# The only version of `flow.json`'s own format this build reads. It is the
# manifest's format, not the schema document's -- the schema carries no version
# at all, because inside a frozen directory a version protects nothing.
MANIFEST_VERSION = 3

# The files a flow is, none of them named by the manifest: a key that can only
# ever hold one value is not a declaration. They sit directly in the directory
# because `manifest_digest` covers regular files only, so a nested layout would
# leave the schema and the briefing outside the freeze while the gate stayed
# green (design.md D1, D3).
#
# **Named, not counted.** `sheet.briefing.md` was the fifth and has had no reader
# since v0.21, so the rule's numeral has now been wrong once; a rule that tallies
# is a rule that goes stale, and `tests/test_flow.py` asserts the length here so
# a sixth sibling cannot be added silently (design.md D10).
MANIFEST_NAME = "flow.json"
GRAPH_NAME = "graph.json"
SCHEMA_NAME = "schema.json"
CAPTION_BRIEFING_NAME = "caption.briefing.md"
SIBLINGS = (GRAPH_NAME, SCHEMA_NAME, CAPTION_BRIEFING_NAME)

# Every key a flow must declare. Checked as a set, so a flow missing one is named
# rather than crashing three frames later on a `KeyError`.
REQUIRED = (
    "flow",
    "manifest_version",
    "inputs",
    "vocabulary",
    "prompt",
    "dials",
    "nodes",
    "models",
    "model",
)
REQUIRED_PROMPT = ("prefix", "trailer", "negative", "separator")

# Every top-level key this build knows, and a manifest carrying any other is
# refused naming it -- `load_flow` is where that reason lives.
#
# **It is exactly `REQUIRED`: there is no optional key.** `hosted` was the one,
# and it is gone. That block named a distinction -- a model reached over a
# network to a third party, as against one over a socket to this machine -- and
# only the second survives, so a block whose name no longer distinguishes
# anything, holding a single key, is not a declaration (design.md D1).
KNOWN = REQUIRED

# What `model` names, and why it is not `reader`. **One alias answers both
# prompts stage (1) sends**: `wiring.py` builds the reader and the hosted tagger
# from this single key, and `TAG_PROMPT` is unframed for exactly that reason --
# two calls to the same alias must not arrive framed differently. A key named
# `reader` would name it after one of its two callers; `model` names what it is.
#
# Deliberately not `models`, which is required, holds the render weights a rented
# GPU loads and pins every one by digest: one names a file on disk, the other a
# name a host resolves at call time, and **nothing verifies the bytes behind
# this one** (design.md D1).

# The node roles every image flow has, checked at load the way the prompt's
# fragments already are. Every other role is optional and guarded at the patch
# site: a photograph, an identity adapter and a pose preprocessor are absent from
# a sheet-only flow, and a hires resize and a hires sampler from any ordinary
# cheaper one. Unchecked, a flow declaring fewer passed the whole gate and died on
# a rented GPU -- after the photograph had already been uploaded (design.md D9).
REQUIRED_NODES = ("positive", "negative", "latent", "sampler")

# Every role that names a transfer as well as a patch, and so has to be declared
# on both sides of the manifest. The photograph is uploaded because `inputs`
# names it and read because `nodes` names it, and those two gates live in
# different modules -- nothing holds them in agreement but this check. Declared
# under `nodes` alone, the flow uploads nothing and the load node keeps the
# filename committed inside `graph.json`: a paid render of whoever that file
# names, with the whole gate green. Declared under `inputs` alone, the
# photograph is transferred and read nowhere.
TRANSFERRED_INPUTS = ("photo",)

# The form every flow this build carries produces. It is answered by the flow
# rather than written into the resume predicate, so "which of my outputs are
# already produced" is a question asked of the flow and not of an extension
# somebody typed. A flow whose output is not a still image is unscheduled, and
# this is the one line it changes when it arrives (design.md D11).
OUTPUT_SUFFIX = ".png"


# --- what a sheet declares ----------------------------------------------------

# The schema's type lives here, beside the flow, because a flow is what decides
# which schema a run is sorted against: the document sits in the flow's own
# directory, and both ends of prompt assembly -- the field order and the prompt
# fragments -- are read off this module. Held in `sheet.py` it made the sorter a
# dependency of the renderer, which is the edge that move removed (design.md D6).


# What the API enforces on a tool input schema's property keys. Held beside the
# reader that checks it, because a name that fails it fails every call rather
# than one.
IDENTIFIER_SAFE = re.compile(r"^[a-zA-Z0-9_.-]{1,64}$")


@dataclass(frozen=True)
class Field:
    """One field of a sheet: its name, whether it is scored, and its suffix."""

    name: str
    scored: bool
    suffix: str | None


@dataclass(frozen=True)
class Schema:
    """A field list, in prompt order. No version, and no vocabulary of its own.

    No version, because inside a frozen flow directory one protects nothing: the
    flow's digest proves the field list byte for byte, and a changed field list is
    a new flow rather than a new schema version. No vocabulary, because the flow
    declares it -- where two things could own a declaration the flow owns it.
    """

    name: str
    fields: tuple[Field, ...]

    @property
    def names(self) -> tuple[str, ...]:
        """Return the field names, in the one order a prompt is assembled in."""
        return tuple(field.name for field in self.fields)

    @property
    def scored(self) -> tuple[str, ...]:
        """Return the names of the fields a measurement is taken over."""
        return tuple(field.name for field in self.fields if field.scored)

    def field(self, name: str) -> Field:
        """Return the named field, or refuse naming what the schema does declare."""
        for field in self.fields:
            if field.name == name:
                return field
        raise Refusal(
            f"{name!r} is not a field of schema {self.name}; this schema declares "
            f"{', '.join(self.names)} -- correct the field name, or write a flow "
            "whose schema declares it"
        )


def load_schema(path: Path) -> Schema:
    """Read a schema document out of a flow's own directory.

    There is no version to check and no migration ladder: the flow's digest proves
    the field list byte for byte, so a changed field list is a new flow rather than
    a new schema version. It lives here, beside `Schema` itself, because a schema
    belongs to a flow -- there is no tracked schema document outside a flow
    directory for a stage to default to.
    """
    document: Any = json.loads(path.read_text())
    fields = tuple(
        Field(str(entry["name"]), bool(entry["scored"]), entry["suffix"])
        for entry in document["fields"]
    )
    unsafe = [field.name for field in fields if not IDENTIFIER_SAFE.match(field.name)]
    if unsafe:
        raise Refusal(
            f"{path.name}: {', '.join(unsafe)} cannot be a structured-output "
            "property key, which must match "
            f"{IDENTIFIER_SAFE.pattern}; rename the field in the schema document "
            "and in the briefing that names it"
        )
    return Schema(name=str(document["name"]), fields=fields)


@dataclass(frozen=True)
class Model:
    """One model artifact a flow's render is pinned to: where it goes, and its bytes.

    The digest is here as well as in `scripts/models.json` because a destination
    path alone does not pin bytes: re-pinning a checkpoint would make an existing
    flow identifier render differently with the gate green. The duplication is
    only safe because a test holds the two equal, naming the flow (design.md D4).
    """

    dest: str
    sha256: str


@dataclass(frozen=True)
class Flow:
    """One flow, loaded: what it needs, what it renders, and the dials it runs at."""

    id: str
    path: Path
    inputs: tuple[str, ...]
    vocabulary: Mapping[str, str]
    prompt: Mapping[str, str]
    dials: Mapping[str, Any]
    nodes: Mapping[str, str]
    models: tuple[Model, ...]
    model: str

    @property
    def graph_path(self) -> Path:
        """Return this flow's graph file. Fixed name; the manifest declares none."""
        return self.path / GRAPH_NAME

    @cached_property
    def schema(self) -> Schema:
        """Return this flow's schema, parsed. Read once per loaded flow.

        Cached for the same reason the flows themselves are loaded once per
        invocation: the document cannot change while a command runs, and a batch
        would otherwise re-read and re-parse it per photograph.
        """
        return load_schema(self.schema_path)

    @property
    def output_suffix(self) -> str:
        """Return the form this flow's renders take, as a filename suffix."""
        return OUTPUT_SUFFIX

    @property
    def schema_path(self) -> Path:
        """Return this flow's schema document."""
        return self.path / SCHEMA_NAME

    @property
    def caption_briefing_path(self) -> Path:
        """Return the standing instructions this flow reads a photograph under."""
        return self.path / CAPTION_BRIEFING_NAME

    def graph(self) -> Workflow:
        """Return a fresh copy of this flow's graph, parsed."""
        parsed: Any = json.loads(self.graph_path.read_text())
        return parsed

    def graph_digest(self) -> str:
        """Return the digest of the graph as it sits on disk, before injection."""
        return hashlib.sha256(self.graph_path.read_bytes()).hexdigest()

    def node(self, role: str) -> str:
        """Return the graph id the manifest gives a role, or refuse naming the role."""
        if role not in self.nodes:
            raise Refusal(
                f"flow {self.id} declares no node for {role!r}; add it to "
                f"{MANIFEST_NAME}'s `nodes`, under a new flow identifier"
            )
        return self.nodes[role]


def flow_path(flow: str, flows_dir: Path = FLOWS_DIR) -> Path:
    """Return the directory a flow lives in."""
    return flows_dir / flow


def tracked_flows(flows_dir: Path = FLOWS_DIR) -> list[str]:
    """Return every flow this repository tracks, by identifier."""
    if not flows_dir.is_dir():
        return []
    return sorted(
        path.name for path in flows_dir.iterdir() if (path / MANIFEST_NAME).is_file()
    )


def load_flow(flow: str, flows_dir: Path = FLOWS_DIR) -> Flow:
    """Read one flow's manifest, refusing naming the field that is wrong.

    Nothing here is derived at load time: every value returned is a value the
    manifest states. The refusals are all shape, so a broken flow fails in the
    suite rather than on a rented machine.

    **A key this build does not read is refused too, not ignored**, and with
    every key now required the allowlist below is the whole of what closes a
    misspelling: `modl` is caught as an unknown key *and* as a missing one, in
    the same load, with no check written for it. That is what flattening `hosted`
    bought -- the block had no allowlist of its own, so `{"sortr": "x"}` inside it
    loaded clean (design.md D3).
    """
    directory = flow_path(flow, flows_dir)
    manifest = directory / MANIFEST_NAME
    if not manifest.is_file():
        raise Refusal(
            f"flow {flow} has no {MANIFEST_NAME}; the flows this build carries "
            f"are {', '.join(tracked_flows(flows_dir)) or '(none)'}"
        )
    document: Any = json.loads(manifest.read_text())

    # **The version is checked before any shape check, because it decides what
    # the other keys mean.** A version 2 manifest is a live input -- it declares
    # `hosted` and no `model` -- and under a shape-first order it is refused for a
    # misspelling it does not have, never reaching the one refusal that names the
    # real fix. Version, then the key set, then the values, then the files.
    if "manifest_version" not in document:
        raise Refusal(
            f"{flow}/{MANIFEST_NAME} declares no manifest_version; add the field "
            "to the manifest, which declares every value and derives none"
        )
    declared = document["manifest_version"]
    if declared != MANIFEST_VERSION:
        raise Refusal(
            f"{flow}/{MANIFEST_NAME}: declares manifest version {declared!r} and "
            f"this build reads version {MANIFEST_VERSION}; upgrade isekai, or "
            "point at a flow this build reads"
        )
    # **The allowlist runs before the missing-key check, and the order is the
    # message.** Every key is required, so a misspelling fails twice at once: the
    # key this build reads is absent, and one it does not read is present.
    # Reporting the absence first names `model` -- a key the operator did not
    # misspell -- and sends him to add a second one rather than to fix the one he
    # wrote.
    unknown = [key for key in document if key not in KNOWN]
    if unknown:
        raise Refusal(
            f"{flow}/{MANIFEST_NAME} declares {', '.join(sorted(unknown))}, which "
            f"this build does not read; the keys it reads are "
            f"{', '.join(KNOWN)} -- correct the spelling, or point at a flow this "
            "build reads"
        )
    missing = [key for key in REQUIRED if key not in document]
    if missing:
        raise Refusal(
            f"{flow}/{MANIFEST_NAME} declares no {', '.join(missing)}; add the "
            "field to the manifest, which declares every value and derives none"
        )
    absent = [key for key in REQUIRED_PROMPT if key not in document["prompt"]]
    if absent:
        raise Refusal(
            f"{flow}/{MANIFEST_NAME}: `prompt` declares no {', '.join(absent)}; "
            "every fragment a prompt is assembled from is stated by the flow"
        )
    # The value, not only its presence. A bare `str()` here would load
    # `{"model": null}` as the string `"None"` and send a run at an alias that
    # cannot exist, which is a refusal at first call with the manifest looking
    # correct on the way there (design.md D4).
    named = document["model"]
    if not isinstance(named, str) or not named.strip():
        raise Refusal(
            f"{flow}/{MANIFEST_NAME}: `model` declares {named!r}; a flow names "
            "the one model its first two stages run, as a non-empty string"
        )
    if document["flow"] != flow:
        raise Refusal(
            f"{flow}/{MANIFEST_NAME} calls itself {document['flow']!r}; a flow's "
            "identifier is its directory name, and the two must agree"
        )
    unnamed = [role for role in REQUIRED_NODES if role not in document["nodes"]]
    if unnamed:
        raise Refusal(
            f"{flow}/{MANIFEST_NAME}: `nodes` declares no {', '.join(unnamed)}; "
            "every flow patches those four, so one that names fewer would fail on "
            "a rented machine rather than here"
        )
    for role in TRANSFERRED_INPUTS:
        sides = [
            side
            for side in ("inputs", "nodes")
            if role not in document[side]  # `inputs` is a list, `nodes` a mapping
        ]
        if len(sides) == 1:
            raise Refusal(
                f"{flow}/{MANIFEST_NAME}: `{sides[0]}` declares no {role!r} and the "
                f"other half of the manifest does; a {role} is transferred because "
                "`inputs` names it and read because `nodes` names it, so declaring "
                "one side alone renders what the graph file itself names, or "
                f"transfers a {role} no node reads -- add {role!r} to "
                f"`{sides[0]}`, under a new flow identifier"
            )
    absent_files = [name for name in SIBLINGS if not (directory / name).is_file()]
    if absent_files:
        raise Refusal(
            f"{flow}/ has no {', '.join(absent_files)}; a flow is "
            f"{MANIFEST_NAME} and {', '.join(SIBLINGS)}, flat in one directory "
            "-- add the file, or point at a flow that is complete"
        )
    return Flow(
        id=flow,
        path=directory,
        inputs=tuple(str(name) for name in document["inputs"]),
        vocabulary=dict(document["vocabulary"]),
        prompt={key: str(value) for key, value in document["prompt"].items()},
        dials=dict(document["dials"]),
        nodes={key: str(value) for key, value in document["nodes"].items()},
        models=tuple(
            Model(str(entry["dest"]), str(entry["sha256"]))
            for entry in document["models"]
        ),
        model=named,
    )


def manifest_digest(flow: str, flows_dir: Path = FLOWS_DIR) -> str:
    """Return the digest of every file in a flow's directory, as bytes on disk.

    All of them, because each one changes what the flow renders: the briefing
    decides the caption, the caption decides the sheet, and the sheet decides the
    render. This is what the suite pins by equality -- a changed dial fails the
    gate naming the flow, rather than quietly making an existing identifier mean
    something else. It covers regular files only, which is why a flow is flat.
    """
    directory = flow_path(flow, flows_dir)
    digest = hashlib.sha256()
    for name in sorted(path.name for path in directory.iterdir() if path.is_file()):
        digest.update(name.encode())
        digest.update((directory / name).read_bytes())
    return digest.hexdigest()


def assemble(
    fields: Mapping[str, Sequence[str]],
    order: Sequence[str],
    flow: Flow,
) -> tuple[str, str]:
    """Return the positive and negative prompts, from the sheet and the flow only.

    Pure, local and free, so a malformed sheet costs nothing rather than a boot
    and several minutes. Nothing is taken from the graph's own committed strings:
    the flow states its prefix, its trailer and its negative, and the sheet states
    everything between them, in the order the schema declares.
    """
    separator = flow.prompt["separator"]
    tags = [tag for name in order for tag in fields.get(name, ())]
    positive = separator.join(
        part
        for part in (
            flow.prompt["prefix"],
            separator.join(tags),
            flow.prompt["trailer"],
        )
        if part
    )
    return positive, flow.prompt["negative"]
