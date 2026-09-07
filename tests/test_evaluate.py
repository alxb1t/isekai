import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from isekai.comfy_types import Workflow
from isekai.evaluate import (
    AUTHORITATIVE_GUARD_METHOD,
    CLAIMS,
    MIN_KEYPOINT_CONFIDENCE,
    MIN_REGION_AREA,
    Axis,
    Canvas,
    FaceReading,
    Keypoint,
    Refusal,
    Region,
    Report,
    canvas_for,
    check_render_matches,
    pck,
    pod_image_of,
    refuse_embedding_axes_across_bases,
    run_guard,
    score_render,
    table,
    usable_regions,
)
from isekai.pipeline import run
from isekai.workflow import working_resolution
from tests.eval_fakes import (
    FakeDetector,
    FakeEncoder,
    FakeParser,
    FakePoseReader,
    FakeSampler,
)
from tests.fakes import FakeComfyClient
from tests.images import jpeg_bytes, jpeg_with_header, png_bytes

# A face filling a plausible slice of the canvas, and the same face nudged by a
# few pixels -- close enough that both guard methods locate it.
PHOTO_FACE = FaceReading(box=(400.0, 200.0, 700.0, 560.0))
RENDER_FACE = FaceReading(box=(408.0, 206.0, 706.0, 564.0))

# Far enough away that neither method can call it the same face.
MOVED_FACE = FaceReading(box=(20.0, 20.0, 320.0, 380.0))

BROWN_HAIR = Region(name="hair", area=0.08, colour=(30.0, 8.0, 12.0))


def _canvas_images(tmp_path: Path) -> tuple[str, str]:
    """Write a photo and a render that agree on the canvas the injector derives."""
    photo = tmp_path / "photo.jpg"
    photo.write_bytes(jpeg_bytes(1600, 1200))
    width, height = working_resolution(1600, 1200)
    render = tmp_path / "0.png"
    render.write_bytes(png_bytes(width, height))
    return str(photo), str(render)


def _score(
    tmp_path: Path,
    *,
    photo_face: FaceReading = PHOTO_FACE,
    render_face: FaceReading = RENDER_FACE,
    regions: dict[str, Region] | None = None,
    photo_base: str | None = "wai.safetensors",
    render_base: str | None = "wai.safetensors",
    points: dict[str, tuple[Keypoint, ...] | None] | None = None,
    render_colour: tuple[float, float, float] | None = (34.0, 9.0, 13.0),
    guard_method: str = "iou",
) -> tuple[Report, dict[str, object]]:
    """Score one render against fakes, returning the report and the fakes used."""
    photo, render = _canvas_images(tmp_path)
    default_points = (
        Keypoint(500.0, 300.0, 0.9),
        Keypoint(600.0, 400.0, 0.9),
        Keypoint(550.0, 700.0, 0.9),
    )
    detector = FakeDetector({photo: photo_face, render: render_face})
    style = FakeEncoder({photo: (1.0, 0.0, 0.0), render: (0.8, 0.6, 0.0)})
    arcface = FakeEncoder({photo: (0.0, 1.0, 0.0), render: (0.0, 0.9, 0.1)})
    parser = FakeParser(regions if regions is not None else {"hair": BROWN_HAIR})
    sampler = FakeSampler({render: render_colour})
    pose = FakePoseReader(
        points
        if points is not None
        else {photo: default_points, render: default_points}
    )
    report = score_render(
        photo,
        render,
        detector=detector,
        style_encoder=style,
        recognizer=arcface,
        parser=parser,
        sampler=sampler,
        pose=pose,
        subject="subject-1",
        photo_base=photo_base,
        render_base=render_base,
        image="0.png",
        guard_method=guard_method,
    )
    fakes: dict[str, object] = {
        "photo": photo,
        "render": render,
        "detector": detector,
        "style": style,
        "arcface": arcface,
        "parser": parser,
        "sampler": sampler,
        "pose": pose,
    }
    return report, fakes


