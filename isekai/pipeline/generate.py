"""Stage (4): assemble every prompt locally, then render what was approved.

**Assembly happens before any endpoint is acquired, for the whole batch.**
Assembly is free and rendering is not, so a malformed sheet should cost nothing
rather than a boot and several minutes of waiting. Doing the whole batch first is
what turns that from a per-item saving into a guarantee -- and it makes the
entirety of prompt construction testable offline.

**Only an approved artifact is rendered.** The correction is the single largest
measured gain in this pipeline; rendering an unapproved draft would silently
spend money producing the result the correction exists to improve on, and would
make the two indistinguishable afterwards.

**Seeds are drawn or named, never both.** One verb explores and the other
reproduces, and combining them has no meaning. The output is named by its seed,
which is the reproducibility contract at the finest grain the system has: one
image, one integer -- a stronger guarantee than "one integer reproduces a run's
whole sequence", because it reproduces an image rather than an ordering.

**No session lifecycle.** This stage talks to an endpoint somebody else brought
up, exactly as the prototype did by hand. Acquiring, tunnelling, releasing and
reconciling orphaned machines land with the version that adds a second flow,
rather than being dragged into the one whose only risk is the architecture. The
cost is that an orphaned machine is exactly as possible as it is today, and no
less.

Stdlib only; the endpoint is behind the repository's existing `ComfyTransport`.
"""

import hashlib
import json
import random
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from isekai.boundary.comfy import ComfyTransport, Unreachable
from isekai.foundation.artifacts import (
    APPROVED_FILE,
    PROMPT_FILE,
    RENDER_FILE,
    Prompt,
    read,
    write,
)
from isekai.foundation.artifacts import Render as RenderSidecar
from isekai.foundation.atomic_write import write_atomically
from isekai.foundation.flow import (
    SAMPLER_DIALS,
    SECOND_PASS_DIALS,
    Flow,
    Schema,
    Workflow,
    assemble,
)
from isekai.foundation.refusal import Refusal
from isekai.foundation.run import (
    APPROVED,
    OUTPUTS,
    PROMPTS,
    REVIEW,
    Run,
    across,
    approved_versions,
    artifact_name,
    check_budget,
    record_failure,
)
from isekai.shared.image import (
    MAX_TARGET_LONG_SIDE,
    dimensions_or_refuse,
    working_resolution,
)

STAGE_ASSEMBLE = "assemble"
STAGE_RENDER = "render"

# A seed is what the sampler takes: an unsigned 64-bit integer.
SEED_BITS = 64


@dataclass(frozen=True)
class Render:
    """One rendered image and the provenance that says what produced it."""

    seed: int
    image: Path
    provenance: Path


def draw_seeds(
    count: int, rng: random.Random, already: Sequence[int] = ()
) -> list[int]:
    """Draw `count` seeds that are distinct from each other and from `already`.

    The source is injected, which is what keeps the suite deterministic without
    making production output predictable.
    """
    drawn: list[int] = []
    seen = set(already)
    while len(drawn) < count:
        seed = rng.getrandbits(SEED_BITS)
        if seed in seen:
            continue
        seen.add(seed)
        drawn.append(seed)
    return drawn


def seeds_for(
    count: int | None,
    explicit: Sequence[int] | None,
    rng: random.Random,
    already: Sequence[int] = (),
) -> list[int]:
    """Return the seeds to render, refusing a count and explicit seeds together."""
    if count is not None and explicit:
        raise Refusal(
            "--count and --seed are alternatives: one explores and the other "
            "reproduces, and asking for both has no meaning; drop whichever you "
            "did not mean"
        )
    if explicit:
        return [seed for seed in explicit if seed not in set(already)]
    wanted = 1 if count is None else count
    shortfall = max(wanted - len(already), 0)
    return draw_seeds(shortfall, rng, already)


def approved_artifact(run: Run, flow: str) -> tuple[int, Path]:
    """Return the highest approved artifact for `flow`, or refuse naming the way out."""
    directory = run.directory(flow, REVIEW)
    approved = approved_versions(directory)
    if not approved:
        raise Refusal(
            f"{run.id}: flow {flow} has no approved sheet, and only an approved "
            "sheet is rendered; run `python -m isekai review --flow "
            f"{flow}`, edit the draft, then `python -m isekai approve --flow "
            f"{flow}`"
        )
    return approved[-1], directory / artifact_name(approved[-1], APPROVED)


