# Hyper3D MCP Tool Contract

## Prerequisite check

Before any upload or paid generation, verify that the current Codex or Claude Code client exposes the Hyper3D MCP tools. If it does not, stop and show this exact prompt:

> 请在我当前使用的客户端（Codex 或 Claude Code）中配置 Hyper3D MCP：服务名 hyper3d，Streamable HTTP 地址 https://api.hyper3d.com/api/mcp，使用 OAuth 授权。按当前客户端的方式配置，保留其他设置，已有配置请复用或更新。引导我在浏览器中完成授权，然后验证连接并列出可用工具。如需重启，请告诉我。

After configuration, verify the connection and list the available tools before resuming. Never silently switch to the direct Hyper3D HTTP workflow.

Use the MCP tools in this order:

1. `mcp__hyper3d__rodin_create_uploads` for local/downloaded images, then HTTP PUT each image to its presigned URL.
2. `mcp__hyper3d__rodin_import_images` for conversation attachments when attachment metadata is available.
3. `mcp__hyper3d__rodin_generate` with `reference_upload_ids`, a concrete prompt, and the requested output format.
4. `mcp__hyper3d__rodin_wait` with the returned `generation_id` until the result is complete.
5. `mcp__hyper3d__rodin_get_result` for the permanent `display_url` and temporary output file URLs.
6. Optional: `mcp__hyper3d__rodin_generate_bang` with the completed base `generation_id`, then `rodin_wait` and `rodin_get_result` again.

## Result handling

- Present only `display_url` as the user-facing Hyper3D result page.
- Download `files[].url` only when the user requested the geometry file or when it is required to build the requested landing page.
- Do not expose API keys, upload URLs, subscription data, or raw credentials in the frontend or final handoff.
- If the model result is not downloadable, keep the result page and explain that limitation instead of fabricating a local file.