def _axis(report: Report, name: str) -> Axis:
    """Return the named axis, failing loudly if the report does not carry it."""
    for axis in report.axes:
        if axis.name == name:
            return axis
    raise AssertionError(f"{name} is not in {[a.name for a in report.axes]}")


# --- the canvas -------------------------------------------------------------


@pytest.mark.spec("evaluation:canvas:resolution-comes-from-the-injector")
def test_the_canvas_is_the_target_the_injector_computes(tmp_path: Path) -> None:
    photo = tmp_path / "photo.jpg"
    photo.write_bytes(jpeg_bytes(1600, 1200))

    assert canvas_for(str(photo)).size == working_resolution(1600, 1200)


@pytest.mark.spec("evaluation:canvas:resolution-comes-from-the-injector")
@pytest.mark.parametrize(
    ("width", "height"), [(1600, 1200), (1200, 1600), (900, 900), (3000, 1000)]
)
def test_the_canvas_never_states_a_resolution_rule_of_its_own(
    tmp_path: Path, width: int, height: int
) -> None:
    # Asserted across shapes rather than one, because "it agrees on the one case
    # I tried" is what a second, subtly different implementation also does.
    photo = tmp_path / "photo.jpg"
    photo.write_bytes(jpeg_bytes(width, height))

    assert canvas_for(str(photo)).size == working_resolution(width, height)


@pytest.mark.spec("evaluation:canvas:orientation-is-applied-before-parsing")
def test_a_transposing_orientation_is_honoured_in_the_derived_canvas(
    tmp_path: Path,
) -> None:
    # The loader transposes the pixels for a transposing EXIF orientation, so the
    # canvas has to be derived from the transposed dimensions. Derived otherwise,
    # every region would land rotated against the render's own pixels.
    upright = tmp_path / "upright.jpg"
    upright.write_bytes(jpeg_bytes(1600, 1200))
    turned = tmp_path / "turned.jpg"
    turned.write_bytes(jpeg_with_header(1600, 1200, orientation=6))

    assert canvas_for(str(turned)).size == working_resolution(1200, 1600)
    assert canvas_for(str(turned)).size != canvas_for(str(upright)).size


@pytest.mark.spec("evaluation:canvas:mismatched-render-is-refused")
def test_a_render_whose_dimensions_disagree_is_refused_naming_both_sizes(
    tmp_path: Path,
) -> None:
    photo = tmp_path / "photo.jpg"
    photo.write_bytes(jpeg_bytes(1600, 1200))
    wrong = tmp_path / "wrong.png"
    wrong.write_bytes(png_bytes(512, 512))

    with pytest.raises(Refusal) as refused:
        check_render_matches(canvas_for(str(photo)), str(wrong))

    message = str(refused.value)
    assert "512x512" in message
    assert "x".join(str(v) for v in working_resolution(1600, 1200)) in message


@pytest.mark.spec("evaluation:canvas:mismatched-render-is-refused")
def test_no_axis_is_scored_against_a_canvas_the_two_images_do_not_share(
    tmp_path: Path,
) -> None:
    photo = tmp_path / "photo.jpg"
    photo.write_bytes(jpeg_bytes(1600, 1200))
    wrong = tmp_path / "wrong.png"
    wrong.write_bytes(png_bytes(512, 512))
    detector = FakeDetector({})

    with pytest.raises(Refusal):
        score_render(
            str(photo),
            str(wrong),
            detector=detector,
            style_encoder=FakeEncoder({}),
            recognizer=FakeEncoder({}),
            parser=FakeParser({}),
            sampler=FakeSampler({}),
            pose=FakePoseReader({}),
            subject="s",
            photo_base="wai",
            render_base="wai",
        )

    # The canvas is settled before any model is asked anything at all.
    assert detector.asked == []


# --- the regions ------------------------------------------------------------


