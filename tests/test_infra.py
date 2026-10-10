"""Checks over the tracked pod configuration: the image and the pod lifecycle.

These read the shipped files themselves rather than a fixture copy, for the same
reason the suite reads the shipped graph: a byte-identical copy with no drift
check is a second thing to rename and a silent divergence waiting to happen.
"""

import json
import os
import re
import shlex
import subprocess
import tomllib
from pathlib import Path

import pytest

from isekai.boundary.provision import (
    MANIFEST_PATH,
    MODELS_NAMESPACE,
    MODELS_ROOT,
    VOLUME_MOUNT,
    Manifest,
    annotator_files,
    manifest_dest,
)
from isekai.foundation.flow import Workflow
from tools.derive_image_project import CLONE, pinned_commits, uv_required
from tools.image_record import record

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
    assert len(needed) == 2
    for filename in needed:
        dest = manifest_dest(filename, manifest)
        assert dest is not None
        assert f"{MODELS_ROOT}/{dest}".startswith(f"{path}/")


@pytest.mark.spec_exempt(
    "structural: names the 352 MB the redirect exists to move onto the volume"
)
def test_the_annotator_checkpoints_are_the_two_the_preprocessors_fetch(
    workflow: Workflow,
) -> None:
    assert set(annotator_files(workflow)) == {
        "yolox_l.onnx",
        "dw-ll_ucoco_384_bs5.torchscript.pt",
    }


@pytest.fixture(scope="session")
def start_sh() -> str:
    """Read the shipped `start.sh` once for the whole session."""
    return (REPO / "start.sh").read_text()


@pytest.mark.spec(
    "model-provisioning:namespace:annotator-checkpoints-resolve-onto-the-models-tree"
)
def test_the_pod_symlinks_the_models_directory_onto_this_project_namespace(
    start_sh: str,
) -> None:
    assert MODELS_NAMESPACE.startswith(f"{VOLUME_MOUNT}/")
    assert MODELS_NAMESPACE != VOLUME_MOUNT
    assert 'ln -s "$MODELS_NAMESPACE" "$MODELS_ROOT"' in start_sh
    project = MODELS_NAMESPACE.removeprefix(VOLUME_MOUNT)
    assert f'MODELS_NAMESPACE="${{GPUNIT_VOLUME_PATH:-}}{project}"' in start_sh
    assert f"MODELS_ROOT={MODELS_ROOT}" in start_sh


@pytest.mark.spec_exempt(
    "structural: nothing in this project reaches outside its own namespace"
)
def test_the_pod_startup_touches_nothing_outside_the_project_namespace(
    start_sh: str,
) -> None:
    # The volume's path is read to name the namespace and to refuse an unset one.
    reaches_out = [
        line.strip()
        for line in start_sh.splitlines()
        if not line.lstrip().startswith("#")
        and (re.search(r"\$\{?GPUNIT_VOLUME_PATH", line) or VOLUME_MOUNT in line)
        and not line.startswith("MODELS_NAMESPACE=")
        and '[ -z "${GPUNIT_VOLUME_PATH:-}" ]' not in line
    ]
    assert reaches_out == []


@pytest.fixture(scope="session")
def download_models_sh() -> str:
    """Read the shipped `tools/download_models.sh` once for the whole session."""
    return (REPO / "tools" / "download_models.sh").read_text()


@pytest.mark.spec(
    "model-provisioning:source-fallback:a-failed-transfer-advances-to-the-next-source"
)
def test_the_driver_walks_every_source_the_plan_carries(
    download_models_sh: str,
) -> None:
    assert "read -r -a fields" in download_models_sh
    assert 'urls=("${fields[@]:2}")' in download_models_sh
    assert 'for url in "${urls[@]}"' in download_models_sh
    # the word split is gone, and so is the suppression that made it legal
    assert "SC2086" not in download_models_sh
    assert "for url in $urls" not in download_models_sh


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
    assert "ERROR: every source for $target failed" in download_models_sh
    assert "landed=0" in download_models_sh


def hold_calls(script: str) -> list[int]:
    """Return the index of each line that calls `hold`."""
    return [
        i
        for i, ln in enumerate(script.splitlines())
        if ln.lstrip().startswith('hold "')
    ]


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
    assert hold_calls(boot_step(start_sh, "provisioning"))


@pytest.mark.spec(
    "model-provisioning:reachability:a-provisioning-abort-holds-the-pod-open"
)
def test_the_hold_replaces_the_inference_server_rather_than_preceding_it(
    start_sh: str,
) -> None:
    lines = start_sh.splitlines()
    hold = hold_calls(start_sh)[0]
    serve = next(i for i, line in enumerate(lines) if "python main.py" in line)
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


def shell_function(script: str, name: str) -> str:
    """Return the definition of `name` as the script writes it, or "" if absent.

    e.g. `g` in a script holding `g() { :; }` -> "g() { :; }"
    """
    lines = script.splitlines()
    start = next(
        (i for i, ln in enumerate(lines) if ln.startswith(f"{name}() {{")), None
    )
    if start is None:
        return ""
    if lines[start].rstrip().endswith("}"):
        return lines[start]
    end = next(i for i in range(start, len(lines)) if lines[i] == "}")
    return "\n".join(lines[start : end + 1])


def provision_body(start_sh: str) -> str:
    """Return the body of `start.sh`'s `provision` function.

    The scenario is about provisioning as a whole rather than about one of its
    steps, so what the test needs is which lines are *inside* the guarded unit.
    """
    return shell_function(start_sh, "provision")


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
    hold = shell_function(start_sh, "hold")
    assert 'sleep "$HOLD_SECONDS"' in hold
    # a hold that returns leaves the pod billing; its exit is the boot script's stop
    assert hold.removesuffix("}").rstrip().endswith("exit 1")
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
def test_the_entrypoint_refuses_before_preparing_the_namespace(start_sh: str) -> None:
    body = provision_body(start_sh).splitlines()
    named = next(i for i, line in enumerate(body) if 'GPUNIT_VOLUME_ID:-}" ]' in line)
    floor = next(i for i, line in enumerate(body) if "VOLUME_SIZE_FLOOR_KIB" in line)
    prepares = next(
        i for i, line in enumerate(body) if 'mkdir -p "$MODELS_NAMESPACE"' in line
    )
    assert named < prepares
    assert floor < prepares
    # a capacity floor, not `mountpoint`: RunPod mounts the pod's own volume
    # disk at the same path when no network volume is attached, so the path is a
    # mountpoint either way.
    assert "df -k --output=size" in "\n".join(body)


@pytest.mark.spec(
    "model-provisioning:reachability:provisioning-requires-the-network-volume"
)
def test_the_volume_guard_measures_capacity_rather_than_fill_level(
    start_sh: str,
) -> None:
    # What the guard proves is identity -- the 20 GB ephemeral container disk is
    # not the network volume -- and capacity discriminates those two whatever the
    # volume's fill level is. Free space does not: this project already put
    # the models on a volume it shares with a second project, so a floor on
    # availability degrades as the volume fills and would refuse a warm boot that
    # needed to download nothing.
    body = provision_body(start_sh)
    assert "--output=avail" not in body
    floor = re.search(r"^VOLUME_SIZE_FLOOR_KIB=", start_sh, re.M)
    assert floor is not None
    # and the message says what is measured
    assert "free" not in body.lower()


@pytest.mark.spec_exempt(
    "structural: a clone with no checkout is not a pin, and this holds every clone"
)
def test_every_git_clone_in_the_image_is_pinned_to_a_commit(dockerfile: str) -> None:
    clones = CLONE.findall(dockerfile)
    assert clones
    assert len(pinned_commits(dockerfile)) == len(clones)


