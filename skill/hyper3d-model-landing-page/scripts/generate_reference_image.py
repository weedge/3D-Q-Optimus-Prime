#!/usr/bin/env python3
"""使用 OpenAI Images API 生成参考图。"""

from __future__ import annotations

import argparse
import base64
import os
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt", required=True, help="参考图生成提示词")
    parser.add_argument("--output", default="./artifacts/reference.png", help="图片输出路径")
    parser.add_argument("--model", default="gpt-image-2", help="OpenAI Images API 模型")
    parser.add_argument("--size", default="1024x1024", help="图片尺寸，例如 1024x1024")
    parser.add_argument("--quality", default="high", choices=("low", "medium", "high"), help="图片质量")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("需要设置 OPENAI_API_KEY")
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise SystemExit("缺少 openai 依赖，请运行 python3 -m pip install -r requirements.txt") from exc

    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    client = OpenAI()
    response = client.images.generate(
        model=args.model,
        prompt=args.prompt,
        size=args.size,
        quality=args.quality,
    )
    item = response.data[0]
    encoded = getattr(item, "b64_json", None)
    if not encoded:
        raise SystemExit("OpenAI 生图响应中没有 b64_json")
    output.write_bytes(base64.b64decode(encoded))
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