@pytest.mark.spec("evaluation:regions:render-is-never-parsed")
def test_every_region_applied_to_a_render_was_derived_from_the_photograph(
    tmp_path: Path,
) -> None:
    _, fakes = _score(tmp_path)
    parser = fakes["parser"]
    assert isinstance(parser, FakeParser)

    assert [asked for asked, _ in parser.asked] == [fakes["photo"]]
    assert fakes["render"] not in [asked for asked, _ in parser.asked]


@pytest.mark.spec("evaluation:regions:render-is-never-parsed")
def test_the_parser_is_asked_at_the_canvas_the_injector_derived(
    tmp_path: Path,
) -> None:
    _, fakes = _score(tmp_path)
    parser = fakes["parser"]
    assert isinstance(parser, FakeParser)

    assert parser.asked[0][1] == Canvas(*working_resolution(1600, 1200))


@pytest.mark.spec("evaluation:regions:render-is-never-parsed")
def test_the_render_is_sampled_inside_the_photographs_own_mask(
    tmp_path: Path,
) -> None:
    # Sampling a given mask is not parsing: the region still came from the
    # photograph, and this is what applies it to the render unchanged.
    _, fakes = _score(tmp_path)
    sampler = fakes["sampler"]
    assert isinstance(sampler, FakeSampler)

    assert [asked for asked, _ in sampler.asked] == [fakes["render"]]
    assert [region for _, region in sampler.asked] == [BROWN_HAIR]


@pytest.mark.spec("evaluation:regions:tiny-region-is-refused")
def test_a_region_under_the_area_floor_refuses_naming_itself_and_its_area(
    tmp_path: Path,
) -> None:
    sliver = Region(name="hair", area=MIN_REGION_AREA / 10, colour=(30.0, 8.0, 12.0))
    usable, refused = usable_regions({"hair": sliver})

    assert usable == {}
    assert len(refused) == 1
    assert "hair" in (refused[0].refused or "")
    assert f"{sliver.area:.4f}" in (refused[0].refused or "")
    assert refused[0].value is None


@pytest.mark.spec("evaluation:regions:tiny-region-is-refused")
def test_a_tiny_region_reports_no_number_derived_from_too_few_pixels(
    tmp_path: Path,
) -> None:
    sliver = Region(name="hair", area=MIN_REGION_AREA / 10, colour=(30.0, 8.0, 12.0))
    report, _ = _score(tmp_path, regions={"hair": sliver})

    colour = _axis(report, "hair_colour_delta_e")
    assert colour.value is None
    assert colour.refused is not None


# --- the guard --------------------------------------------------------------


@pytest.mark.spec("evaluation:guard:method-is-reported")
def test_the_guard_names_the_method_it_used_and_the_agreement_it_measured() -> None:
    result = run_guard(PHOTO_FACE, RENDER_FACE, method="iou")

    assert result.method == "iou"
    assert result.iou is not None
    assert result.centroid_offset is not None
    assert "IoU" in result.detail
    assert "centroid" in result.detail
    assert "iou" in result.detail


@pytest.mark.spec("evaluation:guard:method-is-reported")
def test_the_guard_measures_both_methods_whichever_one_is_authoritative() -> None:
    # Both numbers are computed on every run at no extra cost, which is what lets
    # phase 8 choose between them on real renders rather than on an argument.
    by_iou = run_guard(PHOTO_FACE, RENDER_FACE, method="iou")
    by_centroid = run_guard(PHOTO_FACE, RENDER_FACE, method="centroid")

    assert by_iou.iou == by_centroid.iou
    assert by_iou.centroid_offset == by_centroid.centroid_offset
    assert by_iou.method != by_centroid.method


@pytest.mark.spec("evaluation:guard:method-is-reported")
def test_the_report_carries_the_guards_measurement(tmp_path: Path) -> None:
    report, _ = _score(tmp_path)

    assert any(note.startswith("guard: ") for note in report.notes)


