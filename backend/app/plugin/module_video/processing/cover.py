from __future__ import annotations

import asyncio
import base64
import json
import re
import textwrap
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from openai import APIConnectionError, APIError, APITimeoutError, AsyncOpenAI
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

from app.config.setting import settings
from app.core.exceptions import CustomException
from app.core.logger import log

from .mediakit_types import VolcMediaKitSubtitleCue
from .processing_config import (
    COVER_IMAGE_PROMPT_TEMPLATE,
    load_processing_config,
    render_prompt_template,
    resolve_prompt_template,
)
from .provider_concurrency import get_volc_image_semaphore, get_volc_llm_semaphore
from .storage import VideoObjectStorage

# 封面链路单独放宽超时，避免 LLM 策划、生图和图片下载被过早打断。
_COVER_IMAGE_TIMEOUT_SECONDS = 300.0
_COVER_DOWNLOAD_TIMEOUT_SECONDS = 180.0
# 中转站出图是 1024x1536（2:3）、封面画布是 1200x1600（3:4），本地规整必然要裁掉
# 上下各约 5.6% 的高度，所以文字必须避开这两条边。顶部用相对锚点而不是百分比：
# 实测百分比区间模型算不准（落点卡在裁切线上），改成「不小于标签自身高度的两倍」
# 后角标顶边从 1.6% 抬到 7.6%。
_COVER_SAFE_AREA_CLAUSE = (
    "【构图安全区·硬要求】不要贴边："
    "左上角标签的上边缘到画面上边缘的距离，不小于标签自身高度的两倍，留白要一眼看得见；"
    "画面最下方约八分之一的高度内不要放任何文字、标签或图标，所有文字整体向上收。"
)
CoverCheckpointWriter = Callable[[str, dict[str, Any]], Awaitable[None]]


@dataclass(slots=True)
class VideoCoverRenderResult:
    """AI 封面生成结果，记录独立封面图资产。"""

    enabled: bool
    # 本次实际使用的生图通道，由系统参数开关 + env 配置解析而来。
    image_provider: str
    # 本次实际用到的模型名与尺寸。生成时就解析好存进来，不要留给 to_metadata
    # 现查配置 —— 那是同步方法，拿不到全局配置，会把 env 默认值当成实际值写进元数据。
    image_model: str
    image_size: str
    summary_model: str
    title: str
    prompt: str
    # 真正发给生图模型的完整提示词。`prompt` 只是策划给的「排版氛围说明」，
    # 调试时要看的是模板拼装后的成品串。
    image_prompt: str
    frame_refs: list[str]
    source_frame_name: str
    # 参考帧在对象存储里的 key。抽帧产物原本只留在临时目录、跑完就删，
    # 要回看「生图喂进去的是哪张图」必须把它存下来。
    reference_object_key: str | None
    generated_image_url: str
    cover_image_path: Path
    cover_object_key: str
    cover_thumbnail_key: str
    cover_file_size: int
    cover_etag: str
    elapsed_seconds: float

    def to_metadata(self) -> dict[str, Any]:
        """序列化封面处理元数据，方便审核和排查生成效果。"""
        return {
            "cover_enabled": self.enabled,
            "cover_title": self.title,
            "cover_prompt": self.prompt,
            "cover_image_prompt": self.image_prompt,
            "cover_reference_frames": self.frame_refs,
            "cover_reference_object_key": self.reference_object_key,
            "cover_source_frame_name": self.source_frame_name,
            # 中转站只回 b64_json 时这里是 MB 级 data URL，同一份会被写进断点与
            # 封面素材元数据，曾把 config 撑到 6MB 顶穿 MySQL sort_buffer。非 http
            # 一律置空，找图走 cover_object_key / cover_thumbnail_key。
            "cover_generated_image_url": VideoCoverGenerator._checkpoint_image_url(
                self.generated_image_url
            ),
            "cover_object_key": self.cover_object_key,
            "cover_thumbnail_key": self.cover_thumbnail_key,
            "cover_file_size": self.cover_file_size,
            "cover_etag": self.cover_etag,
            "cover_summary_model": self.summary_model,
            "cover_image_provider": self.image_provider,
            "cover_image_model": self.image_model,
            "cover_image_size": self.image_size,
            "cover_render_mode": f"{self.image_provider}_free_cover",
            "cover_elapsed_seconds": round(self.elapsed_seconds, 3),
        }


