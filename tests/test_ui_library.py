"""The library and the hub, read from folders with no server involved."""

import json
import os
import struct
import zlib
from pathlib import Path

import pytest
from PIL import Image

from isekai.foundation.artifacts import DRAFT_FILE, read
from isekai.foundation.flow import FLOWS_DIR, load_flow
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import OUTPUTS, REVIEW, Run, approval_of, open_run
from isekai.interface.ui import library
from isekai.interface.ui.library import Cell, FlowCount, Rendered
from isekai.pipeline.review import approve, review, save_draft
from isekai.shared.vocabulary import Vocabulary
from tests.conftest import tree
from tests.images import jpeg_bytes, jpeg_with_header, photo_jpeg
from tests.stages import sheet, write_wd14

REPO = Path(__file__).resolve().parent.parent
SUMMON = "summon-anime-wai"
CONJURE = "conjure-anime-wai"
CONTROL = "control-anime-wai"
# The suite's own copy of the flows `config/ui.json` offers.
OFFERED = (SUMMON, CONJURE)


def _batch(lib: Path, name: str, *sources: str) -> Path:
    """Write a batch folder holding one distinct photograph per source name."""
    folder = lib / name
    (folder / "sources").mkdir(parents=True)
    for index, source in enumerate(sources):
        body = jpeg_bytes(600 + index, 800)
        (folder / "sources" / source).write_bytes(body)
    return folder


def _run(folder: Path, source: str) -> Run:
    """Open the run a source's bytes name, under the batch's runs root."""
    return open_run(folder / "sources" / source, folder / "runs")


def _approved(run: Run, vocabulary: Vocabulary) -> None:
    """Fill, review and approve `SUMMON`'s sheet for `run`."""
    schema = load_flow(SUMMON).schema
    sheet(run, schema, vocabulary)
    review(run, SUMMON)
    approve(run, SUMMON, schema, vocabulary)


@pytest.mark.spec("ui:library:an-absent-library-is-created")
def test_an_absent_library_is_created(tmp_path: Path) -> None:
    lib = tmp_path / "deep" / "isekai"
    assert library.open_library(lib) == lib.resolve()
    assert lib.is_dir()
    assert library.root({}) == Path("~/isekai").expanduser()
    assert library.root({"ISEKAI_LIBRARY": str(lib)}) == lib


@pytest.mark.spec("ui:library:a-library-git-can-reach-is-refused")
def test_a_library_inside_the_working_tree_is_refused(tmp_path: Path) -> None:
    inside = REPO / "library-in-the-tree"
    with pytest.raises(Refusal) as refused:
        library.open_library(inside)
    assert "ISEKAI_LIBRARY" in str(refused.value)
    assert not inside.exists()


@pytest.mark.spec("ui:batch-folder:a-folder-with-sources-is-a-batch")
def test_a_folder_with_sources_is_a_batch_and_one_without_is_not(
    tmp_path: Path,
) -> None:
    _batch(tmp_path, "2026-10-19", "ada.jpg")
    (tmp_path / "old exports").mkdir()

    rows = library.rows(tmp_path, OFFERED, FLOWS_DIR)

    assert [(row.name, row.batch) for row in rows] == [
        ("2026-10-19", True),
        ("old exports", False),
    ]
    assert library.batch(tmp_path, "2026-10-19") == tmp_path / "2026-10-19"
    with pytest.raises(Refusal, match="no batch named 'old exports'"):
        library.batch(tmp_path, "old exports")


@pytest.mark.spec("ui:batch-folder:a-dot-folder-is-not-listed")
def test_a_dot_folder_is_not_listed(tmp_path: Path) -> None:
    _batch(tmp_path, ".staging", "ada.jpg")
    _batch(tmp_path, "kept", "ada.jpg")

    assert [row.name for row in library.rows(tmp_path, OFFERED, FLOWS_DIR)] == ["kept"]
    with pytest.raises(Refusal):
        library.batch(tmp_path, ".staging")