@pytest.mark.spec("evaluation:guard:failure-refuses-region-axes")
def test_a_failed_guard_refuses_every_region_axis_naming_the_guard(
    tmp_path: Path,
) -> None:
    report, _ = _score(tmp_path, render_face=MOVED_FACE)

    for name in ("face_styleid", "face_arcface", "hair_colour_delta_e"):
        axis = _axis(report, name)
        assert axis.value is None
        assert "guard" in (axis.refused or "")


@pytest.mark.spec("evaluation:guard:whole-image-axes-survive-a-refusal")
def test_an_axis_needing_no_region_still_reports_when_the_guard_fails(
    tmp_path: Path,
) -> None:
    report, _ = _score(tmp_path, render_face=MOVED_FACE)
    pose_axis = _axis(report, "pose_pck")

    assert pose_axis.refused is None
    assert pose_axis.value is not None


@pytest.mark.spec("evaluation:guard:whole-image-axes-survive-a-refusal")
def test_a_guard_failure_does_not_deprive_the_operator_of_valid_measurements(
    tmp_path: Path,
) -> None:
    held, _ = _score(tmp_path)
    failed, _ = _score(tmp_path, render_face=MOVED_FACE)

    assert _axis(failed, "pose_pck").value == _axis(held, "pose_pck").value


# --- absence ----------------------------------------------------------------


@pytest.mark.spec("evaluation:absence:no-face-in-the-photo-is-reported")
def test_no_face_in_the_photograph_is_reported_as_absence_not_a_low_score(
    tmp_path: Path,
) -> None:
    report, _ = _score(tmp_path, photo_face=FaceReading(box=None))

    assert report.face_detected is False
    for name in ("face_styleid", "face_arcface"):
        assert _axis(report, name).value is None
        refused = _axis(report, name).refused or ""
        assert "no face was found in the photograph" in refused


@pytest.mark.spec("evaluation:absence:no-face-in-the-render-is-reported")
def test_no_face_in_the_render_is_reported_as_absence_not_a_low_score(
    tmp_path: Path,
) -> None:
    report, _ = _score(tmp_path, render_face=FaceReading(box=None))

    assert report.render_face_detected is False
    assert report.face_detected is True
    for name in ("face_styleid", "face_arcface"):
        assert _axis(report, name).value is None
        assert "no face was found in the render" in (_axis(report, name).refused or "")


@pytest.mark.spec("evaluation:absence:no-face-in-the-render-is-reported")
def test_absence_is_a_distinct_field_and_never_a_zero(tmp_path: Path) -> None:
    absent, _ = _score(tmp_path, render_face=FaceReading(box=None))
    record = absent.as_record()

    assert record["render_face_detected"] is False
    for axis in record["axes"]:  # ty: ignore[not-iterable]
        assert axis["value"] != 0.0


# --- what each axis may claim -----------------------------------------------


@pytest.mark.spec("evaluation:claims:axes-are-tagged-absolute-or-relative")
def test_every_axis_in_a_report_is_tagged_absolute_or_relative(
    tmp_path: Path,
) -> None:
    report, _ = _score(tmp_path)

    assert report.axes
    for axis in report.axes:
        assert axis.kind in ("absolute", "relative")


@pytest.mark.spec("evaluation:claims:axes-are-tagged-absolute-or-relative")
def test_the_embedding_axes_are_relative_and_the_rest_absolute(
    tmp_path: Path,
) -> None:
    # The distinction is the whole of design.md D1: a colour distance and a
    # keypoint agreement mean the same thing in both domains; a cosine across the
    # photograph-to-drawing gap does not.
    report, _ = _score(tmp_path)

    assert _axis(report, "face_styleid").kind == "relative"
    assert _axis(report, "face_arcface").kind == "relative"
    assert _axis(report, "pose_pck").kind == "absolute"
    assert _axis(report, "hair_colour_delta_e").kind == "absolute"


