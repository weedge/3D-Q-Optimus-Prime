---
name: hyper3d-model-landing-page
description: "从本地图片、图片 URL 或 OpenAI 生成图片创建完整的 3D 产品/角色展示页：获取参考图，通过 Hyper3D Rodin HTTP API 生成 GLB/3D 资产，可选拆分为独立爆炸视图部件，接入 Three.js/React 落地页并完成验证。适用于图片转 Hyper3D 模型、交互式 3D 展示页、爆炸视图模型或生成 3D 文件与可运行展示页的请求。"
---

# Hyper3D 模型落地页

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

本 Skill 覆盖从视觉参考图到可运行 3D 展示页的完整流程，包含资源生成 Python 脚本，以及将 GLB 接入现有或新前端的实现规范。

两个 Python 脚本分别处理参考图生成和 3D 模型生成：`generate_reference_image.py` 负责 OpenAI 生图；`generate_hyper3d_model.py` 负责本地/URL 图片准备、Hyper3D Rodin 提交、任务轮询、模型下载、可选 BANG 拆解，以及可选复制到前端项目的 `public/` 目录。页面视觉实现和浏览器验证由执行代理完成。

## 输入与输出

模型脚本支持以下参考图输入：

- 本地栅格图片：`--image-path path/to/reference.png`
- 图片 URL：`--image-url https://example.com/reference.png`
- 通过配套脚本生成的图片：同样使用 `--image-path`

输出目录通常包含：

- `reference.*`：本次生成使用的参考图
- `rodin-submit.json`：已脱敏的提交信息
- `rodin-status.json`：基础模型任务状态
- `model.glb`：下载的基础模型
- `bang-status.json` 与 `model-exploded.glb`：可选的拆解模型
- `model-manifest.json`：模型路径、任务 ID 和页面接入信息

传入 `--project-dir` 后，最终模型会复制到 `<project-dir>/public/`。除非明确传入 `--force`，不要覆盖已有模型。

## 快速开始

安装 Python 依赖：

```bash
python3 -m pip install -r requirements.txt
```

使用 OpenAI 生成参考图：

```bash
OPENAI_API_KEY="$OPENAI_API_KEY" \
python3 scripts/generate_reference_image.py \
  --prompt "A full-body Q-style robot product render, front three-quarter view, centered, clean silhouette, complete feet" \
  --output ./artifacts/robot/reference.png
```

将参考图提交给 Hyper3D，并拆分为部件：

```bash
HYPER3D_API_KEY="$HYPER3D_API_KEY" \
python3 scripts/generate_hyper3d_model.py \
  --image-path ./artifacts/robot/reference.png \
  --prompt "Full-body Q-style robot with distinct head, arms, torso, legs and feet, polished painted metal, web-ready 3D asset" \
  --bang \
  --bang-instruction "Split into 8 readable symmetric parts: head, left arm, right arm, left chest, right chest, core torso, left leg and foot, right leg and foot" \
  --out-dir ./artifacts/robot
```

`generate_reference_image.py` 需要 `OPENAI_API_KEY`；`generate_hyper3d_model.py` 需要 `HYPER3D_API_KEY`。不要把密钥写入源码、清单、提示词、日志或前端代码。

## 工作流程

### 1. 准备参考图

- 校验本地图片非空且为支持的栅格格式。
- 下载 URL 时限制请求大小，检查 HTTP 状态和内容类型，拒绝 HTML 或空响应。
- OpenAI 生图使用 `generate_reference_image.py` 和官方 Python SDK；默认模型为 `gpt-image-2`，可通过 `--model` 覆盖。
- 角色或机器人必须要求完整身体、居中构图、清晰轮廓，并明确包含脚部和下半身。
- 生成图片只作为视觉参考，不要宣称其为官方角色或授权设计。

### 2. 通过 HTTP API 生成 Hyper3D 模型

`generate_hyper3d_model.py` 使用 Hyper3D v2 Rodin HTTP API，以 multipart 图片上传和 JSON 参数提交任务。默认使用适合网页展示的 GLB、`Quad` 网格和可配置的中等质量档位。

基础任务必须完成后才能执行拆解。轮询时遵守服务端的 `Retry-After`，超时不要盲目重复提交；保存任务状态并使用任务 ID 继续检查。

