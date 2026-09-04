from typing import Any

from isekai.comfy_types import Image, Workflow


class FakeComfyClient:
    """In-memory stand-in for ComfyClient: records calls, replays canned responses.

    Structurally satisfies ComfyTransport, so pipeline.run can't tell it from the
    real client. No network, no GPU.
    """

    def __init__(
        self,
        pending_polls: int = 0,
        image: Image | None = None,
        view_bytes: bytes = b"\x89PNG\r\n",
    ) -> None:
        self.pending_polls = pending_polls
        self.image: Image = image or {
            "filename": "out.png",
            "subfolder": "",
            "type": "output",
        }
        self.view_bytes = view_bytes
        self.prompt_id = "pid-123"
        # recorded calls, for assertions
        self.uploaded: str | None = None
        self.submitted_workflow: Workflow | None = None
        # every submission, in order — `submitted_workflow` keeps only the last,
        # which cannot see a multi-variation run's earlier workflows.
        self.submissions: list[Workflow] = []
        self.history_calls = 0
        self.viewed: Image | None = None

    def upload_image(self, path: str) -> str:
        self.uploaded = path
        return "uploaded.png"

    def submit(self, workflow: Workflow) -> str:
        self.submitted_workflow = workflow
        self.submissions.append(workflow)
        return self.prompt_id

    def history(self, prompt_id: str) -> dict[str, Any]:
        self.history_calls += 1
        if self.history_calls <= self.pending_polls:
            return {}
        return {prompt_id: {"outputs": {"SaveImage": {"images": [self.image]}}}}

    def view(self, image: Image) -> bytes:
        self.viewed = image
        return self.view_bytes


class FakeFetcher:
    """In-memory stand-in for the pre-flight seam: canned answers, no network.

    Structurally satisfies `Fetcher`, so `decide` cannot tell it from the real
    thing. `published` maps a source URL to the digest that source claims it
    would serve; a URL absent from the map publishes nothing, which is the case
    where pre-flight has to degrade to post-download verification rather than to
    trust (design.md D10).
    """

    def __init__(self, published: dict[str, str] | None = None) -> None:
        self.published = published or {}
        # every URL asked about, in order — so a test can assert that a source
        # rejected before transfer was still pre-flighted.
        self.asked: list[str] = []

    def published_digest(self, url: str) -> str | None:
        self.asked.append(url)
        return self.published.get(url)