@pytest.mark.spec("evaluation:claims:no-axis-isolates-one-dial")
def test_the_report_states_that_the_photo_reaches_the_render_by_several_paths(
    tmp_path: Path,
) -> None:
    report, _ = _score(tmp_path)
    claims = " ".join(str(c) for c in report.as_record()["claims"])  # ty: ignore[not-iterable]

    assert "several paths at once" in claims
    assert "isolates a single dial" in claims
    assert "attributable to the pipeline" in claims


@pytest.mark.spec("evaluation:claims:shared-recognizer-is-a-sanity-channel")
def test_the_generators_own_recognizer_is_marked_as_falsifying_only(
    tmp_path: Path,
) -> None:
    report, _ = _score(tmp_path)

    assert _axis(report, "face_arcface").falsifies_only is True
    assert _axis(report, "face_styleid").falsifies_only is False


@pytest.mark.spec("evaluation:claims:shared-recognizer-is-a-sanity-channel")
def test_the_report_states_that_a_high_value_from_it_asserts_nothing(
    tmp_path: Path,
) -> None:
    report, _ = _score(tmp_path)
    claims = " ".join(str(c) for c in report.as_record()["claims"])  # ty: ignore[not-iterable]

    assert "A high value from it asserts nothing" in claims
    assert "only a low value is a finding" in claims


# --- across bases -----------------------------------------------------------


@pytest.mark.spec("evaluation:cross-base:embedding-axes-are-refused")
def test_differing_bases_refuse_each_embedding_axis_naming_the_reason(
    tmp_path: Path,
) -> None:
    report, _ = _score(tmp_path, render_base="animagine.safetensors")

    for name in ("face_styleid", "face_arcface"):
        axis = _axis(report, name)
        assert axis.value is None
        assert "different bases" in (axis.refused or "")


@pytest.mark.spec("evaluation:cross-base:absolute-axes-still-report")
def test_the_colour_area_and_keypoint_axes_still_report_across_bases(
    tmp_path: Path,
) -> None:
    report, _ = _score(tmp_path, render_base="animagine.safetensors")

    for name in ("pose_pck", "hair_colour_delta_e", "hair_mask_area"):
        axis = _axis(report, name)
        assert axis.refused is None
        assert axis.value is not None


@pytest.mark.spec("evaluation:cross-base:missing-base-is-not-assumed-equal")
def test_a_run_recording_no_base_is_treated_as_unknown_rather_than_matching(
    tmp_path: Path,
) -> None:
    # The case this exists for: a manifest predating the provenance keys records
    # no base at all, and assuming it matches would compare across bases silently.
    assert refuse_embedding_axes_across_bases(None, None) is not None
    assert refuse_embedding_axes_across_bases("wai", None) is not None
    assert refuse_embedding_axes_across_bases(None, "wai") is not None
    assert refuse_embedding_axes_across_bases("wai", "wai") is None


@pytest.mark.spec("evaluation:cross-base:missing-base-is-not-assumed-equal")
def test_the_embedding_axes_refuse_when_a_run_records_no_base(
    tmp_path: Path,
) -> None:
    report, _ = _score(tmp_path, render_base=None)

    for name in ("face_styleid", "face_arcface"):
        assert "unknown rather than matching" in (_axis(report, name).refused or "")


# --- the report -------------------------------------------------------------


@pytest.mark.spec("evaluation:report:one-record-per-render")
def test_each_render_gets_its_own_machine_readable_record_naming_it(
    tmp_path: Path,
) -> None:
    report, fakes = _score(tmp_path)
    record = report.as_record()

    assert record["render"] == fakes["render"]
    # Machine-readable means it survives a round trip, not merely that it is a
    # dict in this process.
    assert json.loads(json.dumps(record))["render"] == fakes["render"]


@pytest.mark.spec("evaluation:report:table-states-column-directions")
def test_the_table_states_for_every_column_which_direction_is_closer(
    tmp_path: Path,
) -> None:
    report, _ = _score(tmp_path)
    rendered = table([report], "20260906T101500Z", "wai.safetensors", "isekai:v0.11-rc")

    for axis in report.axes:
        assert f"{axis.name}: {axis.kind}, {axis.direction}" in rendered


