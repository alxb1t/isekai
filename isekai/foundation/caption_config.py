"""The caption config: the model the reader runs and the briefing it reads under.

`config/caption.json` names both, and the briefing sits beside it. The config is
the library's, not a flow's: every flow is read by one model under one briefing,
so a flow's manifest declares neither (D14).

Stdlib only.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from isekai.foundation.refusal import Refusal

CAPTION_CONFIG_PATH = (
    Path(__file__).resolve().parent.parent.parent / "config" / "caption.json"
)

KEYS = ("briefing", "model")


@dataclass(frozen=True)
class CaptionConfig:
    """The model the reader and the hosted tagger run, and the reader's briefing."""

    model: str
    briefing_path: Path


def load_caption_config(path: Path = CAPTION_CONFIG_PATH) -> CaptionConfig:
    """Return the caption config, refusing naming the key or the file that is wrong."""
    document: Any = json.loads(path.read_text())
    unknown = sorted(key for key in document if key not in KEYS)
    if unknown:
        raise Refusal(
            f"{path.name} declares {', '.join(unknown)}, which this build does not "
            f"read; the keys it reads are {', '.join(KEYS)} -- correct the spelling"
        )
    missing = [key for key in KEYS if key not in document]
    if missing:
        raise Refusal(
            f"{path.name} declares no {', '.join(missing)}; add the key to {path.name}"
        )
    # The value's repr, never `str()`: `{"model": null}` would name an alias
    # called "None" and refuse at first call instead of here.
    model = document["model"]
    if not isinstance(model, str) or not model.strip():
        raise Refusal(
            f"{path.name}: `model` declares {model!r}; it names the one model the "
            "reader and the hosted tagger run, as a non-empty string"
        )
    briefing = document["briefing"]
    if not isinstance(briefing, str) or Path(briefing).name != briefing:
        raise Refusal(
            f"{path.name}: `briefing` declares {briefing!r}; it names a file "
            f"beside {path.name}, by its bare name"
        )
    briefing_path = path.parent / briefing
    if not briefing_path.is_file():
        raise Refusal(
            f"{path.name}: `briefing` names {briefing}, and there is no such file "
            f"beside {path.name}; add it, or name the briefing that is there"
        )
    return CaptionConfig(model=model, briefing_path=briefing_path)
