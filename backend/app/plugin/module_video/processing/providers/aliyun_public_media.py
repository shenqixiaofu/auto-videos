from __future__ import annotations

import asyncio
import hashlib
from dataclasses import dataclass, replace
from typing import Any

from alibabacloud_ice20201109 import models as ice_models
from alibabacloud_ice20201109.client import Client as IceClient
from alibabacloud_tea_openapi import models as openapi_models

from app.config.setting import settings
from app.core.exceptions import CustomException


@dataclass(frozen=True, slots=True)
class AliyunPublicBgmTrack:
    """阿里公共版权音乐曲目。"""

    media_id: str
    title: str
    duration_ms: int
    media_tag_id: str
    media_tag_label: str | None
    volume_gain: float
    preview_url: str | None = None
    media_url: str | None = None
    cover_url: str | None = None

    def to_metadata(self) -> dict[str, Any]:
        """序列化为任务元数据。"""
        return {
            "provider": "aliyun_public_media",
            "media_id": self.media_id,
            "title": self.title,
            "duration_ms": self.duration_ms,
            "media_tag_id": self.media_tag_id,
            "media_tag_label": self.media_tag_label,
            "volume_gain": self.volume_gain,
            "preview_url": self.preview_url,
            "media_url": self.media_url,
            "cover_url": self.cover_url,
        }

    def to_timeline_asset(self) -> dict[str, Any]:
        """转换为阿里 Timeline 音频资产。"""
        return {
            "kind": "audio",
            "media_id": self.media_id,
            "media_url": self.media_url,
            "duration_seconds": self.duration_ms / 1000 if self.duration_ms > 0 else None,
            "volume_gain": self.volume_gain,
            "loop_mode": True,
            "fade_in_seconds": 0.25,
            "fade_out_seconds": 0.9,
            "preview_url": self.preview_url,
            "cover_url": self.cover_url,
            "media_tag_id": self.media_tag_id,
            "media_tag_label": self.media_tag_label,
            "title": self.title,
        }


