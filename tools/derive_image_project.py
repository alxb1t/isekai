"""Re-derive `image/` -- the pod's Python environment, as a locked uv project.

Run it from the repository root:

    uv run python -m tools.derive_image_project

It reads the commits the `Dockerfile` checks out, fetches ComfyUI's and
comfyui_controlnet_aux's requirement lists at those commits, writes
`image/pyproject.toml`, and runs `uv lock --project image`. Re-running without a
change upstream leaves `image/` byte-identical -- `git diff --stat -- image/` is
the check. Why the image is a project of its own: 0033 design D2.

It writes no provisioning manifest, so `tests/test_derivation.py` does not list it.
"""

import json
import re
import subprocess
import tomllib
import urllib.request
from pathlib import Path

from tools.manifest import USER_AGENT

REPO = Path(__file__).resolve().parent.parent
DOCKERFILE = REPO / "Dockerfile"
PROJECT = REPO / "image"

# The repositories whose requirement lists become the image's dependencies, in the
# order they are written. InstantID's own list is not read: `insightface` below is
# the one package it needs that the others do not bring.
UPSTREAMS = ("comfyanonymous/ComfyUI", "Fannovel16/comfyui_controlnet_aux")

# Each wins over an upstream entry of the same name. The torch stack is the cu128
# build, which ships the Blackwell (sm_120) kernels.
PINS = (
    "torch==2.8.0",
    "torchvision==0.23.0",
    "torchaudio==2.8.0",
    "insightface==0.7.3",
    "onnxruntime==1.30.0",
)
TORCH_STACK = ("torch", "torchvision", "torchaudio")
TORCH_INDEX = "https://download.pytorch.org/whl/cu128"

# Both ship the `onnxruntime` module. The -gpu build is for CUDA 13, which the image
# lacks, so it runs on the CPU anyway; the CPU build says so. Not a relabel: without
# the -gpu build, DWPose runs its box detector on OpenCV, not onnxruntime, which can
# move `summon-anime-wai`'s pose (0042 design D4).
DROPPED = ("onnxruntime-gpu",)

# insightface 0.7.3 is an sdist; its `build-system.requires` names these unpinned.
# Each carries its wheel hashes from `image/uv.lock`, so uv checks what it builds
# with (0042 design D5).
BUILD_CONSTRAINTS = {
    "setuptools==84.0.0": [
        "sha256:51a52592b3b99e102b609654876bd65f19f999935166d1352678931132b0c670",
    ],
    "numpy==2.5.3": [
        "sha256:b7e18c623bb5c95acb3b3328861272816ba199fb531921c5d6d0b675f1fde9e3",
    ],
    "cython==3.3.0": [
        "sha256:428fafed98ea26927000a287b4dfc9ef07339f56656a5329a34eaa593f79a4f8",
        "sha256:9b24b5c8cd536946b62086fcafee6d5509d3f549f72d553d2336af87ffbe0da1",
    ],
}

PYTHON = "3.12.14"


def pinned_commits(dockerfile: str) -> dict[str, str]:
    """Return each cloned repository's `owner/name`, to the commit it checks out.

    e.g. "git clone https://github.com/a/b.git ... git checkout <sha>" -> {"a/b": sha}
    """
    clones = re.findall(r"git clone https://github\.com/(\S+?)(?:\.git)?\s", dockerfile)
    checkouts = re.findall(r"git checkout ([0-9a-f]{40})\b", dockerfile)
    if len(clones) != len(checkouts):
        raise SystemExit("Dockerfile: a `git clone` without its `git checkout <sha>`")
    return dict(zip(clones, checkouts, strict=True))


def requirement_name(line: str) -> str:
    """Return a requirement's normalised name, e.g. "trimesh[easy]" -> "trimesh"."""
    found = re.match(r"[A-Za-z0-9._-]+", line)
    if found is None:
        raise SystemExit(f"not a requirement: {line!r}")
    return re.sub(r"[-_.]+", "-", found.group(0)).lower()


def requirement_lines(text: str) -> list[str]:
    """Return a requirements file's entries, without comments or blank lines."""
    lines = (line.split("#", 1)[0].strip() for line in text.splitlines())
    return [line for line in lines if line]


def dependencies(upstream_lists: list[str]) -> list[str]:
    """Return the pins, then every upstream entry a pin or `DROPPED` leaves, once."""
    overridden = {requirement_name(pin) for pin in PINS} | set(DROPPED)
    written = list(PINS)
    for text in upstream_lists:
        for line in requirement_lines(text):
            if requirement_name(line) not in overridden and line not in written:
                written.append(line)
    return written


def fetch(url: str) -> str:
    """Return the text `url` serves."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode()


def uv_required(pyproject: str) -> str:
    """Return a project's `[tool.uv] required-version`, e.g. "==0.12.19"."""
    return tomllib.loads(pyproject)["tool"]["uv"]["required-version"]


def render(deps: list[str], uv: str) -> str:
    """Return `image/pyproject.toml`'s text for `deps`, requiring uv as `uv` says."""

    # A JSON string or array is a TOML one; `array` lays an array out one item a line.
    def array(items: list[str]) -> str:
        return "[\n" + "".join(f"    {item},\n" for item in items) + "]"

    constraints = [
        f"{{ requirement = {json.dumps(r)}, hashes = {json.dumps(h)} }}"
        for r, h in BUILD_CONSTRAINTS.items()
    ]

    sources = "".join(
        f'{name} = {{ index = "pytorch-cu128" }}\n' for name in TORCH_STACK
    )
    return (
        "# Derived by `tools/derive_image_project.py`; edit that, not this.\n"
        "[project]\n"
        'name = "isekai-image"\n'
        'version = "0"\n'
        'requires-python = "==3.12.*"\n'
        f"dependencies = {array([json.dumps(dep) for dep in deps])}\n"
        "\n"
        "[tool.uv]\n"
        "package = false\n"
        f'required-version = "{uv}"\n'
        "environments = "
        "[\"sys_platform == 'linux' and platform_machine == 'x86_64'\"]\n"
        f"build-constraint-dependencies = {array(constraints)}\n"
        "\n"
        "[[tool.uv.index]]\n"
        'name = "pytorch-cu128"\n'
        f'url = "{TORCH_INDEX}"\n'
        "explicit = true\n"
        "\n"
        "[tool.uv.sources]\n"
        f"{sources}"
    )


def main() -> None:
    """Write `image/pyproject.toml` and `image/.python-version`, then lock them."""
    commits = pinned_commits(DOCKERFILE.read_text())
    lists = [
        fetch(
            f"https://raw.githubusercontent.com/{repo}/{commits[repo]}/requirements.txt"
        )
        for repo in UPSTREAMS
    ]
    uv = uv_required((REPO / "pyproject.toml").read_text())
    PROJECT.mkdir(exist_ok=True)
    (PROJECT / "pyproject.toml").write_text(render(dependencies(lists), uv))
    (PROJECT / ".python-version").write_text(f"{PYTHON}\n")
    subprocess.run(["uv", "lock", "--project", str(PROJECT)], check=True)


if __name__ == "__main__":
    main()