@pytest.mark.spec_exempt(
    "structural: twin of test_every_git_clone_in_the_image_is_pinned_to_a_commit"
)
@pytest.mark.parametrize(
    "unpinned",
    [
        "RUN git clone --depth 1 https://github.com/c/d.git /d\n",
        "RUN git clone https://gitlab.com/c/d.git /d\n",
        "RUN git -C /opt clone https://github.com/c/d.git\n",
        "RUN git -c advice.detachedHead=false clone https://github.com/c/d.git /d\n",
        "ADD https://github.com/c/d.git /d\n",
        "ADD ssh://deploy@example.com/nodes /opt/nodes\n",
        "ADD deploy@example.com:nodes /opt/nodes\n",
        'ADD ["deploy@example.com:nodes", "/opt/nodes"]\n',
    ],
    ids=[
        "a-flag",
        "another-host",
        "a-directory-option",
        "a-config-option",
        "an-add",
        "an-ssh-add",
        "an-scp-add",
        "an-scp-exec-add",
    ],
)
def test_the_count_catches_a_clone_with_a_flag_and_another_host(
    unpinned: str,
) -> None:
    pinned = f"RUN git clone https://github.com/a/b.git /b && git checkout {'0' * 40}\n"
    assert pinned_commits(pinned) == {"a/b": "0" * 40}
    with pytest.raises(SystemExit):
        pinned_commits(pinned + unpinned)


@pytest.mark.spec(
    "model-provisioning:immutable-pins:an-escaping-destination-is-refused"
)
def test_the_driver_joins_no_path_of_its_own(download_models_sh: str) -> None:
    assert 'target="${MODELS_DIR}/${dest}"' not in download_models_sh
    assert 'target="${fields[1]:-}"' in download_models_sh


@pytest.mark.spec(
    "model-provisioning:reachability:provisioning-requires-the-network-volume"
)
def test_the_capacity_floor_clears_the_container_disk_as_well(
    start_sh: str, gpunit_spec: dict[str, object]
) -> None:
    # The one case this pod-side guard still exists for is the one the laptop
    # cannot see: the id is set and the mount silently failed, so the volume's path
    # resolves to the container overlay rather than to the volume (D27).
    # That overlay's backing disk is the container `disk`, LARGER than the
    # pod's own volume disk, so a floor that only clears the volume disk lets the
    # overlay through and the models land on storage that dies at teardown.
    floor = re.search(
        r"^VOLUME_SIZE_FLOOR_KIB=\$\(\((\d+) \* 1024 \* 1024\)\)", start_sh, re.M
    )
    assert floor is not None
    container_disk = gpunit_spec.get("disk_gb")
    assert isinstance(container_disk, int)
    # RunPod states those sizes in decimal GB, and decimal is the reading that
    # makes the disk look BIGGEST in KiB, so it is the one the floor must clear.
    largest_container_kib = container_disk * 1000**3 // 1024
    assert int(floor.group(1)) * 1024 * 1024 > largest_container_kib


# The image mirrors the repository's layout, and no boot proves a rebuilt image
# before a pod uses it, so these hold its paths statically.

IMAGE_ROOT = "/opt/isekai"


def image_copies(dockerfile: str) -> dict[str, str]:
    """Return each destination a `COPY` from the build context names, to its source.

    e.g. `COPY start.sh /start.sh` -> {"/start.sh": "start.sh"}
    """
    found = re.findall(r"^COPY\s+(?!--)(\S+)\s+(\S+)\s*$", dockerfile, re.M)
    return {dest: source for source, dest in found}


def missing_copy_sources(dockerfile: str) -> list[str]:
    """Return each `COPY` source that is not a file in the repository."""
    return [
        source
        for source in image_copies(dockerfile).values()
        if not (REPO / source).is_file()
    ]


def uncopied_provisioner(dockerfile: str, start_sh: str) -> str | None:
    """Return the provisioner the entrypoint runs, or None if the image copies it."""
    found = re.search(rf"bash ({IMAGE_ROOT}/\S+/download_models\.sh)", start_sh)
    assert found is not None
    called = found.group(1)
    return None if called in image_copies(dockerfile) else called


def manifest_in_image() -> str:
    """Return where `provision.py`'s anchor finds the manifest inside the image."""
    return f"{IMAGE_ROOT}/{MANIFEST_PATH.relative_to(REPO).as_posix()}"


@pytest.mark.spec_exempt("structural: the image copies files the repository holds")
def test_every_file_the_image_copies_exists(dockerfile: str) -> None:
    assert image_copies(dockerfile)
    assert missing_copy_sources(dockerfile) == []


@pytest.mark.spec_exempt("structural: twin of test_every_file_the_image_copies_exists")
def test_the_check_catches_a_copy_of_a_file_that_is_gone() -> None:
    broken = "FROM scratch\nCOPY start.sh /start.sh\nCOPY gone/models.json /x\n"
    assert missing_copy_sources(broken) == ["gone/models.json"]


@pytest.mark.spec_exempt("structural: the entrypoint runs a script the image holds")
def test_the_entrypoint_runs_the_provisioner_the_image_copies(
    dockerfile: str, start_sh: str
) -> None:
    assert uncopied_provisioner(dockerfile, start_sh) is None


@pytest.mark.spec_exempt(
    "structural: twin of test_the_entrypoint_runs_the_provisioner_the_image_copies"
)
def test_the_check_catches_an_entrypoint_calling_a_path_not_copied() -> None:
    broken = f"COPY x/download_models.sh {IMAGE_ROOT}/x/download_models.sh\n"
    start_sh = f"bash {IMAGE_ROOT}/y/download_models.sh || return 1\n"
    assert (
        uncopied_provisioner(broken, start_sh) == f"{IMAGE_ROOT}/y/download_models.sh"
    )


@pytest.mark.spec_exempt(
    "structural: the provisioner's anchor resolves to a file inside the image"
)
def test_the_manifest_the_provisioner_reads_is_copied_where_it_looks(
    dockerfile: str,
) -> None:
    assert manifest_in_image() in image_copies(dockerfile)


@pytest.mark.spec_exempt(
    "structural: twin of "
    "test_the_manifest_the_provisioner_reads_is_copied_where_it_looks"
)
def test_the_check_catches_a_manifest_copied_beside_where_it_looks() -> None:
    broken = f"COPY models.json {IMAGE_ROOT}/elsewhere/models.json\n"
    assert manifest_in_image() not in image_copies(broken)


# The image is built on request, from inputs named by digest, into a locked
# environment (D28).

BUILD_WORKFLOW = REPO / ".github" / "workflows" / "build-image.yml"


def workflow_triggers(workflow: str) -> list[str]:
    """Return the event names under a workflow's top-level `on:` key.

    e.g. `on:` over `push:` and `workflow_dispatch:` -> ["push", "workflow_dispatch"]
    """
    lines = workflow.splitlines()
    opens = lines.index("on:")
    triggers = []
    for line in lines[opens + 1 :]:
        if line and not line.startswith(" "):
            break
        found = re.match(r"^  ([a-z_]+):", line)
        if found:
            triggers.append(found.group(1))
    return triggers


@pytest.mark.spec("pod-image:build:only-a-request-builds")
def test_the_image_workflow_builds_only_on_a_manual_request() -> None:
    workflow = BUILD_WORKFLOW.read_text()
    assert workflow_triggers(workflow) == ["workflow_dispatch"]
    assert "${{ steps.build.outputs.digest }}" in workflow
    assert "$GITHUB_STEP_SUMMARY" in workflow


@pytest.mark.spec_exempt(
    "structural: twin of test_the_image_workflow_builds_only_on_a_manual_request"
)
def test_the_check_catches_a_workflow_that_builds_on_a_push() -> None:
    workflow = "on:\n  push:\n    branches: [main]\n  workflow_dispatch:\njobs:\n"
    assert workflow_triggers(workflow) == ["push", "workflow_dispatch"]


def record_faults(config: dict[str, object], derived: dict[str, str]) -> list[str]:
    """Return each file whose recorded SHA-256 is not the tree's, by path.

    e.g. `start.sh` edited after the record -> ["start.sh"]
    """
    files = config.get("files")
    if not isinstance(files, dict):
        return ["config/image.json records no files"]
    names = sorted({str(name) for name in files} | set(derived))
    return [name for name in names if files.get(name) != derived.get(name)]


