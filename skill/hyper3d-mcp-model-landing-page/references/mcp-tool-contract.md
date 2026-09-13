# Hyper3D MCP 工具契约

## 前置检查

在上传图片或开始付费生成前，确认当前 Codex 或 Claude Code 客户端暴露了 Hyper3D MCP 工具。如果不可用，停止并原样显示：

> 请在我当前使用的客户端（Codex 或 Claude Code）中配置 Hyper3D MCP：服务名 hyper3d，Streamable HTTP 地址 https://api.hyper3d.com/api/mcp，使用 OAuth 授权。按当前客户端的方式配置，保留其他设置，已有配置请复用或更新。引导我在浏览器中完成授权，然后验证连接并列出可用工具。如需重启，请告诉我。

完成配置后，先验证连接并列出可用工具，再恢复工作。不要静默切换到直接 Hyper3D HTTP 流程。

## 工具调用顺序

1. 本地/下载图片：调用 `mcp__hyper3d__rodin_create_uploads`，再通过 HTTP PUT 上传到预签名地址。
2. 对话附件：在附件元数据可用时调用 `mcp__hyper3d__rodin_import_images`。
3. 使用 `reference_upload_ids`、具体提示词和目标格式调用 `mcp__hyper3d__rodin_generate`。
4. 使用返回的 `generation_id` 调用 `mcp__hyper3d__rodin_wait`，直到完成。
5. 调用 `mcp__hyper3d__rodin_get_result` 获取永久 `display_url` 和临时输出文件 URL。
6. 可选：使用基础 `generation_id` 调用 `mcp__hyper3d__rodin_generate_bang`，然后再次等待并获取结果。

## 结果处理

- 面向用户只展示 `display_url`。
- 只有在用户要求几何文件或落地页必须使用模型时，才下载 `files[].url`。
- 不要在前端或最终交付说明中暴露 API 密钥、上传地址、订阅信息或原始凭证。
- 如果结果只有网页而没有可下载模型，保留结果页并明确说明，不要伪造本地文件。
