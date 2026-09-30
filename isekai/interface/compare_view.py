"""The comparison page: every run's photograph beside each flow's renders.

A batch ends in a question a person answers by eye -- which flow kept whom -- and
this writes the page they answer it on, so an agent can hand it over without
reading a run. Like `run_view`, it reads and decides nothing.

    <batch>/runs/<id>/...  ->  <batch>/compare.html

Images are linked relative to the page and none is embedded: the page stays
small, and every image stays where the run put it. Stdlib only.
"""

import html
import shlex
from collections.abc import Mapping
from pathlib import Path
from urllib.parse import quote

from isekai.foundation.artifacts import CAPTION_FILE, PROMPT_FILE, read
from isekai.foundation.atomic_write import write_atomically
from isekai.foundation.flow import FLOWS_DIR, Flow, load_flow, tracked_flows
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    CAPTIONS,
    FRAME_NAME,
    OUTPUTS,
    PROMPTS,
    REVIEW,
    Run,
    approved_versions,
    artifact_name,
    latest_artifact,
)
from isekai.pipeline.generate import rendered_seeds

PAGE_NAME = "compare.html"
BATCH_RUNS = "runs"
# Where the run-flows skill keeps a batch's photographs; named only in a refusal.
BATCH_PHOTOS = "photos"

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
        gap: 20px; padding: 20px; align-items: start; }
