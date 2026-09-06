"""Checks over the tracked pod configuration: the image and the pod lifecycle.

These read the shipped files themselves rather than a fixture copy, for the same
reason the suite reads the shipped graph: a byte-identical copy with no drift
check is a second thing to rename and a silent divergence waiting to happen.
"""

import re
from pathlib import Path

import pytest

from isekai.comfy_types import Workflow
from isekai.provision import (
    MODELS_NAMESPACE,
    MODELS_ROOT,
    VOLUME_MOUNT,
    Manifest,
    annotator_files,
    manifest_dest,
)

REPO = Path(__file__).resolve().parent.parent
DOCKERFILE = REPO / "Dockerfile"


def aux_annotator_ckpts_path(dockerfile: str) -> str | None:
    """Return the `AUX_ANNOTATOR_CKPTS_PATH` the image sets, or None if it sets none.

    None is the failure the scenario names: with the variable unset the pack falls
    back to `<node dir>/ckpts`, which is container disk.
    """
    found = re.search(r"^ENV\s+AUX_ANNOTATOR_CKPTS_PATH=(\S+)", dockerfile, re.M)
    return found.group(1) if found else None


@pytest.fixture(scope="session")
def dockerfile() -> str:
    """Read the shipped `Dockerfile` once for the whole session."""
    return DOCKERFILE.read_text()


@pytest.mark.spec(
    "model-provisioning:namespace:annotator-checkpoints-resolve-onto-the-models-tree"
)
def test_the_image_sets_the_annotator_ckpts_path_inside_the_models_tree(
    dockerfile: str,
) -> None:
    path = aux_annotator_ckpts_path(dockerfile)
    assert path is not None
    assert path.startswith(f"{MODELS_ROOT}/")


@pytest.mark.spec(
    "model-provisioning:namespace:annotator-checkpoints-resolve-onto-the-models-tree"
)
def test_a_configuration_leaving_the_pack_at_its_own_default_fails_the_check() -> None:
    assert aux_annotator_ckpts_path("FROM scratch\nENV PYTHONUNBUFFERED=1\n") is None


@pytest.mark.spec(
    "model-provisioning:namespace:annotator-checkpoints-resolve-onto-the-models-tree"
)
def test_every_annotator_checkpoint_the_graph_needs_lands_under_that_path(
    dockerfile: str, workflow: Workflow, manifest: Manifest
) -> None:
    path = aux_annotator_ckpts_path(dockerfile)
    assert path is not None
    needed = annotator_files(workflow)
    assert len(needed) == 4
    for filename in needed:
        dest = manifest_dest(filename, manifest)
        assert dest is not None
        assert f"{MODELS_ROOT}/{dest}".startswith(f"{path}/")


@pytest.mark.spec_exempt(
    "structural: names the 386 MB the redirect exists to move onto the volume"
)
def test_the_annotator_checkpoints_are_the_four_the_preprocessors_fetch(
    workflow: Workflow,
) -> None:
    assert set(annotator_files(workflow)) == {
        "yolox_l.onnx",
        "dw-ll_ucoco_384_bs5.torchscript.pt",
        "sk_model.pth",
        "sk_model2.pth",
    }


@pytest.fixture(scope="session")
def up_sh() -> str:
    """Read the shipped `infra/up.sh` once for the whole session."""
    return (REPO / "infra" / "up.sh").read_text()


@pytest.fixture(scope="session")
def start_sh() -> str:
    """Read the shipped `start.sh` once for the whole session."""
    return (REPO / "start.sh").read_text()


@pytest.mark.spec_exempt(
    "structural: the mount is a precondition of the namespace, not a scenario"
)
def test_the_pod_mounts_the_volume_at_its_own_root(up_sh: str) -> None:
    assert f'volumeMountPath: "{VOLUME_MOUNT}"' in up_sh


@pytest.mark.spec_exempt(
    "structural: the mount is a precondition of the namespace, not a scenario"
)
def test_the_pod_no_longer_mounts_the_volume_over_the_models_directory(
    up_sh: str,
) -> None:
    assert f'volumeMountPath: "{MODELS_ROOT}"' not in up_sh


