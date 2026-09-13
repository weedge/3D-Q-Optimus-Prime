# Hyper3D Rodin API Notes

The script targets Hyper3D's v2 Rodin HTTP API. Keep the endpoint configurable with `HYPER3D_API_BASE_URL`; the default is `https://api.hyper3d.ai/api/v2`.

## Base generation

`POST /rodin` uses multipart form data:

- `images`: one or more reference images
- `images_assets`: optional image metadata JSON
- `tier`: `Gen-2.5-Medium` or `Gen-2.5-Extreme-Low`
- `mesh_mode`: `Raw` or `Quad`
- `quality_override`: a mode-valid polygon target
- `geometry_file_format`: `glb`, `usdz`, `fbx`, `obj`, or `stl`
- `material`: `PBR` or `Shaded` when supported by the account

The response contains task identifiers, commonly `uuid` and `jobs`. Preserve the complete redacted response because response fields can evolve.

## Status and download

Poll `POST /status` with `subscription_key`. When all jobs are terminal, call `POST /download` with the task UUID and inspect the response for model URLs. The script downloads a returned GLB URL when it can identify one and always saves the raw response.

## BANG split

`POST /bang` accepts the completed task UUID as `asset_id`, plus optional split guidance, strength, resolution, and output format. Poll the returned jobs in the same way as the base task and download the completed model response.

## Safety

- Keep `HYPER3D_API_KEY` and any subscription key in environment variables.
- Never put API keys in a frontend bundle, URL query string, or checked-in JSON.
- Do not retry a timed-out paid request blindly; first inspect the task status.
- If the API response shape changes, preserve the raw response and fail clearly rather than guessing a download URL.

Reference: [Hyper3D Rodin API Quick Start](https://docs.hyper3d.ai/en/get-started/quick-start)
