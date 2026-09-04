#!/usr/bin/env bash

set -euo pipefail

# ComfyUI's models root
MODELS_DIR="${MODELS_DIR:-./models}"

# Download <repo> <path-in-repo> <target-subfolder>
download() {
    local repo="$1" path="$2" dest="$3"
    local fname; fname="$(basename "$path")"
    if [ -f "$MODELS_DIR/$dest/$fname" ]; then
        echo "✓ $dest/$fname present — skipping"
        return
    fi
    mkdir -p "$MODELS_DIR/$dest"
    hf download "$repo" "$path" --local-dir "$MODELS_DIR/.hf"
    mv "$MODELS_DIR/.hf/$path" "$MODELS_DIR/$dest/"
}

# Download a folder: <repo> <target-subfolder> <include-glob>
download_folder() {
    local repo="$1" dest="$2" glob="$3"
    mkdir -p "$MODELS_DIR/$dest"
    if compgen -G "$MODELS_DIR/$dest/$glob" >/dev/null; then
        echo "✓ $dest/$glob present — skipping"
        return
    fi
    hf download "$repo" --include "$glob" --local-dir "$MODELS_DIR/$dest"
}

# Animagine XL 4.0 + InstantID + InsightFace
download cagliostrolab/animagine-xl-4.0 \
    animagine-xl-4.0.safetensors \
    checkpoints

download InstantX/InstantID \
    ip-adapter.bin \
    instantid

download InstantX/InstantID \
    ControlNetModel/diffusion_pytorch_model.safetensors \
    controlnet/instantid

download_folder DIAMONIK7777/antelopev2 \
    insightface/models/antelopev2 \
    "*.onnx"

# SDXL ControlNet stack
download TTPlanet/TTPLanet_SDXL_Controlnet_Tile_Realistic \
    TTPLANET_Controlnet_Tile_realistic_v2_fp16.safetensors \
    controlnet

download xinsir/controlnet-openpose-sdxl-1.0 \
    diffusion_pytorch_model.safetensors \
    controlnet/openpose

download TheMistoAI/MistoLine \
    mistoLine_rank256.safetensors \
    controlnet

echo "Models downloaded into $MODELS_DIR"