@pytest.mark.spec(
    "model-provisioning:namespace:annotator-checkpoints-resolve-onto-the-models-tree"
)
def test_the_pod_symlinks_the_models_directory_onto_this_project_namespace(
    start_sh: str,
) -> None:
    assert MODELS_NAMESPACE.startswith(f"{VOLUME_MOUNT}/")
    assert MODELS_NAMESPACE != VOLUME_MOUNT
    assert 'ln -s "$MODELS_NAMESPACE" "$MODELS_ROOT"' in start_sh
    assert f"MODELS_NAMESPACE={MODELS_NAMESPACE}" in start_sh
    assert f"MODELS_ROOT={MODELS_ROOT}" in start_sh


@pytest.mark.spec_exempt(
    "structural: nothing in this project reaches outside its own namespace"
)
def test_the_pod_startup_touches_nothing_outside_the_project_namespace(
    start_sh: str,
) -> None:
    reaches_out = [
        line
        for line in start_sh.splitlines()
        if not line.lstrip().startswith("#")
        and VOLUME_MOUNT in line
        and MODELS_NAMESPACE not in line
    ]
    assert reaches_out == []


@pytest.fixture(scope="session")
def download_models_sh() -> str:
    """Read the shipped `scripts/download_models.sh` once for the whole session."""
    return (REPO / "scripts" / "download_models.sh").read_text()


@pytest.mark.spec(
    "model-provisioning:source-fallback:a-failed-transfer-advances-to-the-next-source"
)
def test_the_driver_walks_every_source_the_plan_carries(
    download_models_sh: str,
) -> None:
    assert "read -r action dest urls" in download_models_sh
    assert "for url in $urls" in download_models_sh


@pytest.mark.spec(
    "model-provisioning:source-fallback:a-failed-transfer-advances-to-the-next-source"
)
def test_the_driver_aborts_only_once_every_source_is_exhausted(
    download_models_sh: str,
) -> None:
    lines = [line.strip() for line in download_models_sh.splitlines()]
    # a transfer failure and a verification failure each continue the walk ...
    assert lines.count("continue") == 2
    # ... and the only abort on the fetch path is the one after the loop.
    assert "ERROR: every source for $dest failed" in download_models_sh
    assert "landed=0" in download_models_sh


@pytest.mark.spec(
    "model-provisioning:reachability:a-provisioning-abort-holds-the-pod-open"
)
def test_a_provisioning_failure_does_not_take_the_container_down(
    start_sh: str,
) -> None:
    provisioning = [
        line for line in start_sh.splitlines() if "download_models.sh" in line
    ]
    assert len(provisioning) == 1
    # It returns rather than exits, and the step it belongs to is itself guarded,
    # so `set -e` cannot terminate the shell that owns sshd.
    assert provisioning[0].rstrip().endswith("|| return 1")
    assert "if ! provision; then" in start_sh
    assert 'exec sleep "$HOLD_SECONDS"' in start_sh


@pytest.mark.spec(
    "model-provisioning:reachability:a-provisioning-abort-holds-the-pod-open"
)
def test_the_hold_replaces_the_inference_server_rather_than_preceding_it(
    start_sh: str,
) -> None:
    lines = start_sh.splitlines()
    hold = next(
        i for i, line in enumerate(lines) if 'exec sleep "$HOLD_SECONDS"' in line
    )
    serve = next(i for i, line in enumerate(lines) if "exec python main.py" in line)
    assert hold < serve
    # nothing on the volume is removed on the failure path
    assert "rm " not in "\n".join(lines[hold - 6 : serve])


# The pod entrypoint's provisioning step, and the two halves of the volume guard.
#
# These are text checks over the shipped shell, for the same reason the checks
# above are: the suite is offline and there is no pod to run the entrypoint on.
# What they hold is the *shape* the scenarios name -- one guarded provisioning
# step, a bounded hold, a marker off the volume, and a refusal on each side of
# the boundary.

# The repository's per-session spending ceiling, in seconds at the halt.
SESSION_CEILING_SECONDS = 45 * 60


def provision_body(start_sh: str) -> str:
    """Return the body of `start.sh`'s `provision` function.

    The scenario is about provisioning as a whole rather than about one of its
    steps, so what the test needs is which lines are *inside* the guarded unit.
    """
    lines = start_sh.splitlines()
    opens = next(i for i, line in enumerate(lines) if line.startswith("provision()"))
    closes = next(i for i, line in enumerate(lines[opens:], opens) if line == "}")
    return "\n".join(lines[opens : closes + 1])