@pytest.mark.spec("pod-image:build:the-record-matches-the-tree")
def test_the_build_record_agrees_with_the_tree() -> None:
    derived = record()
    assert {"Dockerfile", "start.sh"} <= set(derived)
    assert record_faults(json.loads(IMAGE_CONFIG.read_text()), derived) == []


@pytest.mark.spec_exempt(
    "structural: twin of test_the_build_record_agrees_with_the_tree"
)
def test_the_record_check_catches_a_file_edited_after_the_record(
    tmp_path: Path,
) -> None:
    (tmp_path / "Dockerfile").write_text("FROM x\nCOPY a.sh /a.sh\n")
    (tmp_path / "a.sh").write_text("echo one\n")
    config: dict[str, object] = {"files": record(tmp_path)}
    assert record_faults(config, record(tmp_path)) == []
    (tmp_path / "a.sh").write_text("echo two\n")
    assert record_faults(config, record(tmp_path)) == ["a.sh"]
    (tmp_path / "Dockerfile").write_text("FROM x\nCOPY a.sh /a.sh\nCOPY b.sh /b\n")
    (tmp_path / "b.sh").write_text("")
    assert record_faults(config, record(tmp_path)) == ["Dockerfile", "a.sh", "b.sh"]
    assert record_faults({}, record(tmp_path)) == ["config/image.json records no files"]


def unprinted_record(workflow: str) -> list[str]:
    """Return what the image workflow lacks of printing the build record it checked out.

    e.g. a workflow that never runs the tool -> ["never runs tools.image_record"]
    """
    lines = workflow.splitlines()
    tool = re.compile(r"python3? -m tools\.image_record\b")
    runs = next((i for i, ln in enumerate(lines) if tool.search(ln)), None)
    if runs is None:
        return ["never runs tools.image_record"]
    faults = []
    checkout = next(
        (i for i, ln in enumerate(lines) if "actions/checkout@" in ln), None
    )
    if checkout is None or checkout > runs:
        faults.append("runs it before the checkout")
    if "GITHUB_STEP_SUMMARY" not in "\n".join(lines[runs : runs + 3]):
        faults.append("does not write it to the summary")
    return faults


@pytest.mark.spec("pod-image:build:the-workflow-prints-the-record")
def test_the_image_workflow_prints_the_build_record() -> None:
    assert unprinted_record(BUILD_WORKFLOW.read_text()) == []


@pytest.mark.spec_exempt(
    "structural: twin of test_the_image_workflow_prints_the_build_record"
)
def test_the_print_check_catches_a_record_missing_late_or_unsummarised() -> None:
    checkout = "      - uses: actions/checkout@0000 # v4\n"
    printed = (
        "      - run: |\n          {\n            python3 -m tools.image_record\n"
        '          } >> "$GITHUB_STEP_SUMMARY"\n'
    )
    assert unprinted_record(checkout + printed) == []
    assert unprinted_record(checkout) == ["never runs tools.image_record"]
    assert unprinted_record(printed + checkout) == ["runs it before the checkout"]
    stdout = "      - run: python3 -m tools.image_record\n"
    assert unprinted_record(checkout + stdout) == ["does not write it to the summary"]


def undigested_images(dockerfile: str) -> list[str]:
    """Return each image used without a digest, and each URL added without a checksum.

    e.g. `ADD https://h/x /x` -> ["https://h/x"]
    """
    named = re.findall(r"^FROM\s+(\S+)", dockerfile, re.M)
    named += re.findall(r"^COPY\s+--from=(\S+)", dockerfile, re.M)
    unpinned = [i for i in named if not re.search(r"@sha256:[0-9a-f]{64}$", i)]
    for line in joined_lines(dockerfile):
        added = re.match(r"ADD\s+((?:--\S+\s+)*)(https?://\S+)", line)
        if added and not re.search(r"--checksum=sha256:[0-9a-f]{64}\s", added[1]):
            unpinned.append(added[2])
    return unpinned


@pytest.mark.spec("pod-image:build:inputs-are-named-by-digest")
def test_the_base_and_the_build_tool_are_named_by_digest(dockerfile: str) -> None:
    assert re.search(r"^FROM\s", dockerfile, re.M)
    assert re.search(r"^COPY\s+--from=", dockerfile, re.M)
    assert re.search(r"^ADD\s+--checksum=", dockerfile, re.M)
    assert undigested_images(dockerfile) == []


@pytest.mark.spec_exempt(
    "structural: twin of test_the_base_and_the_build_tool_are_named_by_digest"
)
def test_the_check_catches_an_image_named_by_tag() -> None:
    broken = (
        "FROM ubuntu:22.04\nCOPY --from=ghcr.io/astral-sh/uv:latest /uv /\n"
        "ADD --chmod=755 \\\n    https://example.com/boot.sh /boot.sh\n"
        f"ADD --checksum=sha256:{'0' * 64} https://example.com/kept.sh /kept.sh\n"
    )
    assert undigested_images(broken) == [
        "ubuntu:22.04",
        "ghcr.io/astral-sh/uv:latest",
        "https://example.com/boot.sh",
    ]


def uv_versions_apart(
    root: str, workflows: dict[str, str], dockerfile: str, image: str
) -> list[str]:
    """Return each place naming a uv version other than the root project's.

    `workflows` maps each workflow's name to its text; one that sets up uv
    names a version. e.g. a `Dockerfile` copying `uv:0.8.24` under `==0.12.19`
    -> ["Dockerfile"]
    """
    named: dict[str, str | None] = {}
    for name, workflow in workflows.items():
        if "astral-sh/setup-uv@" not in workflow:
            continue
        setup = re.search(
            r"astral-sh/setup-uv@.*\n(?:.*\n)*?\s+version:\s*\"?([\w.]+)", workflow
        )
        named[name] = f"=={setup.group(1)}" if setup else None
    copied = re.search(
        r"^COPY\s+--from=ghcr\.io/astral-sh/uv:([\w.]+)@", dockerfile, re.M
    )
    named["Dockerfile"] = f"=={copied.group(1)}" if copied else None
    named["image/pyproject.toml"] = uv_required(image)
    return [where for where, version in named.items() if version != uv_required(root)]


@pytest.mark.spec_exempt(
    "structural: one uv version, in every workflow, the image and both projects"
)
def test_every_uv_version_the_build_names_is_the_root_projects(
    dockerfile: str,
) -> None:
    workflows = {path.name: path.read_text() for path in WORKFLOWS}
    assert "ci.yml" in workflows and "drift.yml" in workflows
    apart = uv_versions_apart(
        (REPO / "pyproject.toml").read_text(),
        workflows,
        dockerfile,
        IMAGE_PROJECT.read_text(),
    )
    assert apart == []


@pytest.mark.spec_exempt(
    "structural: twin of test_every_uv_version_the_build_names_is_the_root_projects"
)
def test_the_check_catches_a_uv_version_that_drifted() -> None:
    root = '[tool.uv]\nrequired-version = "==0.12.19"\n'
    setup = (
        "      - uses: astral-sh/setup-uv@abc # v6\n"
        "        with:\n"
        '          version: "{}"\n'
    )
    workflows = {
        "ci.yml": setup.format("0.12.19"),
        "drift.yml": setup.format("0.8.24"),
        "unversioned.yml": "      - uses: astral-sh/setup-uv@abc # v6\n",
        "build-image.yml": "      - uses: actions/checkout@abc # v4\n",
    }
    dockerfile = (
        "COPY --from=ghcr.io/astral-sh/uv:0.8.24@sha256:abc /uv /usr/local/bin/\n"
    )
    image = '[tool.uv]\nrequired-version = "==0.8.24"\n'
    assert uv_versions_apart(root, workflows, dockerfile, image) == [
        "drift.yml",
        "unversioned.yml",
        "Dockerfile",
        "image/pyproject.toml",
    ]


def unlocked_installs(dockerfile: str) -> list[str]:
    """Return each build line that resolves packages instead of syncing the lock."""
    return [
        line.strip()
        for line in dockerfile.splitlines()
        if re.search(r"\bpip install\b|\buv venv\b|\s-r\s", line)
        or ("uv sync" in line and "--locked" not in line)
    ]


