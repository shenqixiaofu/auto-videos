"""智能视频云端处理 provider 包。

调用方只从这里取实例，新增实现只需在下面注册表里加一条，
不必再去各个阶段改硬编码的类名。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, TypeVar

from app.config.setting import settings
from app.core.exceptions import CustomException

if TYPE_CHECKING:
    from .aliyun_asr import AliyunDashScopeAsrProvider
    from .aliyun_ims import AliyunImsVideoProvider
    from .aliyun_public_media import AliyunPublicMediaProvider

_ProviderT = TypeVar("_ProviderT")

# ASR 与公共素材目前各只有一个阿里实现，留注册表是为了将来换供应商时不动调用方。
_DEFAULT_ASR_PROVIDER = "aliyun_dashscope"
_DEFAULT_PUBLIC_MEDIA_PROVIDER = "aliyun_public_media"


def _build_aliyun_dashscope_asr() -> AliyunDashScopeAsrProvider:
    from .aliyun_asr import AliyunDashScopeAsrProvider

    return AliyunDashScopeAsrProvider()


def _build_aliyun_public_media() -> AliyunPublicMediaProvider:
    from .aliyun_public_media import AliyunPublicMediaProvider

    return AliyunPublicMediaProvider()


def _build_aliyun_ims_render() -> AliyunImsVideoProvider:
    from .aliyun_ims import AliyunImsVideoProvider

    return AliyunImsVideoProvider()


_ASR_PROVIDERS: dict[str, Callable[[], AliyunDashScopeAsrProvider]] = {
    "aliyun_dashscope": _build_aliyun_dashscope_asr,
}
_PUBLIC_MEDIA_PROVIDERS: dict[str, Callable[[], AliyunPublicMediaProvider]] = {
    "aliyun_public_media": _build_aliyun_public_media,
}
_RENDER_PROVIDERS: dict[str, Callable[[], AliyunImsVideoProvider]] = {
    "aliyun_ims": _build_aliyun_ims_render,
}


def build_asr_provider(name: str | None = None) -> AliyunDashScopeAsrProvider:
    """按名称构造语音识别 provider。"""
    return _resolve(_ASR_PROVIDERS, name or _DEFAULT_ASR_PROVIDER, "语音识别 provider")


def build_public_media_provider(name: str | None = None) -> AliyunPublicMediaProvider:
    """按名称构造公共素材 provider。"""
    return _resolve(
        _PUBLIC_MEDIA_PROVIDERS,
        name or _DEFAULT_PUBLIC_MEDIA_PROVIDER,
        "公共素材 provider",
    )


def build_render_provider(name: str | None = None) -> AliyunImsVideoProvider:
    """按名称构造视频渲染 provider，默认取配置项。"""
    return _resolve(
        _RENDER_PROVIDERS,
        name or settings.VIDEO_RENDER_PROVIDER,
        "视频渲染 provider",
    )


def _resolve(
    registry: dict[str, Callable[[], _ProviderT]],
    name: str,
    kind: str,
) -> _ProviderT:
    """从注册表取出工厂并实例化，未注册时给出可读错误。"""
    factory = registry.get(name)
    if factory is None:
        raise CustomException(msg=f"未注册的{kind}: {name}")
    return factory()
