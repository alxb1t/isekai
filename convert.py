#!/usr/bin/env python3
"""Headless photo -> anime via a running ComfyUI (Qwen-Image-Edit) over its HTTP API."""
import argparse
import json
import sys
import time
from pathlib import Path
from urllib import request, error, parse


def parse_args():
    p = argparse.ArgumentParser(description="Photo -> anime via ComfyUI (Qwen-Image-Edit).")
    p.add_argument("input", help="input photo (jpg/png)")
    p.add_argument("-o", "--output", default="out.png", help="output image path")
    p.add_argument("--prompt", required=True, help="edit instruction")
    p.add_argument("--workflow", default="workflows/qwen-image-edit.json",
        help="API-format ComfyUI workflow JSON")
    p.add_argument("--server", default="http://127.0.0.1:8188",
        help="ComfyUI base URL (reached via the SSH tunnel)")

    return p.parse_args()


def find_node(workflow, *, class_type=None, title=None):
    """Return the single node ID matching class_type and/or title. Fail if not exactly one."""
    matches = [
        nid for nid, node in workflow.items()
        if (class_type is None or node.get("class_type") == class_type)
        and (title is None or node.get("_meta", {}).get("title") == title)
    ]

    if len(matches) != 1:
        sys.exit(f"find_node(class_type={class_type!r}, title={title!r}): "
                 f"expected exactly 1 match, found {len(matches)}")

    return matches[0]


def _multipart(fields, files):
    """Build a multipart/form-data body by hand. Returns (body_bytes, content_type)."""
    boundary = "---convertpyBoundary7MA4YWxkTrZu0gW"
    body = bytearray()

    for name, value in fields.items():
        body += (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
            f"{value}\r\n"
        ).encode()

    for name, (filename, data, ctype) in files.items():
        body += (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
            f"Content-Type: {ctype}\r\n\r\n"
        ).encode()
        body += data + b"\r\n"

    body += f"--{boundary}--\r\n".encode()

    return bytes(body), f"multipart/form-data; boundary={boundary}"


def _post_json(url, payload):
    req = request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with request.urlopen(req) as resp:
        return json.loads(resp.read())


def _get(url):
    with request.urlopen(url) as resp:
        return resp.read()


def upload_image(server, path):
    """Upload a local image into ComfyUI's input/ folder; return the stored filename."""
    body, content_type = _multipart(
        fields={"overwrite": "true"},
        files={"image": (Path(path).name, Path(path).read_bytes(), "application/octet-stream")},
    )

    req = request.Request(
        f"{server}/upload/image",
        data=body,
        headers={"Content-Type": content_type},
        method="POST"
    )

    with request.urlopen(req) as resp:
        return json.loads(resp.read())["name"]


def main():
    args = parse_args()
    server = args.server.rstrip("/")
    workflow = json.loads(Path(args.workflow).read_text())

    # Upload the photo into ComfyUI's input/ folder (on the pod)
    image_name = upload_image(server, args.input)

    # Point the LoadImage node at the uploaded file
    load_id = find_node(workflow, class_type="LoadImage")
    workflow[load_id]["inputs"]["image"] = image_name

    # Inject the prompt into the positive text-encode node
    pos_id = find_node(workflow, title="positive")
    workflow[pos_id]["inputs"]["text"] = args.prompt

    # Submit the graph to ComfyUI's queue
    try:
        result = _post_json(f"{server}/prompt", {"prompt": workflow})
    except error.HTTPError as e:
        sys.exit(f"ComfyUI rejected the workflow ({e.code}):\n{e.read().decode()}")

    prompt_id = result["prompt_id"]
    print(f"queued {prompt_id} — waiting for the GPU...")

    # Poll the history until this prompt finishes
    while True:
        history = json.loads(_get(f"{server}/history/{prompt_id}"))
        if prompt_id in history:
            break
        time.sleep(1)

    # Find the saved image among the node outputs and download it
    outputs = history[prompt_id]["outputs"]
    for node_output in outputs.values():
        if "images" in node_output:
            img = node_output["images"][0]
            break
    else:
        sys.exit("no image found in the workflow outputs")

    query = parse.urlencode({
        "filename": img["filename"],
        "subfolder": img["subfolder"],
        "type": img["type"],
    })
    Path(args.output).write_bytes(_get(f"{server}/view?{query}"))
    print(f"saved {args.output}")


if __name__ == "__main__":
    main()
