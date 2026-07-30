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

# Download Qwen model
download Comfy-Org/Qwen-Image-Edit_ComfyUI \
    split_files/diffusion_models/qwen_image_edit_2511_fp8mixed.safetensors \
    diffusion_models

download Comfy-Org/Qwen-Image_ComfyUI \
    split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors \
    text_encoders

download Comfy-Org/Qwen-Image_ComfyUI \
    split_files/vae/qwen_image_vae.safetensors \
    vae

download lightx2v/Qwen-Image-Edit-2511-Lightning \
    Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors \
    loras

# Animagine XL 4.0 + InstantID + InsightFace (v0.2, --model animagine)
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

echo "Models downloaded into $MODELS_DIR"