@pytest.mark.spec("pod-image:build:the-environment-is-locked")
def test_the_environment_is_installed_from_the_committed_lock(
    dockerfile: str,
) -> None:
    assert "uv sync --locked" in dockerfile
    assert "image/uv.lock" in image_copies(dockerfile).values()
    assert unlocked_installs(dockerfile) == []


@pytest.mark.spec_exempt(
    "structural: twin of test_the_environment_is_installed_from_the_committed_lock"
)
def test_the_check_catches_a_resolving_install() -> None:
    broken = "RUN uv pip install -r requirements.txt\nRUN uv sync\n"
    assert unlocked_installs(broken) == [
        "RUN uv pip install -r requirements.txt",
        "RUN uv sync",
    ]


IMAGE_PROJECT = REPO / "image" / "pyproject.toml"


def unhashed_build_tools(image_pyproject: str) -> list[str]:
    """Return each build constraint not named by exact version with a sha256 hash.

    e.g. `"cython==3.3.0"` -> ["cython==3.3.0"]
    """
    uv = tomllib.loads(image_pyproject)["tool"]["uv"]
    tools = uv.get("build-constraint-dependencies", [])
    if not tools:
        return ["none listed"]
    unhashed = []
    for tool in tools:
        tool = tool if isinstance(tool, dict) else {"requirement": tool}
        named, hashes = tool.get("requirement", ""), tool.get("hashes", [])
        if not (
            re.fullmatch(r"[\w.-]+==[\w.]+", named)
            and hashes
            and all(re.fullmatch(r"sha256:[0-9a-f]{64}", h) for h in hashes)
        ):
            unhashed.append(named)
    return unhashed


@pytest.mark.spec("pod-image:build:the-build-tools-are-hashed")
def test_the_build_tools_are_checked_by_hash() -> None:
    assert unhashed_build_tools(IMAGE_PROJECT.read_text()) == []


@pytest.mark.spec_exempt("structural: twin of test_the_build_tools_are_checked_by_hash")
def test_the_check_catches_a_build_tool_by_version_alone() -> None:
    assert unhashed_build_tools("[tool.uv]\n") == ["none listed"]
    digest = "sha256:" + "0" * 64
    image_pyproject = (
        "[tool.uv]\nbuild-constraint-dependencies = [\n"
        '    "cython==3.3.0",\n'
        f'    {{ requirement = "numpy>=2", hashes = ["{digest}"] }},\n'
        '    { requirement = "setuptools==84.0.0", hashes = [] },\n'
        f'    {{ requirement = "wheel==0.45.0", hashes = ["{digest}"] }},\n'
        "]\n"
    )
    assert unhashed_build_tools(image_pyproject) == [
        "cython==3.3.0",
        "numpy>=2",
        "setuptools==84.0.0",
    ]


IMAGE_LOCK = REPO / "image" / "uv.lock"

# Each source-only package in the image's lock, by name and version, to the tools its
# build asks for: its `build-system.requires`, or setuptools for a `setup.py` with none.
# A bump is a new key, so it fails until its tools are read again.
SDIST_BUILDS = {
    ("antlr4-python3-runtime", "4.9.3"): ("setuptools",),
    ("fvcore", "0.1.5.post20221221"): ("setuptools",),
    ("insightface", "0.7.3"): ("setuptools", "numpy", "cython"),
    ("iopath", "0.1.10"): ("setuptools",),
}


def uncovered_sdists(image_lock: str, image_pyproject: str) -> list[str]:
    """Return each source-only package whose build tools the constraints do not name.

    e.g. a lock gaining `pycocotools` 2.0.8 as an sdist alone -> ["pycocotools 2.0.8"]
    """
    tools = tomllib.loads(image_pyproject)["tool"]["uv"].get(
        "build-constraint-dependencies", []
    )
    named = {
        re.split(r"[=<>!~ ]", tool if isinstance(tool, str) else tool["requirement"])[0]
        for tool in tools
    }
    uncovered = []
    for package in tomllib.loads(image_lock)["package"]:
        if "sdist" not in package or package.get("wheels"):
            continue
        name, version = package["name"], package["version"]
        if (name, version) not in SDIST_BUILDS:
            uncovered.append(f"{name} {version}")
            continue
        build = SDIST_BUILDS[name, version]
        uncovered += [f"{name}: {t}" for t in build if t not in named]
    return uncovered


@pytest.mark.spec("pod-image:build:the-build-tools-are-hashed")
def test_every_source_only_package_builds_with_constrained_tools() -> None:
    assert uncovered_sdists(IMAGE_LOCK.read_text(), IMAGE_PROJECT.read_text()) == []


@pytest.mark.spec_exempt(
    "structural: twin of test_every_source_only_package_builds_with_constrained_tools"
)
def test_the_check_catches_a_source_only_package_the_constraints_miss() -> None:
    lock = IMAGE_LOCK.read_text()
    image_lock = lock + (
        '\n[[package]]\nname = "pycocotools"\nversion = "2.0.8"\n'
        'source = { registry = "https://pypi.org/simple" }\n'
        'sdist = { url = "https://example.invalid/pycocotools-2.0.8.tar.gz" }\n'
    )
    image_pyproject = IMAGE_PROJECT.read_text()
    assert uncovered_sdists(image_lock, image_pyproject) == ["pycocotools 2.0.8"]
    bumped = lock.replace(
        'name = "insightface"\nversion = "0.7.3"',
        'name = "insightface"\nversion = "0.7.4"',
    )
    assert uncovered_sdists(bumped, image_pyproject) == ["insightface 0.7.4"]
    no_cython = re.sub(r'\{ requirement = "cython==[^}]*\},?', "", image_pyproject)
    assert uncovered_sdists(lock, no_cython) == ["insightface: cython"]


# The line each step of `start.sh` begins with: provisioning, the download inside
# it, the memory directories, and ComfyUI.
BOOT_STEPS = (
    "if ! provision; then",
    'MODELS_DIR="$MODELS_ROOT" bash',
    "mkdir -p /dev/shm/comfyui/input",
    "exec python main.py",
)


def unstamped_steps(start_sh: str) -> list[str]:
    """Return each boot step whose line is not preceded by a UTC timestamp."""
    lines = [line.strip() for line in start_sh.splitlines()]
    unstamped = []
    for step in BOOT_STEPS:
        at = next(i for i, line in enumerate(lines) if line.startswith(step))
        if "date -u" not in lines[at - 1]:
            unstamped.append(step)
    return unstamped


@pytest.mark.spec("pod-image:boot:each-step-is-timestamped")
def test_each_boot_step_prints_a_utc_time_before_it_begins(start_sh: str) -> None:
    assert unstamped_steps(start_sh) == []


@pytest.mark.spec_exempt(
    "structural: twin of test_each_boot_step_prints_a_utc_time_before_it_begins"
)
def test_the_check_catches_a_step_with_no_timestamp() -> None:
    stamped = "\n".join(f'echo "$(date -u +%FT%TZ)"\n{step}' for step in BOOT_STEPS)
    assert unstamped_steps(stamped) == []
    assert unstamped_steps(
        stamped.replace('echo "$(date -u +%FT%TZ)"\nexec python', "exec python")
    ) == ["exec python main.py"]


# The pod's own host key, and ComfyUI's writing kept in memory: text checks over
# the shipped files, proved on a pod.


def joined_lines(text: str) -> list[str]:
    """Return each line of a script, its continuation lines joined into one."""
    return re.sub(r"\\\n", " ", text).splitlines()


def baked_host_key_faults(dockerfile: str) -> list[str]:
    """Return how a host key could reach the image.

    Kept by the layer installing the SSH server, or made or installed again by any
    other line; comments are not read.
    """
    lines = [
        line for line in joined_lines(dockerfile) if not line.lstrip().startswith("#")
    ]
    install = next(
        line for line in lines if line.startswith("RUN ") and "openssh-server" in line
    )
    faults = []
    if install.find("rm -f /etc/ssh/ssh_host_*") < install.index("openssh-server"):
        faults.append("the install layer keeps its keys")
    if any(
        word in line
        for line in lines
        if line is not install
        for word in ("ssh_host_", "ssh-keygen", "openssh")
    ):
        faults.append("another line touches the SSH server's keys")
    return faults