@pytest.mark.spec("evaluation:report:no-combined-score")
def test_the_report_contains_no_average_no_verdict_and_no_percentage(
    tmp_path: Path,
) -> None:
    report, _ = _score(tmp_path)
    rendered = table([report], "20260906T101500Z", "wai.safetensors", "isekai:v0.11-rc")
    record = json.dumps(report.as_record())

    # Scanned over the table's DATA rows only. The prose below them says the
    # words "verdict" and "score" precisely in order to disclaim them, so a
    # substring scan of the whole document would fail on the disclaimer.
    data = rendered.split("note:")[0]
    for forbidden in ("overall", "average", "combined", "verdict", "%"):
        assert forbidden not in data.lower()

    # And no axis is named as a rollup, in the table or in the record.
    for axis in report.axes:
        assert not any(
            word in axis.name for word in ("overall", "average", "combined", "score")
        )
    assert '"claims"' in record
    assert "no combined score, no verdict and no threshold" in rendered


@pytest.mark.spec("evaluation:report:no-combined-score")
def test_the_axes_are_never_rolled_up_into_one_number(tmp_path: Path) -> None:
    report, _ = _score(tmp_path)
    record = report.as_record()
    axes = record["axes"]
    assert isinstance(axes, list)

    # Four axes reported separately, and nothing beside them that summarises them.
    assert len(axes) >= 4
    assert set(record) == {
        "render",
        "subject",
        "base",
        "image",
        "face_detected",
        "render_face_detected",
        "axes",
        "notes",
        "claims",
    }


@pytest.mark.spec("evaluation:report:names-its-run")
def test_the_report_names_the_subject_the_base_and_the_render(
    tmp_path: Path,
) -> None:
    report, _ = _score(tmp_path)
    record = report.as_record()

    assert record["subject"] == "subject-1"
    assert record["base"] == "wai.safetensors"
    # The record's `image` is the render's own file name -- the same key
    # `renders[]` uses in `run.json`, and what the labels correlate by. The
    # container image is the run's, not the render's, and is named on the table.
    assert record["image"] == "0.png"


@pytest.mark.spec("evaluation:report:names-its-run")
def test_the_table_names_the_run_the_base_and_the_image_it_was_produced_on(
    tmp_path: Path,
) -> None:
    report, _ = _score(tmp_path)
    rendered = table([report], "20260906T101500Z", "wai.safetensors", "isekai:v0.11-rc")

    assert "run: 20260906T101500Z" in rendered
    assert "base: wai.safetensors" in rendered
    assert "image: isekai:v0.11-rc" in rendered


@pytest.mark.spec("evaluation:report:names-its-run")
def test_the_table_names_the_image_the_pipeline_itself_recorded(
    workflow: Workflow, tmp_path: Path, photo: str
) -> None:
    # Driven off a manifest the pipeline actually wrote, never a literal handed
    # to the formatter: the placeholder this closes was invisible for exactly
    # that reason -- the formatter was proven while the key it reads was not.
    run_dir = tmp_path / "run"
    run(
        FakeComfyClient(),
        workflow,
        photo,
        run_dir,
        variations=1,
        seed=7,
        pod_image="ghcr.io/owner/isekai:v0.11-rc",
    )
    manifest = json.loads((run_dir / "run.json").read_text())
    report, _ = _score(tmp_path)

    rendered = table([report], run_dir.name, manifest["base"], pod_image_of(manifest))

    assert "image: ghcr.io/owner/isekai:v0.11-rc" in rendered