@pytest.mark.spec("ui:batch-folder:a-flows-counts-are-of-its-sources")
def test_a_flows_counts_are_out_of_the_sources_that_have_it(
    tmp_path: Path, vocabulary: Vocabulary
) -> None:
    folder = _batch(tmp_path, "b", "ada.jpg", "bea.jpg", "cid.jpg", "dot.jpg")
    _approved(_run(folder, "ada.jpg"), vocabulary)
    bea = _run(folder, "bea.jpg")
    write_wd14(bea)
    bea.directory(CONJURE).mkdir()
    _run(folder, "cid.jpg")

    (row,) = library.rows(tmp_path, OFFERED, FLOWS_DIR)

    assert row.sources == 4
    assert row.flows == (
        FlowCount(SUMMON, approved=1, rendered=0, of=2),
        FlowCount(CONJURE, approved=0, rendered=0, of=1),
    )
    assert row.without_flow == 2


@pytest.mark.spec("ui:batch-folder:a-row-names-its-first-sources")
def test_a_row_names_its_first_seven_sources_in_the_hubs_order(
    tmp_path: Path,
) -> None:
    names = [f"{letter}.jpg" for letter in "ihgfedcba"]
    folder = _batch(tmp_path, "b", *names)

    (row,) = library.rows(tmp_path, OFFERED, FLOWS_DIR)

    grid = library.hub(folder, OFFERED, FLOWS_DIR)
    assert row.thumbs == tuple(one.name for one in grid.sources[:7])
    assert row.thumbs == ("a.jpg", "b.jpg", "c.jpg", "d.jpg", "e.jpg", "f.jpg", "g.jpg")
    assert row.sources == 9


@pytest.mark.spec("ui:batch-folder:batches-are-ordered-by-their-newest-file")
def test_batches_are_ordered_by_their_newest_file(tmp_path: Path) -> None:
    old = _batch(tmp_path, "a-old", "ada.jpg")
    new = _batch(tmp_path, "z-new", "bea.jpg")
    _batch(tmp_path, "m-mid", "cid.jpg")
    os.utime(old / "sources" / "ada.jpg", (1_000, 1_000))
    os.utime(tmp_path / "m-mid" / "sources" / "cid.jpg", (2_000, 2_000))
    later = new / "runs" / "x" / SUMMON / "outputs" / "001"
    later.mkdir(parents=True)
    (later / "7.png").write_bytes(b"png")
    os.utime(new / "sources" / "bea.jpg", (500, 500))
    os.utime(later / "7.png", (3_000, 3_000))

    rows = library.rows(tmp_path, OFFERED, FLOWS_DIR)

    assert [row.name for row in rows] == ["z-new", "m-mid", "a-old"]
    assert (rows[0].newest, rows[0].kind) == (3_000, "render")
    assert (rows[2].newest, rows[2].kind) == (1_000, "import")


@pytest.mark.spec("ui:batch-folder:no-file-records-a-batch")
def test_listing_and_opening_a_batch_writes_no_file(
    tmp_path: Path, vocabulary: Vocabulary
) -> None:
    folder = _batch(tmp_path, "b", "ada.jpg", "bea.jpg")
    _approved(_run(folder, "ada.jpg"), vocabulary)
    before = tree(tmp_path)

    library.rows(tmp_path, OFFERED, FLOWS_DIR)
    library.hub(library.batch(tmp_path, "b"), OFFERED, FLOWS_DIR)

    assert tree(tmp_path) == before