@pytest.mark.spec("pod-image:host-key:the-image-carries-none")
def test_the_image_carries_no_host_key(dockerfile: str) -> None:
    assert baked_host_key_faults(dockerfile) == []


@pytest.mark.spec_exempt("structural: twin of test_the_image_carries_no_host_key")
def test_the_check_catches_a_host_key_kept_or_made_again() -> None:
    install = (
        "# the keys `openssh-server` makes are deleted here\n"
        "RUN apt-get install -y \\\n        openssh-server \\\n"
        "    && rm -f /etc/ssh/ssh_host_* \\\n"
        "    && rm -rf /var/lib/apt/lists/*\n"
    )
    assert baked_host_key_faults(install) == []
    later = install.replace(" \\\n    && rm -f", "\nRUN rm -f")
    assert baked_host_key_faults(later) == [
        "the install layer keeps its keys",
        "another line touches the SSH server's keys",
    ]
    before = (
        "RUN rm -f /etc/ssh/ssh_host_* \\\n    && apt-get install -y openssh-server\n"
    )
    assert baked_host_key_faults(before) == ["the install layer keeps its keys"]
    for again in ("RUN ssh-keygen -A", "RUN dpkg-reconfigure openssh-server"):
        assert baked_host_key_faults(f"{install}{again}\n") == [
            "another line touches the SSH server's keys"
        ]


def boot_step(start_sh: str, name: str) -> str:
    """Return the `start.sh` step `name` opens, from its timestamp to its blank line."""
    lines = start_sh.splitlines()
    opens = next(i for i, line in enumerate(lines) if line.endswith(f'step: {name}"'))
    closes = next(i for i, line in enumerate(lines[opens:], opens) if not line)
    return "\n".join(lines[opens:closes])


BOOT_SCRIPT = "/opt/gpunit/boot.sh"
BOOT_SOURCE = "https://raw.githubusercontent.com/alxb1t/gpunit/{tag}/boot/boot.sh"


def gpunit_tag(pyproject: str) -> str | None:
    """Return the tag `pyproject.toml` pins gpunit at, or None if it pins none."""
    pinned = re.search(
        r'"gpunit @ git\+https://github\.com/alxb1t/gpunit@([\w.]+)"', pyproject
    )
    return pinned[1] if pinned else None


def boot_script_faults(dockerfile: str, pyproject: str) -> list[str]:
    """Return how the image's entrypoint departs from gpunit's boot script at its pin.

    e.g. a build file holding `CMD ["/start.sh"]` alone ->
    ["the boot script is not added ...", "the entrypoint is not ..."]
    """
    lines = [ln for ln in joined_lines(dockerfile) if not ln.lstrip().startswith("#")]
    tag = gpunit_tag(pyproject)
    source = re.escape(BOOT_SOURCE.format(tag=tag or "?"))
    added = re.compile(
        rf"^ADD --checksum=sha256:[0-9a-f]{{64}}\s+{source}\s+{BOOT_SCRIPT}$"
    )
    faults = []
    if tag is None or not any(added.match(ln) for ln in lines):
        faults.append("the boot script is not added at gpunit's pin with a checksum")
    entry = [ln for ln in lines if ln.startswith("ENTRYPOINT")]
    if entry != [f'ENTRYPOINT ["{BOOT_SCRIPT}", "--"]']:
        faults.append("the entrypoint is not the boot script followed by --")
    return faults


@pytest.mark.spec("pod-image:host-key:each-boot-makes-and-prints-one")
def test_each_boot_runs_gpunits_boot_script_at_its_pin(dockerfile: str) -> None:
    pyproject = (REPO / "pyproject.toml").read_text()
    assert gpunit_tag(pyproject) is not None
    assert boot_script_faults(dockerfile, pyproject) == []


@pytest.mark.spec_exempt(
    "structural: twin of test_each_boot_runs_gpunits_boot_script_at_its_pin"
)
def test_the_check_catches_a_boot_script_at_another_tag_or_unchecked() -> None:
    pyproject = 'dependencies = ["gpunit @ git+https://github.com/alxb1t/gpunit@v9"]'
    pinned = (
        f"ADD --checksum=sha256:{'0' * 64} \\\n    "
        f"{BOOT_SOURCE.format(tag='v9')} {BOOT_SCRIPT}\n"
        f'ENTRYPOINT ["{BOOT_SCRIPT}", "--"]\n'
    )
    assert boot_script_faults(pinned, pyproject) == []
    elsewhere = pinned.replace("/v9/", "/v8/")
    unchecked = pinned.replace(f"--checksum=sha256:{'0' * 64} ", "")
    for broken in (elsewhere, unchecked):
        assert boot_script_faults(broken, pyproject) == [
            "the boot script is not added at gpunit's pin with a checksum"
        ]
    assert boot_script_faults('CMD ["/start.sh"]\n', pyproject) == [
        "the boot script is not added at gpunit's pin with a checksum",
        "the entrypoint is not the boot script followed by --",
    ]


def serve_command(start_sh: str) -> str:
    """Return the line that starts ComfyUI, its continuation lines joined into one."""
    return next(
        line
        for line in joined_lines(start_sh)
        if line.startswith("exec python main.py")
    )


def comfyui_directories(start_sh: str) -> dict[str, str]:
    """Return each directory ComfyUI writes to, by kind, as its start line sets it.

    e.g. `--temp-directory /dev/shm/comfyui` -> {"temp": "/dev/shm/comfyui/temp"}
    """
    found = dict(
        re.findall(
            r"--(input|output|temp|user)-directory (\S+)", serve_command(start_sh)
        )
    )
    # ComfyUI writes its temp files to `temp` under the directory it is given.
    if "temp" in found:
        found["temp"] += "/temp"
    return found


def before_serve(start_sh: str) -> str:
    """Return the start script up to the line that starts ComfyUI."""
    return start_sh[: start_sh.index("python main.py")]


def made_directories(start_sh: str) -> set[str]:
    """Return each directory a `mkdir -p` makes before ComfyUI starts."""
    return {
        path
        for line in before_serve(start_sh).splitlines()
        if line.startswith("mkdir -p ")
        for path in line.split()[2:]
    }


def unmade_directories(start_sh: str) -> list[str]:
    """Return each directory ComfyUI writes to that no `mkdir -p` makes before it."""
    made = made_directories(start_sh)
    return sorted(set(comfyui_directories(start_sh).values()) - made)


@pytest.mark.spec("pod-image:memory:comfyui-writes-to-memory")
def test_comfyui_writes_to_memory(start_sh: str) -> None:
    directories = comfyui_directories(start_sh)
    assert sorted(directories) == ["input", "output", "temp", "user"]
    assert all(path.startswith("/dev/shm/") for path in directories.values())
    assert unmade_directories(start_sh) == []


@pytest.mark.spec_exempt("structural: twin of test_comfyui_writes_to_memory")
def test_the_check_catches_a_directory_on_disk_or_not_made() -> None:
    assert comfyui_directories("exec python main.py --port 8188\n") == {}
    unmade = (
        "mkdir -p /dev/shm/comfyui/input\n"
        "exec python main.py --input-directory /dev/shm/comfyui/input \\\n"
        "    --temp-directory /dev/shm/comfyui\n"
    )
    assert unmade_directories(unmade) == ["/dev/shm/comfyui/temp"]


def memory_hold_faults(start_sh: str) -> list[str]:
    """Return what the memory step lacks of a hold on too little free memory."""
    step = boot_step(start_sh, "the memory directories")
    faults = []
    measured = re.search(r"df -k --output=(\S+) /dev/shm", step)
    if measured is None:
        faults.append("does not measure /dev/shm")
    else:
        columns = measured.group(1).split(",")
        free = columns.index("avail") + 1 if "avail" in columns else 0
        if f"free_kib=\"$(awk '{{print ${free}}}'" not in step:
            faults.append("reads other than the free column")
    if not re.search(
        r'^if \[ "\$free_kib" -lt "\$SHM_FREE_FLOOR_KIB" \]; then$', step, re.M
    ):
        faults.append("compares against no floor")
    if any(int(guess) for guess in re.findall(r"\bfree_kib=(\d+)", step)):
        faults.append("defaults an unreadable figure to free memory")
    if not re.search(r'SHM_FREE_FLOOR_KIB" \]; then\n\s*hold "ERROR: ', step):
        faults.append("does not say why and hold")
    return faults


