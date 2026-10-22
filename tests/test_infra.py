"""Checks over the tracked pod configuration: the image and the pod lifecycle.

These read the shipped files themselves rather than a fixture copy, for the same
reason the suite reads the shipped graph: a byte-identical copy with no drift
check is a second thing to rename and a silent divergence waiting to happen.
"""

import argparse
import io
import json
import re
import tomllib
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path, PurePosixPath

import gpunit
import pytest
from gpunit.spec import Spec, parse_ceiling

from isekai.boundary import gpu
from isekai.boundary.pod_start import PROVISION, VOLUME_SIZE_FLOOR
from isekai.boundary.provision import (
    MANIFEST_PATH,
    MODELS_ROOT,
    Manifest,
    annotator_files,
    manifest_dest,
)
from isekai.foundation.flow import Workflow
from isekai.foundation.run import REPOSITORY
from isekai.interface import render
from isekai.interface.wiring import Wiring
from tests.conftest import SESSION_CEILING_SECONDS, VOCABULARY
from tests.stages import FIELD_MAP
from tools.derive_image_project import CLONE, pinned_commits, uv_required
from tools.image_record import copied, copies, record

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


# The image mirrors the repository's layout, and no boot proves a rebuilt image
# before a pod uses it, so these hold its paths statically.

IMAGE_ROOT = "/opt/isekai"


def image_copies(dockerfile: str) -> dict[str, str]:
    """Return each destination a `COPY` from the build context names, to its source.

    e.g. `COPY config/models.json /m.json` -> {"/m.json": "config/models.json"}
    """
    return {dest: source for source, dest in copies(dockerfile)}


def missing_copy_sources(dockerfile: str) -> list[str]:
    """Return each `COPY` source that is not a file in the repository."""
    return [
        source
        for source in image_copies(dockerfile).values()
        if not (REPO / source).is_file()
    ]


def manifest_in_image() -> str:
    """Return where `provision.py`'s anchor finds the manifest inside the image."""
    return f"{IMAGE_ROOT}/{MANIFEST_PATH.relative_to(REPO).as_posix()}"


@pytest.mark.spec_exempt("structural: the image copies files the repository holds")
def test_every_file_the_image_copies_exists(dockerfile: str) -> None:
    assert image_copies(dockerfile)
    assert missing_copy_sources(dockerfile) == []


@pytest.mark.spec_exempt("structural: twin of test_every_file_the_image_copies_exists")
def test_the_check_catches_a_copy_of_a_file_that_is_gone() -> None:
    broken = "FROM scratch\nCOPY Dockerfile /d\nCOPY gone/models.json /x\n"
    assert missing_copy_sources(broken) == ["gone/models.json"]


def uncopied_command(dockerfile: str) -> list[str]:
    """Return each file the image's command runs that the image does not copy.

    The start runs `provision.py` from its own directory, so both land there.
    e.g. `CMD ["python", "/o/s.py"]`, nothing copied -> ["/o/s.py", "/o/provision.py"]
    """
    command = re.search(r'^CMD \["python", "(\S+)"\]$', dockerfile, re.M)
    if command is None:
        return ["the command is not python running one file"]
    start = PurePosixPath(command[1])
    wanted = [str(start), str(start.parent / PROVISION.name)]
    copied = image_copies(dockerfile)
    return [path for path in wanted if path not in copied]


@pytest.mark.spec_exempt("structural: the command runs files the image holds")
def test_the_command_runs_the_start_the_image_copies(dockerfile: str) -> None:
    assert uncopied_command(dockerfile) == []