def approved_flows(run: Run) -> list[str]:
    """Return every flow this run has an approved artifact for, by identifier.

    A listing, and the layout is what makes it one: every flow's work is one
    directory under the run, so the flows a run has been approved for are the
    flows whose `review/` holds an approved artifact.
    """
    return [
        flow for flow in run.flows if approved_versions(run.directory(flow, REVIEW))
    ]


def prompt_artifact(
    run: Run,
    flow: Flow,
    schema: Schema,
    *,
    new_version: bool = False,
) -> Path:
    """Assemble `flow`'s prompt for this run and write it, without touching a network.

    The artifact takes the approved sheet's number rather than counting its own,
    because only an approved artifact is ever rendered and the chain back to the
    photograph is the producer record.
    """
    version, source = approved_artifact(run, flow.id)
    directory = run.directory(flow.id, PROMPTS)
    path = directory / artifact_name(version)
    if path.exists() and not new_version:
        return path

    check_budget(STAGE_ASSEMBLE, directory, version, run)
    try:
        body = read(source, APPROVED_FILE)
        positive, negative = assemble(body["fields"], schema.names, flow)
        # Read here and thrown away, for the reason the whole stage is here: the
        # render target comes from the photograph's own header, and a header
        # nothing can read must cost an assembly rather than a boot.
        photo_resolution(run.photo)
    except (Refusal, KeyError, TypeError) as broken:
        record = record_failure(
            directory,
            version,
            "permanent",
            {"stage": STAGE_ASSEMBLE, "detail": str(broken)},
        )
        raise Refusal(
            f"{run.id}: flow {flow.id}'s approved sheet cannot be assembled -- "
            f"{broken}; see {record.name} in {flow.id}/{PROMPTS}/"
        ) from broken

    prompt: Prompt = {
        "schema": PROMPT_FILE.schema,
        "producer": {
            "implementation": STAGE_ASSEMBLE,
            "from": version,
            "source": REVIEW,
        },
        "flow": flow.id,
        "positive": positive,
        "negative": negative,
        "edited": bool(body["producer"].get("edited")),
    }
    write(path, PROMPT_FILE, prompt)
    return path


def prepare(run: Run, flows: Mapping[str, Flow]) -> tuple[dict[str, Path], list[str]]:
    """Assemble every approved flow's prompt for one run, before anything is rented.

    A run that has been approved for *nothing* asked for is refused rather than
    returning empty. Selecting among several approved flows still needs no flag --
    the refusal fires only when none of the flows asked for has an approved sheet,
    so "a run renders everything it has been approved for" is unchanged and
    "rendering did nothing and said nothing" is no longer reachable.

    **One flow's malformed sheet costs that flow alone**, and it is `across`
    that says so -- the same call `cli.py` collects photographs with, one axis
    down. The flows of a run are independent -- separate subtrees, separate
    sheets, separate error records -- so a dict comprehension raising at the
    first broken one took every sibling's turn with it, and did it after
    already writing a permanent record (v0.16 R6).
    """
    ready = [flow for flow in approved_flows(run) if flow in flows]
    if flows and not ready:
        asked = ", ".join(sorted(flows))
        # `--flow` is required and repeatable, so the remedy names every flow
        # that was asked for rather than a command argparse would refuse.
        naming = " ".join(f"--flow {one}" for one in sorted(flows))
        raise Refusal(
            f"{run.id}: no approved sheet for {asked}, and only an approved sheet "
            f"is rendered; run `python -m isekai review {naming}`, edit the "
            f"draft, then `python -m isekai approve {naming}`"
        )
    assembled: dict[str, Path] = {}

    def assemble_one(flow: str) -> None:
        assembled[flow] = prompt_artifact(run, flows[flow], flows[flow].schema)

    return assembled, across(ready, assemble_one)


def rendered_seeds(directory: Path, suffix: str) -> list[int]:
    """Return the seeds already produced into `directory`, from filenames alone.

    `suffix` is what the flow says it produces, so the predicate names no format
    of its own. Every "is this done?" check here is a directory listing, and this
    was the one with an extension written into it -- a flow whose output is not a
    still image would have had its finished work reported as missing and rendered
    again, on the one stage that costs money on every pass (design.md D11).
    """
    if not directory.is_dir():
        return []
    return sorted(
        int(path.stem)
        for path in directory.iterdir()
        if path.suffix == suffix and path.stem.isdigit()
    )