@pytest.mark.spec("evaluation:report:names-its-run")
def test_the_table_says_unrecorded_when_the_run_never_learned_its_image(
    workflow: Workflow, tmp_path: Path, photo: str
) -> None:
    run_dir = tmp_path / "run"
    run(FakeComfyClient(), workflow, photo, run_dir, variations=1, seed=7)
    manifest = json.loads((run_dir / "run.json").read_text())
    report, _ = _score(tmp_path)

    rendered = table([report], run_dir.name, manifest["base"], pod_image_of(manifest))

    assert "image: unrecorded" in rendered


@pytest.mark.spec("evaluation:report:names-its-run")
def test_a_table_from_a_run_that_recorded_no_base_says_so_rather_than_omitting_it(
    tmp_path: Path,
) -> None:
    report, _ = _score(tmp_path, render_base=None)
    rendered = table([report], "20260906T101500Z", None, "isekai:v0.11-rc")

    assert "base: unrecorded" in rendered


# --- the pose axis's own arithmetic -----------------------------------------


@pytest.mark.spec("evaluation:guard:whole-image-axes-survive-a-refusal")
def test_low_confidence_keypoints_are_dropped_and_counted_not_scored() -> None:
    photo = (
        Keypoint(100.0, 100.0, 0.9),
        Keypoint(200.0, 200.0, MIN_KEYPOINT_CONFIDENCE - 0.01),
    )
    render = (
        Keypoint(101.0, 101.0, 0.9),
        Keypoint(900.0, 900.0, 0.9),
    )
    value, used, dropped = pck(photo, render, (0.0, 0.0, 1000.0, 1000.0))

    # The dropped pair is wildly wrong. Scored, it would halve the value; dropped,
    # it is counted and reported instead.
    assert (used, dropped) == (1, 1)
    assert value == 1.0


@pytest.mark.spec("evaluation:guard:whole-image-axes-survive-a-refusal")
def test_a_pose_axis_that_read_nothing_reports_absence_rather_than_a_zero(
    tmp_path: Path,
) -> None:
    photo, render = _canvas_images(tmp_path)
    report, _ = _score(tmp_path, points={photo: None, render: None})
    axis = _axis(report, "pose_pck")

    assert axis.value is None
    assert "its own absence, not a zero" in (axis.refused or "")


@pytest.mark.spec("evaluation:guard:whole-image-axes-survive-a-refusal")
def test_every_keypoint_dropped_is_absence_rather_than_a_zero(
    tmp_path: Path,
) -> None:
    photo, render = _canvas_images(tmp_path)
    faint = (Keypoint(100.0, 100.0, 0.01), Keypoint(200.0, 200.0, 0.01))
    report, _ = _score(tmp_path, points={photo: faint, render: faint})
    axis = _axis(report, "pose_pck")

    assert axis.value is None
    assert "none was scored at a guessed coordinate" in (axis.refused or "")


# --- the licence control ----------------------------------------------------


@pytest.mark.spec_exempt(
    "structural: a licence constraint, enforced as a test because a review "
    "nobody runs is not a control"
)
def test_ultralytics_is_absent_from_the_projects_declared_dependencies() -> None:
    pyproject = (Path(__file__).resolve().parent.parent / "pyproject.toml").read_text()

    assert "ultralytics" not in pyproject.lower().replace("`ultralytics`", "").replace(
        "ultralytics`", ""
    )


@pytest.mark.spec_exempt(
    "structural: a licence constraint, enforced as a test because a review "
    "nobody runs is not a control"
)
def test_ultralytics_is_absent_from_the_resolved_lockfile() -> None:
    lock = (Path(__file__).resolve().parent.parent / "uv.lock").read_text()

    # AGPL-3.0 code linked into an Apache-2.0 public repository would, on the
    # standard reading, force the whole work to AGPL. The detector's weights are
    # loaded through onnxruntime instead; loading weights is not linking code.
    assert 'name = "ultralytics"' not in lock