class AliyunPublicMediaProvider:
    """阿里公共素材库 provider，当前只负责版权 BGM。"""

    _style_tag_candidates = {
        "vlog": ("bgm-upbeat", "bgm-dynamic", "bgm-relaxing", "bgm-beauty", "bgm-quirky"),
        "travel": ("bgm-dynamic", "bgm-relaxing"),
        "food": ("bgm-cuisine", "bgm-relaxing"),
        "clean": ("bgm-relaxing", "bgm-beauty"),
    }
    _default_style_tags = ("bgm-upbeat", "bgm-relaxing")
    # BGM 响度改由时间线侧的 ALoudNorm 统一控制，这里保持原始增益不再预先压低。
    _default_volume_gain = 1.0
    _page_size = 100
    _page_limit = 3

    def __init__(self) -> None:
        self._validate_settings()
        self._ice_client = self._build_ice_client()

    async def pick_bgm_track(
        self,
        *,
        style_preset: str,
        task_seed: str,
    ) -> AliyunPublicBgmTrack:
        """按风格标签稳定随机选一首官方版权音乐。"""
        tag_ids = self._style_tag_candidates.get(style_preset, self._default_style_tags)
        tag_tracks: dict[str, list[AliyunPublicBgmTrack]] = {}
        for tag_id in tag_ids:
            tag_tracks[tag_id] = await self._list_bgm_tracks_by_tag(tag_id)

        available_tags = [tag_id for tag_id in tag_ids if tag_tracks.get(tag_id)]
        if not available_tags:
            raise CustomException(msg=f"阿里公共版权音乐没有可用曲目: style_preset={style_preset}")

        tag_digest = hashlib.sha1(f"{task_seed}:aliyun_public_bgm:tag".encode()).hexdigest()
        selected_tag = available_tags[int(tag_digest[:8], 16) % len(available_tags)]
        tracks = sorted(
            {track.media_id: track for track in tag_tracks[selected_tag]}.values(),
            key=lambda item: (item.media_id, item.title),
        )
        digest = hashlib.sha1(f"{task_seed}:aliyun_public_bgm:track".encode()).hexdigest()
        selected_track = tracks[int(digest[:8], 16) % len(tracks)]
        formal_media_url = await self._get_formal_media_url(selected_track.media_id)
        return replace(selected_track, media_url=formal_media_url)

    async def _list_bgm_tracks_by_tag(self, tag_id: str) -> list[AliyunPublicBgmTrack]:
        """按标签分页读取公共版权音乐列表。"""
        tracks: list[AliyunPublicBgmTrack] = []
        for page_no in range(1, self._page_limit + 1):
            request = ice_models.ListPublicMediaBasicInfosRequest(
                business_type="bgm",
                media_tag_id=tag_id,
                include_file_basic_info=True,
                page_no=page_no,
                page_size=self._page_size,
            )
            response = await asyncio.to_thread(
                self._ice_client.list_public_media_basic_infos,
                request,
            )
            response_body = self._response_body(response)
            media_infos = self._pick(response_body, "MediaInfos") or []
            if not isinstance(media_infos, list):
                break
            page_tracks = [self._parse_track(item, tag_id) for item in media_infos]
            page_tracks = [track for track in page_tracks if track is not None]
            tracks.extend(page_tracks)
            total_count = int(self._pick(response_body, "TotalCount") or 0)
            if page_no * self._page_size >= total_count:
                break
        return tracks

    async def _get_formal_media_url(self, media_id: str) -> str:
        """读取公共媒资正式合成地址。"""
        request = ice_models.GetPublicMediaInfoRequest(media_id=media_id)
        response = await asyncio.to_thread(
            self._ice_client.get_public_media_info,
            request,
        )
        response_body = self._response_body(response)
        media_info = self._pick(response_body, "MediaInfo") or response_body
        file_info_list = self._pick(media_info, "FileInfoList") or []
        if isinstance(file_info_list, list):
            for file_info in file_info_list:
                if not isinstance(file_info, dict):
                    continue
                file_basic_info = self._pick(file_info, "FileBasicInfo") or file_info
                media_url = str(
                    self._pick(file_info, "FileURL")
                    or self._pick(file_info, "FileUrl")
                    or self._pick(file_basic_info, "FileURL")
                    or self._pick(file_basic_info, "FileUrl")
                    or ""
                ).strip()
                if media_url:
                    return media_url
        raise CustomException(msg=f"阿里公共媒资缺少正式 MediaURL: media_id={media_id}")

    def _parse_track(
        self,
        media_payload: Any,
        tag_id: str,
    ) -> AliyunPublicBgmTrack | None:
        """把公共素材条目解析成内部曲目结构。"""
        if not isinstance(media_payload, dict):
            return None
        media_basic_info = self._pick(media_payload, "MediaBasicInfo") or media_payload
        if not isinstance(media_basic_info, dict):
            return None
        media_id = str(self._pick(media_basic_info, "MediaId") or "").strip()
        title = str(
            self._pick(media_basic_info, "Title")
            or self._pick(media_basic_info, "MediaName")
            or ""
        ).strip()
        if not media_id or not title:
            return None

        file_info_list = self._pick(media_payload, "FileInfoList") or []
        duration_ms = 0
        preview_url: str | None = None
        cover_url = str(self._pick(media_basic_info, "CoverURL") or "").strip() or None
        if isinstance(file_info_list, list):
            for file_info in file_info_list:
                if not isinstance(file_info, dict):
                    continue
                file_basic_info = self._pick(file_info, "FileBasicInfo") or file_info
                if isinstance(file_basic_info, dict):
                    duration_ms = max(
                        duration_ms,
                        int(float(self._pick(file_basic_info, "Duration") or 0) * 1000),
                    )
                candidate_url = str(
                    self._pick(file_info, "FileURL")
                    or self._pick(file_info, "FileUrl")
                    or self._pick(file_basic_info, "FileURL")
                    or ""
                ).strip()
                if candidate_url and preview_url is None:
                    preview_url = candidate_url

        tag_name = str(self._pick(media_basic_info, "MediaTagName") or "").strip() or None
        return AliyunPublicBgmTrack(
            media_id=media_id,
            title=title,
            duration_ms=duration_ms,
            media_tag_id=tag_id,
            media_tag_label=tag_name,
            volume_gain=self._default_volume_gain,
            preview_url=preview_url,
            cover_url=cover_url,
        )

    @staticmethod
    def _build_ice_client() -> IceClient:
        """创建阿里智能媒体服务客户端。"""
        config = openapi_models.Config(
            access_key_id=settings.ALIYUN_ACCESS_KEY_ID,
            access_key_secret=settings.ALIYUN_ACCESS_KEY_SECRET,
            endpoint=settings.ALIYUN_ICE_ENDPOINT,
            region_id=settings.ALIYUN_ICE_REGION,
        )
        return IceClient(config)

    @staticmethod
    def _response_body(response: Any) -> dict[str, Any]:
        """把阿里 SDK 响应模型转成字典。"""
        body = getattr(response, "body", response)
        if hasattr(body, "to_map"):
            body = body.to_map()
        if not isinstance(body, dict):
            raise CustomException(msg=f"阿里公共素材库响应不是对象: {body!r}")
        return body

    @staticmethod
    def _pick(payload: dict[str, Any], name: str) -> Any:
        """按大小写和下划线无关方式读取 SDK 字段。"""
        expected = name.replace("_", "").lower()
        for key, value in payload.items():
            if str(key).replace("_", "").lower() == expected:
                return value
        return None

    @staticmethod
    def _validate_settings() -> None:
        """校验公共素材库访问配置。"""
        missing_names = [
            name
            for name, value in {
                "ALIYUN_ACCESS_KEY_ID": settings.ALIYUN_ACCESS_KEY_ID,
                "ALIYUN_ACCESS_KEY_SECRET": settings.ALIYUN_ACCESS_KEY_SECRET,
                "ALIYUN_ICE_REGION": settings.ALIYUN_ICE_REGION,
                "ALIYUN_ICE_ENDPOINT": settings.ALIYUN_ICE_ENDPOINT,
            }.items()
            if not value
        ]
        if missing_names:
            raise CustomException(msg=f"阿里公共素材库配置缺失: {', '.join(missing_names)}")