@pytest.mark.spec("ui:hub:a-cells-stage-comes-from-its-run")
def test_a_cells_stage_is_the_furthest_its_run_directory_holds(
    tmp_path: Path, vocabulary: Vocabulary
) -> None:
    folder = _batch(tmp_path, "b", "ada.jpg")
    run = _run(folder, "ada.jpg")
    loaded = load_flow(SUMMON)
    suffix = loaded.output_suffix

    def now() -> Cell:
        return library.stage(run, loaded)

    assert now() == Cell(None)
    run.directory(SUMMON).mkdir()
    assert now() == Cell("assigned")
    write_wd14(run)
    assert now() == Cell("tagged")
    schema = load_flow(SUMMON).schema
    sheet(run, schema, vocabulary)
    assert now() == Cell("sheet", status="draft")
    review(run, SUMMON)
    assert now() == Cell("draft", status="draft")
    approve(run, SUMMON, schema, vocabulary)
    assert now() == Cell("approved", status="approved", short=1)
    rendered = run.directory(SUMMON, OUTPUTS, "001")
    rendered.mkdir(parents=True)
    for seed in (7, 8):
        (rendered / f"{seed}{suffix}").write_bytes(b"png")
    newest = Rendered(1, 8)
    done = Cell("rendered", 2, status="approved", newest=newest, short=0)
    assert now() == done

    grid = library.hub(folder, OFFERED, FLOWS_DIR)
    (source,) = grid.sources
    assert source.cells[SUMMON] == done
    assert source.digest == run.digest


@pytest.mark.spec("ui:hub:a-cell-names-its-newest-image")
def test_an_approved_cell_names_the_last_image_of_its_newest_rendered_version(
    tmp_path: Path, vocabulary: Vocabulary
) -> None:
    folder = _batch(tmp_path, "b", "ada.jpg")
    run = _run(folder, "ada.jpg")
    loaded = load_flow(SUMMON)
    suffix = loaded.output_suffix
    _approved(run, vocabulary)
    older = run.directory(SUMMON, OUTPUTS, "001")
    older.mkdir(parents=True)
    # Seed 5 is written last, though 9 is the highest.
    for seed, at in ((3, 1_000), (9, 2_000), (5, 3_000)):
        image = older / f"{seed}{suffix}"
        image.write_bytes(b"png")
        os.utime(image, (at, at))
    review(run, SUMMON, new_version=True)
    approve(run, SUMMON, load_flow(SUMMON).schema, vocabulary)

    cell = library.stage(run, loaded)

    assert cell.stage == "approved"
    assert cell.renders == 0
    assert cell.newest == Rendered(1, 5)
    # A zero-padded name lists as seed 42, though no `42` file exists.
    padded = older / f"0042{suffix}"
    padded.write_bytes(b"png")
    os.utime(padded, (500, 500))
    assert library.stage(run, loaded).newest == Rendered(1, 5)
    # Written last, a padded name or one of digits outside ASCII is still no
    # render: no image of seed 42 is where a large view looks for it.
    os.utime(padded, (4_000, 4_000))
    assert library.stage(run, loaded).newest == Rendered(1, 5)
    superscript = older / f"²{suffix}"
    superscript.write_bytes(b"png")
    os.utime(superscript, (5_000, 5_000))
    assert library.stage(run, loaded).newest == Rendered(1, 5)
    # Home reads no image's time: it shows no newest image.
    assert library.stage(run, loaded, newest=False) == Cell(
        "approved", status="approved", short=1
    )


@pytest.mark.spec("ui:review:a-cell-counts-what-it-lacks")
def test_a_cell_counts_what_its_newest_approval_lacks(
    tmp_path: Path, vocabulary: Vocabulary
) -> None:
    folder = _batch(tmp_path, "b", "ada.jpg")
    run = _run(folder, "ada.jpg")
    loaded = load_flow(SUMMON)
    sheet(run, loaded.schema, vocabulary)
    draft = review(run, SUMMON)
    assert draft is not None
    save_draft(
        run, SUMMON, read(draft, DRAFT_FILE)["fields"], {"count": 3, "seeds": []}
    )
    assert library.stage(run, loaded).short is None
    approve(run, SUMMON, loaded.schema, vocabulary)
    group = run.directory(SUMMON, OUTPUTS, "001")
    group.mkdir(parents=True)
    (group / f"7{loaded.output_suffix}").write_bytes(b"png")

    grid = library.hub(folder, OFFERED, FLOWS_DIR)

    (source,) = grid.sources
    assert source.cells[SUMMON].short == 2
    # A count no approval can carry is refused, and counts nothing.
    approval = approval_of(run, SUMMON, 1)
    body = json.loads(approval.read_text())
    body["renders"] = {"count": 0, "seeds": []}
    approval.write_text(json.dumps(body))
    assert library.stage(run, loaded).short == 0


