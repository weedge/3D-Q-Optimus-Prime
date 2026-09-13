#!/usr/bin/env python3
"""使用本地图片或图片 URL 生成 Hyper3D 模型文件。"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    import requests
except ImportError as exc:
    raise SystemExit("缺少 requests 依赖，请运行 python3 -m pip install -r requirements.txt") from exc


IMAGE_SIGNATURES = {
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
    b"BM": "image/bmp",
    b"II*\x00": "image/tiff",
    b"MM\x00*": "image/tiff",
}
TERMINAL_STATES = {"completed", "complete", "success", "succeeded", "failed", "error", "cancelled", "canceled"}
FAILED_STATES = {"failed", "error", "cancelled", "canceled"}


def fail(message: str) -> None:
    raise RuntimeError(message)


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if any(token in key.lower() for token in ("key", "token", "secret", "authorization")) else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def detect_image_mime(path: Path) -> str:
    header = path.read_bytes()[:32]
    for signature, mime in IMAGE_SIGNATURES.items():
        if header.startswith(signature):
            return mime
    if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return "image/webp"
    if len(header) >= 12 and header[4:12] in (b"ftypavif", b"ftypavis"):
        return "image/avif"
    fail(f"不支持或无效的图片文件：{path}")


def extension_for_mime(mime: str) -> str:
    return {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif",
        "image/bmp": ".bmp",
        "image/tiff": ".tiff",
        "image/avif": ".avif",
    }.get(mime, ".img")


def copy_local_image(source: str, output: Path) -> Path:
    source_path = Path(source).expanduser().resolve()
    if not source_path.is_file() or source_path.stat().st_size == 0:
        fail(f"本地图片不存在或为空：{source_path}")
    mime = detect_image_mime(source_path)
    target = output / f"reference{extension_for_mime(mime)}"
    shutil.copy2(source_path, target)
    return target


def download_image(url: str, output: Path) -> Path:
    request = Request(url, headers={"User-Agent": "hyper3d-model-landing-page/1.0"})
    try:
        with urlopen(request, timeout=30) as response:
            content_type = response.headers.get_content_type()
            payload = response.read(25 * 1024 * 1024 + 1)
    except (HTTPError, URLError, TimeoutError) as exc:
        fail(f"无法下载图片 URL：{exc}")
    if len(payload) == 0:
        fail("图片 URL 返回了空响应")
    if len(payload) > 25 * 1024 * 1024:
        fail("图片 URL 响应超过 25 MB 安全限制")
    suffix = extension_for_mime(content_type) if content_type.startswith("image/") else Path(url.split("?", 1)[0]).suffix
    target = output / f"reference{suffix or '.img'}"
    target.write_bytes(payload)
    detect_image_mime(target)
    return target


def response_json(response: requests.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        return {"status_code": response.status_code, "text": response.text[:2000]}


def request_json(session: requests.Session, method: str, url: str, **kwargs: Any) -> Any:
    response = session.request(method, url, timeout=120, **kwargs)
    payload = response_json(response)
    if not response.ok:
        detail = json.dumps(redact(payload), ensure_ascii=False)[:2000]
        fail(f"Hyper3D API 请求失败（{response.status_code}）：{detail}")
    return payload


def find_values(value: Any, keys: Iterable[str]) -> list[Any]:
    wanted = {key.lower() for key in keys}
    found: list[Any] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key.lower() in wanted:
                found.append(item)
            found.extend(find_values(item, wanted))
    elif isinstance(value, list):
        for item in value:
            found.extend(find_values(item, wanted))
    return found


def first_scalar(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        for item in value:
            result = first_scalar(item)
            if result:
                return result
    if isinstance(value, dict):
        for item in value.values():
            result = first_scalar(item)
            if result:
                return result
    return None


def find_task_id(payload: Any) -> str:
    for key in ("uuid", "task_uuid", "taskUuid", "asset_id", "assetId"):
        values = find_values(payload, (key,))
        for value in values:
            result = first_scalar(value)
            if result:
                return result
    fail(f"响应中没有找到 Rodin 任务 ID：{json.dumps(redact(payload), ensure_ascii=False)[:2000]}")


def find_subscription_key(payload: Any) -> str | None:
    values = find_values(payload, ("subscription_key", "subscriptionKey"))
    for value in values:
        result = first_scalar(value)
        if result:
            return result
    return None


def collect_statuses(value: Any) -> list[str]:
    statuses: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key.lower() in {"status", "state", "job_status", "jobStatus"}:
                scalar = first_scalar(item)
                if scalar:
                    statuses.append(scalar.lower().replace("_", "").replace("-", ""))
            statuses.extend(collect_statuses(item))
    elif isinstance(value, list):
        for item in value:
            statuses.extend(collect_statuses(item))
    return statuses


def is_done(payload: Any) -> tuple[bool, bool]:
    statuses = collect_statuses(payload)
    if not statuses:
        return False, False
    normalized_terminal = {state.replace("_", "").replace("-", "") for state in TERMINAL_STATES}
    normalized_failed = {state.replace("_", "").replace("-", "") for state in FAILED_STATES}
    has_failed = any(status in normalized_failed for status in statuses)
    return all(status in normalized_terminal for status in statuses), has_failed


def poll_task(session: requests.Session, base_url: str, task_id: str, subscription_key: str | None, timeout: int) -> Any:
    started = time.monotonic()
    latest: Any = None
    interval = 5
    while time.monotonic() - started < timeout:
        body: dict[str, Any] = {"task_uuid": task_id}
        if subscription_key:
            body["subscription_key"] = subscription_key
        response = session.post(f"{base_url}/status", json=body, timeout=120)
        latest = response_json(response)
        if not response.ok:
            fail(f"Hyper3D 状态请求失败（{response.status_code}）：{json.dumps(redact(latest), ensure_ascii=False)[:2000]}")
        done, failed = is_done(latest)
        if failed:
            fail(f"Hyper3D 任务失败：{json.dumps(redact(latest), ensure_ascii=False)[:4000]}")
        if done:
            return latest
        retry_after = response.headers.get("Retry-After")
        try:
            interval = max(3, min(30, int(retry_after))) if retry_after else interval
        except ValueError:
            pass
        time.sleep(interval)
    fail(f"等待 Hyper3D 任务 {task_id} 超时。最后状态：{json.dumps(redact(latest), ensure_ascii=False)[:2000]}")


def find_urls(value: Any) -> list[str]:
    urls: list[str] = []
    if isinstance(value, str) and value.startswith(("http://", "https://")):
        urls.append(value)
    elif isinstance(value, dict):
        for item in value.values():
            urls.extend(find_urls(item))
    elif isinstance(value, list):
        for item in value:
            urls.extend(find_urls(item))
    return list(dict.fromkeys(urls))


def download_result(session: requests.Session, base_url: str, task_id: str, output: Path, filename: str) -> tuple[Path | None, Any]:
    payload = request_json(session, "POST", f"{base_url}/download", json={"task_uuid": task_id})
    write_json(output / f"{filename}.json", redact(payload))
    urls = find_urls(payload)
    for url in urls:
        response = session.get(url, stream=True, timeout=180)
        if not response.ok:
            continue
        content = response.content
        if content[:4] == b"glTF":
            target = output / f"{filename}.glb"
            target.write_bytes(content)
            return target, payload
        if content[:2] == b"PK":
            target = output / f"{filename}.zip"
            target.write_bytes(content)
            return target, payload
    return None, payload


def make_session(api_key: str) -> requests.Session:
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {api_key}", "Accept": "application/json"})
    return session


def submit_rodin(session: requests.Session, base_url: str, image: Path, args: argparse.Namespace) -> Any:
    data: dict[str, str] = {
        "tier": args.tier,
        "mesh_mode": args.mesh_mode,
        "quality_override": str(args.quality),
        "geometry_file_format": args.geometry_format,
    }
    if args.material:
        data["material"] = args.material
    mime = detect_image_mime(image)
    with image.open("rb") as image_file:
        response = session.post(
            f"{base_url}/rodin",
            data=data,
            files={"images": (image.name, image_file, mime)},
            timeout=180,
        )
    payload = response_json(response)
    if not response.ok:
        fail(f"Hyper3D 生成失败（{response.status_code}）：{json.dumps(redact(payload), ensure_ascii=False)[:3000]}")
    return payload


def submit_bang(session: requests.Session, base_url: str, task_id: str, args: argparse.Namespace) -> Any:
    data: dict[str, Any] = {
        "asset_id": task_id,
        "geometry_file_format": args.geometry_format,
        "strength": args.bang_strength,
    }
    if args.bang_instruction:
        data["instruction"] = args.bang_instruction
    return request_json(session, "POST", f"{base_url}/bang", json=data)


def copy_to_project(model: Path, project_dir: Path, asset_name: str, force: bool) -> Path:
    public_dir = project_dir.expanduser().resolve() / "public"
    public_dir.mkdir(parents=True, exist_ok=True)
    target = public_dir / f"{asset_name}.glb"
    if target.exists() and not force:
        fail(f"项目模型已存在：{target}。如需替换，请使用 --force。")
    shutil.copy2(model, target)
    return target


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--image-path", help="本地参考图片路径，也可以是配套脚本生成的图片")
    source.add_argument("--image-url", help="参考图片 URL")
    parser.add_argument("--prompt", required=True, help="发送给 Hyper3D 的 3D 重建提示词")
    parser.add_argument("--out-dir", default="./artifacts/hyper3d", help="模型输出目录")
    parser.add_argument("--project-dir", help="接收最终 GLB 的前端项目目录")
    parser.add_argument("--asset-name", default="generated-model", help="前端 public 目录中的模型文件名")
    parser.add_argument("--force", action="store_true", help="允许替换已有前端模型")
    parser.add_argument("--hyper3d-api-base-url", default=os.getenv("HYPER3D_API_BASE_URL", "https://api.hyper3d.ai/api/v2"))
    parser.add_argument("--tier", default="Gen-2.5-Medium", choices=("Gen-2.5-Medium", "Gen-2.5-Extreme-Low"))
    parser.add_argument("--mesh-mode", default="Quad", choices=("Raw", "Quad"))
    parser.add_argument("--quality", type=int, default=100000, help="Rodin 面数目标，必须符合所选网格模式")
    parser.add_argument("--geometry-format", default="glb", choices=("glb", "usdz", "fbx", "obj", "stl"))
    parser.add_argument("--material", choices=("PBR", "Shaded"), help="可选的 Rodin 材质模式")
    parser.add_argument("--poll-timeout", type=int, default=1800, help="每个任务的最大等待秒数")
    parser.add_argument("--bang", action="store_true", help="基础模型完成后运行 Hyper3D BANG 拆解")
    parser.add_argument("--bang-instruction", help="语义化部件拆解指令")
    parser.add_argument("--bang-strength", type=int, default=5, help="BANG 拆解强度")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    api_key = os.getenv("HYPER3D_API_KEY")
    if not api_key:
        fail("需要设置 HYPER3D_API_KEY")

    if args.image_path:
        reference = copy_local_image(args.image_path, out_dir)
    elif args.image_url:
        reference = download_image(args.image_url, out_dir)
    detect_image_mime(reference)

    base_url = args.hyper3d_api_base_url.rstrip("/")
    session = make_session(api_key)
    submit_payload = submit_rodin(session, base_url, reference, args)
    write_json(out_dir / "rodin-submit.json", redact(submit_payload))
    base_task_id = find_task_id(submit_payload)
    base_subscription_key = find_subscription_key(submit_payload)
    base_status = poll_task(session, base_url, base_task_id, base_subscription_key, args.poll_timeout)
    write_json(out_dir / "rodin-status.json", redact(base_status))
    base_model, _ = download_result(session, base_url, base_task_id, out_dir, "model")
    if base_model is None:
        fail("Rodin 已完成，但没有找到可下载的模型 URL；请检查 model.json 和 rodin-status.json")

    final_model = base_model
    exploded_model: Path | None = None
    bang_task_id: str | None = None
    if args.bang:
        bang_submit = submit_bang(session, base_url, base_task_id, args)
        write_json(out_dir / "bang-submit.json", redact(bang_submit))
        bang_task_id = find_task_id(bang_submit)
        bang_subscription_key = find_subscription_key(bang_submit)
        bang_status = poll_task(session, base_url, bang_task_id, bang_subscription_key, args.poll_timeout)
        write_json(out_dir / "bang-status.json", redact(bang_status))
        exploded_model, _ = download_result(session, base_url, bang_task_id, out_dir, "model-exploded")
        if exploded_model is None:
            fail("BANG 已完成，但没有找到可下载的模型 URL；请检查 model-exploded.json")
        final_model = exploded_model

    project_model: Path | None = None
    if args.project_dir:
        project_model = copy_to_project(final_model, Path(args.project_dir), args.asset_name, args.force)

    manifest = {
        "reference": str(reference),
        "baseModel": str(base_model),
        "explodedModel": str(exploded_model) if exploded_model else None,
        "finalModel": str(final_model),
        "projectModel": str(project_model) if project_model else None,
        "baseTaskId": base_task_id,
        "bangTaskId": bang_task_id,
        "geometryFormat": args.geometry_format,
        "meshMode": args.mesh_mode,
        "tier": args.tier,
        "bangRequested": args.bang,
        "hyper3dApiBaseUrl": base_url,
    }
    write_json(out_dir / "model-manifest.json", manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        raise SystemExit(130)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