def photo_resolution(photo: Path) -> tuple[int, int]:
    """Return the working resolution for `photo`, as a refusal rather than an exit.

    The `sys.exit` that `image_dimensions` reports an unreadable header with is
    turned into a `Refusal` by `shared.image.dimensions_or_refuse`, which owns
    that wrap for every caller -- this one and the review surface's.

    `MAX_TARGET_LONG_SIDE` is enforced here for the same reason and in the same
    currency -- see its own comment in `isekai.shared.image` for what it bounds and why.
    The one fact that belongs here rather than beside the constant: it bounds the
    *working* target and not the hires one, because hires scales both axes by the
    same factor and so does not change the aspect ratio, and bounding the hires
    value would silently tighten 4:1 to 2.67:1 for a reason unrelated to aspect
    (design.md D4).
    """
    width, height = working_resolution(
        *dimensions_or_refuse(
            photo,
            "the render target is derived from the photograph's own header and "
            "there is nothing to fall back to -- re-export the photograph as a "
            "JPEG or PNG and open the run again",
        )
    )
    if max(width, height) > MAX_TARGET_LONG_SIDE:
        raise Refusal(
            f"{photo.name}: a {width}x{height} target is past the "
            f"{MAX_TARGET_LONG_SIDE} limit on the long side; the short-side rule "
            "bounds one axis and this photograph's aspect ratio is extreme -- "
            "crop it closer to the subject and open the run again"
        )
    return width, height


# The dials each sampler takes from the manifest -- the hires pass declares its
# own `denoise` and `steps`, so it takes neither from that list -- now live in
# `foundation/flow.py` beside `ROLE_DIALS`, because `load_flow` validates what
# this module reads and a second copy of the list is a second thing to drift.


def build_graph(
    flow: Flow,
    photo: Path,
    image_name: str | None,
    prompt: Mapping[str, Any],
    seed: int,
) -> Workflow:
    """Return the graph to submit: the flow's own, with its dials and this seed.

    The dials come from the manifest and not from the graph file.
    `summon-anime-wai`'s graph carries cfg 7 and identity strength 0.5; the
    measured configuration is
    5 and 0.8, and a render that used the file's values would be a configuration
    nothing measured (design.md D12).

    **Every patch below is conditional on the flow declaring the role.**
    `load_flow` has already refused a flow missing one of the four required ones,
    so those four always land; a flow without a photograph, an identity adapter, a
    pose preprocessor or a hires pass renders rather than raising on a rented
    machine (design.md D9).
    """
    graph = flow.graph()
    dials = flow.dials
    width, height = photo_resolution(photo)

    def patch(role: str, **values: object) -> None:
        """Set inputs on the node a role names, where the flow declares the role.

        One writer for every role, so a role a flow leaves out is a patch that
        does nothing rather than a branch somebody remembered to add. `load_flow`
        has already refused a flow missing one of the four required roles.
        """
        if role in flow.nodes:
            graph[flow.node(role)]["inputs"].update(values)

    if image_name is not None:
        patch("photo", image=image_name)
    patch("positive", text=prompt["positive"])
    patch("negative", text=prompt["negative"])
    patch("latent", width=width, height=height)
    patch("scale", width=width, height=height)
    patch("sampler", seed=seed, **{dial: dials[dial] for dial in SAMPLER_DIALS})

    # Each guard below reads a dial that only a flow with that role declares --
    # an identity adapter, a pose preprocessor, a clip skip, a hires pass. So the
    # role check happens *before* the lookup, not inside `patch`: an argument is
    # evaluated whether or not the call does anything with it.
    if "identity" in flow.nodes:
        patch(
            "identity",
            ip_weight=dials["ip_weight"],
            cn_strength=dials["identity_cn_strength"],
        )
    if "openpose" in flow.nodes:
        patch("openpose", strength=dials["openpose_strength"])
    if "clip_skip" in flow.nodes:
        patch("clip_skip", stop_at_clip_layer=dials["clip_skip"])
    if "hires_resize" in flow.nodes:
        patch("hires_resize", **_hires_target(flow, width, height))
    if "hires_sampler" in flow.nodes:
        patch(
            "hires_sampler",
            seed=seed,
            steps=dials["hires_steps"],
            denoise=dials["hires_denoise"],
            **{dial: dials[dial] for dial in SECOND_PASS_DIALS},
        )
    return graph


