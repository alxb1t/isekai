"""A flow: a directory whose manifest declares, and never computes.

**Declaration, not computation, is the whole point.** A manifest with no derived
value is fully checkable without executing anything, which is what lets a broken
flow be caught by the suite rather than after a pod boot and several minutes of
waiting. That property is also the standing argument against anyone later adding
a computed field.

**A flow is immutable.** Changing a dial, a prompt fragment or any other declared
value does not edit this flow -- it creates a new identifier. A tuned dial is not
a variant of a flow, it is an untested flow, and an output's path identifies a
configuration only if a flow identifier never silently means something else. The
suite holds each tracked manifest against a committed digest, the same mechanism
this repository already uses to pin its committed prompts.

**The dials are the measured ones, not the graph file's.** `summon-v1`'s graph
carries a guidance scale of 7 and an identity control strength of 0.5, and every
measured run overrode them to 5 and 0.8. A manifest transcribed from the graph
would ship a configuration nothing measured (design.md D12), so the two disagree
on purpose and a test says so.

Stdlib only.
"""

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from isekai.comfy_types import Workflow
from isekai.refusal import Refusal

FLOWS_DIR = Path(__file__).resolve().parent.parent / "flows"

# The only flow-manifest version this build reads.
FLOW_SCHEMA_VERSION = 1

# The manifest's name inside a flow's directory, and every key a flow must
# declare. Checked as a set, so a flow missing one is named rather than crashing
# three frames later on a `KeyError`.
MANIFEST_NAME = "flow.json"
REQUIRED = (
    "flow",
    "schema_version",
    "inputs",
    "schema",
    "vocabulary",
    "graph",
    "prompt",
    "dials",
    "nodes",
    "models",
)
REQUIRED_PROMPT = ("prefix", "trailer", "negative", "separator")


# --- what a sheet declares ----------------------------------------------------

# The schema lives here, beside the flow, because a flow is what decides which
# schema a run is sorted against: `flow.json` names the schema document, and both
# ends of prompt assembly -- the field order and the prompt fragments -- are read
# off this module. Held in `sheet.py` it made the sorter a dependency of the
# renderer, which is the edge this move removes (design.md D6). Only the type's
# home moves; what a schema *is* is unchanged.


@dataclass(frozen=True)
class Field:
    """One field of a sheet: its name, whether it is scored, and its suffix."""

    name: str
    scored: bool
    suffix: str | None


@dataclass(frozen=True)
class Schema:
    """A versioned field list, in prompt order, and the vocabulary it assumes."""

    name: str
    version: int
    vocabulary: Mapping[str, str]
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
            f"{name!r} is not a field of schema {self.name} v{self.version}; "
            f"this schema declares {', '.join(self.names)} -- correct the field "
            "name, or write a new schema version that declares it"
        )


@dataclass(frozen=True)
class Flow:
    """One flow, loaded: what it needs, what it renders, and the dials it runs at."""

    id: str
    path: Path
    inputs: tuple[str, ...]
    schema: str
    vocabulary: Mapping[str, str]
    prompt: Mapping[str, str]
    dials: Mapping[str, Any]
    nodes: Mapping[str, str]
    models: tuple[str, ...]
    graph_path: Path

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
    """
    directory = flow_path(flow, flows_dir)
    manifest = directory / MANIFEST_NAME
    if not manifest.is_file():
        raise Refusal(
            f"flow {flow} has no {MANIFEST_NAME}; the flows this build carries "
            f"are {', '.join(tracked_flows(flows_dir)) or '(none)'}"
        )
    document: Any = json.loads(manifest.read_text())

    missing = [key for key in REQUIRED if key not in document]
    if missing:
        raise Refusal(
            f"{flow}/{MANIFEST_NAME} declares no {', '.join(missing)}; add the "
            "field to the manifest, which declares every value and derives none"
        )
    declared = document["schema_version"]
    if declared != FLOW_SCHEMA_VERSION:
        raise Refusal(
            f"{flow}/{MANIFEST_NAME}: declares manifest version {declared!r} and "
            f"this build reads version {FLOW_SCHEMA_VERSION}; upgrade isekai, or "
            "point at a flow this build reads"
        )
    absent = [key for key in REQUIRED_PROMPT if key not in document["prompt"]]
    if absent:
        raise Refusal(
            f"{flow}/{MANIFEST_NAME}: `prompt` declares no {', '.join(absent)}; "
            "every fragment a prompt is assembled from is stated by the flow"
        )
    if document["flow"] != flow:
        raise Refusal(
            f"{flow}/{MANIFEST_NAME} calls itself {document['flow']!r}; a flow's "
            "identifier is its directory name, and the two must agree"
        )
    graph_path = directory / str(document["graph"])
    if not graph_path.is_file():
        raise Refusal(
            f"{flow}/{MANIFEST_NAME} names graph {document['graph']!r}, which is "
            f"not in {flow}/; add the graph, or point the manifest at one that is"
        )
    return Flow(
        id=flow,
        path=directory,
        inputs=tuple(str(name) for name in document["inputs"]),
        schema=str(document["schema"]),
        vocabulary=dict(document["vocabulary"]),
        prompt={key: str(value) for key, value in document["prompt"].items()},
        dials=dict(document["dials"]),
        nodes={key: str(value) for key, value in document["nodes"].items()},
        models=tuple(str(dest) for dest in document["models"]),
        graph_path=graph_path,
    )


def manifest_digest(flow: str, flows_dir: Path = FLOWS_DIR) -> str:
    """Return the digest of a flow's manifest and graph, as bytes on disk.

    Both, because either one changes what the flow renders. This is what the
    suite pins by equality: a changed dial fails the gate naming the flow, rather
    than quietly making an existing identifier mean something else.
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