figure { margin: 0; min-width: 0; }
figcaption { padding: 0 0 8px; font-size: 11px; letter-spacing: .06em;
             text-transform: uppercase; color: #8b8f9a; }
img { display: block; width: auto; height: auto; max-width: 100%; max-height: 80vh;
      border-radius: 6px; cursor: zoom-in; }
#overlay { position: fixed; inset: 0; z-index: 10; display: none; overflow: auto;
           background: #000000e6; cursor: zoom-out; }
#overlay.open { display: flex; }
/* margin: auto centres an image that fits and starts one that overflows at the
   top left, so a full-size image scrolls from its edge rather than being cut. */
#overlay img { margin: auto; max-width: 96vw; max-height: 96vh; cursor: zoom-in; }
#overlay.full img { max-width: none; max-height: none; cursor: zoom-out; }
.captions { padding: 0 20px 16px; }
.caption, .prompt { margin: 10px 0 0; color: #9aa0ad; font-size: 12px; }
.prompt { font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
          font-size: 11.5px; word-break: break-word; }
.caption b, .prompt b { color: #8b8f9a; }
.none { color: #6f7481; font-style: italic; }
"""

# Click an image to see it fitted to the screen, click it again for its full size;
# Esc or a click beside it closes. Inline: the page loads nothing but its images.
_OVERLAY = """<div id="overlay"><img alt=""></div><script>
const overlay = document.getElementById("overlay");
const shown = overlay.querySelector("img");
const close = () => {
  overlay.classList.remove("open", "full");
  shown.removeAttribute("src");
};
document.querySelector("main").addEventListener("click", (event) => {
  if (event.target.tagName !== "IMG") return;
  shown.src = event.target.src;
  overlay.classList.add("open");
  overlay.scrollTo(0, 0);
});
shown.addEventListener("click", () => overlay.classList.toggle("full"));
overlay.addEventListener("click", (event) => {
  if (event.target === overlay) close();
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") close();
});
</script>"""


def _link(path: Path, batch: Path) -> str:
    """Return `path` as an attribute-safe URL relative to the page in `batch`."""
    return html.escape(quote(path.relative_to(batch).as_posix()), quote=True)


def _runs(batch: Path, flows_dir: Path) -> list[Run]:
    """Return every run under the batch's `runs/`, by id, or refuse naming the batch."""
    root = batch / BATCH_RUNS
    if not root.is_dir():
        flows = " ".join(f"--flow {flow}" for flow in tracked_flows(flows_dir))
        raise Refusal(
            f"{batch} holds no {BATCH_RUNS}/ directory, so it is not a batch; give "
            f"the path of the batch directory that holds {BATCH_RUNS}/, or open its "
            f"runs with `python -m isekai tag {flows} --runs {shlex.quote(str(root))} "
            f"{shlex.quote(str(batch / BATCH_PHOTOS))}/*`"
        )
    return [
        Run(path.name, path)
        for path in sorted(root.iterdir())
        if (path / FRAME_NAME).is_file()
    ]


def _prompt(run: Run, flow: str, version: int) -> str:
    """Return the positive prompt assembled from `version`, as a block, or nothing."""
    path = run.directory(flow, PROMPTS) / artifact_name(version)
    if not path.is_file():
        return ""
    positive = read(path, PROMPT_FILE)["positive"]
    return f'<p class="prompt"><b>positive</b> {html.escape(positive)}</p>'


def _renders(run: Run, name: str, flow: Flow | None, batch: Path) -> list[str]:
    """Return a figure per render of the flow's latest approval, or say why none.

    `flow` is None for a directory this build carries no flow for -- work left by
    a flow since renamed -- whose renders cannot be found without its manifest.
    """
    if flow is None:
        return [
            f"<figure><figcaption>{html.escape(name)}</figcaption>"
            f'<p class="none">not a tracked flow</p></figure>'
        ]
    approved = approved_versions(run.directory(name, REVIEW))
    if approved:
        directory = run.directory(name, OUTPUTS, f"{approved[-1]:03d}")
        if seeds := rendered_seeds(directory, flow.output_suffix):
            prompt = _prompt(run, name, approved[-1])
            return [
                f"<figure><figcaption>{html.escape(name)} &middot; seed {seed}"
                f"</figcaption><img loading=lazy "
                f'src="{_link(directory / f"{seed}{flow.output_suffix}", batch)}" '
                f'alt="">{prompt}</figure>'
                for seed in seeds
            ]
    return [
        f"<figure><figcaption>{html.escape(name)}</figcaption>"
        f'<p class="none">no render yet</p></figure>'
    ]


def _entry(run: Run, flows: Mapping[str, Flow | None], batch: Path) -> str:
    """Return one run's section: the photograph and each flow's renders, then captions.

    Each render carries the positive prompt it came from; the captions span the
    row, because a column is too narrow for prose.
    """
    figures = [
        f"<figure><figcaption>photograph</figcaption>"
        f'<img loading=lazy src="{_link(run.photo, batch)}" alt=""></figure>'
    ]
    captions = []
    for name, flow in flows.items():
        path = latest_artifact(run.directory(name, CAPTIONS))
        if path is not None:
            prose = read(path, CAPTION_FILE)["prose"]
            captions.append(
                f'<p class="caption"><b>{html.escape(name)}</b> '
                f"{html.escape(prose)}</p>"
            )
        figures.extend(_renders(run, name, flow, batch))
    return (
        f'<section><div class="id">{html.escape(run.id)}</div>'
        f'<div class="grid">{"".join(figures)}</div>'
        f'<div class="captions">{"".join(captions)}</div></section>'
    )


def _column(item: tuple[str, Flow | None]) -> tuple[int, str]:
    """Order a flow's column: reads the photograph, then tracked, then untracked."""
    name, flow = item
    if flow is None:
        return 2, name
    return int("photo" not in flow.inputs), name


def page(batch: Path, flows_dir: Path = FLOWS_DIR) -> str:
    """Return the comparison page for `batch`, or refuse a directory with no `runs/`.

    Every run shows every flow any run in the batch holds, so each row has the same
    columns and a flow a run never reached reads *no render yet*. A flow that reads
    the photograph sits beside it, then the rest, then any directory this build
    carries no flow for, marked so rather than failing the page: each group by name.
    """
    runs = _runs(batch, flows_dir)
    tracked = set(tracked_flows(flows_dir))
    loaded = {
        name: load_flow(name, flows_dir) if name in tracked else None
        for name in {name for run in runs for name in run.flows}
    }
    flows = dict(sorted(loaded.items(), key=_column))
    title = f"isekai &mdash; {html.escape(batch.name)}"
    entries = "".join(_entry(run, flows, batch) for run in runs)
    return (
        "<!doctype html><html lang=en><meta charset=utf-8>"
        f"<title>{title}</title><style>{_STYLE}</style>"
        f"<header><h1>{title}</h1></header><main>{entries}</main>{_OVERLAY}\n"
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
