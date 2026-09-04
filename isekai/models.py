"""The model registry: a name from `--model` to the workflow and adapters it owns."""

import sys
from dataclasses import dataclass

from isekai.comfy_types import Injector, Mutator
from isekai.mutate import mutate
from isekai.workflow import inject


@dataclass(frozen=True)
class Model:
    """One selectable pipeline: the graph it runs and the adapters that drive it."""

    workflow_path: str
    inject: Injector
    mutate: Mutator | None = None


MODELS: dict[str, Model] = {
    "pipeline": Model("workflows/pipeline.json", inject, mutate=mutate),
}


def get_model(name: str) -> Model:
    """Resolve a `--model` name, exiting with the valid choices if it is unknown."""
    if name not in MODELS:
        sys.exit(f"unknown model {name!r}; choose from {', '.join(MODELS)}")

    return MODELS[name]
