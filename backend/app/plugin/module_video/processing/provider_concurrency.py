from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any

from redis.asyncio import Redis

from app.config.setting import settings
from app.core.logger import log

# ponytail: 并发闸门跨进程共享（Redis 有序集合租约）；Redis 不可用时退回进程内信号量。
_KEY_PREFIX = "auto-nexus:video:concurrency:"
# 抢不到租约时的重试间隔。
_RETRY_INTERVAL_SECONDS = 0.2

# 租约必须覆盖被限流操作的最长耗时，否则操作还在跑、租约已过期，全局并发会被突破。
_LEASE_SECONDS: dict[str, int] = {
    "aliyun_render_submit": 300,
    "aliyun_render_poll": 60,
    "volc_llm": 240,
    "volc_image": 360,
}

# 原子抢租约：先清掉过期租约，再判断当前占用数是否低于上限。
_ACQUIRE_SCRIPT = """
redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', ARGV[1])
if redis.call('ZCARD', KEYS[1]) < tonumber(ARGV[2]) then
    redis.call('ZADD', KEYS[1], ARGV[3], ARGV[4])
    redis.call('PEXPIRE', KEYS[1], ARGV[5])
    return 1
end
return 0
"""

_local_semaphores: dict[str, asyncio.Semaphore] = {}
_redis_client: Redis | None = None
_redis_init_lock = asyncio.Lock()


async def _get_redis() -> Redis | None:
    """懒建闸门自用的 Redis 连接，连不上时返回 None 交给调用方降级。"""
    global _redis_client
    if not settings.REDIS_ENABLE:
        return None
    if _redis_client is not None:
        return _redis_client
    async with _redis_init_lock:
        if _redis_client is not None:
            return _redis_client
        try:
            _redis_client = await Redis.from_url(
                url=settings.REDIS_URI,
                encoding="utf-8",
                decode_responses=True,
                health_check_interval=20,
                socket_timeout=settings.POOL_TIMEOUT,
            )
        except Exception as exc:
            log.warning(f"并发闸门连接 Redis 失败，本次退回进程内限流: {exc}")
            return None
        return _redis_client


def _drop_redis() -> None:
    """丢弃失效连接，下次调用时重建。"""
    global _redis_client
    _redis_client = None


class _ConcurrencyGate:
    """跨进程并发闸门，用法与 asyncio.Semaphore 一致（async with）。"""

    __slots__ = ("_name", "_limit", "_lease", "_local", "_member", "_via_redis")

    def __init__(self, name: str, limit: int) -> None:
        self._name = name
        self._limit = max(1, limit)
        self._lease = _LEASE_SECONDS.get(name, 300)
        self._local = _local_semaphores.setdefault(name, asyncio.Semaphore(self._limit))
        self._member = ""
        self._via_redis = False

    async def __aenter__(self) -> _ConcurrencyGate:
        redis = await _get_redis()
        if redis is None:
            await self._local.acquire()
            return self

        self._member = uuid.uuid4().hex
        key = f"{_KEY_PREFIX}{self._name}"
        while True:
            now_ms = int(time.time() * 1000)
            try:
                acquired = await redis.eval(
                    _ACQUIRE_SCRIPT,
                    1,
                    key,
                    now_ms,
                    self._limit,
                    now_ms + self._lease * 1000,
                    self._member,
                    self._lease * 1000,
                )
            except Exception as exc:
                _drop_redis()
                log.warning(f"并发闸门 Redis 调用失败，本次退回进程内限流: {exc}")
                await self._local.acquire()
                return self
            if int(acquired) == 1:
                self._via_redis = True
                return self
            await asyncio.sleep(_RETRY_INTERVAL_SECONDS)

    async def __aexit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        if not self._via_redis:
            self._local.release()
            return
        self._via_redis = False
        redis = await _get_redis()
        if redis is not None and self._member:
            try:
                await redis.zrem(f"{_KEY_PREFIX}{self._name}", self._member)
            except Exception as exc:
                _drop_redis()
                log.warning(f"并发闸门释放租约失败: {exc}")
        self._member = ""


def get_aliyun_render_submit_semaphore() -> _ConcurrencyGate:
    """获取阿里云 IMS 提交并发闸门。"""
    return _ConcurrencyGate(
        "aliyun_render_submit", settings.VIDEO_ALIYUN_RENDER_SUBMIT_CONCURRENCY
    )


def get_aliyun_render_poll_semaphore() -> _ConcurrencyGate:
    """获取阿里云 IMS 轮询并发闸门。"""
    return _ConcurrencyGate(
        "aliyun_render_poll", settings.VIDEO_ALIYUN_RENDER_POLL_CONCURRENCY
    )


def get_volc_llm_semaphore() -> _ConcurrencyGate:
    """获取火山方舟大模型并发闸门。"""
    return _ConcurrencyGate("volc_llm", settings.VIDEO_VOLC_LLM_CONCURRENCY)


def get_volc_image_semaphore() -> _ConcurrencyGate:
    """获取火山方舟生图并发闸门。"""
    return _ConcurrencyGate("volc_image", settings.VIDEO_VOLC_IMAGE_CONCURRENCY)
