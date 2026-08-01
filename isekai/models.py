import sys
from dataclasses import dataclass

from isekai.comfy_types import Injector, Mutator
from isekai.mutate import mutate
from isekai.workflow import inject_animagine, inject_qwen


@dataclass(frozen=True)
class Model:
    workflow_path: str
    inject: Injector
    mutate: Mutator | None = None


MODELS: dict[str, Model] = {
    "qwen": Model("workflows/qwen-image-edit.json", inject_qwen),
    "animagine": Model("workflows/animagine-instantid.json", inject_animagine),
    "animagine-i2i": Model(
        "workflows/animagine-i2i.json", inject_animagine, mutate=mutate
    ),
}


def get_model(name: str) -> Model:
    if name not in MODELS:
        sys.exit(f"unknown model ${name!r}; choose from {', '.join(MODELS)}")

    return MODELS[name]