@pytest.mark.spec("pod-image:memory:too-little-memory-holds")
def test_too_little_memory_holds_the_pod(start_sh: str) -> None:
    floor = re.search(
        r"^SHM_FREE_FLOOR_KIB=\$\(\((\d+) \* 1024 \* 1024\)\)$", start_sh, re.M
    )
    assert floor is not None
    assert int(floor.group(1)) >= 1
    assert memory_hold_faults(start_sh) == []
    step = boot_step(start_sh, "the memory directories")
    assert start_sh.index(step) < start_sh.index("python main.py")


@pytest.mark.spec_exempt("structural: twin of test_too_little_memory_holds_the_pod")
def test_the_check_catches_a_memory_step_that_never_holds() -> None:
    holds = (
        'echo "$(date -u +%FT%TZ) step: the memory directories"\n'
        "mkdir -p /dev/shm/comfyui/input\n"
        "shm_kib=\"$(df -k --output=size,avail /dev/shm | tail -n 1)\" || shm_kib=''\n"
        'free_kib="$(awk \'{print $2}\' <<<"$shm_kib")"\n'
        'case "$free_kib" in\n'
        "    '' | *[!0-9]*) free_kib=0 ;;\n"
        "esac\n"
        'if [ "$free_kib" -lt "$SHM_FREE_FLOOR_KIB" ]; then\n'
        '    hold "ERROR: too little"\n'
        "fi\n\n"
    )
    assert memory_hold_faults(holds) == []
    silent = holds.replace('    hold "ERROR: too little"\n', "    true\n")
    assert memory_hold_faults(silent) == ["does not say why and hold"]
    for inverted in ('[ "$free_kib" -ge', '! [ "$free_kib" -lt'):
        assert memory_hold_faults(holds.replace('[ "$free_kib" -lt', inverted)) == [
            "compares against no floor"
        ]
    size_column = holds.replace("{print $2}", "{print $1}")
    assert memory_hold_faults(size_column) == ["reads other than the free column"]
    guessed = holds.replace("free_kib=0 ;;", "free_kib=99999999 ;;")
    assert memory_hold_faults(guessed) == [
        "defaults an unreadable figure to free memory"
    ]


def spool_faults(start_sh: str) -> list[str]:
    """Return what the start script lacks of a `TMPDIR` made in memory for ComfyUI."""
    exported = re.search(r"^export TMPDIR=(\S+)$", before_serve(start_sh), re.M)
    if exported is None:
        return ["sets no TMPDIR"]
    faults = []
    if not exported.group(1).startswith("/dev/shm/"):
        faults.append("spools outside /dev/shm")
    if exported.group(1) not in made_directories(start_sh):
        faults.append("spools to a directory not made")
    return faults


@pytest.mark.spec("pod-image:memory:uploads-spool-to-memory")
def test_comfyui_spools_uploads_to_memory(start_sh: str) -> None:
    assert spool_faults(start_sh) == []


@pytest.mark.spec_exempt("structural: twin of test_comfyui_spools_uploads_to_memory")
def test_the_check_catches_an_upload_spooled_to_disk() -> None:
    made = "mkdir -p /dev/shm/comfyui/tmp\n"
    serve = "python main.py\n"
    assert spool_faults(made + serve) == ["sets no TMPDIR"]
    assert spool_faults(made + serve + "export TMPDIR=/dev/shm/comfyui/tmp\n") == [
        "sets no TMPDIR"
    ]
    assert spool_faults(made + "export TMPDIR=/tmp\n" + serve) == [
        "spools outside /dev/shm",
        "spools to a directory not made",
    ]