@pytest.mark.spec("ui:hub:an-untracked-flow-is-ignored")
def test_a_flow_the_surface_does_not_offer_is_ignored(tmp_path: Path) -> None:
    folder = _batch(tmp_path, "b", "ada.jpg")
    run = _run(folder, "ada.jpg")
    (run.directory(CONTROL, "sheets")).mkdir(parents=True)

    grid = library.hub(folder, OFFERED, FLOWS_DIR)

    assert CONTROL not in grid.flows
    (source,) = grid.sources
    assert CONTROL not in source.cells
    assert all(cell == Cell(None) for cell in source.cells.values())


@pytest.mark.spec("ui:batch-folder:an-unoffered-flow-has-no-count")
def test_a_flow_the_configuration_does_not_offer_has_no_count(
    tmp_path: Path,
) -> None:
    lib = tmp_path / "lib"
    folder = _batch(lib, "b", "ada.jpg")
    _run(folder, "ada.jpg").directory(CONTROL).mkdir()
    config = tmp_path / "ui.json"
    config.write_text(json.dumps({"flows": list(OFFERED)}))

    (row,) = library.rows(lib, library.offered(FLOWS_DIR, config), FLOWS_DIR)

    assert row.flows == ()
    assert row.without_flow == 1
    config.write_text(json.dumps({"flows": [SUMMON, "retired-anime-wai"]}))
    with pytest.raises(Refusal, match="config/ui.json offers retired-anime-wai"):
        library.offered(FLOWS_DIR, config)


@pytest.mark.spec("ui:hub:an-uncleaned-source-is-marked")
def test_a_source_still_carrying_metadata_is_marked_not_cleaned(
    tmp_path: Path,
) -> None:
    folder = _batch(tmp_path, "b")
    exif = Image.Exif()
    exif[0x010F] = "Canon"
    for name, options in (("clean.jpg", {}), ("as-is.jpg", {"exif": exif.tobytes()})):
        body = photo_jpeg((90, 60, 30), (64, 48), **options)
        (folder / "sources" / name).write_bytes(body)

    grid = library.hub(folder, OFFERED, FLOWS_DIR)

    carries = {one.name: one.carries for one in grid.sources}
    assert carries == {"as-is.jpg": ("EXIF",), "clean.jpg": ()}

    # A clean source render would refuse for its shape carries nothing.
    banner = folder / "sources" / "banner.jpg"
    banner.write_bytes(photo_jpeg((90, 60, 30), (500, 100)))

    grid = library.hub(folder, OFFERED, FLOWS_DIR)

    assert {one.name: one.carries for one in grid.sources}["banner.jpg"] == ()


@pytest.mark.spec("ui:hub:a-source-is-sized-from-its-file")
def test_a_source_with_no_run_is_sized_from_its_own_file(tmp_path: Path) -> None:
    folder = _batch(tmp_path, "b", "ada.jpg")
    (folder / "sources" / "turned.jpg").write_bytes(
        jpeg_with_header(1200, 900, orientation=6)
    )
    (folder / "sources" / "broken.jpg").write_bytes(b"not an image")

    grid = library.hub(folder, OFFERED, FLOWS_DIR)

    assert not (folder / "runs").exists()
    sizes = {one.name: one.size for one in grid.sources}
    assert sizes == {
        "ada.jpg": (600, 800),
        "turned.jpg": (900, 1200),
        "broken.jpg": None,
    }


