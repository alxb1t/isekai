from collections.abc import Callable
from typing import Any, Protocol

Workflow = dict[str, Any]
Image = dict[str, str]
Injector = Callable[[Workflow, str, str], None]


class ComfyTransport(Protocol):
    """The transport seam as a type: anything with these four methods can drive `run`."""

    def upload_image(self, path: str) -> str: ...
    def submit(self, workflow: Workflow) -> str: ...
    def history(self, prompt_id: str) -> dict[str, Any]: ...
    def view(self, image: Image) -> bytes: ...
