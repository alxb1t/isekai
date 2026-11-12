"""An edit: a directory whose manifest declares, and never computes.

An edit takes a finished render and a hand-made composite and writes a new image
beside its source. It is no flow: a flow takes one photograph and gates on a sheet.

**An edit is flat, and its files are the manifest and its graph.** The manifest
names neither, and both sit directly in the directory, because the digest that
freezes an edit covers regular files only (D51). The suite holds each tracked
directory against a committed digest, as it does a flow's.

Stdlib only.
"""

import json
from collections.abc import Mapping
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any

from isekai.foundation.flow import Workflow, manifest_digest
from isekai.foundation.refusal import Refusal

EDITS_DIR = Path(__file__).resolve().parent.parent.parent / "edits"

# The only version of `edit.json`'s own format this build reads.
MANIFEST_VERSION = 1

MANIFEST_NAME = "edit.json"
GRAPH_NAME = "graph.json"

# Every key an edit must declare, checked as a set so one missing is named.
REQUIRED = (
    "edit",
    "manifest_version",
    "prompt",
    "dials",
    "nodes",
    "checkpoint",
    "controlnet",
    "union_type",
)
REQUIRED_PROMPT = ("positive", "negative")

# Every top-level key this build reads: exactly `REQUIRED`, there is no optional key.
KNOWN = REQUIRED

REQUIRED_DIALS = (
    "denoise",
    "strength",
    "lines",
    "start_percent",
    "end_percent",
    "long_side",
    "margin",
    "min_aspect",
    "max_upscale",
    "grow",
    "feather",
    "ink_threshold",
    "control_gain",
    "lit_floor",
    "rounding",
    "steps",
    "cfg",
    "sampler_name",
    "scheduler",
    "clip_skip",
)

# The roles the sampling patches, each named by its id in the edit's graph.
REQUIRED_NODES = (
    "checkpoint",
    "clip_skip",
    "positive",
    "negative",
    "image",
    "mask",
    "control",
    "controlnet",
    "union",
    "apply",
    "sampler",
)


@dataclass(frozen=True)
class Edit:
    """One edit, loaded: the words, dials and files its sampling is made of."""

    id: str
    path: Path
    prompt: Mapping[str, str]
    dials: Mapping[str, Any]
    nodes: Mapping[str, str]
    checkpoint: str
    controlnet: str
    union_type: str

    @property
    def graph_path(self) -> Path:
        """Return this edit's graph file. Fixed name; the manifest declares none."""
        return self.path / GRAPH_NAME

    def graph(self) -> Workflow:
        """Return a fresh copy of this edit's graph, parsed."""
        parsed: Any = json.loads(self.graph_path.read_text())
        return parsed

    @cached_property
    def digest(self) -> str:
        """Return `edit_digest` for this edit, read once per loaded edit."""
        return edit_digest(self.id, self.path.parent)

    def node(self, role: str) -> str:
        """Return the graph id the manifest gives a role, or refuse naming the role."""
        if role not in self.nodes:
            raise Refusal(
                f"edit {self.id} declares no node for {role!r}; add it to "
                f"{MANIFEST_NAME}'s `nodes`, under a new edit identifier"
            )
        return self.nodes[role]


def edit_path(edit: str, edits_dir: Path = EDITS_DIR) -> Path:
    """Return the directory an edit lives in."""
    return edits_dir / edit


def tracked_edits(edits_dir: Path = EDITS_DIR) -> list[str]:
    """Return every edit this repository tracks, by identifier."""
    if not edits_dir.is_dir():
        return []
    return sorted(
        path.name for path in edits_dir.iterdir() if (path / MANIFEST_NAME).is_file()
    )


def edit_digest(edit: str, edits_dir: Path = EDITS_DIR) -> str:
    """Return the digest of every file in an edit's directory, as bytes on disk."""
    return manifest_digest(edit, edits_dir)


def load_edit(edit: str, edits_dir: Path = EDITS_DIR) -> Edit:
    """Read one edit's manifest, refusing naming the field that is wrong.

    Nothing here is derived at load time: every value returned is a value the
    manifest states. A key this build does not read is refused, not ignored, and
    the allowlist runs before the missing-key check so a misspelling names the key
    the operator wrote.
    """
    directory = edit_path(edit, edits_dir)
    manifest = directory / MANIFEST_NAME
    if not manifest.is_file():
        raise Refusal(
            f"edit {edit} has no {MANIFEST_NAME}; the edits this build carries "
            f"are {', '.join(tracked_edits(edits_dir)) or '(none)'}"
        )
    document: Any = json.loads(manifest.read_text())

    if "manifest_version" not in document:
        raise Refusal(
            f"{edit}/{MANIFEST_NAME} declares no manifest_version; add the field "
            "to the manifest, which declares every value and derives none"
        )
    declared = document["manifest_version"]
    if declared != MANIFEST_VERSION:
        raise Refusal(
            f"{edit}/{MANIFEST_NAME}: declares manifest version {declared!r} and "
            f"this build reads version {MANIFEST_VERSION}; upgrade isekai, or "
            "point at an edit this build reads"
        )
    unknown = [key for key in document if key not in KNOWN]
    if unknown:
        raise Refusal(
            f"{edit}/{MANIFEST_NAME} declares {', '.join(sorted(unknown))}, which "
            f"this build does not read; the keys it reads are "
            f"{', '.join(KNOWN)} -- correct the spelling, or point at an edit "
            "this build reads"
        )
    missing = [key for key in REQUIRED if key not in document]
    if missing:
        raise Refusal(
            f"{edit}/{MANIFEST_NAME} declares no {', '.join(missing)}; add the "
            "field to the manifest, which declares every value and derives none"
        )
    if document["edit"] != edit:
        raise Refusal(
            f"{edit}/{MANIFEST_NAME} calls itself {document['edit']!r}; an edit's "
            "identifier is its directory name, and the two must agree"
        )
    for key, required, held in (
        ("prompt", REQUIRED_PROMPT, document["prompt"]),
        ("dials", REQUIRED_DIALS, document["dials"]),
        ("nodes", REQUIRED_NODES, document["nodes"]),
    ):
        absent = [name for name in required if name not in held]
        if absent:
            raise Refusal(
                f"{edit}/{MANIFEST_NAME}: `{key}` declares no {', '.join(absent)}; "
                "the sampling reads each of them, so one that is absent would "
                "fail on a rented machine rather than here"
            )
    if not (directory / GRAPH_NAME).is_file():
        raise Refusal(
            f"{edit}/ has no {GRAPH_NAME}; an edit is {MANIFEST_NAME} and "
            f"{GRAPH_NAME}, flat in one directory -- add the file, or point at "
            "an edit that is complete"
        )
    committed: Any = json.loads((directory / GRAPH_NAME).read_text())
    dangling = sorted(
        f"{role} -> {node}"
        for role, node in document["nodes"].items()
        if str(node) not in committed
    )
    if dangling:
        raise Refusal(
            f"{edit}/{MANIFEST_NAME}: `nodes` names {', '.join(dangling)}, and "
            f"{GRAPH_NAME} carries no such node; the manifest names every node "
            "the sampling edits, by role, so correct the id -- under a new edit "
            "identifier"
        )
    return Edit(
        id=edit,
        path=directory,
        prompt={key: str(value) for key, value in document["prompt"].items()},
        dials=dict(document["dials"]),
        nodes={key: str(value) for key, value in document["nodes"].items()},
        checkpoint=str(document["checkpoint"]),
        controlnet=str(document["controlnet"]),
        union_type=str(document["union_type"]),
    )