@pytest.mark.spec_exempt(
    "structural: a licence constraint, enforced as a test because a review "
    "nobody runs is not a control"
)
def test_ultralytics_is_absent_from_the_scorers_import_graph() -> None:
    import isekai.evaluate

    source = Path(isekai.evaluate.__file__).read_text()

    assert "import ultralytics" not in source
    assert "from ultralytics" not in source


@pytest.mark.spec_exempt("structural: the claims are printed, not remembered")
def test_the_claims_a_report_prints_are_the_ones_the_design_requires() -> None:
    joined = " ".join(CLAIMS)

    assert "no verdict" in joined
    assert "no threshold" in joined
    assert "not a percentage" in joined


@pytest.mark.spec_exempt(
    "structural: holds `convert.py`'s stdlib-only runtime, which is a repo "
    "invariant rather than a scenario about evaluation"
)
def test_convert_imports_with_site_packages_off_the_path() -> None:
    # The mechanism is `-S`, chosen over an AST walk against
    # `sys.stdlib_module_names` because it was verified to work here: inside this
    # uv venv, `-S` leaves no site-packages on `sys.path` at all, so a
    # third-party import in the runtime's graph raises rather than resolving.
    # The AST fallback design.md D12 names was not needed.
    root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [sys.executable, "-S", "-c", "import convert"],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(root)},
        cwd=root,
    )

    assert result.returncode == 0, result.stderr


@pytest.mark.spec_exempt(
    "structural: the guard above proves nothing unless -S really refuses"
)
def test_the_stdlib_guard_would_actually_catch_a_third_party_import() -> None:
    # A check that cannot fail is not a check. If `-S` ever stopped removing
    # site-packages, the test above would pass for the wrong reason and an
    # accidental wheel in `convert.py`'s graph would ship silently.
    root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [sys.executable, "-S", "-c", "import pytest"],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(root)},
        cwd=root,
    )

    assert result.returncode != 0
    assert "No module named 'pytest'" in result.stderr


# --- phase 8: the guard's method, settled by measurement and pinned here -------


@pytest.mark.spec("evaluation:guard:method-is-reported")
def test_the_authoritative_guard_method_is_the_one_phase_eight_measured() -> None:
    # Pinned the way the graph's dials are pinned: both methods held on all
    # thirty baseline renders, IoU was chosen because it constrains size as well
    # as position, and changing that is a deliberate test edit rather than a
    # quiet one. `baseline/README.md` records the measurement.
    assert AUTHORITATIVE_GUARD_METHOD == "iou"


@pytest.mark.spec("evaluation:guard:method-is-reported")
def test_the_report_uses_the_authoritative_method_by_default(
    tmp_path: Path,
) -> None:
    report, _ = _score(tmp_path)
    guard_note = next(n for n in report.notes if n.startswith("guard: "))

    assert f"authoritative method: {AUTHORITATIVE_GUARD_METHOD}" in guard_note


@pytest.mark.spec("evaluation:guard:method-is-reported")
def test_the_method_not_chosen_is_still_measured_and_reported(
    tmp_path: Path,
) -> None:
    # The centroid method stays computed on every run, so the day the two
    # disagree is a visible event rather than a silent one.
    report, _ = _score(tmp_path)
    guard_note = next(n for n in report.notes if n.startswith("guard: "))

    assert "IoU" in guard_note
    assert "face-box centroid offset" in guard_note


@pytest.mark.spec("evaluation:guard:method-is-reported")
def test_size_is_what_the_two_guard_methods_disagree_about(
    tmp_path: Path,
) -> None:
    # The reason IoU ships, made falsifiable: a face centred correctly but at the
    # wrong scale passes the centroid test and fails IoU. If that ever stopped
    # being true, the justification recorded beside the constant would be wrong.
    photo = FaceReading(box=(400.0, 200.0, 700.0, 560.0))
    # Same centre, three times the size.
    scaled = FaceReading(box=(250.0, 20.0, 850.0, 740.0))

    assert run_guard(photo, scaled, method="centroid").located is True
    assert run_guard(photo, scaled, method="iou").located is False