### 3. 使用 BANG 拆解部件

仅在基础模型完成后使用 `--bang`。通过 `--bang-instruction` 传入用户需要的部件数量和语义拆分方式。对于对称机器人，优先使用头部、左右手臂、左右胸甲、核心躯干、左右腿/脚等明确部件。

如果用户要求真实独立部件，不要用单个未拆分网格配合前端位移伪造爆炸视图。

### 4. 接入落地展示页

编辑前先检查现有项目，优先复用当前 React/Vite/Three.js 技术栈、依赖和视觉模板。将最终 GLB 放入 `public/`，并提供加载中与加载失败状态。

展示器必须：

- 使用 `GLTFLoader` 加载真实 GLB。
- 先检查场景层级，再创建部件名称和索引，不得假设 `root0` 或固定顺序。
- 用同一个映射表关联索引、展示名称、颜色、节点、基础变换和爆炸目标。
- 在同一坐标系中记录部件的完整形态和爆炸形态，并用带缓动的连续进度插值。
- 使用左右镜像的目标位移并保持模型中心线稳定。
- 根据所有可见网格和两种形态的范围适配相机，确保脚部和最低点在画面内。
- 点击索引时只高亮真实对应的节点/部件，不得高亮错误代理对象。
- 支持拖动旋转、滚轮/双指缩放、重置和全屏等控件。

产品风格落地页应包含标题、模型状态、结构索引、完整/爆炸时间轴、交互提示和信息面板。参考页面只用于视觉方向，不要照搬受版权保护的文本、图片或布局资源。

### 5. 添加资料说明

页面包含角色或产品介绍时，先使用网页搜索查找权威资料，在页面中保留来源链接，并区分公开事实、AI 生成内容和视觉再创作。涉及版权角色时，默认标注为非官方视觉研究，除非用户提供相应授权。

### 6. 验证并交付

运行项目已有的构建命令，通常为 `npm run build`。然后检查：

- 页面和模型资源返回 HTTP 200。
- 完整形态能显示整个对象，包括脚部。
- 拖动进度条时所有请求部件都能逐步展开。
- 每个结构索引都能高亮对应实体部件。
- 没有新增的模型加载或交互控制台错误。
- 档案弹窗、时间轴和交互提示在桌面与移动端不重叠。

交付时说明项目路径、模型路径、任务清单和验证结果。

## Python 脚本说明

### `generate_reference_image.py`

只负责调用 OpenAI Images API 生成参考图：

- `--prompt`：生图提示词
- `--output`：PNG 输出路径
- `--model`、`--size`、`--quality`：生图参数

### `generate_hyper3d_model.py`

只负责调用 Hyper3D HTTP API：

- `--image-path`、`--image-url`：互斥的参考图输入
- `--prompt`：Hyper3D 模型提示词
- `--out-dir`：输出目录
- `--project-dir`：接收 GLB 的前端项目目录
- `--bang`、`--bang-instruction`：可选部件拆解
- `--tier`、`--mesh-mode`、`--quality`、`--geometry-format`：Rodin 生成参数
- `--poll-timeout`：任务轮询超时时间
- `--force`：允许替换已有前端模型

两个脚本都会保存脱敏后的元数据，绝不写出 API 密钥。它们负责资源准备，不负责修改 React 源码；页面实现应使用生成的清单和现有前端模板完成。

## 常见问题

- **只生成了头部**：参考图或提示词被裁切。重新生成时明确要求完整身体、脚部和居中轮廓，不要只靠缩小相机隐藏缺失几何体。
- **页面看不到脚**：相机只根据部分节点计算范围。重新遍历全部网格和爆炸目标。
- **部件拧巴或重叠**：父子层级或局部/世界坐标混用。统一坐标系后再计算对称目标。
- **索引和模型不对应**：节点名称是猜出来的。检查实际场景层级并绑定确认过的节点。
- **没有爆炸效果**：页面只切换状态，没有插值真实部件，或输入仍是单一网格。使用 BANG 独立部件结果。
- **图片上传失败**：保存原始图片和错误信息，不要伪装成已提交任务；改用可用的上传方式。
- **已扣费但结果下载失败**：使用已有任务结果或恢复链接，不要重复提交相同生成任务。
