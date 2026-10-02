"""Score a batch of runs against the cohort its photographs came from.

    uv run python -m evaluation <batch>/runs --cohort <cohort>

Each run is matched to its cohort photograph by the digest its frame records;
each flow's first render is ranked against every cohort photograph. The record
is written beside the runs, as `<batch>/evaluation.json`, and the table printed.
A separate entry point, not a verb: the evaluator measures the pipeline and
`isekai` never imports it.
"""

import argparse
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from evaluation.cohort import (
    Cohort,
    Photograph,
    Record,
    Row,
    Vector,
    load_cohort,
    rank,
    record,
    scored,
    table,
    unscored,
)
from evaluation.eval_models import DETECTOR, ENCODER
from isekai.foundation.artifacts import write_json
from isekai.foundation.flow import FLOWS_DIR, load_flow
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import FRAME_NAME, OUTPUTS, Run
from isekai.interface.run_view import rendered
from isekai.shared.vocabulary import DEFAULT_MODELS_DIR

Embed = Callable[[Path], Vector | None]


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    """Parse the command line."""
    p = argparse.ArgumentParser(
        prog="python -m evaluation",
        description="Count, over a cohort, how often each render is nearest its own "
        "photograph and its own person.",
    )
    p.add_argument("runs", type=Path, help="a batch's runs directory")
    p.add_argument(
        "--cohort",
        type=Path,
        required=True,
        help="the directory holding one sub-directory per person",
    )
    p.add_argument(
        "--models",
        type=Path,
        default=DEFAULT_MODELS_DIR,
        help="where the pinned detector and encoder live",
    )
    p.add_argument(
        "--flows", type=Path, default=FLOWS_DIR, help="where the flows are declared"
    )
    return p.parse_args(argv)


def _runs(directory: Path) -> list[Run]:
    """Return every run under `directory` that has a frame, in name order."""
    if not directory.is_dir():
        raise Refusal(
            f"{directory} is not a directory; give the batch's runs directory, the "
            "one `infra/render.sh` rendered into"
        )
    return [
        Run(frame.parent.name, frame.parent)
        for frame in sorted(directory.glob(f"*/{FRAME_NAME}"))
    ]


def _gallery(cohort: Cohort, embed: Embed) -> dict[Photograph, Vector]:
    """Return every cohort photograph's embedding, refusing one with no face."""
    gallery: dict[Photograph, Vector] = {}
    for photograph in cohort.photographs:
        vector = embed(photograph.path)
        if vector is None:
            raise Refusal(
                f"no face is found in {photograph.path}, so no render can be ranked "
                "against it; replace or remove it from the cohort"
            )
        gallery[photograph] = vector
    return gallery


def _rows(
    run: Run,
    source: Photograph,
    gallery: dict[Photograph, Vector],
    embed: Embed,
    flows_dir: Path,
) -> dict[str, Row]:
    """Return the row of each flow `run` rendered: its first seed, ranked."""
    seeds: dict[str, list[tuple[int, int]]] = {}
    for flow, group, found in rendered(run, flows_dir):
        seeds.setdefault(flow, []).extend((group, seed) for seed in found)
    rows: dict[str, Row] = {}
    for flow, renders in seeds.items():
        if not renders:
            continue
        (group, seed), rest = renders[0], renders[1:]
        name = f"{seed}{load_flow(flow, flows_dir).output_suffix}"
        vector = embed(run.directory(flow, OUTPUTS, f"{group:03d}", name))
        rows[flow] = (
            unscored(source, run.id, seed, "no face found")
            if vector is None
            else scored(source, run.id, seed, rank(vector, gallery))
        )
        rows[flow]["also_rendered"] = [s for _, s in rest]
    return rows


def score(runs: Path, cohort_dir: Path, embed: Embed, flows_dir: Path) -> Record:
    """Return the batch's record: every cohort photograph's row in every flow.

    Every cohort photograph is embedded before any render is opened, so a cohort
    with a faceless photograph refuses while nothing has been scored.
    """
    cohort = load_cohort(cohort_dir)
    matched: list[tuple[Run, Photograph]] = []
    outside: list[str] = []
    for run in _runs(runs):
        source = cohort.by_digest(run.photo_record["sha256"])
        if source is None:
            outside.append(run.id)
        else:
            matched.append((run, source))
    gallery = _gallery(cohort, embed)
    flows: dict[str, list[Row]] = {}
    for run, source in matched:
        for flow, row in _rows(run, source, gallery, embed, flows_dir).items():
            flows.setdefault(flow, []).append(row)
    return record(cohort, flows, outside, {"detector": DETECTOR, "encoder": ENCODER})


def _embedder(models: Path) -> Embed:
    """Return the real embedder: the pinned detector and encoder, verified."""
    from evaluation.eval_models import load_eval_manifest, shared_with_the_graph
    from evaluation.face import Detector, Encoder, embed
    from isekai.boundary.provision import DigestMismatch, load_manifest, resolve

    manifest = load_eval_manifest()
    shared = shared_with_the_graph(manifest, load_manifest())
    if shared:
        raise Refusal(
            f"the evaluator's manifest carries {', '.join(shared)}, which the "
            "generator's manifest carries too, so the count would be the generator "
            "grading itself; pin another model in `evaluation/eval_models.json`"
        )
    try:
        detector = Detector(resolve(DETECTOR, models, manifest))
        encoder = Encoder(resolve(ENCODER, models, manifest))
    except FileNotFoundError as absent:
        raise Refusal(
            f"{absent.filename} is not provisioned; run `bash tools/download_models.sh "
            "evaluation/eval_models.json`, then this command again"
        ) from absent
    except DigestMismatch as swapped:
        raise Refusal(
            f"{swapped}; delete that file, run `bash tools/download_models.sh "
            "evaluation/eval_models.json`, then this command again"
        ) from swapped
    return lambda path: embed(path, detector, encoder)


def main(argv: Sequence[str]) -> int:
    """Score the batch, write its record beside the runs, and print the table."""
    args = parse_args(argv)
    try:
        embed = _embedder(args.models)
        rec = score(args.runs, args.cohort, embed, args.flows)
    except Refusal as refused:
        print(f"refused: {refused}", file=sys.stderr)
        return 1
    write_json(args.runs.parent / "evaluation.json", rec)
    print(table(rec), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
