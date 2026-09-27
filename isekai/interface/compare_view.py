"""The comparison page: every run's photograph beside each flow's renders.

A batch ends in a question a person answers by eye -- which flow kept whom -- and
this writes the page they answer it on, so an agent can hand it over without
reading a run. Like `run_view`, it reads and decides nothing (0035 design D2).

    <batch>/runs/<id>/...  ->  <batch>/compare.html

Images are linked relative to the page and none is embedded: the page stays
small, and every image stays where the run put it. Stdlib only.
"""

import html
from pathlib import Path
from urllib.parse import quote

from isekai.foundation.artifacts import CAPTION_FILE, read
from isekai.foundation.atomic_write import write_atomically
from isekai.foundation.flow import FLOWS_DIR, load_flow
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    CAPTIONS,
    FRAME_NAME,
    OUTPUTS,
    REVIEW,
    Run,
    approved_versions,
    latest_artifact,
)
from isekai.interface.run_view import rendered

PAGE_NAME = "compare.html"
BATCH_RUNS = "runs"

_STYLE = """
:root { color-scheme: dark; }
* { box-sizing: border-box; }
body { margin: 0; background: #0e0f13; color: #e6e7ea;
       font: 14px/1.5 ui-sans-serif, -apple-system, "Segoe UI", sans-serif; }
header { padding: 18px 24px; border-bottom: 1px solid #23252d; }
h1 { margin: 0; font-size: 16px; font-weight: 600; }
main { padding: 24px; display: flex; flex-direction: column; gap: 32px; }
section { border: 1px solid #23252d; border-radius: 10px; background: #14161c; }
.id { padding: 12px 16px; border-bottom: 1px solid #23252d;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 13px; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 20px; padding: 20px; }
figure { margin: 0; min-width: 0; }
figcaption { padding: 0 0 8px; font-size: 11px; letter-spacing: .06em;
             text-transform: uppercase; color: #8b8f9a; }
img { width: 100%; height: 80vh; object-fit: contain; object-position: top;
      display: block; background: #0a0b0e; border-radius: 6px; }
.caption { margin: 10px 0 0; color: #9aa0ad; font-size: 12px; }
.caption b { color: #8b8f9a; }
.none { color: #6f7481; font-style: italic; }
"""


def _link(path: Path, batch: Path) -> str:
    """Return `path` as an attribute-safe URL relative to the page in `batch`."""
    return html.escape(quote(path.relative_to(batch).as_posix()), quote=True)


def _runs(batch: Path) -> list[Run]:
    """Return every run under the batch's `runs/`, by id, or refuse naming the batch."""
    root = batch / BATCH_RUNS
    if not root.is_dir():
        raise Refusal(
            f"{batch} holds no {BATCH_RUNS}/ directory, so it is not a batch; run "
            f"the stages with `--runs {root}` first, or give the batch directory "
            f"that holds {BATCH_RUNS}/"
        )
    return [
        Run(path.name, path)
        for path in sorted(root.iterdir())
        if (path / FRAME_NAME).is_file()
    ]


def _entry(run: Run, flows: list[str], batch: Path, flows_dir: Path) -> str:
    """Return one run's section: photograph and captions, then each flow's renders."""
    captions = []
    for flow in flows:
        path = latest_artifact(run.directory(flow, CAPTIONS))
        if path is not None:
            prose = read(path, CAPTION_FILE)["prose"]
            captions.append(
                f'<p class="caption"><b>{html.escape(flow)}</b> '
                f"{html.escape(prose)}</p>"
            )
    figures = [
        f"<figure><figcaption>photograph</figcaption>"
        f'<img loading=lazy src="{_link(run.photo, batch)}" alt="">'
        f"{''.join(captions)}</figure>"
    ]
    seeds_of = {
        (flow, version): seeds for flow, version, seeds in rendered(run, flows_dir)
    }
    for flow in flows:
        approved = approved_versions(run.directory(flow, REVIEW))
        version = approved[-1] if approved else None
        seeds = seeds_of.get((flow, version), []) if version is not None else []
        if not seeds:
            figures.append(
                f"<figure><figcaption>{html.escape(flow)}</figcaption>"
                f'<p class="none">no render yet</p></figure>'
            )
            continue
        suffix = load_flow(flow, flows_dir).output_suffix
        directory = run.directory(flow, OUTPUTS, f"{version:03d}")
        for seed in seeds:
            figures.append(
                f"<figure><figcaption>{html.escape(flow)} &middot; seed {seed}"
                f"</figcaption><img loading=lazy "
                f'src="{_link(directory / f"{seed}{suffix}", batch)}" alt=""></figure>'
            )
    return (
        f'<section><div class="id">{html.escape(run.id)}</div>'
        f'<div class="grid">{"".join(figures)}</div></section>'
    )


def page(batch: Path, flows_dir: Path = FLOWS_DIR) -> str:
    """Return the comparison page for `batch`, or refuse a directory with no `runs/`.

    Every run shows every flow any run in the batch holds, so each row has the same
    columns and a flow a run never reached reads *no render yet*.
    """
    runs = _runs(batch)
    flows = sorted({flow for run in runs for flow in run.flows})
    title = f"isekai &mdash; {html.escape(batch.name)}"
    entries = "".join(_entry(run, flows, batch, flows_dir) for run in runs)
    return (
        "<!doctype html><html lang=en><meta charset=utf-8>"
        f"<title>{title}</title><style>{_STYLE}</style>"
        f"<header><h1>{title}</h1></header><main>{entries}</main>\n"
    )


def write_page(batch: Path, flows_dir: Path = FLOWS_DIR) -> Path:
    """Write the comparison page into `batch` and return its path.

    The page is built whole before anything is written, so a refusal leaves the
    batch as it was.
    """
    body = page(batch, flows_dir)
    path = batch / PAGE_NAME
    write_atomically(path, body.encode())
    return path