def _hires_target(flow: Flow, width: int, height: int) -> dict[str, int]:
    """Return the hires pass's canvas, refusing one the VAE cannot encode."""
    scale = flow.dials["hires_scale"]
    scaled = {"width": round(width * scale), "height": round(height * scale)}
    # SDXL's VAE needs a multiple of 8. 1.5x of a /64 canvas always is, and this
    # asserts it rather than trusting it.
    if any(side % 8 for side in scaled.values()):
        raise Refusal(
            f"flow {flow.id}: a hires target of {tuple(scaled.values())} is not a "
            "multiple of 8, which the VAE requires; change `hires_scale` under a "
            "new flow identifier"
        )
    return scaled


def graph_digest(graph: Workflow) -> str:
    """Return the digest of the graph as submitted, keys sorted so it is stable."""
    return hashlib.sha256(
        json.dumps(graph, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def render(
    run: Run,
    flow: Flow,
    client: ComfyTransport,
    *,
    count: int | None = None,
    seeds: Sequence[int] | None = None,
    rng: random.Random | None = None,
    poll: float = 1.0,
) -> list[Render]:
    """Render `flow`'s approved sheet for this run, one image per seed.

    Idempotent per image: a seed whose output already exists is not rendered
    again, and raising the count renders only the shortfall. Rendering is the one
    step that costs money on every pass, so it is where idempotence is worth the
    most -- and the decision is a directory listing, the same rule every other
    stage is held to.
    """
    version, _ = approved_artifact(run, flow.id)
    prompt = read(run.directory(flow.id, PROMPTS) / artifact_name(version), PROMPT_FILE)
    directory = run.directory(flow.id, OUTPUTS, f"{version:03d}")
    already = rendered_seeds(directory, flow.output_suffix)
    wanted = seeds_for(count, seeds, rng or random.Random(), already)
    if not wanted:
        return []

    check_budget(STAGE_RENDER, directory, version, run)

    # `flow.inputs` gates the transfer: a flow that does not declare a photograph
    # has nothing to upload, and uploading one anyway spends the endpoint's time
    # on an input no node reads. The patch below it is gated on `flow.nodes`
    # instead, and `load_flow` is what holds the two halves in agreement -- a
    # manifest declaring the photograph on one side alone never loads, so this
    # gate and that one cannot disagree about the same run.
    image_name = client.upload_image(str(run.photo)) if "photo" in flow.inputs else None
    # Constant across seeds: the flow's graph on disk does not change mid-render.
    flow_graph = flow.graph_digest()
    produced: list[Render] = []
    for seed in wanted:
        image = directory / f"{seed}{flow.output_suffix}"
        # `build_graph` is inside the guard and not before it: it refuses on an
        # unreadable photograph header, and a refusal this stage does not record
        # leaves resume nothing on disk to reason about.
        try:
            graph = build_graph(flow, run.photo, image_name, prompt, seed)
            body = _submit(client, graph, poll)
        except Refusal as failed:
            # A closed tunnel says nothing about this graph, and `check_budget`
            # short-circuits a `permanent` record for good -- so recording one
            # here made the operator's remedy deleting a file by hand, on the
            # one failure that is over the moment the pod comes back (v0.13 R7).
            record_failure(
                directory,
                version,
                "transient" if isinstance(failed, Unreachable) else "permanent",
                {"stage": STAGE_RENDER, "seed": seed, "detail": str(failed)},
            )
            raise
        # Atomically, like every other artifact in a run, and for a sharper
        # reason: `rendered_seeds` treats the presence of the render as proof the
        # seed is done, so a truncated file is a seed resume skips forever -- on
        # the one stage that costs money on every pass.
        write_atomically(image, body)
        provenance = directory / f"{seed}.json"
        sidecar: RenderSidecar = {
            "schema": RENDER_FILE.schema,
            "producer": {
                "implementation": STAGE_RENDER,
                "from": version,
                "source": PROMPTS,
            },
            "flow": flow.id,
            "seed": seed,
            "sheet_version": version,
            "graph_sha256": graph_digest(graph),
            "flow_graph_sha256": flow_graph,
            "edited": prompt["edited"],
        }
        write(provenance, RENDER_FILE, sidecar)
        produced.append(Render(seed, image, provenance))
    return produced


def _submit(client: ComfyTransport, graph: Workflow, poll: float) -> bytes:
    """Queue one graph, wait for it, and return the image's bytes."""
    prompt_id = client.submit(graph)
    while prompt_id not in (history := client.history(prompt_id)):
        time.sleep(poll)
    for output in history[prompt_id]["outputs"].values():
        if "images" in output:
            return client.view(output["images"][0])
    raise Refusal(
        "the endpoint returned no image for a graph it accepted; check the pod's "
        "ComfyUI log, then render again"
    )
