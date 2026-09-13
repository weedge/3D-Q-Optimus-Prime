---
name: hyper3d-mcp-model-landing-page
description: "Create a complete 3D product or character showcase from a local image, image URL, or OpenAI-generated image, using the Hyper3D MCP tools rather than the direct Hyper3D HTTP Python script. Import the reference, call Rodin generation, wait for completion, retrieve the model, optionally run BANG part splitting, integrate the GLB into a Three.js/React landing page, and verify the result."
---

# Hyper3D MCP Model Landing Page

## Purpose

Use this Skill when the 3D generation step must run through Hyper3D MCP. The image-generation step remains a separate Python script, while model generation, waiting, result retrieval, and optional part splitting use `mcp__hyper3d__*` tools directly.

Do not call the direct HTTP workflow in `../hyper3d-model-landing-page/scripts/generate_hyper3d_model.py` for this Skill. That script belongs to the non-MCP variant.

## MCP Prerequisite

Before preparing uploads or spending generation credits, confirm that the current client exposes the Hyper3D MCP tools, especially `rodin_generate`, `rodin_wait`, and `rodin_get_result`. If Hyper3D MCP is unavailable, do not fall back to the direct HTTP script and do not pretend that generation can start. Stop and show the following installation prompt verbatim:

> 请在我当前使用的客户端（Codex 或 Claude Code）中配置 Hyper3D MCP：服务名 hyper3d，Streamable HTTP 地址 https://api.hyper3d.com/api/mcp，使用 OAuth 授权。按当前客户端的方式配置，保留其他设置，已有配置请复用或更新。引导我在浏览器中完成授权，然后验证连接并列出可用工具。如需重启，请告诉我。

After the user completes the setup, re-check the MCP connection and list the available Hyper3D tools before continuing. Reuse an existing configuration when present; do not overwrite unrelated MCP services or settings.

## Inputs and Outputs

Reference inputs:

- Local image: upload through `rodin_create_uploads` and its presigned PUT URL.
- Image URL: download and validate it locally, then upload it through `rodin_create_uploads`.
- OpenAI-generated image: run `scripts/generate_reference_image.py`, then upload its output.
- Chat attachment: use `rodin_import_images` when the current host supplies the required attachment metadata.

Expected outputs:

- A permanent Hyper3D result page from `rodin_get_result.display_url`.
- A downloaded GLB or other requested geometry file for the frontend.
- Optional BANG result and separate-part model.
- A runnable landing page using the generated model.
- A concise handoff containing model paths, result page, and verification status.

Generation and BANG splitting consume credits. Submit only the exact generation and split requested by the user. Do not create extra variants or retry a timed-out paid generation blindly.

## Quick Start

Install the image-script dependency only when OpenAI image generation is needed:

```bash
python3 -m pip install -r scripts/requirements.txt
```

Generate a reference image:

```bash
OPENAI_API_KEY="$OPENAI_API_KEY" \
python3 scripts/generate_reference_image.py \
  --prompt "A full-body stylized robot product render, centered, front three-quarter view, complete feet and lower body" \
  --output ./artifacts/reference.png
```

Then use the Hyper3D MCP flow described below with the generated file. The MCP calls are not replaced by a Python HTTP request.

## MCP Workflow

### 1. Prepare and upload the reference

For local files and downloaded URLs:

1. Confirm the file is non-empty and is a supported raster image.
2. Call `mcp__hyper3d__rodin_create_uploads` with filename, MIME type, and byte size.
3. Upload the file bytes to every returned presigned PUT URL.
4. Pass the returned `upload_id` values to `mcp__hyper3d__rodin_generate` in `reference_upload_ids`, preserving image order.

For ChatGPT conversation attachments, call `mcp__hyper3d__rodin_import_images` with the attachment `file_id`, `download_url`, filename, and MIME type. Pass its upload IDs to `rodin_generate`.

If image upload is blocked, report that limitation and direct the user to upload through Hyper3D's hosted flow. Do not pretend the generation job was submitted.

### 2. Generate the base model

Call `mcp__hyper3d__rodin_generate` with a non-empty prompt, uploaded reference IDs, or both. Default to:

- `geometry_file_format: "glb"`
- `tier: "Gen-2.5-Medium"`
- `mesh_mode: "Quad"`
- A quality target valid for the chosen mesh mode

