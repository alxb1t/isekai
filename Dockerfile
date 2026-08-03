# CUDA runtime
FROM nvidia/cuda:12.4.1-devel-ubuntu22.04

ENV PYTHONUNBUFFERED=1 DEBIAN_FRONTEND=noninteractive

# System packages
RUN apt-get update && apt-get install -y --no-install-recommends \
        git python3 python3-pip curl openssh-server \
        libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# ComfyUI source
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /opt/ComfyUI
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

COPY start.sh /start.sh
COPY scripts/download_models.sh /download_models.sh
RUN chmod +x /start.sh /download_models.sh

EXPOSE 8188 22

CMD ["/start.sh"]
