from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx

from app.core.exceptions import CustomException

from ..providers import build_render_provider
from ..storage import VideoObjectStorage


def aliyun_reference_from_creative_metadata(
    creative_result_metadata: dict[str, Any],
) -> dict[str, Any]:
    """从阿里 Timeline 结果提取 OSS 输出引用。"""
    submit_result = dict(creative_result_metadata.get("submit_result") or {})
    raw = dict(submit_result.get("raw") or {})
    object_key = str(raw.get("output_object_key") or "").strip()
    if not object_key:
        raise CustomException(msg="阿里 Timeline 结果缺少 OSS 输出对象键")
    return {
        "provider": "aliyun_oss",
        "object_key": object_key,
        "url": str(creative_result_metadata.get("enhanced_video_url") or ""),
    }


async def upload_local_video_to_aliyun_oss(
    *,
    file_path: Path,
    file_name: str,
    role: str = "source",
) -> dict[str, Any]:
    """把本地视频上传到阿里 OSS 并返回通用引用。"""
    provider = build_render_provider()
    return await provider.upload_local_video_to_oss(
        file_path=file_path,
        file_name=file_name,
        role=role,
    )


async def resolve_video_url(
    reference: dict[str, Any],
) -> str:
    """解析云端视频引用。"""
    provider = str(reference.get("provider") or "")
    if provider == "aliyun_oss":
        url = str(reference.get("url") or "").strip()
        if url:
            return url
        object_key = str(reference.get("object_key") or "").strip()
        if not object_key:
            raise CustomException(msg="阿里 OSS 视频引用缺少 object_key")
        return build_render_provider().get_output_object_url(object_key)
    raise CustomException(msg=f"不支持的远程视频引用类型: {provider or 'unknown'}")


async def download_video_reference(
    reference: dict[str, Any],
    *,
    target_path: Path,
) -> None:
    """把云端视频引用下载到 worker 临时目录。"""
    provider = str(reference.get("provider") or "")
    if not provider and reference.get("object_key"):
        provider = "legacy_minio"
    if provider in {"legacy_minio", "minio_final"}:
        await VideoObjectStorage.download_object_to_file(
            object_key=str(reference["object_key"]),
            target_path=target_path,
        )
        return

    url = str(reference.get("url") or "").strip() or await resolve_video_url(reference)
    timeout = httpx.Timeout(connect=30.0, read=None, write=30.0, pool=30.0)
    # 必须显式跟随重定向：httpx 默认 follow_redirects=False，而 raise_for_status()
    # 连 3xx 一起判失败，云端输出地址（HTTP 跳 HTTPS）会直接被判成下载失败。
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            with target_path.open("wb") as target_file:
                async for chunk in response.aiter_bytes():
                    target_file.write(chunk)