@pytest.mark.spec_exempt(
    "structural: twin of test_the_command_runs_the_start_the_image_copies"
)
def test_the_check_catches_a_command_running_a_file_not_copied() -> None:
    start = f"{IMAGE_ROOT}/isekai/boundary/pod_start.py"
    alone = f'COPY a.py {start}\nCMD ["python", "{start}"]\n'
    assert uncopied_command(alone) == [f"{IMAGE_ROOT}/isekai/boundary/provision.py"]
    assert uncopied_command('CMD ["/serve.sh"]\n') == [
        "the command is not python running one file"
    ]


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

    e.g. `config/models.json` edited after the record -> ["config/models.json"]
    """
    files = config.get("files")
    if not isinstance(files, dict):
        return ["config/image.json records no files"]
    names = sorted({str(name) for name in files} | set(derived))
    return [name for name in names if files.get(name) != derived.get(name)]


@pytest.mark.spec("pod-image:build:the-record-matches-the-tree")
def test_the_build_record_agrees_with_the_tree() -> None:
    derived = record()
    assert {"Dockerfile", "isekai/boundary/pod_start.py"} <= set(derived)
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


@pytest.mark.spec("pod-image:build:the-record-matches-the-tree")
@pytest.mark.parametrize(
    "line",
    [
        "COPY --chmod=755 a.py /a.py",
        "COPY a.py b.py /opt/",
        "COPY a.py \\",
        "COPY\\\n    a.py /a.py",
        "ADD a.py /a.py",
        "add a.py /a.py",
        "  ADD a.py /a.py",
        "ADD https://example.com/a.py /a.py",
        "ADD --checksum=sha256:" + "0" * 64 + " a.py /a.py",
    ],
)
def test_the_record_refuses_a_copy_it_cannot_read(line: str) -> None:
    with pytest.raises(ValueError, match=re.escape(repr(line))):
        copied(f"FROM x\nCOPY ok.py /ok.py\n{line}\n")


@pytest.mark.spec("pod-image:build:the-record-matches-the-tree")
@pytest.mark.parametrize(
    ("line", "read"),
    [
        ("copy a.py /a.py", ["a.py"]),
        ("  COPY a.py /a.py", ["a.py"]),
        ("\tCoPy a.py /a.py", ["a.py"]),
        ("# a note \\\nCOPY a.py /a.py", ["a.py"]),
        ("ADD --checksum=sha256:" + "0" * 64 + " \\\n    https://x.org/b /b", []),
    ],
)
def test_the_record_reads_a_copy_in_any_case_and_passes_a_checksummed_url(
    line: str, read: list[str]
) -> None:
    dockerfile = f"FROM x\nRUN echo \\\n    copy add\n{line}\nCOPY c.py /c.py\n"
    assert copied(dockerfile) == [*read, "c.py"]


@pytest.mark.spec_exempt(
    "structural: twin of test_the_record_refuses_a_copy_it_cannot_read"
)
def test_the_record_reads_a_plain_copy_and_skips_a_copy_from_an_image() -> None:
    dockerfile = "FROM x\nCOPY --from=img@sha256:0 /uv /uvx /bin/\nCOPY a.py /a.py\n"
    assert copied(dockerfile) == ["a.py"]


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


# The pod's own host key: text checks over the shipped files, proved on a pod.


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


BOOT_SCRIPT = "/opt/gpunit/boot.sh"
BOOT_SOURCE = "https://raw.githubusercontent.com/alxb1t/gpunit/{tag}/boot/boot.sh"


def gpunit_tag(pyproject: str) -> str | None:
    """Return the tag `pyproject.toml` pins gpunit at, or None if it pins none."""
    pinned = re.search(
        r'"gpunit @ git\+https://github\.com/alxb1t/gpunit@([\w.]+)"', pyproject
    )
    return pinned[1] if pinned else None


def boots_the_boot_script(dockerfile: str) -> bool:
    """Return whether the image's one entrypoint is gpunit's boot script, then `--`."""
    entry = [ln for ln in dockerfile.splitlines() if ln.startswith("ENTRYPOINT")]
    return entry == [f'ENTRYPOINT ["{BOOT_SCRIPT}", "--"]']


def boot_script_faults(dockerfile: str, pyproject: str) -> list[str]:
    """Return how the image's entrypoint departs from gpunit's boot script at its pin.

    e.g. a build file holding `CMD ["python", "serve.py"]` alone ->
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
    if not boots_the_boot_script(dockerfile):
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
    assert boot_script_faults('CMD ["python", "serve.py"]\n', pyproject) == [
        "the boot script is not added at gpunit's pin with a checksum",
        "the entrypoint is not the boot script followed by --",
    ]


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
    # torch's cu128 build, which the Blackwell pod needs (AGENTS.md).
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


def window_volume_faults(spec: dict[str, object]) -> list[str]:
    """Return each way `gpunit.toml` fails to declare a window volume.

    e.g. `{"volume_gb": 1, "volume_ceiling": "4h"}` -> ["under the capacity floor"]
    """
    faults = []
    if "volume" in spec:
        faults.append("names a kept volume")
    size = spec.get("volume_gb")
    if not isinstance(size, int):
        faults.append("no volume_gb")
    # RunPod's sizes are decimal, as the container disk's floor test reads them.
    elif size * 1000**3 < VOLUME_SIZE_FLOOR:
        faults.append("under the capacity floor")
    ceiling = spec.get("volume_ceiling")
    if not (isinstance(ceiling, str) and ceiling.strip()):
        faults.append("no volume_ceiling")
    return faults


@pytest.mark.spec(
    "model-provisioning:reachability:provisioning-requires-the-network-volume"
)
def test_the_session_spec_declares_a_window_volume(
    gpunit_spec: dict[str, object],
) -> None:
    faults = window_volume_faults(gpunit_spec)
    assert "names a kept volume" not in faults
    assert "no volume_gb" not in faults
    assert "no volume_ceiling" not in faults


