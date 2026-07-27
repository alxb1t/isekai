# CUDA runtime
FROM nvidia/cuda:12.4.1-devel-ubuntu22.04

ENV PYTHONUNBUFFERED=1 DEBIAN_FRONTEND=noninteractive

# System packages
RUN apt-get update && apt-get install -y --no-install-recommends \
        git python3 python3-pip curl openssh-server \
    && rm -rf /var/lib/apt/lists/*

# uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# ComfyUI source
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /opt/ComfyUI
WORKDIR /opt/ComfyUI

# Isolated venv
ENV VIRTUAL_ENV=/opt/ComfyUI/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN uv venv "$VIRTUAL_ENV"

# CUDA-matched PyTorch
RUN uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# ComfyUI python deps
RUN uv pip install -r requirements.txt

COPY start.sh /start.sh
COPY scripts/download_models.sh /download_models.sh
RUN chmod +x /start.sh /download_models.sh

EXPOSE 8188 22

CMD ["/start.sh"]
