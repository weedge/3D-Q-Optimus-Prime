---
name: hyper3d-mcp-model-landing-page
description: "从本地图片、图片 URL 或 OpenAI 生成图片创建完整的 3D 产品/角色展示页，并使用 Hyper3D MCP 而不是直接 HTTP Python 脚本生成模型。流程包括导入参考图、调用 Rodin、等待完成、获取模型、可选 BANG 部件拆解、接入 Three.js/React 落地页和结果验证。"
---

# Hyper3D MCP 模型落地页

## 项目隔离规则

创建新的 3D 展示页时，必须先创建新的项目目录，并将该展示页的前端代码、模型、图片、生成元数据和验证产物全部放在这个目录中。默认规则如下：

- 每个 3D 展示页对应一个独立文件夹，例如 `projects/<project-slug>/`；文件夹名称使用稳定、可读且不重复的 slug。
- 不要复用已有展示页项目，不要直接覆盖已有项目的 `src/`、`public/`、模型文件或配置。
- 不要把新页面写入当前打开的旧项目；“当前已有项目”不等于“新项目的目标项目”。
- 只有用户明确说“修改/继续某个已有项目”并给出项目路径或名称时，才允许复用该项目目录；继续前先确认目标目录。
- 如果已有素材可以复用，复制或引用到新项目的独立资源目录，并记录来源；不要通过修改旧项目文件来共享资源。
- 交付时同时报告新项目的绝对路径和页面入口文件，明确说明它与已有项目隔离。

项目初始化顺序固定为：确定页面 slug → 创建新目录 → 初始化或复制最小前端模板 → 导入/生成模型资源 → 接入展示页 → 构建和验证。不要先在旧目录中试写，再移动文件。

## 作用

本 Skill 与 `hyper3d-model-landing-page` 的区别是：3D 模型生成、任务等待、结果获取和可选部件拆解必须使用 Hyper3D MCP 工具直接完成。

不要调用 `../hyper3d-model-landing-page/scripts/generate_hyper3d_model.py`。该脚本属于直接 HTTP API 版本。

## MCP 前置检查

在准备上传或消耗生成额度前，先确认当前客户端能使用 Hyper3D MCP 工具，至少包括 `rodin_generate`、`rodin_wait` 和 `rodin_get_result`。如果 Hyper3D MCP 不可用：

1. 不要退回直接 HTTP 脚本。
2. 不要假装生成任务已经开始。
3. 停止流程，并原样显示以下安装提示：

> 请在我当前使用的客户端（Codex 或 Claude Code）中配置 Hyper3D MCP：服务名 hyper3d，Streamable HTTP 地址 https://api.hyper3d.com/api/mcp，使用 OAuth 授权。按当前客户端的方式配置，保留其他设置，已有配置请复用或更新。引导我在浏览器中完成授权，然后验证连接并列出可用工具。如需重启，请告诉我。

用户完成配置后，重新检查 MCP 连接并列出可用的 Hyper3D 工具，再继续流程。已有配置应复用或更新，不要覆盖无关的 MCP 服务或设置。

## 输入与输出

支持的参考图输入：

- 本地图片：通过 `rodin_create_uploads` 获取上传地址后上传。
- 图片 URL：下载并校验后，通过 `rodin_create_uploads` 上传。
- OpenAI 生成图片：运行 `scripts/generate_reference_image.py` 后上传输出文件。
- 对话附件：当前宿主提供附件元数据时，使用 `rodin_import_images`。

预期输出：

- `rodin_get_result.display_url` 返回的永久 Hyper3D 结果页。
- 用于前端的 GLB 或其他指定格式模型文件。
- 可选的 BANG 拆解结果和独立部件模型。
- 使用生成模型的可运行落地展示页。
- 包含模型路径、结果页和验证状态的交付说明。

生成和 BANG 拆解会消耗额度。只提交用户明确要求的生成和拆解，不要自动创建额外版本，也不要盲目重试超时的付费任务。

## 快速开始

只有在需要 OpenAI 生图时才安装图片脚本依赖：

```bash
python3 -m pip install -r scripts/requirements.txt
```

生成参考图：

```bash
OPENAI_API_KEY="$OPENAI_API_KEY" \
python3 scripts/generate_reference_image.py \
  --prompt "A full-body stylized robot product render, centered, front three-quarter view, complete feet and lower body" \
  --output ./artifacts/reference.png
```

然后使用下面的 Hyper3D MCP 流程处理生成的图片。不要用 Python HTTP 请求替代 MCP 调用。

## MCP 工作流程

### 1. 准备并上传参考图

对于本地文件和下载的 URL：

1. 确认文件非空且为支持的栅格图片。
2. 使用文件名、MIME 类型和字节数调用 `mcp__hyper3d__rodin_create_uploads`。
3. 将文件字节上传到每个返回的预签名 PUT 地址。
4. 按图片顺序，将返回的 `upload_id` 传给 `mcp__hyper3d__rodin_generate` 的 `reference_upload_ids`。

对于 ChatGPT 对话附件，在附件元数据可用时调用 `mcp__hyper3d__rodin_import_images`，传入 `file_id`、`download_url`、文件名和 MIME 类型，再将返回的上传 ID 传给 `rodin_generate`。

