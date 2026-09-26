"""The ComfyUI transport's front door: the seam, the client, and how it fails.

Import from here. `multipart.py` is private to the package; only its own test
reaches inside.
"""

from isekai.boundary.comfy.client import ComfyClient
from isekai.boundary.comfy.contract import ComfyTransport, Image, TransportFailure

__all__ = ["ComfyClient", "ComfyTransport", "Image", "TransportFailure"]
