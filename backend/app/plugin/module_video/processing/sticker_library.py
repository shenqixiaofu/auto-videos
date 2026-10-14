from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_ASSETS_DIR = Path(__file__).with_name("assets")
_INDEX_FILE = _ASSETS_DIR / "sticker_index.json"
_HOSTED_FILE = _ASSETS_DIR / "sticker_hosted.json"


@lru_cache(maxsize=1)
def _index() -> dict[str, Any]:
    """读取素材语义索引，进程内只解析一次。"""
    return json.loads(_INDEX_FILE.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _hosted() -> dict[str, str]:
    """CDN 原始 URL → 自托管公开 URL。缺这个文件就继续用 CDN 原址。"""
    if not _HOSTED_FILE.exists():
        return {}
    return json.loads(_HOSTED_FILE.read_text(encoding="utf-8"))


# 一条素材的标签 = 情绪基调（正向/中性/负向/惊讶）+ 素材分类（动图/气泡/表情/日常/
# 气氛/可爱），两个轴互相独立。所以「惊讶」池里的那张动图同时带「惊讶」和「动图」，
# 不是二选一 —— 抽图按标签筛，不按单一分类硬切池。分类取值就是 IMS 控制台的 6 个页签。
_CAT_LABELS = {
    "gif": "动图",
    "bubble": "气泡",
    "expression": "表情",
    "daily": "日常",
    "atmosphere": "气氛",
    "cute": "可爱",
}
_ANIMATED_TAG = "动图"
# 动图权重。抽图是在标签筛完的候选里按权重取，不是硬切出「只从动图池抽」——
# 硬切会让「惊讶」这种整池只有 1 张动图的小池每次都抽到同一张。按权重取则是
# 池子越大越偏向动图，小池自动降级，不需要额外阈值。当前 10 约等于整体 84% 动图、
# 「惊讶」48%（1 张动图 vs 11 张静态）。池里动图静态比变了就重新算一遍。
_ANIMATED_WEIGHT = 10


def tags_of(item: dict[str, Any], tone: str) -> set[str]:
    """读一条素材的标签集合，供抽图筛选与排查使用。"""
    return {tone, _CAT_LABELS.get(str(item.get("cat") or ""), "其他")}


def tone_pool(tone: str) -> list[dict[str, Any]]:
    """取带某个情绪标签的纯图形素材池。

    tone 未知或该池为空时退到最大的池 —— 宁可主题不贴切，也不能没有图可出。
    """
    pools = _index()["pools"]
    if pools.get(tone):
        return pools[tone]
    return max(pools.values(), key=len)


def pick_sticker(tone: str, seed: str) -> str:
    """按情绪基调稳定抽一张贴纸 URL。

    seed 相同必然抽到同一张（可重放），这是全模块的基线约定，别改成随机。
    候选是带该情绪标签的全部素材，其中带「动图」标签的按 `_ANIMATED_WEIGHT` 加权，
    避免同一条视频里贴纸全是静态的。
    """
    pool = tone_pool(tone)
    weights = [_ANIMATED_WEIGHT if _ANIMATED_TAG in tags_of(item, tone) else 1 for item in pool]
    digest = hashlib.sha1(f"{tone}:{seed}".encode()).hexdigest()
    target = int(digest[:8], 16) % sum(weights)
    for item, weight in zip(pool, weights, strict=True):
        target -= weight
        if target < 0:
            cdn_url = str(item["url"])
            return _hosted().get(cdn_url) or cdn_url
    # 权重和为正时上面必然命中，这里只是让类型收敛。
    cdn_url = str(pool[-1]["url"])
    return _hosted().get(cdn_url) or cdn_url


def effect_pool() -> list[dict[str, Any]]:
    """氛围装饰素材池：公共库里的迷你装饰动图，不承载语义，只负责画面在动。"""
    return _index().get("effect_pool") or []


def pick_effect(seed: str) -> str:
    """按种子稳定抽一张氛围装饰图，池空时返回空串由调用方跳过。"""
    pool = effect_pool()
    if not pool:
        return ""
    digest = hashlib.sha1(f"effect:{seed}".encode()).hexdigest()
    cdn_url = str(pool[int(digest[:8], 16) % len(pool)]["url"])
    return _hosted().get(cdn_url) or cdn_url
