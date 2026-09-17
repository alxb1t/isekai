"""The shared vocabulary: graph aliases and the transport seam."""

from typing import Any, Protocol

Workflow = dict[str, Any]
Image = dict[str, str]


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