class VideoCoverGenerator:
    """基于视频关键帧、ASR 字幕和生图模型生成短视频封面图。"""

    @classmethod
    def effective_provider(cls, override: str | None, config: dict[str, Any]) -> str:
        """任务选定值 > 全局配置 > env 默认；密钥缺失时一律回落 seedream。

        密钥是后补的，不能让「配置先切、密钥后填」这个顺序把封面链路卡死。
        """
        candidate = str(
            override
            or config.get("cover_image_provider")
            or settings.VIDEO_COVER_IMAGE_PROVIDER
            or ""
        ).strip().lower()
        if candidate == "relay" and settings.COVER_RELAY_API_KEY:
            return "relay"
        return "seedream"

    @classmethod
    def image_model_for(cls, provider: str, config: dict[str, Any]) -> str:
        """某个 provider 对应的生图模型名，供元数据记录。"""
        if provider == "relay":
            return str(config.get("relay_image_model") or settings.COVER_RELAY_IMAGE_MODEL)
        return settings.VIDEO_COVER_IMAGE_MODEL

    @classmethod
    def image_size_for(cls, provider: str, config: dict[str, Any]) -> str:
        """某个 provider 对应的生图尺寸档。"""
        if provider == "relay":
            return str(config.get("relay_image_size") or settings.COVER_RELAY_IMAGE_SIZE)
        return settings.VIDEO_COVER_IMAGE_SIZE

    @classmethod
    def resolve_image_provider(cls, override: str | None, config: dict[str, Any]) -> str:
        """解析本次封面生图走哪个通道：任务选定值 > 全局配置 > env 配置。

        返回值同时落进封面元数据，方便事后核对实际走了哪条。
        """
        provider = cls.effective_provider(override, config)
        log.info(
            "封面生图通道解析: "
            f"任务={override or '未指定'}, 全局配置={config.get('cover_image_provider')}, "
            f"env={settings.VIDEO_COVER_IMAGE_PROVIDER}, 实际={provider}"
        )
        return provider

    _cover_width = 1200
    _cover_height = 1600
    # 原图存 PNG（用户下载用，保持无损）；另出一张 JPEG 缩略图给前端展示，
    # 列表 / 详情 / 成片预览都拉缩略图，避免每处都吃 1.9MB 的原图。
    _cover_thumbnail_width = 600
    _cover_thumbnail_height = 800
    _cover_thumbnail_jpeg_quality = 88
    _first_frame_width = 1080
    _first_frame_height = 1920

    @classmethod
    async def generate_cover_image(
        cls,
        *,
        task_no: str,
        task_title: str,
        source_path: Path,
        source_duration_ms: int,
        temp_dir: Path,
        subtitles: list[VolcMediaKitSubtitleCue],
        cover_plan_override: dict[str, Any] | None,
        generated_image_url_override: str | None,
        save_cover_checkpoint: CoverCheckpointWriter,
        provider_override: str | None = None,
    ) -> VideoCoverRenderResult:
        """基于参考帧生成 AI 封面图并上传为独立封面资产。"""
        started_at = time.monotonic()
        # 全局配置读一次，本次封面用到的模型名、尺寸、提示词模板都从它取。
        processing_config = await load_processing_config()
        provider = cls.resolve_image_provider(provider_override, processing_config)
        log.info(
            "智能视频封面开始生成: "
            f"task_no={task_no}, title={task_title}, subtitle_count={len(subtitles)}, "
            f"provider={provider}"
        )
        frame_paths = await cls._extract_reference_frames(source_path, temp_dir, source_duration_ms)
        source_frame_path = frame_paths[0]
        # 参考帧顺手存一份到对象存储，key 由 task_no 推导，重跑会覆盖同一个对象。
        # 抽帧产物原本只留在临时目录、跑完就删，调试时没法回答「生图喂的是哪张图」。
        reference_object_key = VideoObjectStorage.build_object_key(
            task_no=task_no,
            asset_role="cover",
            file_name=f"{task_no}-cover-reference.jpg",
        )
        try:
            await VideoObjectStorage.upload_file(
                object_key=reference_object_key,
                file_path=source_frame_path,
                content_type="image/jpeg",
            )
        except Exception as exc:
            # 只是调试素材，存不下不该把整条封面链路拖垮。
            log.warning(f"封面参考帧上传失败，跳过: task_no={task_no}, error={exc}")
            reference_object_key = None
        log.info(
            "智能视频封面参考帧抽取完成: "
            f"task_no={task_no}, frame_name={source_frame_path.name}"
        )
        if cover_plan_override is None:
            cover_plan_timeout_seconds = float(settings.VIDEO_COVER_PLAN_TIMEOUT_SECONDS)
            try:
                cover_plan = await cls._build_cover_plan(
                    task_title, subtitles, processing_config
                )
            except APITimeoutError as exc:
                raise CustomException(
                    msg=f"AI 封面策划请求超时: {cover_plan_timeout_seconds:.0f} 秒"
                ) from exc
            except APIConnectionError as exc:
                raise CustomException(msg=f"AI 封面策划连接失败: {exc}") from exc
            except APIError as exc:
                raise CustomException(msg=f"AI 封面策划失败: {exc}") from exc
        else:
            cover_plan = cover_plan_override
        log.info(
            "智能视频封面策划完成: "
            f"task_no={task_no}, title={cover_plan['title']}"
        )
        # 纯函数（策划结果 + 模板），两个分支都先算出来，调试元数据才有完整提示词。
        # 续跑时若模板被改过，这里重建的串可能与首次实际发出的不同，仅影响调试展示。
        cover_prompt = cls._build_seedream_prompt(cover_plan, processing_config)
        if generated_image_url_override:
            generated_image_url = generated_image_url_override
            # 已有生图地址时直接进入下载阶段，不能把断点退回生图阶段。
            await save_cover_checkpoint(
                "cover_download",
                {
                    "plan": cover_plan,
                    "generated_image_url": generated_image_url,
                },
            )
        else:
            await save_cover_checkpoint("cover_generate", {"plan": cover_plan})
            reference_frames = [source_frame_path]
            try:
                generated_image_url = await cls._generate_cover_image(
                    cover_prompt, reference_frames, provider, processing_config
                )
            except APITimeoutError as exc:
                raise CustomException(
                    msg=f"AI 封面生图请求超时({provider}): {_COVER_IMAGE_TIMEOUT_SECONDS:.0f} 秒"
                ) from exc
            except APIConnectionError as exc:
                raise CustomException(msg=f"AI 封面生图连接失败({provider}): {exc}") from exc
            except APIError as exc:
                raise CustomException(msg=f"AI 封面生图失败({provider}): {exc}") from exc
            await save_cover_checkpoint(
                "cover_download",
                {
                    "plan": cover_plan,
                    "generated_image_url": cls._checkpoint_image_url(generated_image_url),
                },
            )
        log.info(f"智能视频封面生图完成: task_no={task_no}")

        titled_cover_path = temp_dir / "cover-generated.png"
        try:
            await cls._download_file(generated_image_url, titled_cover_path)
        except httpx.TimeoutException as exc:
            raise CustomException(
                msg=f"AI 封面图片下载超时: {_COVER_DOWNLOAD_TIMEOUT_SECONDS:.0f} 秒"
            ) from exc
        except httpx.HTTPStatusError as exc:
            # 中转站有上游会回一个拉不到的地址（实测 http→https 后 404），
            # 直说拉不下来，让它去修，别退化成「随便出一张」。
            raise CustomException(
                msg=(
                    f"AI 封面图片下载失败: HTTP {exc.response.status_code}, "
                    f"地址={generated_image_url[:120]}"
                )
            ) from exc
        except httpx.HTTPError as exc:
            raise CustomException(msg=f"AI 封面图片下载失败: {exc}") from exc
        cls._normalize_generated_cover_image(titled_cover_path)
        log.info(
            "智能视频封面图片下载完成: "
            f"task_no={task_no}, file_name={titled_cover_path.name}"
        )

        # 原图保持 PNG 无损（用户下载用），另出一张 JPEG 缩略图给前端展示。
        cover_thumbnail_path = temp_dir / "cover-thumbnail.jpg"
        cls._build_cover_thumbnail(titled_cover_path, cover_thumbnail_path)

        cover_object_key = VideoObjectStorage.build_object_key(
            task_no=task_no,
            asset_role="cover",
            file_name=f"{task_no}-cover.png",
        )
        cover_metadata = await VideoObjectStorage.upload_file(
            object_key=cover_object_key,
            file_path=titled_cover_path,
            content_type="image/png",
        )
        cover_thumbnail_key = VideoObjectStorage.build_object_key(
            task_no=task_no,
            asset_role="cover",
            file_name=f"{task_no}-cover-thumb.jpg",
        )
        await VideoObjectStorage.upload_file(
            object_key=cover_thumbnail_key,
            file_path=cover_thumbnail_path,
            content_type="image/jpeg",
        )
        log.info(
            "智能视频封面上传完成: "
            f"task_no={task_no}, cover_object_key={cover_object_key}"
        )

        return VideoCoverRenderResult(
            enabled=True,
            image_provider=provider,
            image_model=cls.image_model_for(provider, processing_config),
            image_size=cls.image_size_for(provider, processing_config),
            summary_model=str(
                processing_config.get("cover_summary_model")
                or settings.VIDEO_COVER_SUMMARY_MODEL
            ),
            title=str(cover_plan["title"]),
            prompt=str(cover_plan["prompt"]),
            image_prompt=cover_prompt,
            frame_refs=[frame_path.name for frame_path in frame_paths],
            source_frame_name=source_frame_path.name,
            reference_object_key=reference_object_key,
            generated_image_url=generated_image_url,
            cover_image_path=titled_cover_path,
            cover_object_key=cover_object_key,
            cover_thumbnail_key=cover_thumbnail_key,
            cover_file_size=int(cover_metadata["file_size"]),
            cover_etag=str(cover_metadata["etag"]),
            elapsed_seconds=time.monotonic() - started_at,
        )

    @classmethod
    async def _extract_reference_frames(
        cls,
        source_path: Path,
        temp_dir: Path,
        source_duration_ms: int,
    ) -> list[Path]:
        """用 FFmpeg 从锁定时间线的视频中抽取封面主体帧。"""
        probed_duration_seconds = await cls._probe_video_duration_seconds(source_path)
        duration_seconds = max(min(source_duration_ms / 1000, probed_duration_seconds), 1.0)
        frame_path = temp_dir / "cover-frame.jpg"
        await cls._extract_reference_frame(
            source_path=source_path,
            frame_path=frame_path,
            duration_seconds=duration_seconds,
            preferred_ratio=float(settings.VIDEO_COVER_SOURCE_FRAME_RATIO),
        )
        return [frame_path]

    @staticmethod
    def _encode_reference_frames(frame_paths: list[Path]) -> list[str]:
        """把参考帧转成 data URL，避免方舟回源访问本地 MinIO 内网地址。"""
        return [
            f"data:image/jpeg;base64,{base64.b64encode(frame_path.read_bytes()).decode('ascii')}"
            for frame_path in frame_paths
        ]

    @classmethod
    async def _extract_reference_frame(
        cls,
        *,
        source_path: Path,
        frame_path: Path,
        duration_seconds: float,
        preferred_ratio: float,
    ) -> None:
        """按多个安全时间点回退抽帧，确保参考帧真实落盘。"""
        candidate_ratios = [
            preferred_ratio,
            0.5,
            0.28,
            0.72,
            0.12,
        ]
        attempted_seconds: set[float] = set()
        for ratio in candidate_ratios:
            seek_seconds = round(
                min(max(duration_seconds * ratio, 0.0), max(duration_seconds - 0.08, 0.0)),
                3,
            )
            if seek_seconds in attempted_seconds:
                continue
            attempted_seconds.add(seek_seconds)
            if frame_path.exists():
                frame_path.unlink()
            command = [
                "ffmpeg",
                "-y",
                # -ss 必须在 -i 之前：ffmpeg 直接定位到目标附近的关键帧再解码到该帧。
                # 放在 -i 之后会从文件头逐帧解码，长视频上慢一个数量级。
                "-ss",
                f"{seek_seconds:.3f}",
                "-i",
                str(source_path),
                "-frames:v",
                "1",
                "-vf",
                (
                    f"scale={cls._cover_width}:{cls._cover_height}:"
                    "force_original_aspect_ratio=increase,"
                    f"crop={cls._cover_width}:{cls._cover_height},"
                    "format=yuvj420p"
                ),
                "-pix_fmt",
                "yuvj420p",
                str(frame_path),
            ]
            await cls._run_command(command, "抽取封面参考帧失败")
            if frame_path.exists() and frame_path.stat().st_size > 0:
                return
        raise CustomException(
            msg=f"抽取封面参考帧失败: 未生成有效文件 {frame_path.name}"
        )

    @classmethod
    async def _probe_video_duration_seconds(cls, media_path: Path) -> float:
        """读取本地视频真实时长，避免使用云端时长导致抽帧越界。"""
        command = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(media_path),
        ]
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            stderr_text = stderr.decode("utf-8", errors="replace")
            raise CustomException(msg=f"读取封面参考视频时长失败: {stderr_text[-800:]}")
        try:
            payload = json.loads(stdout.decode("utf-8", errors="replace"))
            return max(float(payload["format"]["duration"]), 0.1)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise CustomException(msg="读取封面参考视频时长失败: ffprobe 输出格式异常") from exc

    @staticmethod
    async def _build_cover_plan(
        task_title: str,
        subtitles: list[VolcMediaKitSubtitleCue],
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """根据任务标题和字幕内容生成封面标题与排版说明。"""
        summary_model = str(
            config.get("cover_summary_model") or settings.VIDEO_COVER_SUMMARY_MODEL
        )
        transcript = " ".join(subtitle.subtitle_text for subtitle in subtitles)
        cover_plan_timeout_seconds = float(settings.VIDEO_COVER_PLAN_TIMEOUT_SECONDS)
        style_samples = "\n".join([
            "看透表层现象，所有生意底层逻辑高度相通",
            "圈内不会公开讲的经营常识，句句扎心现实",
            "通用做事逻辑，不管做实体还是做流量都适用",
            "万事皆有固定规律，读懂少走好几年弯路",
            "所有结果，背后都藏着一套可复制的逻辑",
            "普通人接触不到，生意人必备的底层底牌",
            "一件事想做顺，先要把内在道理彻底想通透",
            "做生意的核心能力，从来都是懂得合理取舍",
            "被多数人忽略的常识，恰恰是赚钱关键",
            "问题反复解决不了，一定要去找最原始根源",
        ])
        log.info(
            "智能视频封面提交策划请求: "
            f"model={summary_model}, "
            f"timeout_seconds={cover_plan_timeout_seconds:.0f}, "
            f"title_length={len(task_title)}, "
            f"subtitle_count={len(subtitles)}, "
            f"transcript_length={len(transcript)}"
        )
        client = AsyncOpenAI(api_key=settings.DOUBAO_API_KEY, base_url=settings.DOUBAO_API_URL)
        # 火山大模型规划和创意编排共用同一组 LLM 并发预算。
        async with get_volc_llm_semaphore():
            response = await client.chat.completions.create(
                model=summary_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是短视频封面策划。只返回 JSON，不要 Markdown。"
                            "封面要像知识博主、商业认知、干货口播封面。"
                            "主标题要短、有冲突、有利益点，最多 16 个字。"
                            "允许 AI 优化背景、光效和中文字设计，但人物必须保留参考图主体特征。"
                            f"{_COVER_SAFE_AREA_CLAUSE}"
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"任务标题：{task_title}\n"
                            f"口播字幕：{transcript[:3000]}\n"
                            f"标题风格样本：\n{style_samples}\n"
                            "请生成 JSON："
                            '{"title":"主标题","subtitle":"副标题，最多18个字",'
                            '"badge":"标签，最多4个字","highlights":["高亮词1","高亮词2"],'
                            '"prompt":"封面排版和氛围说明"}'
                        ),
                    },
                ],
                response_format={"type": "json_object"},
                timeout=cover_plan_timeout_seconds,
            )
        content = response.choices[0].message.content
        if not content:
            raise CustomException(msg="AI 封面策划未返回内容")
        plan = json.loads(content)
        title = str(plan["title"]).strip()
        subtitle = str(plan.get("subtitle") or "").strip()
        badge = str(plan.get("badge") or "认知干货").strip()
        highlights = [
            str(item).strip() for item in plan.get("highlights") or [] if str(item).strip()
        ]
        prompt = str(plan["prompt"]).strip()
        if not title or not prompt:
            raise CustomException(msg="AI 封面策划缺少标题或提示词")
        return {
            "title": title[:24],
            "subtitle": subtitle[:24],
            "badge": badge[:6],
            "highlights": highlights[:2],
            "prompt": prompt,
        }

    @staticmethod
    def _build_seedream_prompt(plan: dict[str, Any], config: dict[str, Any]) -> str:
        """按全局模板组装封面生图提示词，允许模型生成中文大字。

        模板里的 `{{safe_area}}` 必须保留：排版氛围描述里常写「放在封面左上角」
        这类贴边导向，安全区子句必须最后压一遍。缺占位符的模板在保存时就被拒了。
        """
        template = resolve_prompt_template(
            config.get("cover_prompt_template"), COVER_IMAGE_PROMPT_TEMPLATE
        )
        return render_prompt_template(
            template,
            {
                "title": str(plan["title"]),
                "subtitle": str(plan.get("subtitle") or ""),
                "badge": str(plan.get("badge") or "认知干货"),
                "highlights": "、".join(str(item) for item in plan.get("highlights") or []),
                "plan_prompt": str(plan["prompt"]),
                "safe_area": _COVER_SAFE_AREA_CLAUSE,
            },
        )

    @classmethod
    async def _generate_cover_image(
        cls,
        prompt: str,
        frame_paths: list[Path],
        provider: str,
        config: dict[str, Any],
    ) -> str:
        """把封面生图请求发给解析好的 provider。

        参考帧按本地文件传参：relay 走 multipart 编辑端点要文件本体，
        seedream 才需要 data URL，编码只在它自己那一侧做。
        """
        if provider == "relay":
            return await cls._generate_relay_cover(prompt, frame_paths, config)
        return await cls._generate_seedream_cover(
            prompt, cls._encode_reference_frames(frame_paths), config
        )

    @staticmethod
    def _checkpoint_image_url(image_url: str) -> str | None:
        """断点里只留能跨进程复用的 http 地址。

        中转站若只回 b64_json，我们会转成 data URL 直接落盘；这种串有 MB 级，
        写进 JSON 断点会撑爆数据库，换个进程也复用不了，所以不入断点。
        """
        return image_url if image_url.startswith("http") else None

    @staticmethod
    async def _generate_seedream_cover(
        prompt: str, frame_inputs: list[str], config: dict[str, Any]
    ) -> str:
        """调用火山方舟 Seedream，基于参考帧自由生成封面图。"""
        model = VideoCoverGenerator.image_model_for("seedream", config)
        image_size = VideoCoverGenerator.image_size_for("seedream", config)
        client = AsyncOpenAI(api_key=settings.DOUBAO_API_KEY, base_url=settings.DOUBAO_API_URL)
        log.info(
            "智能视频封面提交 Seedream 生图请求: "
            f"model={model}, "
            f"image_count={len(frame_inputs)}, "
            f"image_size={image_size}, "
            f"prompt_length={len(prompt)}"
        )
        # 生图接口单独限流，避免封面批量生成把图片接口打满。
        async with get_volc_image_semaphore():
            response = await client.images.generate(
                model=model,
                prompt=prompt,
                size=image_size,
                response_format="url",
                extra_body={
                    "image": frame_inputs,
                    "watermark": False,
                    # 当前模型不支持 sequential_image_generation，单张参考图直接走默认融合流程。
                    "send": 1111,
                },
                timeout=_COVER_IMAGE_TIMEOUT_SECONDS,
            )
        if not response.data or not response.data[0].url:
            raise CustomException(msg="AI 封面生图未返回图片地址")
        return response.data[0].url

    @classmethod
    async def _generate_relay_cover(
        cls, prompt: str, frame_paths: list[Path], config: dict[str, Any]
    ) -> str:
        """调用 OpenAI 协议中转站做图生图（multipart 传参考帧）。

        参考图只能走 `/v1/images/edits`：`extra_body["image"]` 是火山 Seedream 的字段，
        在 `/v1/images/generations` 上会返回 200 但不生效。这里**不做任何降级** ——
        中转站出错就一路报上去，别静默换一张「人不对」的封面糊过去。
        """
        model = cls.image_model_for("relay", config)
        image_size = cls.image_size_for("relay", config)
        client = AsyncOpenAI(
            api_key=settings.COVER_RELAY_API_KEY,
            base_url=settings.COVER_RELAY_API_URL,
        )
        log.info(
            "智能视频封面提交中转站生图请求: "
            f"model={model}, "
            f"image_count={len(frame_paths)}, "
            f"image_size={image_size}, "
            f"prompt_length={len(prompt)}"
        )
        # 生图接口单独限流，避免封面批量生成把图片接口打满。
        async with get_volc_image_semaphore():
            return await cls._request_relay_edit(
                client, prompt, frame_paths, model, image_size
            )

    @staticmethod
    async def _request_relay_edit(
        client: AsyncOpenAI,
        prompt: str,
        frame_paths: list[Path],
        model: str,
        image_size: str,
    ) -> str:
        """提交一次中转站图生图，参考帧以 multipart 文件形式挂上。

        不传 `response_format`：部分渠道对该参数直接报错。回 url 还是 b64_json
        由渠道决定，统一由 `_relay_image_url` 归一化。
        """
        image_files = [
            (path.name, path.read_bytes(), "image/jpeg") for path in frame_paths
        ]
        response = await client.images.edit(
            model=model,
            image=image_files,
            prompt=prompt,
            size=image_size,
            timeout=_COVER_IMAGE_TIMEOUT_SECONDS,
        )
        return VideoCoverGenerator._relay_image_url(response)

    @staticmethod
    def _relay_image_url(response: Any) -> str:
        """把中转站返回的 url / b64_json 统一成一个可下载的地址字符串。"""
        if not response.data:
            raise CustomException(msg="AI 封面生图未返回图片数据")
        image = response.data[0]
        if image.url:
            return image.url
        if image.b64_json:
            return f"data:image/png;base64,{image.b64_json}"
        raise CustomException(msg="AI 封面生图既没有返回 url 也没有返回 b64_json")

    @staticmethod
    async def _download_file(url: str, target_path: Path) -> None:
        """下载 AI 生成封面图到 worker 临时目录，兼容渠道直回 b64 的情况。"""
        if url.startswith("data:"):
            _, _, payload = url.partition(",")
            target_path.write_bytes(base64.b64decode(payload))
            return
        timeout = httpx.Timeout(connect=30.0, read=_COVER_DOWNLOAD_TIMEOUT_SECONDS, write=30.0, pool=30.0)
        # 必须显式跟随重定向：httpx 默认 follow_redirects=False，而 raise_for_status()
        # 连 3xx 一起判失败，中转站有上游回的是 http:// 地址（308 跳 https）会直接报错。
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            target_path.write_bytes(response.content)

    @classmethod
    def _normalize_generated_cover_image(cls, image_path: Path) -> None:
        """把生图结果规范到 3:4 封面比例，避免平台侧再次裁切。

        保持居中裁切。试过「固定顶部、只裁底部」，实测更差：模型常把主标题排成
        三行、内容底边到 84%~94%，把 11% 的损失全压到底部会切到标题最后一行。
        对称裁掉上下各 5.6% 反而更贴合模型的实际排版。
        """
        source_image = Image.open(image_path).convert("RGB")
        normalized = cls._fit_image_to_canvas(
            source_image,
            cls._cover_width,
            cls._cover_height,
        )
        normalized.save(image_path, "PNG")

    @classmethod
    def _build_cover_thumbnail(cls, source_path: Path, output_path: Path) -> None:
        """生成前端展示用的 JPEG 缩略图，等比缩到 600x800 以内。"""
        source_image = Image.open(source_path).convert("RGB")
        thumbnail = cls._fit_image_to_contain(
            source_image,
            cls._cover_thumbnail_width,
            cls._cover_thumbnail_height,
        )
        thumbnail.save(
            output_path,
            "JPEG",
            quality=cls._cover_thumbnail_jpeg_quality,
            optimize=True,
        )

    @classmethod
    def _draw_cover_title(cls, source_path: Path, output_path: Path, plan: dict[str, Any]) -> None:
        """在真实视频帧上叠加可控中文标题，避免 AI 重绘真人脸。"""
        title = str(plan["title"])
        subtitle = str(plan.get("subtitle") or "")
        badge = str(plan.get("badge") or "认知干货")
        highlights = [str(item) for item in plan.get("highlights") or []]
        source_image = Image.open(source_path).convert("RGB")
        image = cls._fit_cover_image(source_image).convert("RGBA")
        enhanced = ImageEnhance.Contrast(image).enhance(1.12)
        image = ImageEnhance.Color(enhanced).enhance(1.08)
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # 标题区域用渐变压暗，保留真实人物画面同时提升短视频封面冲击力。
        for y in range(0, 760):
            alpha = int(170 * (1 - y / 760))
            draw.line((0, y, 1080, y), fill=(0, 0, 0, alpha))
        draw.rectangle((0, 1510, 1080, 1920), fill=(0, 0, 0, 48))
        draw.rounded_rectangle((72, 92, 306, 158), radius=24, fill=(255, 214, 64, 235))
        badge_font = cls._load_font(34)
        draw.text((104, 108), badge, font=badge_font, fill=(0, 0, 0, 255))
        draw.rounded_rectangle(
            (332, 96, 520, 154),
            radius=20,
            outline=(255, 255, 255, 180),
            width=3,
        )
        draw.text((360, 108), "少走弯路", font=badge_font, fill=(255, 255, 255, 235))

        image = Image.alpha_composite(image, overlay)
        draw = ImageDraw.Draw(image)

        lines = textwrap.wrap(title, width=7) or [title]
        font = cls._load_cover_title_font(lines)
        line_boxes = [draw.textbbox((0, 0), line, font=font, stroke_width=5) for line in lines]
        line_height = max(box[3] - box[1] for box in line_boxes)
        start_y = 202
        panel_bottom = start_y + len(lines) * (line_height + 24) + 128
        panel = Image.new("RGBA", image.size, (0, 0, 0, 0))
        panel_draw = ImageDraw.Draw(panel)
        panel_draw.rounded_rectangle(
            (52, start_y - 52, 1028, panel_bottom),
            radius=36,
            fill=(0, 0, 0, 74),
        )
        image = Image.alpha_composite(image, panel)
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle(
            (72, start_y - 26, 94, start_y + len(lines) * (line_height + 24) - 8),
            radius=10,
            fill=(255, 214, 64, 255),
        )
        for index, line in enumerate(lines):
            fill = (255, 214, 64) if index == len(lines) - 1 else (255, 255, 255)
            draw.text(
                (118, start_y + index * (line_height + 24)),
                line,
                font=font,
                fill=fill,
                stroke_width=5,
                stroke_fill=(0, 0, 0),
            )
        if subtitle:
            subtitle_font = cls._load_font(42)
            draw.rounded_rectangle(
                (118, panel_bottom - 84, 960, panel_bottom - 22),
                radius=20,
                fill=(255, 214, 64, 235),
            )
            draw.text(
                (148, panel_bottom - 74),
                subtitle,
                font=subtitle_font,
                fill=(0, 0, 0),
                stroke_width=1,
                stroke_fill=(255, 255, 255),
            )
        if highlights:
            tag_font = cls._load_font(36)
            x = 72
            y = 1672
            for highlight in highlights:
                box = draw.textbbox((0, 0), highlight, font=tag_font)
                width = box[2] - box[0] + 42
                draw.rounded_rectangle(
                    (x, y, x + width, y + 58),
                    radius=22,
                    fill=(196, 42, 34, 238),
                )
                draw.text(
                    (x + 21, y + 9),
                    highlight,
                    font=tag_font,
                    fill=(255, 255, 255),
                    stroke_width=2,
                    stroke_fill=(0, 0, 0),
                )
                x += width + 18
        image.convert("RGB").save(output_path, "PNG")

    @staticmethod
    def _fit_cover_image(image: Image.Image) -> Image.Image:
        """按 9:16 封面画布居中裁切，输入来自已转正的视频真实帧。"""
        target_width, target_height = 1080, 1920
        source_width, source_height = image.size
        scale = max(target_width / source_width, target_height / source_height)
        resized_width = round(source_width * scale)
        resized_height = round(source_height * scale)
        resized = image.resize((resized_width, resized_height), Image.Resampling.LANCZOS)
        left = (resized_width - target_width) // 2
        top = (resized_height - target_height) // 2
        return resized.crop((left, top, left + target_width, top + target_height))

    @classmethod
    def _load_cover_title_font(
        cls,
        lines: list[str],
    ) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        """按标题宽度动态选择字号，避免封面大字溢出画布。"""
        probe_image = Image.new("RGB", (1080, 1920))
        probe_draw = ImageDraw.Draw(probe_image)
        for size in range(118, 77, -6):
            font = cls._load_font(size)
            max_width = max(probe_draw.textbbox((0, 0), line, font=font)[2] for line in lines)
            if max_width <= 880:
                return font
        return cls._load_font(78)

    @classmethod
    async def write_cover_as_first_frame(
        cls,
        *,
        cover_image_path: Path,
        source_video_path: Path,
        output_video_path: Path,
    ) -> None:
        """把封面图覆盖到 MP4 首帧，便于播放器和平台抓取默认封面。"""
        first_frame_cover_path = cover_image_path.with_name(
            f"{cover_image_path.stem}-first-frame{cover_image_path.suffix}"
        )
        cls._build_first_frame_cover_image(cover_image_path, first_frame_cover_path)
        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(first_frame_cover_path),
            "-i",
            str(source_video_path),
            "-filter_complex",
            (
                "[1:v]scale=trunc(iw/2)*2:trunc(ih/2)*2,"
                "setsar=1,format=yuv420p[base];"
                "[0:v]format=rgba[cover_rgba];"
                # 只替换第 1 帧，不改变原视频时长和音频时间线。
                "[base][cover_rgba]overlay=enable='eq(n,0)':x=0:y=0,"
                "format=yuv420p[v]"
            ),
            "-map",
            "[v]",
            "-map",
            "1:a?",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-color_range",
            "tv",
            "-g",
            "60",
            "-keyint_min",
            "60",
            "-sc_threshold",
            "0",
            "-force_key_frames",
            "expr:gte(t,n_forced*2)",
            "-c:a",
            "copy",
            "-movflags",
            "+faststart",
            "-metadata:s:v:0",
            "rotate=0",
            str(output_video_path),
        ]
        await cls._run_command(command, "写入视频首帧封面失败")

    @classmethod
    def _build_first_frame_cover_image(
        cls,
        cover_image_path: Path,
        output_path: Path,
    ) -> None:
        """把 3:4 封面贴到 9:16 首帧画布，避免首帧被强行拉伸。"""
        cover_image = Image.open(cover_image_path).convert("RGB")
        background = cls._fit_image_to_canvas(
            cover_image,
            cls._first_frame_width,
            cls._first_frame_height,
        )
        background = background.filter(ImageFilter.GaussianBlur(28))
        background = ImageEnhance.Brightness(background).enhance(0.72).convert("RGBA")

        cover = cls._fit_image_to_contain(
            cover_image,
            cls._first_frame_width - 96,
            cls._first_frame_height - 320,
        ).convert("RGBA")

        shadow = Image.new("RGBA", cover.size, (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.rounded_rectangle(
            (10, 12, cover.size[0] - 10, cover.size[1] - 10),
            radius=34,
            fill=(0, 0, 0, 128),
        )

        canvas = background.copy()
        offset_x = (cls._first_frame_width - cover.size[0]) // 2
        offset_y = (cls._first_frame_height - cover.size[1]) // 2
        canvas.alpha_composite(shadow, (offset_x, offset_y + 18))
        canvas.alpha_composite(cover, (offset_x, offset_y))
        canvas.convert("RGB").save(output_path, "PNG")

    @staticmethod
    def _fit_image_to_canvas(
        image: Image.Image,
        target_width: int,
        target_height: int,
    ) -> Image.Image:
        """按目标画布裁切图片，避免输出比例漂移。

        居中裁切是权衡后的选择：出图 2:3、画布 3:4，无论怎么裁都要丢掉约 11% 的
        高度；模型的文字会顶到画面顶部也会压到接近底部，只有对称裁才两边都不额外
        吃亏（「只裁底部」实测会把主标题最后一行切掉，别再改回去）。
        """
        source_width, source_height = image.size
        scale = max(target_width / source_width, target_height / source_height)
        resized_width = round(source_width * scale)
        resized_height = round(source_height * scale)
        resized = image.resize((resized_width, resized_height), Image.Resampling.LANCZOS)
        left = (resized_width - target_width) // 2
        top = (resized_height - target_height) // 2
        return resized.crop((left, top, left + target_width, top + target_height))

    @staticmethod
    def _fit_image_to_contain(
        image: Image.Image,
        max_width: int,
        max_height: int,
    ) -> Image.Image:
        """按最大尺寸等比缩放，保留完整封面主体。"""
        source_width, source_height = image.size
        scale = min(max_width / source_width, max_height / source_height)
        resized_width = round(source_width * scale)
        resized_height = round(source_height * scale)
        return image.resize((resized_width, resized_height), Image.Resampling.LANCZOS)

    @staticmethod
    def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        """加载系统中文字体，保证封面标题能正常显示。"""
        font_paths = [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        ]
        for font_path in font_paths:
            if Path(font_path).exists():
                return ImageFont.truetype(font_path, size=size)
        raise CustomException(msg="生成封面标题缺少可用中文字体")

    @staticmethod
    async def _run_command(command: list[str], error_message: str) -> None:
        """执行媒体处理命令，并把 stderr 收敛为业务错误。"""
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            stderr_text = stderr.decode("utf-8", errors="replace")
            stdout_text = stdout.decode("utf-8", errors="replace")
            detail = re.sub(r"\s+", " ", f"{stderr_text} {stdout_text}").strip()
            raise CustomException(msg=f"{error_message}: {detail[-1200:]}")