For a character or robot, prompt for a complete full-body model, readable silhouette, feet, lower legs, and distinct component boundaries. Do not use a head-only reference or crop when the page needs a complete figure.

Use `mcp__hyper3d__rodin_wait` with the returned `generation_id`. A timeout is not a failure; inspect the latest state and continue later rather than submitting the same request again. If generation fails, report the returned status and do not spend credits on an automatic retry.

### 3. Retrieve the model file

After the generation reaches a completed state, call `mcp__hyper3d__rodin_get_result`.

- Use `display_url` as the user-facing permanent result link.
- Use a returned temporary `files[].url` only to download the requested model into the project, because the user explicitly requested a 3D file and landing page.
- Identify the actual geometry file by response metadata and file signature; do not assume the first URL is a GLB.
- Save the downloaded file with a stable name such as `public/generated-model.glb`.
- Preserve the generation response and model path in a local manifest without API keys.

### 4. Split into independent parts when requested

Call `mcp__hyper3d__rodin_generate_bang` only after the base generation completes. Pass its `asset_id` as the completed base `generation_id`, and use the user's requested part count in `instruction` or the split settings.

For a symmetric robot, use explicit semantic guidance such as head, left/right arms, left/right chest, core torso, and left/right legs/feet. Wait for the BANG generation, retrieve its result, and use the BANG file as the exploded-view source. Never simulate independent parts with CSS or arbitrary mesh offsets when the user explicitly requested an actual split.

## Landing Page Integration

Inspect the existing frontend before scaffolding. Reuse the current React/Vite/Three.js page and visual template when it matches the requested showcase. Copy the retrieved GLB into `public/` and keep loading/error states visible.

The viewer must:

- Load the actual GLB with `GLTFLoader`.
- Inspect the scene hierarchy and confirm every top-level part/group before creating labels.
- Map each structure-index button to the exact node/group; never guess names or fixed ordering.
- Capture assembled and exploded transforms in the same coordinate space.
- Interpolate continuously from assembled to exploded state with damping/easing.
- Use mirrored left/right targets and a stable centerline for symmetric displays.
- Fit camera bounds across every visible mesh in both states, including feet and lower geometry.
- Make selection visibly different with emissive color, opacity, outline, or a callout.
- Keep orbit, zoom, reset, progress, and full-screen controls accessible.

For a product-style landing page, include a hero title, model status label, structure index, assembled/exploded timeline, interaction hint, and an information panel. Use external references as visual direction only; do not copy proprietary text or artwork verbatim.

If factual character or product information is added, research authoritative sources, add source links to the page, and label the generated model as a non-official visual study when applicable.

## Verification

Run the existing frontend build, normally `npm run build`. Verify:

- The page and generated GLB return HTTP 200.
- The complete object is visible in assembled view, including feet.
- The progress control visibly separates every requested independent part.
- Every index item highlights the matching physical part.
- The model does not twist or collapse because of mixed local/world transforms.
- The modal, timeline, and interaction hint do not overlap on desktop or mobile.
- The console has no new model-loading or interaction errors.

Deliver the frontend path, model path, Hyper3D `display_url`, and a list of changed files. State clearly if the MCP result only provides a hosted result page and no downloadable geometry file.

## Python Script Contract

`scripts/generate_reference_image.py` is intentionally limited to OpenAI reference-image generation:

- `--prompt`: image prompt
- `--output`: PNG destination
- `--model`, `--size`, `--quality`: image-generation settings

It requires `OPENAI_API_KEY` and writes the image locally. It must not call Hyper3D. The Hyper3D model step belongs exclusively to the MCP tools in this Skill.

## Common Failure Modes

- **Upload rejected**: check MIME type, byte size, and presigned URL upload before calling `rodin_generate`.
- **Head-only model**: improve the reference and prompt with full-body, feet, and lower-body requirements; do not hide missing geometry by zooming out.
- **BANG parts overlap**: inspect actual generated part hierarchy and transform spaces before changing camera scale.
- **Index mismatch**: inspect confirmed scene node names and keep one explicit mapping from index entry to group.
- **No visible explosion**: verify that the BANG result is loaded and that the progress value interpolates real part transforms.
- **Generation timeout**: read the existing generation state and continue; do not submit a duplicate paid job.
- **MCP upload unavailable**: preserve the local reference and explain that the current environment cannot upload it; provide the Hyper3D hosted upload fallback.