@pytest.mark.spec("model-provisioning:reachability:the-window-volume-clears-the-floor")
def test_the_window_volume_clears_the_capacity_floor(
    gpunit_spec: dict[str, object],
) -> None:
    assert "under the capacity floor" not in window_volume_faults(gpunit_spec)


@pytest.mark.spec_exempt(
    "structural: twin of test_the_session_spec_declares_a_window_volume"
    " and test_the_window_volume_clears_the_capacity_floor"
)
def test_the_window_volume_check_catches_each_fault() -> None:
    assert window_volume_faults({"volume": "abc"}) == [
        "names a kept volume",
        "no volume_gb",
        "no volume_ceiling",
    ]
    assert window_volume_faults({"volume_gb": 50, "volume_ceiling": ""}) == [
        "no volume_ceiling"
    ]
    assert window_volume_faults({"volume_gb": 1, "volume_ceiling": "4h"}) == [
        "under the capacity floor"
    ]
    assert window_volume_faults({"volume_gb": 50, "volume_ceiling": "4h"}) == []


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


def unarmed_stop(spec: dict[str, object], dockerfile: str) -> list[str]:
    """Return what the pod lacks of a stop armed at boot within the session's ceiling.

    e.g. a `ceiling = "4h"` spec and a build file with no entrypoint ->
    ["a ceiling within the session's", "gpunit's boot script as the entrypoint"]
    """
    faults = []
    try:
        seconds = parse_ceiling(str(spec.get("ceiling", "")))
    except ValueError:
        seconds = 0
    if not 0 < seconds <= SESSION_CEILING_SECONDS:
        faults.append("a ceiling within the session's")
    if not boots_the_boot_script(dockerfile):
        faults.append("gpunit's boot script as the entrypoint")
    return faults


def outlived(spec: dict[str, object]) -> bool:
    """Return whether the longest session and its timeout end inside a fresh window.

    e.g. `ceiling = "4h"`, `timeout = 420`, `volume_ceiling = "4h"` -> False
    """
    longest = parse_ceiling(str(spec["ceiling"])) + int(str(spec["timeout"]))
    return longest < parse_ceiling(str(spec["volume_ceiling"]))


@pytest.mark.spec("pod-image:stop:the-window-outlasts-the-longest-session")
def test_a_fresh_window_outlasts_the_longest_session(
    gpunit_spec: dict[str, object],
) -> None:
    assert outlived(gpunit_spec)
    # The twin: a ceiling as long as the window leaves no room for the timeout.
    assert not outlived({**gpunit_spec, "ceiling": gpunit_spec["volume_ceiling"]})


@pytest.mark.spec("pod-image:stop:a-sessions-ceiling-is-its-limit")
def test_a_sessions_ceiling_is_its_limit_and_one_over_the_maximum_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    received: list[Spec] = []

    @contextmanager
    def recorded(spec: Spec, **_: object) -> Iterator[None]:
        received.append(spec)
        yield None

    monkeypatch.setattr(gpunit, "session", recorded)
    with gpu.open_session(REPOSITORY, {}, print, 1500):
        pass
    runs = tmp_path / "b" / "runs"
    (runs / "r1").mkdir(parents=True)
    (runs / "r1" / "run.json").write_text("{}")
    over = argparse.Namespace(
        runs=runs, requests=["summon-anime-wai=1"], limit=SESSION_CEILING_SECONDS + 1
    )
    nothing = Wiring(
        reader=None,
        tagger=None,
        hosted_tagger=None,
        client=None,
        vocabulary=lambda: VOCABULARY,
        field_map=lambda _: FIELD_MAP,
        runs_root=runs,
        out=io.StringIO(),
        err=io.StringIO(),
    )

    status = render.run_session(over, nothing, lambda argv, wired: 0)

    assert [spec.ceiling_s for spec in received] == [1500]
    assert status == 1
    assert len(received) == 1
    assert "above gpunit.toml's ceiling" in (runs.parent / "log.txt").read_text()


@pytest.mark.spec("pod-image:stop:armed-at-boot")
def test_the_pod_arms_its_stop_first(
    gpunit_spec: dict[str, object], dockerfile: str
) -> None:
    assert unarmed_stop(gpunit_spec, dockerfile) == []


@pytest.mark.spec_exempt("structural: twin of test_the_pod_arms_its_stop_first")
def test_the_armed_stop_check_catches_a_long_ceiling_and_no_boot_script() -> None:
    assert unarmed_stop({"ceiling": "4h"}, 'CMD ["python", "serve.py"]\n') == [
        "a ceiling within the session's",
        "gpunit's boot script as the entrypoint",
    ]
    assert unarmed_stop({"ceiling": "45"}, "") == [
        "a ceiling within the session's",
        "gpunit's boot script as the entrypoint",
    ]
