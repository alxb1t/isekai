# Plain Ubuntu, no CUDA: torch's own wheels bring every CUDA library it loads, and
# the host's driver is mounted by the container runtime (0042 design D1). The base
# and uv are named by digest; `docker buildx imagetools inspect <tag>` resolves one.
FROM ubuntu:22.04@sha256:b8b6ee6aa931ecd9d0d952abc34dc0e5f7c6a30c6bb71b079fe399fde0329c02

ENV PYTHONUNBUFFERED=1 DEBIAN_FRONTEND=noninteractive
# What the CUDA base set, kept for a runtime that honours it. RunPod sets
# NVIDIA_VISIBLE_DEVICES=void and mounts the driver regardless (0042 design D1).
ENV NVIDIA_VISIBLE_DEVICES=all NVIDIA_DRIVER_CAPABILITIES=compute,utility
# The pod renders a likeness; its libraries are told to report nothing (0042 design D3).
ENV ORT_DISABLE_TELEMETRY=1 HF_HUB_DISABLE_TELEMETRY=1 DO_NOT_TRACK=1 NO_ALBUMENTATIONS_UPDATE=1

# System packages. The host keys `openssh-server` makes are deleted in this layer:
# a later one would only hide them. Each pod makes its own (0040 design D1).
# Python is uv's; `build-essential` compiles insightface's extension.
RUN apt-get update && apt-get install -y --no-install-recommends \
        git curl wget ca-certificates openssh-server build-essential \
        libgl1 libglib2.0-0 \
    && rm -f /etc/ssh/ssh_host_* \
    && rm -rf /var/lib/apt/lists/*

# uv
COPY --from=ghcr.io/astral-sh/uv:0.12.19@sha256:04d046b13e60d6bcec73cbc5e1cad25d680dea90c8573340950a0ac2d1aef424 /uv /uvx /usr/local/bin/

# ComfyUI source — pinned to the commit `:v0.10-rc` was built from, recovered from
# the image itself (`git -C /opt/ComfyUI rev-parse HEAD`). The pin is a record of
# what already ran: these are the renders v0.10 shipped. Upstream head would have
# imported an untested core into a repair version and made "does the core alone
# shift output at a fixed seed?" a live question (design.md D3). Bumping it forward
# is a separate, deliberate act that must carry its own render comparison.
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /opt/ComfyUI \
    && cd /opt/ComfyUI \
    && git checkout 250b2e9551a7bc7a8ebb5beb07e0fecd2983e04a
WORKDIR /opt/ComfyUI

# The Python environment: `image/` is a uv project whose lock carries every hash
# of ComfyUI's, the preprocessors' and InstantID's packages, and the cu128 torch
# stack with the Blackwell (sm_120) kernels. `--locked` refuses a stale lock, so
# nothing resolves at build time. `tools/derive_image_project.py` writes it.
# Before the node clones, so bumping a node's pin does not reinstall torch
# (0040 design D4).
COPY image/pyproject.toml /opt/isekai/image/pyproject.toml
COPY image/uv.lock /opt/isekai/image/uv.lock
COPY image/.python-version /opt/isekai/image/.python-version
ENV VIRTUAL_ENV=/opt/ComfyUI/.venv
ENV UV_PROJECT_ENVIRONMENT=$VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN uv sync --locked --project /opt/isekai/image

# InstantID custom nodes — pinned (pack is maintenance-only since Apr 2025)
RUN git clone https://github.com/cubiq/ComfyUI_InstantID.git \
        /opt/ComfyUI/custom_nodes/ComfyUI_InstantID \
    && cd /opt/ComfyUI/custom_nodes/ComfyUI_InstantID \
    && git checkout 72495e806bc2ab9c41581e15ccaa1bcf83c477e8

# ControlNet preprocessors — pinned (repos drift; v1.1.5)
RUN git clone https://github.com/Fannovel16/comfyui_controlnet_aux.git \
        /opt/ComfyUI/custom_nodes/comfyui_controlnet_aux \
    && cd /opt/ComfyUI/custom_nodes/comfyui_controlnet_aux \
    && git checkout e8b689a513c3e6b63edc44066560ca5919c0576e

# Provisioning is three tracked files, not one: the driver, the pinned manifest it
# reads, and the module that owns every decision taken about it. Copying only the
# script would put a downloader on the pod without the two things it depends on
# (design.md D15). The layout is preserved because provision.py resolves the
# manifest relative to itself -- `parent.parent.parent / "config"` -- so the
# module's depth under /opt/isekai is load-bearing, and it must land at
# isekai/boundary/ to match the tree it was moved into at v0.15.
# `comfyui_controlnet_aux` writes annotator checkpoints to `<node dir>/ckpts` --
# the pod's container disk, which does not survive the pod. That is 386 MB
# re-fetched from Hugging Face, unpinned, during the first render of every pod,
# on metered time. Redirected onto the models tree they become ordinary manifest
# entries, fetched and verified ahead of time (design.md D7).
#
# The pack reads this as `os.getenv(NAME, default)`, so the environment wins over
# its own `config.yaml`. It also logs `Using ckpts path: ...` from the
# config-derived value, NOT from this override -- so the log will report the old
# path while writing to the new one. Confirm this on the filesystem, never from
# the log.
ENV AUX_ANNOTATOR_CKPTS_PATH=/opt/ComfyUI/models/annotator_ckpts

COPY start.sh /start.sh
COPY tools/download_models.sh /opt/isekai/tools/download_models.sh
COPY config/models.json /opt/isekai/config/models.json
COPY isekai/boundary/provision.py /opt/isekai/isekai/boundary/provision.py
RUN chmod +x /start.sh /opt/isekai/tools/download_models.sh

EXPOSE 8188 22

CMD ["/start.sh"]
