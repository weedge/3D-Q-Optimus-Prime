# Hyper3D Rodin API 说明

脚本使用 Hyper3D v2 Rodin HTTP API。接口地址通过 `HYPER3D_API_BASE_URL` 配置，默认值为 `https://api.hyper3d.ai/api/v2`。

## 基础生成

`POST /rodin` 使用 multipart 表单：

- `images`：一个或多个参考图片
- `images_assets`：可选的图片元数据 JSON
- `tier`：`Gen-2.5-Medium` 或 `Gen-2.5-Extreme-Low`
- `mesh_mode`：`Raw` 或 `Quad`
- `quality_override`：符合所选网格模式的面数目标
- `geometry_file_format`：`glb`、`usdz`、`fbx`、`obj` 或 `stl`
- `material`：在账号支持时使用 `PBR` 或 `Shaded`

响应通常包含任务标识，例如 `uuid` 和 `jobs`。应保存完整的脱敏响应，因为接口字段可能发生变化。

## 状态与下载

使用 `subscription_key` 调用 `POST /status` 轮询任务。所有任务完成后，使用任务 UUID 调用 `POST /download`，并从响应中识别模型 URL。脚本会在识别到 GLB 时下载文件，同时保存原始响应。

## BANG 拆解

`POST /bang` 使用已完成任务的 UUID 作为 `asset_id`，并接受可选的拆解指令、强度、分辨率和输出格式。用相同方式轮询任务并下载结果。

## 安全要求

- 将 `HYPER3D_API_KEY` 放在环境变量中。
- 不要把 API 密钥写入前端、URL 查询参数或提交到代码仓库。
- 付费任务超时后先查询状态，不要直接重复提交。
- 如果响应结构发生变化，保存原始响应并明确报错，不要猜测下载地址。

参考：[Hyper3D Rodin API Quick Start](https://docs.hyper3d.ai/en/get-started/quick-start)