@pytest.mark.spec("model-provisioning:reachability:namespace-setup-is-held-open-too")
def test_preparing_the_namespace_is_inside_the_guarded_provisioning_step(
    start_sh: str,
) -> None:
    body = provision_body(start_sh)
    # every step of preparing the namespace, and the fetch, in one unit ...
    assert 'mkdir -p "$MODELS_NAMESPACE"' in body
    assert 'ln -s "$MODELS_NAMESPACE" "$MODELS_ROOT"' in body
    assert "download_models.sh" in body
    # ... and no step of it can exit the shell that owns sshd.
    assert "exit " not in body


@pytest.mark.spec("model-provisioning:reachability:namespace-setup-is-held-open-too")
def test_the_whole_provisioning_step_is_guarded_exactly_once(start_sh: str) -> None:
    calls = [
        line.strip()
        for line in start_sh.splitlines()
        if line.strip().startswith(("provision", "if ! provision"))
        and not line.startswith("provision()")
    ]
    assert calls == ["if ! provision; then"]


@pytest.mark.spec("model-provisioning:reachability:namespace-setup-is-held-open-too")
def test_deleting_a_non_empty_mounted_models_tree_is_refused(start_sh: str) -> None:
    body = provision_body(start_sh)
    guard = next(line for line in body.splitlines() if "mountpoint -q" in line)
    # the premise of the delete: the image's own tree on container disk. A
    # non-empty mount here is somebody's real models tree.
    assert 'mountpoint -q "$MODELS_ROOT"' in guard
    assert 'ls -A "$MODELS_ROOT"' in guard
    delete = next(i for i, line in enumerate(body.splitlines()) if "rm -rf" in line)
    assert body.splitlines().index(guard) < delete


@pytest.mark.spec("model-provisioning:reachability:the-hold-is-bounded-and-marked")
def test_the_hold_ends_on_its_own_well_inside_the_session_ceiling(
    start_sh: str,
) -> None:
    bound = re.search(r"^HOLD_SECONDS=(\d+)$", start_sh, re.M)
    assert bound is not None
    assert 0 < int(bound.group(1)) < SESSION_CEILING_SECONDS
    assert 'exec sleep "$HOLD_SECONDS"' in start_sh
    # an indefinite hold bills until a human notices it
    assert "tail -f /dev/null" not in start_sh


@pytest.mark.spec("model-provisioning:reachability:the-hold-is-bounded-and-marked")
def test_the_failure_marker_is_written_off_the_volume(start_sh: str) -> None:
    marker = re.search(r"^FAILURE_MARKER=(\S+)$", start_sh, re.M)
    assert marker is not None
    # the volume is exactly the thing that may have failed
    assert not marker.group(1).startswith(f"{VOLUME_MOUNT}/")
    assert '> "$FAILURE_MARKER"' in start_sh


@pytest.mark.spec(
    "model-provisioning:reachability:provisioning-requires-the-network-volume"
)
def test_the_client_refuses_to_create_a_pod_without_a_named_volume(
    up_sh: str,
) -> None:
    lines = up_sh.splitlines()
    guard = next(i for i, line in enumerate(lines) if 'RUNPOD_VOLUME_ID:-}" ]' in line)
    creates = next(
        i for i, line in enumerate(lines) if "POST https://rest.runpod.io" in line
    )
    assert guard < creates
    assert "exit 1" in "\n".join(lines[guard : guard + 6])


@pytest.mark.spec(
    "model-provisioning:reachability:provisioning-requires-the-network-volume"
)
def test_the_pod_is_told_which_volume_to_expect(up_sh: str) -> None:
    assert "RUNPOD_VOLUME_ID: $vol" in up_sh


@pytest.mark.spec(
    "model-provisioning:reachability:provisioning-requires-the-network-volume"
)
def test_the_entrypoint_refuses_before_preparing_the_namespace(start_sh: str) -> None:
    body = provision_body(start_sh).splitlines()
    named = next(i for i, line in enumerate(body) if 'RUNPOD_VOLUME_ID:-}" ]' in line)
    floor = next(i for i, line in enumerate(body) if "VOLUME_FREE_FLOOR_KIB" in line)
    prepares = next(
        i for i, line in enumerate(body) if 'mkdir -p "$MODELS_NAMESPACE"' in line
    )
    assert named < prepares
    assert floor < prepares
    # a free-space floor, not `mountpoint`: RunPod mounts the pod's own volume
    # disk at the same path when no network volume is attached, so the path is a
    # mountpoint either way.
    assert "df -k --output=avail" in "\n".join(body)