def run_memory_step(
    step: str, tmp_path: Path, shm_type: str | None, df_row: str
) -> subprocess.CompletedProcess[str]:
    """Run the memory step on a `/dev/shm` of `shm_type` whose `df` row is `df_row`.

    None is a `stat` that fails. A hold prints `held`; a start prints `started`.
    """
    hold = 'hold() { printf "%s\\n" "$@" >&2; echo held; exit 0; }'
    stat = f"echo {shlex.quote(shm_type)}" if shm_type is not None else "return 1"
    program = "\n".join(
        [
            "set -euo pipefail",
            "HOLD_SECONDS=900 SHM_FREE_FLOOR_KIB=$((1 * 1024 * 1024))",
            "mkdir() { :; }",
            f"stat() {{ {stat}; }}",
            f"df() {{ printf '%s\\n' '1K-blocks Avail' {shlex.quote(df_row)}; }}",
            hold,
            step,
            "echo started",
        ]
    )
    return subprocess.run(
        ["bash", "-c", program],
        env={"PATH": os.environ["PATH"]},
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


ROOMY = "8388608 8388608"


@pytest.mark.spec("pod-image:memory:a-disk-backed-shm-holds")
def test_a_shm_that_is_not_memory_holds_the_pod(start_sh: str, tmp_path: Path) -> None:
    step = boot_step(start_sh, "the memory directories")
    assert run_memory_step(step, tmp_path, "tmpfs", ROOMY).stdout.endswith("started\n")
    for shm_type in ("ext2/ext3", "overlayfs"):
        done = run_memory_step(step, tmp_path, shm_type, ROOMY)
        assert done.stdout.endswith("held\n")
        assert shm_type in done.stderr
    assert run_memory_step(step, tmp_path, None, ROOMY).stdout.endswith("held\n")


@pytest.mark.spec_exempt(
    "structural: twin of test_a_shm_that_is_not_memory_holds_the_pod"
)
def test_the_check_catches_a_shm_never_typed(start_sh: str, tmp_path: Path) -> None:
    step = boot_step(start_sh, "the memory directories")
    untyped = re.sub(r'\nif \[ "\$shm_type".*?\nfi', "", step, flags=re.S)
    assert untyped != step
    done = run_memory_step(untyped, tmp_path, "ext2/ext3", ROOMY)
    assert done.stdout.endswith("started\n")


@pytest.mark.spec("pod-image:memory:an-unread-figure-holds")
def test_an_unread_figure_holds_the_pod(start_sh: str, tmp_path: Path) -> None:
    step = boot_step(start_sh, "the memory directories")
    for row in ("", "- -", "8388608 n/a"):
        done = run_memory_step(step, tmp_path, "tmpfs", row)
        assert done.stdout.endswith("held\n")
        assert "could not read /dev/shm's free space" in done.stderr


@pytest.mark.spec_exempt("structural: twin of test_an_unread_figure_holds_the_pod")
def test_the_check_catches_an_unread_figure_taken_as_zero(
    start_sh: str, tmp_path: Path
) -> None:
    # Held, but by the floor, saying the pod has too little memory: a guess.
    step = boot_step(start_sh, "the memory directories")
    guessed = re.sub(r"(\*\[!0-9\]\*\)).*?;;", r"\1 free_kib=0 ;;", step, flags=re.S)
    assert guessed != step
    done = run_memory_step(guessed, tmp_path, "tmpfs", "- -")
    assert done.stdout.endswith("held\n")
    assert "could not read /dev/shm's free space" not in done.stderr


@pytest.mark.spec("pod-image:render-metadata:none-is-written")
def test_comfyui_writes_no_metadata(start_sh: str) -> None:
    assert "--disable-metadata" in serve_command(start_sh).split()


@pytest.mark.spec_exempt("structural: twin of test_comfyui_writes_no_metadata")
def test_the_check_catches_the_flag_outside_the_start_line() -> None:
    elsewhere = "# --disable-metadata\nexec python main.py --port 8188\n"
    assert "--disable-metadata" not in serve_command(elsewhere).split()


WORKFLOWS = sorted((REPO / ".github" / "workflows").glob("*.yml"))


def unparseable_run_lines(workflow: str) -> list[str]:
    """Return each one-line `run:` whose value holds `: `, which YAML rejects.

    GitHub then refuses the whole workflow, so a dispatch-only build cannot start.
    """
    found = (
        re.match(r"^\s*(?:- )?run: (?![|>])(.*)$", line)
        for line in workflow.splitlines()
    )
    return [
        match.group(0).strip() for match in found if match and ": " in match.group(1)
    ]


@pytest.mark.spec("pod-image:build:only-a-request-builds")
def test_every_workflow_run_line_is_one_yaml_accepts() -> None:
    assert WORKFLOWS
    for workflow in WORKFLOWS:
        assert unparseable_run_lines(workflow.read_text()) == [], workflow.name


@pytest.mark.spec_exempt(
    "structural: twin of test_every_workflow_run_line_is_one_yaml_accepts"
)
def test_the_check_catches_a_plain_run_line_holding_a_colon() -> None:
    broken = '      - run: echo "a: b"\n        run: |\n          echo "a: b"\n'
    assert unparseable_run_lines(broken) == ['- run: echo "a: b"']


# A pod boots the digest `config/image.json` pins, and nothing else (D28).

IMAGE_CONFIG = REPO / "config" / "image.json"


def pinned_reference(config: dict[str, str]) -> str | None:
    """Return `<image>@<digest>` for an image config, or None if it pins no digest."""
    digest = config.get("digest", "")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
        return None
    return f"{config['image']}@{digest}"


@pytest.mark.spec_exempt(
    "structural: twin of test_the_pod_is_created_from_the_pinned_digest"
)
def test_the_check_catches_an_image_config_naming_only_a_tag() -> None:
    assert pinned_reference({"image": "ghcr.io/a/b", "tag": "latest"}) is None
    assert pinned_reference({"image": "ghcr.io/a/b", "digest": "latest"}) is None


# `gpunit.toml` is the session's spec: the pin, the floors and the volume.

GPUNIT_SPEC = REPO / "gpunit.toml"


@pytest.fixture(scope="module")
def gpunit_spec() -> dict[str, object]:
    return tomllib.loads(GPUNIT_SPEC.read_text())


def spec_image_faults(spec: dict[str, object], config: dict[str, str]) -> list[str]:
    """Return how `gpunit.toml`'s `image` departs from `config/image.json`'s pin.

    e.g. `image = "ghcr.io/a/b:latest"` -> ["not config/image.json's pin"]
    """
    pinned = pinned_reference(config)
    if pinned is None:
        return ["config/image.json pins no digest"]
    return [] if spec.get("image") == pinned else ["not config/image.json's pin"]


@pytest.mark.spec("pod-image:boot:the-pinned-digest-is-booted")
def test_the_session_boots_the_digest_the_image_config_pins(
    gpunit_spec: dict[str, object],
) -> None:
    assert spec_image_faults(gpunit_spec, json.loads(IMAGE_CONFIG.read_text())) == []


@pytest.mark.spec_exempt(
    "structural: twin of test_the_session_boots_the_digest_the_image_config_pins"
)
def test_the_spec_image_check_catches_a_tag_and_another_digest() -> None:
    config = {"image": "ghcr.io/a/b", "digest": "sha256:" + "0" * 64}
    other: dict[str, object] = {"image": "ghcr.io/a/b@sha256:" + "1" * 64}
    assert spec_image_faults({"image": "ghcr.io/a/b:latest"}, config) == [
        "not config/image.json's pin"
    ]
    assert spec_image_faults(other, config) == ["not config/image.json's pin"]
    assert spec_image_faults(other, {"image": "ghcr.io/a/b", "tag": "v1"}) == [
        "config/image.json pins no digest"
    ]


def unfloored_spec(spec: dict[str, object]) -> list[str]:
    """Return each floor `gpunit.toml` does not ask for.

    e.g. a spec with `vram_gb = 24` alone -> ["host memory", "CUDA version"]
    """
    missing = []
    for key, floor in (("vram_gb", "card memory"), ("ram_gb", "host memory")):
        value = spec.get(key)
        if not (isinstance(value, int) and value >= 24):
            missing.append(floor)
    # torch's cu128 build, which the Blackwell pod needs (CLAUDE.md).
    if spec.get("cuda") != "12.8":
        missing.append("CUDA version")
    return missing


@pytest.mark.spec("pod-image:placement:the-create-carries-the-floors")
def test_the_session_spec_asks_for_the_floors(gpunit_spec: dict[str, object]) -> None:
    assert unfloored_spec(gpunit_spec) == []


@pytest.mark.spec_exempt(
    "structural: twin of test_the_session_spec_asks_for_the_floors"
)
def test_the_spec_floor_check_catches_a_spec_with_one() -> None:
    assert unfloored_spec({"vram_gb": 24, "ram_gb": 16}) == [
        "host memory",
        "CUDA version",
    ]


def unnamed_volume(spec: dict[str, object]) -> bool:
    """Return whether `gpunit.toml` names no network volume."""
    volume = spec.get("volume")
    return not (isinstance(volume, str) and volume.strip())


@pytest.mark.spec(
    "model-provisioning:reachability:provisioning-requires-the-network-volume"
)
def test_the_session_spec_names_the_volume(gpunit_spec: dict[str, object]) -> None:
    assert not unnamed_volume(gpunit_spec)


@pytest.mark.spec_exempt("structural: twin of test_the_session_spec_names_the_volume")
def test_the_volume_check_catches_a_spec_with_none() -> None:
    assert unnamed_volume({"project": "isekai"})
    assert unnamed_volume({"volume": ""})


def telemetry_set_in_spec(spec: dict[str, object]) -> list[str]:
    """Return each telemetry switch `gpunit.toml`'s `[env]` sets a second time."""
    env = spec.get("env", {})
    assert isinstance(env, dict)
    return [switch for switch in TELEMETRY_SWITCHES if switch in env]


@pytest.mark.spec("pod-image:telemetry:the-switches-are-off")
def test_the_session_spec_sets_no_telemetry_switch(
    gpunit_spec: dict[str, object],
) -> None:
    assert telemetry_set_in_spec(gpunit_spec) == []


@pytest.mark.spec_exempt(
    "structural: twin of test_the_session_spec_sets_no_telemetry_switch"
)
def test_the_spec_telemetry_check_catches_a_switch_in_env() -> None:
    spec: dict[str, object] = {"env": {"DO_NOT_TRACK": "1", "TZ": "UTC"}}
    assert telemetry_set_in_spec(spec) == ["DO_NOT_TRACK"]


# Helpers that run pieces of the start script in strict bash.


def _code(script: str) -> list[str]:
    """Return the script's lines with comment lines blanked, so indices hold."""
    return ["" if ln.lstrip().startswith("#") else ln for ln in script.splitlines()]


def run_functions(
    script: str,
    names: tuple[str, ...],
    stubs: str,
    cwd: Path,
    call: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run `call`, or the last named function, in strict bash beside the stubs.

    e.g. `call='f "a b"'` runs `f` with one argument.
    """
    program = "\n".join(
        [
            "set -euo pipefail",
            stubs,
            *(shell_function(script, n) for n in names),
            call or names[-1],
        ]
    )
    return subprocess.run(
        ["bash", "-c", program],
        cwd=cwd,
        env={"PATH": os.environ["PATH"]},
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


TELEMETRY_SWITCHES = (
    "ORT_DISABLE_TELEMETRY",
    "HF_HUB_DISABLE_TELEMETRY",
    "DO_NOT_TRACK",
    "NO_ALBUMENTATIONS_UPDATE",
)


def telemetry_left_on(dockerfile: str) -> list[str]:
    """Return each switch the image's `ENV` leaves off.

    A switch's last assignment is the one the image keeps, so a later `=0` turns it off.
    e.g. `ENV DO_NOT_TRACK=0` last -> [..., "DO_NOT_TRACK"]
    """
    env = " ".join(line for line in joined_lines(dockerfile) if line.startswith("ENV "))
    last = dict(re.findall(r"\b(\w+)=(\S*)", env))
    return [s for s in TELEMETRY_SWITCHES if last.get(s) != "1"]


@pytest.mark.spec("pod-image:telemetry:the-switches-are-off")
def test_the_pod_is_created_with_telemetry_off(dockerfile: str) -> None:
    assert telemetry_left_on(dockerfile) == []


@pytest.mark.spec_exempt(
    "structural: twin of test_the_pod_is_created_with_telemetry_off"
)
def test_the_telemetry_check_catches_a_switch_left_out() -> None:
    dockerfile = (
        "# DO_NOT_TRACK=1\nENV ORT_DISABLE_TELEMETRY=1 HF_HUB_DISABLE_TELEMETRY=10\n"
    )
    assert telemetry_left_on(dockerfile) == [
        "HF_HUB_DISABLE_TELEMETRY",
        "DO_NOT_TRACK",
        "NO_ALBUMENTATIONS_UPDATE",
    ]


@pytest.mark.spec_exempt(
    "structural: twin of test_the_pod_is_created_with_telemetry_off"
)
def test_the_telemetry_check_catches_a_switch_set_back(dockerfile: str) -> None:
    set_back = dockerfile + "\nENV DO_NOT_TRACK=0\n"
    assert telemetry_left_on(set_back) == ["DO_NOT_TRACK"]


def stub_command(bin_dir: Path, name: str, script: str) -> None:
    """Write `script` as the executable `name` in `bin_dir`, found first on PATH."""
    bin_dir.mkdir(parents=True, exist_ok=True)
    (bin_dir / name).write_text(script)
    (bin_dir / name).chmod(0o755)


def unarmed_stop(spec: dict[str, object], dockerfile: str) -> list[str]:
    """Return what the pod lacks of a stop armed at boot within the session's ceiling.

    e.g. a `ceiling = "1h"` spec and a build file with no entrypoint ->
    ["a ceiling within the session's", "gpunit's boot script as the entrypoint"]
    """
    faults = []
    ceiling = re.fullmatch(r"([1-9][0-9]*)([smh])", str(spec.get("ceiling", "")))
    unit = {"s": 1, "m": 60, "h": 3600}
    seconds = int(ceiling[1]) * unit[ceiling[2]] if ceiling else 0
    if not 0 < seconds <= SESSION_CEILING_SECONDS:
        faults.append("a ceiling within the session's")
    entry = [ln for ln in dockerfile.splitlines() if ln.startswith("ENTRYPOINT")]
    if entry != [f'ENTRYPOINT ["{BOOT_SCRIPT}", "--"]']:
        faults.append("gpunit's boot script as the entrypoint")
    return faults


@pytest.mark.spec("pod-image:stop:armed-at-boot")
def test_the_pod_arms_its_stop_first(
    gpunit_spec: dict[str, object], dockerfile: str
) -> None:
    assert unarmed_stop(gpunit_spec, dockerfile) == []


@pytest.mark.spec_exempt("structural: twin of test_the_pod_arms_its_stop_first")
def test_the_armed_stop_check_catches_a_long_ceiling_and_no_boot_script() -> None:
    assert unarmed_stop({"ceiling": "1h"}, 'CMD ["/start.sh"]\n') == [
        "a ceiling within the session's",
        "gpunit's boot script as the entrypoint",
    ]
    assert unarmed_stop({"ceiling": "45"}, "") == [
        "a ceiling within the session's",
        "gpunit's boot script as the entrypoint",
    ]


def unstopped_holds(start_sh: str, tmp_path: Path) -> list[str]:
    """Return how `start.sh` holds without ending in a non-zero exit.

    Runs `hold` with `sleep` stubbed; each line outside it that waits out
    `HOLD_SECONDS` is a hold that bypasses it.
    """
    body = shell_function(start_sh, "hold")
    faults = [
        f"holds outside hold(): {ln.strip()}"
        for ln in _code(start_sh.replace(body, ""))
        if "HOLD_SECONDS" in ln and not ln.startswith("HOLD_SECONDS=")
    ]
    stubs = 'HOLD_SECONDS=900\nsleep() { echo "slept $1"; }'
    done = run_functions(
        start_sh, ("hold",), stubs, tmp_path, call='hold "ERROR: why"; echo returned'
    )
    if done.stdout != "slept 900\n" or done.returncode == 0:
        faults.append("hold() does not exit non-zero once it has waited")
    if not done.stderr.startswith("ERROR: why\n"):
        faults.append("hold() does not say why")
    return faults


@pytest.mark.spec("pod-image:stop:a-hold-ends-in-the-stop")
def test_every_hold_ends_in_the_stop(start_sh: str, tmp_path: Path) -> None:
    assert unstopped_holds(start_sh, tmp_path) == []
    assert hold_calls(start_sh)


@pytest.mark.spec_exempt("structural: twin of test_every_hold_ends_in_the_stop")
def test_the_hold_check_catches_a_hold_that_returns(tmp_path: Path) -> None:
    returns = (
        "HOLD_SECONDS=900\n"
        'hold() {\n    printf "%s\\n" "$@" >&2\n    sleep "$HOLD_SECONDS"\n}\n'
        'if ! provision; then\n    exec sleep "$HOLD_SECONDS"\nfi\n'
    )
    assert unstopped_holds(returns, tmp_path) == [
        'holds outside hold(): exec sleep "$HOLD_SECONDS"',
        "hold() does not exit non-zero once it has waited",
    ]


def unstopped_ends(start_sh: str, tmp_path: Path) -> list[str]:
    """Return each way a boot ends other than in ComfyUI's process or a failing exit.

    Runs the start script's last step with ComfyUI stubbed: once for each way
    ComfyUI can exit, and once for a step that fails before it. ComfyUI replaces
    the script when both print one process id.
    """
    lines = start_sh.splitlines()
    step = next(i for i, ln in enumerate(lines) if ln.endswith('step: ComfyUI"'))
    tail = "\n".join(lines[step:])
    stub_command(
        tmp_path / "bin", "python", '#!/bin/sh\necho "ComfyUI $$"\nexit "$STATUS"\n'
    )
    cases = {
        "a ComfyUI that exits": ("export STATUS=0", 0),
        "a ComfyUI that fails": ("export STATUS=1", 1),
        "a step that fails before ComfyUI": ("false", None),
    }
    faults = []
    for case, (before, status) in cases.items():
        program = "\n".join(
            [
                "set -euo pipefail",
                f'export PATH="{tmp_path / "bin"}:$PATH"',
                'echo "script $$"',
                before,
                tail,
                "echo after",
            ]
        )
        done = subprocess.run(
            ["bash", "-c", program],
            cwd=tmp_path,
            env={"PATH": os.environ["PATH"]},
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        # The step's own timestamp line is not what is checked.
        words = [ln.split() for ln in done.stdout.splitlines() if " step: " not in ln]
        said = [word[0] for word in words]
        pids = {word[1] for word in words if len(word) > 1}
        if status is None:
            ended = done.returncode != 0 and said == ["script"]
        else:
            replaced = said == ["script", "ComfyUI"] and len(pids) == 1
            ended = replaced and done.returncode == status
        if not ended:
            faults.append(f"{case} does not end the boot")
    return faults


@pytest.mark.spec("pod-image:stop:a-boot-that-ends-stops-the-pod")
def test_a_boot_that_ends_stops_the_pod(start_sh: str, tmp_path: Path) -> None:
    assert unstopped_ends(start_sh, tmp_path) == []


@pytest.mark.spec_exempt("structural: twin of test_a_boot_that_ends_stops_the_pod")
def test_the_boot_end_check_catches_a_comfyui_run_as_a_child(
    tmp_path: Path,
) -> None:
    child = (
        'echo "$(date -u +%FT%TZ) step: ComfyUI"\npython main.py --port 8188 || true\n'
    )
    assert unstopped_ends(child, tmp_path) == [
        "a ComfyUI that exits does not end the boot",
        "a ComfyUI that fails does not end the boot",
    ]
