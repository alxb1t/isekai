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

# Download model
download Comfy-Org/Qwen-Image-Edit_ComfyUI \
    split_files/diffusion_models/qwen_image_edit_2511_fp8mixed.safetensors \
    diffusion_models

download Comfy-Org/Qwen-Image_ComfyUI \
    split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors \
    text_encoders

download Comfy-Org/Qwen-Image_ComfyUI \
    split_files/vae/qwen_image_vae.safetensors \
    vae

echo "Models downloaded into $MODELS_DIR"
