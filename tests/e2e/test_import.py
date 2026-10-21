"""The import sheet in a browser: files chosen in the dialog, each with its own upload.

One upload is held at the network so the page can be seen while it is in flight.
"""

import re
from pathlib import Path

import pytest
from playwright.sync_api import Page, Route, expect

from tests.e2e.conftest import Served
from tests.images import nef_bytes, photo_jpeg

HEIC = Path(__file__).resolve().parents[1] / "fixtures" / "sources" / "plain.heic"


def _jpeg(path: Path, colour: tuple[int, int, int]) -> Path:
    path.write_bytes(photo_jpeg(colour, (64, 80)))
    return path


def _nef(path: Path) -> Path:
    path.write_bytes(nef_bytes())
    return path


def _choose(page: Page, served: Served, files: list[Path]) -> None:
    """Open New batch on Home and choose `files` in the dialog it opens."""
    page.goto(served.url)
    with page.expect_file_chooser() as chooser:
        page.get_by_role("button", name="New batch").click()
    chooser.value.set_files([str(path) for path in files])


def _hold(page: Page, name: str) -> list[Route]:
    """Hold the upload of `name` until the test lets it go."""
    held: list[Route] = []
    page.route(f"**/files/{name}", lambda route: held.append(route))
    return held


def _release(page: Page, held: list[Route]) -> None:
    """Let the held upload go, once the page has sent it."""
    for _ in range(100):
        if held:
            held[0].continue_()
            return
        page.wait_for_timeout(50)
    raise AssertionError("the held upload was never sent")


def _tile(page: Page, name: str):  # noqa: ANN202
    return page.locator(f'.import__tile[data-file="{name}"]')


@pytest.mark.spec("ui:sheet:each-file-shows-its-progress")
def test_each_chosen_file_shows_its_upload_then_its_result(
    page: Page, served: Served, tmp_path: Path
) -> None:
    held = _hold(page, "held.jpg")
    files = [
        _jpeg(tmp_path / "held.jpg", (10, 20, 30)),
        HEIC,
        _nef(tmp_path / "DSC_2291.NEF"),
    ]

    _choose(page, served, files)

    expect(_tile(page, "held.jpg")).to_have_attribute(
        "data-phase", re.compile("uploading|reading")
    )
    expect(_tile(page, "plain.heic")).to_have_attribute("data-state", "converted")
    expect(_tile(page, "plain.heic")).to_contain_text("HEIC → JPEG")
    refused = page.locator('.import__refused[data-file="DSC_2291.NEF"]')
    expect(refused).to_contain_text("a NEF RAW photograph")
    expect(refused).to_contain_text("export it as JPEG")
    _release(page, held)
    expect(_tile(page, "held.jpg")).to_have_attribute("data-state", "ready")
    page.get_by_role("button", name="Cancel").click()


@pytest.mark.spec("ui:sheet:import-waits-for-reading")
def test_import_is_disabled_naming_how_many_are_read_until_all_are(
    page: Page, served: Served, tmp_path: Path
) -> None:
    held = _hold(page, "slow.jpg")
    files = [
        _jpeg(tmp_path / "quick.jpg", (40, 50, 60)),
        _jpeg(tmp_path / "slow.jpg", (70, 80, 90)),
    ]

    _choose(page, served, files)

    importing = page.locator(".import__foot .btn-primary")
    expect(_tile(page, "quick.jpg")).to_have_attribute("data-state", "ready")
    expect(importing).to_be_disabled()
    expect(page.locator(".import__disabled")).to_have_text("Reading 1 of 2")
    _release(page, held)
    expect(importing).to_be_enabled()
    page.get_by_role("button", name="Cancel").click()


@pytest.mark.spec("ui:sheet:an-import-opens-the-hub")
def test_importing_a_new_batch_opens_its_hub_with_every_source_unassigned(
    page: Page, served: Served, tmp_path: Path
) -> None:
    files = [
        _jpeg(tmp_path / "first.jpg", (100, 0, 0)),
        _jpeg(tmp_path / "second.jpg", (0, 100, 0)),
    ]

    _choose(page, served, files)
    expect(page.locator(".import__count")).to_contain_text("2 sources")
    page.get_by_label("Batch name").fill("e2e-imported")
    page.locator(".import__foot .btn-primary").click()

    expect(page).to_have_url(served.hub_of("e2e-imported"))
    expect(page.locator(".hub__name")).to_have_count(2)
    expect(page.locator('.hub__cell[data-stage="none"]')).to_have_count(4)
