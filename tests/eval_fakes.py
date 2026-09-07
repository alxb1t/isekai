"""In-memory stand-ins for every model the evaluator loads.

The same trick `FakeComfyClient` plays on the transport, for the same reason: the
scorer's rules -- the canvas, the guard, the refusals, what each axis may claim --
are what this version is actually about, and they are testable without a
2.3 GiB stack. These fakes are what let those tests run in CI with the `[eval]`
extra absent.

Every fake records what it was asked, because several of the rules are about
*which image* a model was handed. "The render is never parsed" is not observable
from a return value.
"""

from isekai.ciede2000 import Lab
from isekai.evaluate import Box, Canvas, FaceReading, Keypoint, Region


class FakeDetector:
    """Returns a canned face reading per image path, and records every call."""

    def __init__(self, readings: dict[str, FaceReading]) -> None:
        self.readings = readings
        self.asked: list[str] = []

    def read_face(self, image_path: str) -> FaceReading:
        self.asked.append(image_path)
        return self.readings.get(image_path, FaceReading(box=None))


class FakeEncoder:
    """Returns a canned embedding per image path, and records every call."""

    def __init__(self, vectors: dict[str, tuple[float, ...] | None]) -> None:
        self.vectors = vectors
        self.asked: list[tuple[str, Box]] = []

    def embed(self, image_path: str, box: Box) -> tuple[float, ...] | None:
        self.asked.append((image_path, box))
        return self.vectors.get(image_path)


class FakeParser:
    """Returns canned regions, and records which image it was asked to parse.

    `asked` is the whole point of this fake: the rule it exists to prove is that
    a render is never handed to a parser, and that is a property of the calls
    rather than of the result.
    """

    def __init__(self, regions: dict[str, Region]) -> None:
        self.regions = regions
        self.asked: list[tuple[str, Canvas]] = []

    def parse(self, image_path: str, canvas: Canvas) -> dict[str, Region]:
        self.asked.append((image_path, canvas))
        return dict(self.regions)


class FakeSampler:
    """Reads a canned colour out of a region, and records the image and region."""

    def __init__(self, colours: dict[str, Lab | None]) -> None:
        self.colours = colours
        self.asked: list[tuple[str, Region]] = []

    def dominant_colour(self, image_path: str, region: Region) -> Lab | None:
        self.asked.append((image_path, region))
        return self.colours.get(image_path)


class FakePoseReader:
    """Returns canned keypoints per image path, with None meaning "read nothing"."""

    def __init__(self, points: dict[str, tuple[Keypoint, ...] | None]) -> None:
        self.points = points
        self.asked: list[str] = []

    def keypoints(self, image_path: str) -> tuple[Keypoint, ...] | None:
        self.asked.append(image_path)
        return self.points.get(image_path)
