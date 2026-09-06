"""The probe's input recipe -- operator tooling, held to the suite's bar anyway."""

import pytest

from probe.build_inputs import segments


@pytest.mark.spec_exempt(
    "structural: probe/ is operator tooling and states no product requirement"
)
def test_a_jpeg_ending_on_a_lone_marker_byte_is_walked_without_crashing() -> None:
    # The walk read `jpeg[i + 1]` having tested only `i < len(jpeg)`, so a file
    # whose last byte is 0xFF indexed past its end. There is no segment there to
    # report -- a marker needs its code byte -- so the walk simply stops.
    assert list(segments(b"\xff\xd8\xff")) == []