@pytest.mark.spec("ui:hub:an-unreadable-file-marks-its-cell")
def test_an_unreadable_run_file_marks_its_cell_alone(
    tmp_path: Path, vocabulary: Vocabulary
) -> None:
    folder = _batch(tmp_path, "b", "ada.jpg", "bea.jpg")
    ada = _run(folder, "ada.jpg")
    sheet(ada, load_flow(SUMMON).schema, vocabulary)
    review(ada, SUMMON)
    draft = ada.directory(SUMMON, REVIEW) / "001.draft.json"
    body = json.loads(draft.read_text())
    body["schema"]["version"] = 99
    draft.write_text(json.dumps(body))
    bea = _run(folder, "bea.jpg")
    _approved(bea, vocabulary)

    grid = library.hub(folder, OFFERED, FLOWS_DIR)

    cells = {one.name: one.cells[SUMMON] for one in grid.sources}
    assert cells["ada.jpg"].stage == "unreadable"
    assert "001.draft.json" in str(cells["ada.jpg"].refusal)
    assert "version 99" in str(cells["ada.jpg"].refusal)
    assert cells["bea.jpg"] == Cell("approved", status="approved", short=1)


@pytest.mark.spec("ui:hub:the-hub-writes-nothing")
def test_reading_the_hub_writes_nothing(tmp_path: Path, vocabulary: Vocabulary) -> None:
    folder = _batch(tmp_path, "b", "ada.jpg", "bea.jpg")
    ada = _run(folder, "ada.jpg")
    sheet(ada, load_flow(SUMMON).schema, vocabulary)
    _run(folder, "bea.jpg")
    before = tree(folder)

    library.hub(folder, OFFERED, FLOWS_DIR)

    assert tree(folder) == before


@pytest.mark.spec_exempt("structural: a run is found by its digest, or refused")
def test_a_run_is_found_by_its_digest_and_an_unknown_one_refused(
    tmp_path: Path,
) -> None:
    folder = _batch(tmp_path, "b", "ada.jpg")
    run = _run(folder, "ada.jpg")

    assert library.run_named(folder, run.digest) == run
    with pytest.raises(Refusal, match="no run named"):
        library.run_named(folder, "0" * 12)
    with pytest.raises(Refusal, match="no run named"):
        library.run_named(folder, run.id[:6])


@pytest.mark.spec("ui:renders:a-thumbnail-is-its-own-images")
def test_one_source_at_one_seed_in_two_batches_has_two_thumbnails(
    tmp_path: Path,
) -> None:
    lib = tmp_path / "lib"
    colours = {"b1": (200, 30, 30), "b2": (30, 30, 200)}
    thumbs = {}
    for name, colour in colours.items():
        # One photograph, so both batches hold the run of one digest.
        run = _run(_batch(lib, name, "ada.jpg"), "ada.jpg")
        image = run.path / SUMMON / OUTPUTS / "001" / "42.png"
        image.parent.mkdir(parents=True)
        Image.new("RGB", (640, 800), colour).save(image)
        thumbs[name] = library.thumbnail(lib, run, image)

    for name, colour in colours.items():
        with Image.open(thumbs[name]) as made:
            pixel = made.convert("RGB").getpixel((10, 10))
        assert isinstance(pixel, tuple)
        assert (pixel[0] > pixel[2]) == (colour[0] > colour[2])


@pytest.mark.spec("ui:renders:an-unreadable-image-is-refused")
@pytest.mark.parametrize("read", ["_upright", "source_jpeg", "_shrunk"])
def test_an_image_past_pillows_pixel_bound_is_refused_naming_it(
    read: str, tmp_path: Path
) -> None:
    # A PNG header declaring more pixels than Pillow opens, and no pixels at all.
    def chunk(kind: bytes, body: bytes) -> bytes:
        size, check = struct.pack(">I", len(body)), zlib.crc32(kind + body)
        return size + kind + body + struct.pack(">I", check)

    header = struct.pack(">IIBBBBB", 20000, 10000, 8, 2, 0, 0, 0)
    huge = tmp_path / "huge.png"
    huge.write_bytes(
        b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IEND", b"")
    )

    with pytest.raises(Refusal, match="huge.png: is not an image this build can read"):
        getattr(library, read)(huge)
