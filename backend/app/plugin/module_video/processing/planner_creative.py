from __future__ import annotations

import json
from typing import Any

from openai import APIConnectionError, APIError, APITimeoutError, AsyncOpenAI

from app.config.setting import settings
from app.core.exceptions import CustomException
from app.core.logger import log

from .planner_events import (
    ANIMATION_TEMPLATES,
    GRAPHIC_PLACEMENT_OPTIONS,
    PLACEMENT_OPTIONS,
    STICKER_TEMPLATES,
    SUBTITLE_KEYWORD_LIMIT,
    TONE_OPTIONS,
    filter_animation_events_by_stickers,
    filter_graphic_stickers_for_focus,
    filter_micro_stickers_for_focus,
    normalize_sticker_events,
    normalize_subtitle_keywords,
    parse_animation_events,
    parse_graphic_sticker_events,
    parse_sticker_events,
    pick_spread_events,
)
from .planner_models import VideoCreativeEditingPlan
from .processing_config import (
    PLANNER_SYSTEM_PROMPT_TEMPLATE,
    load_processing_config,
    render_prompt_template,
    resolve_prompt_template,
)
from .provider_concurrency import get_volc_llm_semaphore


class VideoCreativePlanner:
    """创意规划模型编排器。"""

    # 枚举与字数上限集中在 planner_events，这里转发给 prompt 与编排使用。
    _sticker_templates = STICKER_TEMPLATES
    _animation_templates = ANIMATION_TEMPLATES
    _tone_options = TONE_OPTIONS
    _placement_options = PLACEMENT_OPTIONS
    _graphic_placement_options = GRAPHIC_PLACEMENT_OPTIONS
    _tail_limit = 3200
    # 观点卡与小贴纸的密度由 _sticker_density_budget() 按成片时长决定，这里只留高亮框开关。
    _max_highlight_boxes = 0
    _subtitle_keyword_limit = SUBTITLE_KEYWORD_LIMIT
    _subtitle_keyword_prompt_chars = 3200

    @classmethod
    async def build_creative_editing_plan(
        cls,
        *,
        task_no: str,
        task_title: str,
        style_preset: str,
        adjustment_prompt: str,
        source_duration_ms: int,
        utterances: list[dict[str, Any]],
    ) -> VideoCreativeEditingPlan:
        """根据口播时间轴生成贴纸和动画事件。"""
        validate_settings()
        config = await load_processing_config()
        planner_model = str(
            config.get("creative_planner_model") or settings.VIDEO_CREATIVE_PLANNER_MODEL
        )
        system_prompt = cls._build_system_prompt(source_duration_ms, config)
        user_prompt = cls._build_user_prompt(
            task_no=task_no,
            task_title=task_title,
            style_preset=style_preset,
            adjustment_prompt=adjustment_prompt,
            source_duration_ms=source_duration_ms,
            transcript_excerpt=cls._build_transcript_excerpt(utterances),
        )
        (
            opinion_card_limit,
            micro_sticker_limit,
            animation_limit,
            graphic_sticker_limit,
        ) = cls._sticker_density_budget(source_duration_ms)
        client = AsyncOpenAI(api_key=settings.DOUBAO_API_KEY, base_url=settings.DOUBAO_API_URL)
        try:
            # 火山大模型规划和封面策划共用同一组 LLM 并发预算。
            async with get_volc_llm_semaphore():
                response = await client.chat.completions.create(
                    model=planner_model,
                    timeout=90,
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt,
                        },
                        {
                            "role": "user",
                            "content": user_prompt,
                        },
                    ],
                    response_format={"type": "json_object"},
                )
        except APITimeoutError as exc:
            raise CustomException(msg="创意规划模型请求超时") from exc
        except APIConnectionError as exc:
            raise CustomException(msg=f"创意规划模型连接失败: {exc}") from exc
        except APIError as exc:
            raise CustomException(msg=f"创意规划模型调用失败: {exc}") from exc

        content = response.choices[0].message.content
        if not content:
            raise CustomException(msg="创意规划模型未返回内容")

        try:
            plan = json.loads(content)
        except ValueError as exc:
            raise CustomException(msg="创意规划模型返回不是 JSON") from exc
        if not isinstance(plan, dict):
            raise CustomException(msg="创意规划模型返回格式错误")

        summary = str(plan.get("summary") or "").strip() or None
        sticker_events = parse_sticker_events(plan.get("sticker_events"), source_duration_ms)
        sticker_events = normalize_sticker_events(sticker_events)
        animation_events = parse_animation_events(plan.get("animation_events"), source_duration_ms)
        graphic_sticker_events = parse_graphic_sticker_events(
            plan.get("graphic_sticker_events"),
            source_duration_ms,
        )
        # 模型没下发 / 被空档过滤吃光 / 被均匀抽取裁掉，三种「图形贴纸为 0」在最终
        # 日志里长得一样，这里先记下漏斗各段的数，排查时不用再猜。
        graphic_parsed_count = len(graphic_sticker_events)
        if not sticker_events and not animation_events and not graphic_sticker_events:
            raise CustomException(msg="创意规划模型未返回任何贴纸或动画事件")

        opinion_cards = pick_spread_events(
            [event for event in sticker_events if event.template_id == "opinion_card"],
            opinion_card_limit,
        )
        micro_stickers = pick_spread_events(
            [event for event in sticker_events if event.template_id == "micro_sticker"],
            micro_sticker_limit,
        )
        micro_stickers = filter_micro_stickers_for_focus(
            micro_stickers=micro_stickers,
            blocking_events=opinion_cards,
        )
        highlight_boxes = pick_spread_events(
            [event for event in sticker_events if event.template_id == "highlight_box"],
            cls._max_highlight_boxes,
        )
        sticker_events = [
            *opinion_cards,
            *micro_stickers,
            *highlight_boxes,
        ]
        sticker_events.sort(key=lambda item: (item.start_ms, item.end_ms, item.id))
        animation_events.sort(key=lambda item: (item.start_ms, item.end_ms, item.id))
        animation_events = filter_animation_events_by_stickers(
            animation_events=animation_events,
            sticker_events=sticker_events,
        )
        animation_events = pick_spread_events(animation_events, animation_limit)
        # 图形贴纸排在文字贴纸之后处理：先按图形互斥裁一轮，再均匀抽取，
        # 避免抽完又被过滤掉、实际数量少于预算。
        graphic_sticker_events = filter_graphic_stickers_for_focus(
            graphic_stickers=graphic_sticker_events,
        )
        graphic_focus_count = len(graphic_sticker_events)
        graphic_sticker_events = pick_spread_events(
            graphic_sticker_events,
            graphic_sticker_limit,
        )
        graphic_sticker_events.sort(key=lambda item: (item.start_ms, item.end_ms, item.id))
        log.info(
            "创意规划模型编排完成: "
            f"task_no={task_no}, sticker_count={len(sticker_events)}, "
            f"animation_count={len(animation_events)}, "
            f"graphic_sticker_count={len(graphic_sticker_events)}"
        )
        log.info(
            "图形贴纸漏斗: "
            f"task_no={task_no}, 模型下发={graphic_parsed_count}, "
            f"图形互斥后={graphic_focus_count}, "
            f"均匀抽取后={len(graphic_sticker_events)}（预算 {graphic_sticker_limit}）, "
            f"文字贴纸={len(sticker_events)}"
        )
        return VideoCreativeEditingPlan(
            summary=summary,
            sticker_events=sticker_events,
            animation_events=animation_events,
            graphic_sticker_events=graphic_sticker_events,
            planner_model=planner_model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

    @classmethod
    async def extract_subtitle_keywords(
        cls,
        *,
        task_no: str,
        subtitle_utterances: list[dict[str, Any]],
    ) -> list[list[str]]:
        """为每条字幕片段提取 0 到 2 个语义关键词，供底部字幕局部高亮。

        关键词必须原样出现在对应字幕里。提取失败时整体降级为空关键词，
        只影响高亮，不阻断贴纸和渲染主链。
        """
        empty_result = [[] for _ in subtitle_utterances]
        if not subtitle_utterances:
            return empty_result
        lines: list[str] = []
        for index, utterance in enumerate(subtitle_utterances, start=1):
            text = str(utterance.get("text") or "").strip()
            if not text:
                continue
            lines.append(f"{index}. {text}")
        if not lines:
            return empty_result
        transcript = "\n".join(lines)[: cls._subtitle_keyword_prompt_chars]

        try:
            validate_settings()
            config = await load_processing_config()
            client = AsyncOpenAI(api_key=settings.DOUBAO_API_KEY, base_url=settings.DOUBAO_API_URL)
            async with get_volc_llm_semaphore():
                response = await client.chat.completions.create(
                    model=str(
                        config.get("creative_planner_model")
                        or settings.VIDEO_CREATIVE_PLANNER_MODEL
                    ),
                    timeout=60,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "你是短视频字幕关键词提取器，只返回 JSON，不要 Markdown。"
                                "给你一组按顺序编号的字幕，为每条挑出 0 到 2 个最值得高亮的关键词。"
                                "关键词必须是该条字幕里原样连续出现的一段文字，优先实词："
                                "名词、动词、数字、英文、专有名词、情绪词。"
                                "不要虚词、不要标点、不要跨条拼接；没有值得强调的词就返回空数组。"
                                f"每条最多 {cls._subtitle_keyword_limit} 个关键词。"
                            ),
                        },
                        {
                            "role": "user",
                            "content": (
                                f"任务编号：{task_no}\n"
                                f"字幕列表：\n{transcript}\n"
                                "请输出 JSON，格式如下："
                                '{"keywords":[{"index":1,"keywords":["关键词A","关键词B"]},'
                                '{"index":2,"keywords":[]}]}'
                            ),
                        },
                    ],
                    response_format={"type": "json_object"},
                )
        except (APITimeoutError, APIConnectionError, APIError, CustomException) as exc:
            log.warning(f"字幕关键词提取失败，降级为不高亮: task_no={task_no}, error={exc}")
            return empty_result

        content = response.choices[0].message.content
        if not content:
            return empty_result
        try:
            payload = json.loads(content)
        except ValueError:
            log.warning(f"字幕关键词提取返回不是 JSON，降级为不高亮: task_no={task_no}")
            return empty_result
        if not isinstance(payload, dict):
            return empty_result
        return normalize_subtitle_keywords(
            raw_keywords=payload.get("keywords"),
            subtitle_utterances=subtitle_utterances,
        )

    @classmethod
    def _build_system_prompt(cls, source_duration_ms: int, config: dict[str, Any]) -> str:
        """按全局模板拼创意规划 system 提示词。

        模板里 `{{sticker_templates}}` 这类占位符是契约，由代码注入枚举清单 ——
        模型吐出枚举外的 template_id / placement 会被下游静默丢弃，所以这些值
        不允许手改，保存模板时会校验占位符是否齐全。
        """
        template = resolve_prompt_template(
            config.get("planner_prompt_template"), PLANNER_SYSTEM_PROMPT_TEMPLATE
        )
        return render_prompt_template(
            template,
            {
                "sticker_templates": ", ".join(cls._sticker_templates),
                "animation_templates": ", ".join(cls._animation_templates),
                "placement_options": ", ".join(cls._placement_options),
                "graphic_placement_options": ", ".join(cls._graphic_placement_options),
                "tone_options": ", ".join(cls._tone_options),
                "density": cls._sticker_density_prompt(source_duration_ms),
            },
        )

    @staticmethod
    def _build_user_prompt(
        *,
        task_no: str,
        task_title: str,
        style_preset: str,
        adjustment_prompt: str,
        source_duration_ms: int,
        transcript_excerpt: str,
    ) -> str:
        """拼创意规划 user 提示词。

        这段是**契约**：末尾的 JSON 格式与下游 parse_*_events 的字段一一对应，
        所以不开放编辑。口播摘要等数据也在这里注入。
        """
        return (
            f"任务编号：{task_no}\n"
            f"任务标题：{task_title}\n"
            f"剪辑风格：{style_preset}\n"
            f"成片时长：{source_duration_ms}ms\n"
            f"用户调整说明：{adjustment_prompt or '无'}\n"
            f"口播摘要：\n{transcript_excerpt}\n"
            "请输出 JSON，格式如下："
            '{"summary":"一句话概述创意方向",'
            '"sticker_events":[{"id":"s1","template_id":"opinion_card","start_ms":3000,"end_ms":8000,"title_text":"4字标题","body_text":"6到8字补充","text":"4字标题\\n6到8字补充","placement":"lower_third","scale":1.0,"rotation":0,"card_style":"blue_white_business","anchor_text":"可选"},'
            '{"id":"s2","template_id":"micro_sticker","start_ms":9000,"end_ms":11000,"text":"短词","placement":"mid_right","scale":1.0,"rotation":0,"card_style":"blue_chip","anchor_text":"可选"}],'
            '"animation_events":[{"id":"a1","template_id":"soft_pop","start_ms":3000,"end_ms":4200,'
            '"description":"首个观点卡入场","placement":"center","intensity":"medium","scale":1.0,'
            '"rotation":0,"anchor_text":"可选"}],'
            '"graphic_sticker_events":[{"id":"g1","tone":"正向","start_ms":1000,"end_ms":2600,'
            '"placement":"top_left","scale":1.0,"rotation":0,"anchor_text":"可选"}]}'
        )

    @classmethod
    def _build_transcript_excerpt(cls, utterances: list[dict[str, Any]]) -> str:
        """把口播句段压缩成供大模型使用的摘要。"""
        lines: list[str] = []
        for utterance in utterances[:24]:
            text = str(utterance.get("text") or "").strip()
            if not text:
                continue
            start_ms = int(utterance.get("start_ms") or 0)
            end_ms = int(utterance.get("end_ms") or start_ms)
            lines.append(f"[{start_ms}-{end_ms}] {text}")
        excerpt = "\n".join(lines)
        return excerpt[: cls._tail_limit]

    @staticmethod
    def _sticker_density_budget(source_duration_ms: int) -> tuple[int, int, int, int]:
        """按成片时长限流贴纸和动画数量，避免短视频信息过密。

        返回 (观点卡, 小贴纸, 动画, 图形贴纸)。产品定位是「图形为主、文字为辅」，
        所以文字贴纸预算压得比图形低 —— 文字只在关键处点一下。
        """
        duration_seconds = max(source_duration_ms, 0) / 1000
        if duration_seconds <= 15:
            return 1, 3, 1, 5
        if duration_seconds <= 30:
            return 1, 4, 1, 8
        if duration_seconds <= 45:
            return 2, 5, 2, 11
        # 45s 一过就跳到 14 是断崖（时长 +4%、预算 +27%），而成片基本落在 45~60s，
        # 等于每条都吃满 —— 这一段收到 10。75s 以上再放回 14：那个档一把罩到
        # 3 分钟，压到 10 会让 100s 的片子稀到 10.4s 一个。
        if duration_seconds <= 75:
            return 2, 6, 2, 10
        return 2, 6, 2, 14

    @staticmethod
    def _sticker_density_prompt(source_duration_ms: int) -> str:
        """把限流规则转换成模型更容易遵守的中文约束。"""
        duration_seconds = max(source_duration_ms, 0) / 1000
        if duration_seconds <= 15:
            return "当前视频在 15 秒内，观点卡 1 个，小贴纸 3 个，图形贴纸 5 个。"
        if duration_seconds <= 30:
            return "当前视频在 30 秒内，观点卡 1 个，小贴纸 4 个，图形贴纸 8 个。"
        if duration_seconds <= 45:
            return "当前视频在 45 秒内，观点卡 2 个，小贴纸 5 个，图形贴纸 11 个。"
        if duration_seconds <= 75:
            return "当前视频在 75 秒内，观点卡 2 个，小贴纸 6 个，图形贴纸 10 个。"
        return "当前视频超过 75 秒，观点卡 2 个，小贴纸 6 个，图形贴纸 14 个。"


def validate_settings() -> None:
    """校验创意规划模型所需配置。"""
    if not settings.DOUBAO_API_KEY or not settings.DOUBAO_API_URL:
        raise CustomException(msg="创意规划模型配置缺失: DOUBAO_API_KEY 或 DOUBAO_API_URL")
