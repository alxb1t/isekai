# CUDA runtime
FROM nvidia/cuda:12.4.1-devel-ubuntu22.04

ENV PYTHONUNBUFFERED=1 DEBIAN_FRONTEND=noninteractive

# System packages
RUN apt-get update && apt-get install -y --no-install-recommends \
        git python3 python3-pip curl wget openssh-server \
        libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

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

# Isolated venv
ENV VIRTUAL_ENV=/opt/ComfyUI/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN uv venv --python 3.12 "$VIRTUAL_ENV"

# CUDA-matched PyTorch — cu128 build ships sm_120 kernels for the Blackwell GPU
RUN uv pip install torch==2.8.0 torchvision==0.23.0 torchaudio==2.8.0 \
    --index-url https://download.pytorch.org/whl/cu128

# ComfyUI python deps
RUN uv pip install -r requirements.txt

# InstantID custom nodes — pinned (pack is maintenance-only since Apr 2025)
RUN git clone https://github.com/cubiq/ComfyUI_InstantID.git \
        /opt/ComfyUI/custom_nodes/ComfyUI_InstantID \
    && cd /opt/ComfyUI/custom_nodes/ComfyUI_InstantID \
    && git checkout 72495e806bc2ab9c41581e15ccaa1bcf83c477e8

# InstantID's runtime deps — CPU onnxruntime only (never -gpu; face pass is a tiny CPU op)
RUN uv pip install insightface==0.7.3 onnxruntime==1.20.1

# ControlNet preprocessors — pinned (repos drift; v1.1.5)
RUN git clone https://github.com/Fannovel16/comfyui_controlnet_aux.git \
        /opt/ComfyUI/custom_nodes/comfyui_controlnet_aux \
    && cd /opt/ComfyUI/custom_nodes/comfyui_controlnet_aux \
    && git checkout e8b689a513c3e6b63edc44066560ca5919c0576e

# Preprocessor runtime deps (DWPose, lineart, depth, tile)
RUN uv pip install -r \
    /opt/ComfyUI/custom_nodes/comfyui_controlnet_aux/requirements.txt

# Provisioning is three tracked files, not one: the driver, the pinned manifest it
# reads, and the module that owns every decision taken about it. Copying only the
# script would put a downloader on the pod without the two things it depends on
# (design.md D15). The layout is preserved because provision.py resolves the
# manifest relative to itself.
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
COPY scripts/download_models.sh /opt/isekai/scripts/download_models.sh
COPY scripts/models.json /opt/isekai/scripts/models.json
COPY isekai/provision.py /opt/isekai/isekai/provision.py
RUN chmod +x /start.sh /opt/isekai/scripts/download_models.sh

EXPOSE 8188 22

CMD ["/start.sh"]
