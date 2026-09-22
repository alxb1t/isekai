"""The shared vocabulary: graph aliases, the transport seam, and how it fails."""

from typing import Any, Protocol

from isekai.foundation.refusal import Refusal

Workflow = dict[str, Any]
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