如果图片上传受阻，说明当前环境限制并引导用户使用 Hyper3D 网页上传，不要声称任务已经提交。

### 2. 生成基础模型

使用非空提示词、上传的参考图 ID 或二者调用 `mcp__hyper3d__rodin_generate`。默认使用：

- `geometry_file_format: "glb"`
- `tier: "Gen-2.5-Medium"`
- `mesh_mode: "Quad"`
- 符合网格模式的质量目标

角色或机器人必须要求完整身体、清晰轮廓、脚部、下腿和明确的部件边界。页面需要完整模型时，不要使用只有头部的参考图或裁切图。

使用返回的 `generation_id` 调用 `mcp__hyper3d__rodin_wait`。超时不代表失败，应读取最新状态并在之后继续，不要重复提交同一任务。生成失败时报告返回状态，不要自动消耗额度重试。

### 3. 获取模型文件

任务完成后调用 `mcp__hyper3d__rodin_get_result`：

- 使用 `display_url` 作为面向用户的永久结果链接。
- 用户明确要求 3D 文件和落地页时，才使用返回的临时 `files[].url` 下载模型。
- 根据响应元数据和文件签名识别真正的几何文件，不要假设第一个 URL 一定是 GLB。
- 使用稳定文件名保存，例如 `public/generated-model.glb`。
- 保存脱敏后的生成响应和模型路径，不要保存 API 密钥。

### 4. 按要求拆分独立部件

基础生成完成后才能调用 `mcp__hyper3d__rodin_generate_bang`。将已完成基础任务的 `generation_id` 作为 `asset_id`，并在 `instruction` 或拆解参数中写明用户要求的部件数量。

对于对称机器人，使用头部、左右手臂、左右胸甲、核心躯干、左右腿/脚等明确语义。等待 BANG 完成后再次获取结果，并用 BANG 文件作为爆炸视图来源。用户要求真实独立部件时，不要用 CSS 或任意网格位移伪造拆解。

## 落地展示页接入

搭建前先检查现有前端，优先复用当前 React/Vite/Three.js 页面与视觉模板。将获取的 GLB 复制到 `public/`，并保留加载中和加载失败状态。

展示器必须：

- 使用 `GLTFLoader` 加载真实 GLB。
- 检查场景层级，确认每个顶层部件/组后再创建索引标签。
- 将每个索引按钮绑定到准确的节点/组，不得猜测名称或固定顺序。
- 在同一坐标系中记录完整形态和爆炸形态的变换。
- 使用带缓动的连续进度进行展开动画。
- 使用左右镜像目标位移并保持中心线稳定。
- 根据两种状态下所有可见网格计算相机范围，确保脚部和最低几何体在画面中。
- 点击索引时用发光、透明度、描边或标注明显区分准确部件。
- 保持旋转、缩放、重置、进度和全屏控件可用。

产品风格页面应包含标题、模型状态、结构索引、完整/爆炸时间轴、交互提示和信息面板。外部参考只用于视觉方向，不要原样复制受版权保护的文本或图片。

页面添加角色或产品资料时，先查找权威来源，保留页面来源链接，并标注生成模型为非官方视觉研究（如适用）。

## 验证

运行已有的前端构建命令，通常是 `npm run build`。验证：

- 页面和生成的 GLB 返回 HTTP 200。
- 完整形态能显示整个对象，包括脚部。
- 进度控制能逐步分离所有请求的独立部件。
- 每个索引项都能高亮对应的实体部件。
- 没有因局部/世界变换混用造成的扭曲或塌缩。
- 弹窗、时间轴和交互提示在桌面端与移动端不重叠。
- 没有新增的模型加载或交互控制台错误。

交付时说明前端路径、模型路径、Hyper3D `display_url` 和修改文件。如果结果只有托管结果页而没有可下载几何文件，必须明确说明。

## Python 脚本说明

`scripts/generate_reference_image.py` 只负责 OpenAI 参考图生成：

- `--prompt`：生图提示词
- `--output`：PNG 目标路径
- `--model`、`--size`、`--quality`：生图参数

该脚本需要 `OPENAI_API_KEY`，会将图片写入本地，不能调用 Hyper3D。Hyper3D 模型步骤专属于本 Skill 的 MCP 工具流程。

## 常见问题

- **未安装 MCP**：停止流程，显示 MCP 安装提示；不要切换到直接 HTTP 版本。
- **上传被拒绝**：检查 MIME 类型、字节数和预签名 URL 上传结果，再调用 `rodin_generate`。
- **只得到头部模型**：优化参考图和提示词，加入完整身体、脚部和下半身要求，不要用缩小相机隐藏缺失几何体。
- **BANG 部件重叠**：检查实际生成的部件层级和坐标系，再调整相机。
- **索引错位**：读取确认过的场景节点名称，使用明确的索引到节点映射。
- **没有爆炸效果**：检查是否加载了 BANG 结果，以及进度值是否插值真实部件变换。
- **MCP 上传不可用**：保留本地参考图，说明当前环境无法上传，并引导用户使用 Hyper3D 网页上传。
- **任务超时**：读取已有 `generation_id` 的状态并继续，不要重复创建付费任务。
