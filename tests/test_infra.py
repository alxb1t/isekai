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
    # guarded, so `set -e` cannot terminate the shell that owns sshd
    assert provisioning[0].lstrip().startswith("if !")
    assert "exec tail -f /dev/null" in start_sh


@pytest.mark.spec(
    "model-provisioning:reachability:a-provisioning-abort-holds-the-pod-open"
)
def test_the_hold_replaces_the_inference_server_rather_than_preceding_it(
    start_sh: str,
) -> None:
    lines = start_sh.splitlines()
    hold = next(i for i, line in enumerate(lines) if "exec tail -f /dev/null" in line)
    serve = next(i for i, line in enumerate(lines) if "exec python main.py" in line)
    assert hold < serve
    # nothing on the volume is removed on the failure path
    assert "rm " not in "\n".join(lines[hold - 6 : serve])
