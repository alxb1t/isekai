"""The transport seam: its Protocol, the image it returns, and how it fails."""

from typing import Any, Protocol

from isekai.foundation.flow import Workflow
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import Kind

Image = dict[str, str]


class TransportFailure(Refusal):
    """The endpoint failed a request, and `kind` says whether trying again may help.

    A `Refusal` like any other to everything that only reports one -- the CLI
    prints its string and exits 1 unchanged. The one caller that writes an error
    record reads `kind`: a graph the endpoint rejects fails identically forever,
    while a closed tunnel or a server error is over once the pod is back, and
    `check_budget` short-circuits a `permanent` record for good.

    A subclass carrying a `Kind`, because `Kind` cannot be attached to `Refusal`
    itself: `refusal.py` imports nothing by design, and `Kind` lives in `run.py`.
    """

    def __init__(self, kind: Kind, message: str) -> None:
        """Carry the kind an error record is written with, beside the message."""
        super().__init__(message)
        self.kind: Kind = kind


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
