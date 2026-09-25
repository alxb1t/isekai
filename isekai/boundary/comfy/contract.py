"""The transport seam: its Protocol, the image it returns, and how it fails."""

from typing import Any, Protocol

from isekai.foundation.flow import Workflow
from isekai.foundation.refusal import Refusal

Image = dict[str, str]


class Unreachable(Refusal):
    """The endpoint could not be reached at all, so nothing about it is settled.

    A `Refusal` like any other to everything that only reports one -- the CLI
    prints its string and exits 1 unchanged. It exists so that the one caller
    that writes an error record can tell *this graph is wrong* from *the tunnel
    is closed*: the first fails identically forever and the second is a pod that
    went away, and `check_budget` short-circuits a `permanent` record for good.
    Recording a closed tunnel as permanent made the operator's remedy deleting a
    file by hand.

    **A subclass, and not the `Kind` this repository otherwise classifies
    with.** `ollama.OllamaFailure` carries a `Kind` field precisely so a
    boundary need not invent a vocabulary, and that is the better pattern where
    it fits. It does not fit here: this one has to stay a `Refusal`, because
    `main()` prints it and exits 1 and every other caller must be unchanged --
    and a `Kind` cannot be attached to `Refusal` itself, since `refusal.py`
    imports nothing by design and `Kind` lives in `run.py`, which imports
    `refusal.py`. A `kind` attribute read through `getattr` with a default
    would be the same conditional, spelled less honestly. If a second transient
    transport failure ever appears -- a queue eviction, a 5xx from the proxy --
    that is the point to add the field rather than a second subclass.
    """


class ComfyTransport(Protocol):
    """The transport seam as a type.

    Anything with these four methods can drive `generate.render` -- which is how
    the suite substitutes an in-memory fake for the network.
    """

    def upload_image(self, path: str) -> str:
        """Upload a local image and return the name ComfyUI stored it under."""
        ...

    def submit(self, workflow: Workflow) -> str:
        """Queue a workflow and return its prompt_id."""
        ...

    def history(self, prompt_id: str) -> dict[str, Any]:
        """Return the /history record for prompt_id, empty until the run finishes."""
        ...

    def view(self, image: Image) -> bytes:
        """Download one generated image, given its {filename, subfolder, type} dict."""
        ...
