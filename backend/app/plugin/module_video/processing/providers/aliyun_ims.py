from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote, urlparse
from uuid import uuid4

import oss2
from alibabacloud_ice20201109 import models as ice_models
from alibabacloud_ice20201109.client import Client as IceClient
from alibabacloud_tea_openapi import models as openapi_models

from app.config.setting import settings
from app.core.exceptions import CustomException
from app.core.logger import log

from ..provider_concurrency import (
    get_aliyun_render_poll_semaphore,
    get_aliyun_render_submit_semaphore,
)
from ..render_contract import (
    VideoRenderResult,
    VideoRenderStatus,
    VideoRenderSubmission,
    VideoTimeline,
)
from ..timeline import VideoTimelineBuilder


class AliyunImsVideoProvider:
    """阿里云智能媒体服务时间线渲染 provider。"""

    provider_name = "aliyun_ims"

    def __init__(self) -> None:
        self._validate_settings()
        self._ice_client = self._build_ice_client()
        self._oss_bucket = self._build_oss_bucket()
        self._output_keys: dict[str, str] = {}

    async def upload_local_video_to_oss(
        self,
        *,
        file_path: Path,
        file_name: str,
        role: str = "source",
    ) -> dict[str, Any]:
        """把本地视频上传到阿里 OSS 并返回通用引用。"""
        object_key = self._build_object_key(file_name, role)
        await asyncio.to_thread(
            self._oss_bucket.put_object_from_file,
            object_key,
            str(file_path),
        )
        return {
            "provider": "aliyun_oss",
            "object_key": object_key,
            "url": self._sign_object_url(object_key),
        }

    async def submit_timeline_render(
        self,
        *,
        timeline: VideoTimeline,
        client_token: str,
        source_path: Path | None = None,
    ) -> VideoRenderSubmission:
        """上传源视频并提交阿里云 Timeline 媒体生产作业。"""
        if source_path is None:
            raise CustomException(msg="阿里云时间线渲染缺少本地源视频路径")

        source_reference = await self.upload_local_video_to_oss(
            file_path=source_path,
            file_name=source_path.name,
            role="source",
        )
        self._replace_source_asset_url(timeline, str(source_reference["url"]))

        output_key = self._build_object_key("creative-output.mp4", "output")
        output_url = self._object_url(output_key)
        request = ice_models.SubmitMediaProducingJobRequest(
            timeline=json.dumps(
                VideoTimelineBuilder.to_aliyun_timeline(timeline),
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            output_media_target="oss-object",
            output_media_config=json.dumps(
                {"MediaURL": output_url},
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            client_token=client_token,
        )
        # 只限制真正提交到阿里 IMS 的调用，OSS 上传不占用这个闸门。
        async with get_aliyun_render_submit_semaphore():
            response = await asyncio.to_thread(
                self._ice_client.submit_media_producing_job,
                request,
            )
        response_body = self._response_body(response)
        job_id = str(self._pick(response_body, "JobId") or "")
        if not job_id:
            raise CustomException(msg=f"阿里云媒体生产提交成功但未返回 JobId: {response_body}")

        self._output_keys[job_id] = output_key
        # 持久化 OSS 对象键，进程重启后可重新生成远程可访问地址。
        submission_raw = {
            **response_body,
            "output_object_key": output_key,
        }
        status = self._normalize_status(str(self._pick(response_body, "Status") or "Init"))
        log.info(
            "阿里云媒体生产作业已提交: "
            f"job_id={job_id}, client_token={client_token}, status={status}"
        )
        return VideoRenderSubmission(
            provider=self.provider_name,
            render_id=job_id,
            request_id=str(self._pick(response_body, "RequestId") or "") or None,
            status=status,
            raw=submission_raw,
        )

    async def get_video_output_result(self, render_id: str) -> VideoRenderResult:
        """查询阿里云媒体生产作业状态。"""
        request = ice_models.GetMediaProducingJobRequest(job_id=render_id)
        # 轮询单独限流，避免大量任务同时查询状态把阿里 IMS 打满。
        async with get_aliyun_render_poll_semaphore():
            response = await asyncio.to_thread(
                self._ice_client.get_media_producing_job,
                request,
            )
        response_body = self._response_body(response)
        request_id = str(self._pick(response_body, "RequestId") or "").strip() or None
        job = self._pick(response_body, "MediaProducingJob") or response_body
        if not isinstance(job, dict):
            raise CustomException(msg=f"阿里云媒体生产查询结果格式错误: {response_body}")

        status = self._normalize_status(str(self._pick(job, "Status") or ""))
        error = None
        if status == "failed":
            error = self._build_failed_error(
                job=job,
                response_body=response_body,
                render_id=render_id,
                request_id=request_id,
            )

        media_url = str(self._pick(job, "MediaURL") or "") or None
        if status == "completed":
            media_url = self._resolve_output_url(media_url, render_id)

        return VideoRenderResult(
            provider=self.provider_name,
            render_id=render_id,
            status=status,
            video_url=media_url,
            error=error,
            raw=response_body,
        )

    @staticmethod
    def _build_ice_client() -> IceClient:
        """创建阿里云智能媒体服务客户端。"""
        config = openapi_models.Config(
            access_key_id=settings.ALIYUN_ACCESS_KEY_ID,
            access_key_secret=settings.ALIYUN_ACCESS_KEY_SECRET,
            endpoint=settings.ALIYUN_ICE_ENDPOINT,
            region_id=settings.ALIYUN_ICE_REGION,
        )
        return IceClient(config)

    @staticmethod
    def _build_oss_bucket() -> oss2.Bucket:
        """创建阿里云 OSS bucket 客户端。"""
        auth = oss2.Auth(
            settings.ALIYUN_ACCESS_KEY_ID,
            settings.ALIYUN_ACCESS_KEY_SECRET,
        )
        return oss2.Bucket(
            auth,
            settings.ALIYUN_OSS_ENDPOINT,
            settings.ALIYUN_OSS_BUCKET,
        )

    @classmethod
    def _build_object_key(cls, file_name: str, role: str) -> str:
        """生成隔离的 OSS 对象键。"""
        safe_name = Path(file_name).name.replace(" ", "-")
        return (
            f"{settings.ALIYUN_OSS_OBJECT_PREFIX.rstrip('/')}/"
            f"{role}/{uuid4().hex}/{safe_name}"
        )

    @classmethod
    def _object_url(cls, object_key: str) -> str:
        """生成阿里 OSS 对象地址。"""
        parsed = urlparse(settings.ALIYUN_OSS_ENDPOINT)
        scheme = parsed.scheme or "https"
        host = parsed.netloc or parsed.path
        encoded_key = quote(object_key, safe="/")
        return f"{scheme}://{settings.ALIYUN_OSS_BUCKET}.{host}/{encoded_key}"

    def _sign_object_url(self, object_key: str) -> str:
        """生成供云端拉取或下游 provider 使用的临时地址。"""
        return self._oss_bucket.sign_url(
            "GET",
            object_key,
            settings.ALIYUN_OSS_PRESIGNED_EXPIRE_SECONDS,
        )

    def get_output_object_url(self, object_key: str) -> str:
        """按持久化 OSS 对象键重新生成输出地址。"""
        return self._sign_object_url(object_key)

    def _resolve_output_url(self, media_url: str | None, render_id: str) -> str | None:
        """优先使用阿里返回的真实地址，并为本 Bucket 地址重新签名。"""
        if media_url:
            parsed = urlparse(media_url)
            bucket_host = f"{settings.ALIYUN_OSS_BUCKET}."
            if parsed.netloc.startswith(bucket_host):
                object_key = unquote(parsed.path.lstrip("/"))
                if object_key:
                    return self._sign_object_url(object_key)
            return media_url
        output_key = self._output_keys.get(render_id)
        return self._sign_object_url(output_key) if output_key else None

    @staticmethod
    def _replace_source_asset_url(timeline: VideoTimeline, source_url: str) -> None:
        """把时间线源视频替换为阿里 OSS 临时地址。"""
        for track in timeline.tracks:
            for clip in track:
                if clip.asset.get("kind") == "video":
                    clip.asset["src"] = source_url
                    return
        raise CustomException(msg="阿里云时间线缺少源视频片段")

    @staticmethod
    def _response_body(response: Any) -> dict[str, Any]:
        """把阿里 SDK 响应模型转成字典。"""
        body = getattr(response, "body", response)
        if hasattr(body, "to_map"):
            body = body.to_map()
        if not isinstance(body, dict):
            raise CustomException(msg=f"阿里云 SDK 响应不是对象: {body!r}")
        return body

    @staticmethod
    def _pick(payload: dict[str, Any], name: str) -> Any:
        """按大小写和下划线无关的方式读取 SDK 字段。"""
        expected = name.replace("_", "").lower()
        for key, value in payload.items():
            if str(key).replace("_", "").lower() == expected:
                return value
        return None

    @staticmethod
    def _normalize_status(raw_status: str) -> VideoRenderStatus:
        """把阿里媒体生产状态转换为标准渲染状态。"""
        status_map = {
            "Init": "queued",
            "Processing": "rendering",
            "Success": "completed",
            "Failed": "failed",
        }
        if raw_status not in status_map:
            raise CustomException(msg=f"阿里云媒体生产返回未知状态: {raw_status}")
        return status_map[raw_status]  # type: ignore[return-value]

    @classmethod
    def _build_failed_error(
        cls,
        *,
        job: dict[str, Any],
        response_body: dict[str, Any],
        render_id: str,
        request_id: str | None,
    ) -> str:
        """把阿里云失败响应拼成可排障的单行错误。"""
        fragments: list[str] = []
        for payload in (job, response_body):
            for key in ("ErrorCode", "ErrorMessage", "Message", "Code"):
                value = str(cls._pick(payload, key) or "").strip()
                if value and value not in fragments:
                    fragments.append(value)
        detail = " | ".join(fragments) or "阿里云媒体生产作业失败"
        trace_parts = [f"render_id={render_id}"]
        if request_id:
            trace_parts.append(f"request_id={request_id}")
        return f"{detail} ({', '.join(trace_parts)})"

    @staticmethod
    def _validate_settings() -> None:
        """校验阿里 IMS 和 OSS 配置。"""
        if settings.VIDEO_RENDER_PROVIDER != "aliyun_ims":
            raise CustomException(
                msg=f"当前时间线渲染 provider 不是 aliyun_ims: {settings.VIDEO_RENDER_PROVIDER}"
            )
        missing_names = [
            name
            for name, value in {
                "ALIYUN_ACCESS_KEY_ID": settings.ALIYUN_ACCESS_KEY_ID,
                "ALIYUN_ACCESS_KEY_SECRET": settings.ALIYUN_ACCESS_KEY_SECRET,
                "ALIYUN_ICE_REGION": settings.ALIYUN_ICE_REGION,
                "ALIYUN_ICE_ENDPOINT": settings.ALIYUN_ICE_ENDPOINT,
                "ALIYUN_OSS_ENDPOINT": settings.ALIYUN_OSS_ENDPOINT,
                "ALIYUN_OSS_BUCKET": settings.ALIYUN_OSS_BUCKET,
            }.items()
            if not value
        ]
        if missing_names:
            raise CustomException(msg=f"阿里 IMS/OSS 配置缺失: {', '.join(missing_names)}")
