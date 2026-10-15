"""自动剪辑全局配置的默认值、读取与保存。

配置只有一行（`VideoProcessingConfigModel.id == CONFIG_ROW_ID`）。env 里的模型名
是**默认值**，DB 里的值覆盖它 —— 所以「高级设置」留空（`None`）等于跟随 env，
改代码里的默认值时已保存的空字段会自然跟上，不用去库里回填。
"""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.module_system.user.model import UserModel
from app.config.setting import settings
from app.core.database import async_db_session

from .model import VideoProcessingConfigModel

CONFIG_ROW_ID = 1

# ---------------------------------------------------------------------------
# 提示词模板
#
# 模板里 `{{名字}}` 是**契约占位符**，由代码注入：枚举清单、时长预算、JSON 格式、
# 构图安全区。这些值直接决定下游解析能不能跑通（枚举写错 → 模型吐非法 template_id
# → 解析静默失败），所以不允许改。保存时校验占位符是否齐全，缺一个就拒绝。
#
# 用 `str.replace` 而不是 `str.format`：提示词里本来就含 `{}`（JSON 示例），
# `format` 会当成字段名直接 KeyError。
# ---------------------------------------------------------------------------

# 创意规划 system 提示词的默认模板。
PLANNER_SYSTEM_PROMPT_TEMPLATE = (
    "你是短视频云端创意编排器，只返回 JSON，不要 Markdown。"
    "你要基于口播时间轴，输出可执行的贴纸和动画事件。"
    "画面以图形贴纸为主、文字贴纸为辅：图形负责铺节奏，文字只在关键处点一下。"
    "文字贴纸模板只允许使用: {{sticker_templates}}。"
    "动画模板只允许使用: {{animation_templates}}。"
    "文字贴纸位置只允许使用: {{placement_options}}。"
    "图形贴纸位置只允许使用: {{graphic_placement_options}}。"
    "图形贴纸基调只允许使用: {{tone_options}}。"
    "事件时长建议控制在 1500ms 到 8000ms。"
    "不要输出常驻标题或裸文字，不要输出 highlight_box。"
    "{{density}}"
    "观点卡必须使用 opinion_card，不要底板、圆角气泡或背景框；"
    "卡片标题控制在 3 到 4 字，补充文案控制在 6 到 8 字。"
    "小贴纸必须使用 micro_sticker，不要背景气泡；"
    "文案只允许超短标签，控制在 2 到 4 字，尽量是数字、箭头或短情绪词。"
    "文字贴纸要克制，只在真正值得强调的地方出现，不要每句话都加。"
    "观点卡只出现在画面中下部，并且贴左边或贴右边。"
    "小贴纸只能放在左右边缘的中段安全区，不能贴人脸，不能放中央。"
    "同一时刻只允许出现 1 个小贴纸，不要让两个花字标签同时出现。"
    "图形贴纸是公共素材库里的纯图形装饰，本身不带文字，表达不了观点，"
    "所以它只用来烘托情绪，不要指望它承担信息；基调按那句话的情绪挑。"
    "图形贴纸统一压在字幕上方一条窄带里、左右两侧轮流摆；placement 的"
    "top_/mid_/bottom_ 只是这条带内的左右与高低微调，不代表画面顶部或底部。"
    "图形贴纸彼此之间不要重叠，同一时刻最多出现 1 个。"
    "只需要更有活力的口播/vlog 贴纸方案，不要做成企业字幕框。"
)

PLANNER_PROMPT_PLACEHOLDERS: tuple[str, ...] = (
    "sticker_templates",
    "animation_templates",
    "placement_options",
    "graphic_placement_options",
    "tone_options",
    "density",
)

# 封面生图提示词的默认模板。`{{safe_area}}` 是构图安全区子句，必须留。
COVER_IMAGE_PROMPT_TEMPLATE = (
    "根据参考图生成一张 3:4 比例的中文短视频封面。"
    "必须以参考图中的人物为主体，尽量保留人物五官、发型、眼镜、衣着和姿态特征。"
    "可以优化杂乱背景，替换为高档写字楼办公室、商务空间、知识博主直播间氛围，"
    "画面高级、清晰、商业认知类口播风格。"
    "封面主标题必须是中文大字：{{title}}。"
    "副标题：{{subtitle}}。"
    "角标标签：{{badge}}。"
    "高亮关键词：{{highlights}}。"
    "请直接在图片中生成醒目的中文封面大字，字体粗壮，有描边、阴影、黄白红重点色，"
    "构图像抖音/视频号商业干货封面，强冲击力，适合手机端点击。"
    "不要生成英文，不要生成乱码，不要改变人物身份，不要多出无关人物。"
    "排版氛围参考：{{plan_prompt}}"
    "{{safe_area}}"
)

COVER_PROMPT_PLACEHOLDERS: tuple[str, ...] = (
    "title",
    "subtitle",
    "badge",
    "highlights",
    "plan_prompt",
    "safe_area",
)

# 封面策划 system 提示词的默认模板。`{{safe_area}}` 是构图安全区子句，必须留。
COVER_PLAN_PROMPT_TEMPLATE = (
    "你是短视频封面策划。只返回 JSON，不要 Markdown。"
    "封面要像知识博主、商业认知、干货口播封面。"
    "主标题要短、有冲突、有利益点，最多 {{title_max_chars}} 个字。"
    "允许 AI 优化背景、光效和中文字设计，但人物必须保留参考图主体特征。"
    "{{safe_area}}"
)

COVER_PLAN_PROMPT_PLACEHOLDERS: tuple[str, ...] = ("safe_area",)

# 封面策划 user 提示词的默认模板。JSON 契约写在里面：字段名是下游 `plan["title"]`
# 等的唯一来源，改坏会让解析直接抛异常。
COVER_PLAN_USER_PROMPT_TEMPLATE = (
    "任务标题：{{task_title}}\n"
    "口播字幕：{{transcript}}\n"
    "标题风格样本：\n{{style_samples}}\n"
    "请生成 JSON："
    '{"title":"主标题","subtitle":"副标题，最多{{subtitle_max_chars}}个字",'
    '"badge":"标签，最多{{badge_max_chars}}个字",'
    '"highlights":["高亮词1","高亮词2"],'
    '"prompt":"封面排版和氛围说明"}'
)

COVER_PLAN_USER_PROMPT_PLACEHOLDERS: tuple[str, ...] = (
    "task_title",
    "transcript",
    "style_samples",
)

# 两个策划模板允许出现的占位符全集。比必需集合宽：字数上限这类值放 system 还是
# user 里都行，不强制位置。
COVER_PLAN_ALL_PLACEHOLDERS: tuple[str, ...] = (
    "safe_area",
    "task_title",
    "transcript",
    "style_samples",
    "title_max_chars",
    "subtitle_max_chars",
    "badge_max_chars",
    "highlight_count",
)

# 封面标题风格样本的默认值，一行一条。这是「行业适配」的实际开关 —— 样本写什么
# 调性模型就往哪边靠，比改 system 提示词直接得多。
COVER_STYLE_SAMPLES = "\n".join([
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

_PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")

# 阿里 IMS 内置中文字体（实测均生效）。名字写错**静默回落默认字体、不报错**，
# 所以前端给下拉而不是输入框，别让管理员手填。
SUBTITLE_FONT_OPTIONS: tuple[str, ...] = (
    "HappyZcool-2016",
    "Alibaba PuHuiTi",
    "Source Han Sans CN",
    "Source Han Serif CN",
    "FZHei-B01S",
    "FZFangSong-Z02S",
    "FZKai-Z03S",
    "FZShuSong-Z01S",
    "Microsoft YaHei",
    "Yuanti SC",
    "SimSun",
    "KaiTi",
    "WenQuanYi MicroHei",
    "WenQuanYi Zen Hei Mono",
    "WenQuanYi Zen Hei Sharp",
)

# 字幕字号上限。底部字幕是 BottomCenter + 距底 140px，两行字幕顶边 ≈ 1780 - 2×字号，
# 而装饰带（图形/氛围贴纸）底边最高到 1658（0.695×1920 + 324）。字号一过 61 就会
# 压到贴纸带上，封到 60 留 1px 余量。改这个值必须回头核对 layout.py 的槽位。
_SUBTITLE_FONT_SIZE_MAX = 60
_SUBTITLE_OUTLINE_MAX = 6

# 字幕样式在配置里的键。中性时间线把这几项原样带进 metadata，阿里侧再解析一次，
# 所以两边读的是同一份键名，别在中间层改名字。
SUBTITLE_STYLE_KEYS: tuple[str, ...] = (
    "subtitle_font",
    "subtitle_font_size",
    "subtitle_outline_width",
    "subtitle_bold",
)


def resolve_prompt_template(stored: str | None, default: str) -> str:
    """取生效的提示词模板：库里没存或存了空串就用内置默认。"""
    return stored if isinstance(stored, str) and stored.strip() else default


def render_prompt_template(template: str, values: dict[str, str]) -> str:
    """替换已知占位符，其余原样保留。

    不用 `str.format`：提示词里含 `{}`（JSON 示例），format 会 KeyError。
    """

    def _replace(match: re.Match[str]) -> str:
        return values.get(match.group(1), match.group(0))

    return _PLACEHOLDER_PATTERN.sub(_replace, template)


def check_prompt_template(
    template: str,
    required: tuple[str, ...],
    allowed: tuple[str, ...] | None = None,
) -> tuple[list[str], list[str]]:
    """返回 (缺失的必需占位符, 多余的未知占位符)，两者都为空才算合法。

    `allowed` 比 `required` 宽时，多出来的占位符可以出现但不必出现。
    """
    found = set(_PLACEHOLDER_PATTERN.findall(template))
    missing = [name for name in required if name not in found]
    unknown = sorted(found - set(allowed if allowed is not None else required))
    return missing, unknown


def resolve_style_samples(config: dict[str, Any]) -> str:
    """取生效的封面标题风格样本：库里没存或存了空串就用内置那十条。"""
    return resolve_prompt_template(config.get("cover_style_samples"), COVER_STYLE_SAMPLES)


def subtitle_style_snapshot(config: dict[str, Any]) -> dict[str, Any]:
    """把字幕样式相关的配置键摘出来，塞进中性时间线的 metadata。

    存的是**配置键**而不是解析后的值：阿里侧再解析一次，默认值只有
    `resolve_subtitle_style` 一处，中间层不做二次兜底。
    """
    return {key: config.get(key) for key in SUBTITLE_STYLE_KEYS}


def resolve_subtitle_style(config: dict[str, Any]) -> dict[str, Any]:
    """字幕样式解析成阿里侧能直接用的值，非法值一律回落内置默认。

    字体名不在清单里就回落 —— 阿里对写错的字体名是静默回落默认字体、不报错，
    拦不住，只能自己兜。字号和描边宽度做区间夹取。
    """
    font = str(config.get("subtitle_font") or "").strip()
    if font not in SUBTITLE_FONT_OPTIONS:
        font = str(DEFAULT_PROCESSING_CONFIG["subtitle_font"])
    font_size = _coerce_int(
        config.get("subtitle_font_size"), DEFAULT_PROCESSING_CONFIG["subtitle_font_size"]
    )
    outline_width = _coerce_int(
        config.get("subtitle_outline_width"),
        DEFAULT_PROCESSING_CONFIG["subtitle_outline_width"],
    )
    bold_raw = config.get("subtitle_bold")
    return {
        "font": font,
        "font_size": min(max(font_size, 24), _SUBTITLE_FONT_SIZE_MAX),
        "outline_width": min(max(outline_width, 0), _SUBTITLE_OUTLINE_MAX),
        "bold": bool(
            DEFAULT_PROCESSING_CONFIG["subtitle_bold"] if bold_raw is None else bold_raw
        ),
    }


def _coerce_int(value: Any, fallback: Any) -> int:
    """转 int，转不动就用兜底值。配置里可能是 null / 字符串 / 越界数字。"""
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(fallback)


def cover_plan_limits(config: dict[str, Any]) -> dict[str, int]:
    """封面策划四个数字上限：提示词占位符与落库硬截共用一份，避免两处走偏。

    返回 `<name>_max`（写进提示词）与 `<name>_guard`（落库前截断）。硬截取「配置
    上限」与兜底下限里的较大者 —— 模型偶尔超字数，按提示词上限直接截会切出半截词；
    兜底值按改造前写死的 24/24/6/2 定，所以默认 16/18/4/2 下行为逐字不变。
    """
    limits: dict[str, int] = {}
    for name, key, floor in (
        ("title", "cover_title_max_chars", 24),
        ("subtitle", "cover_subtitle_max_chars", 24),
        ("badge", "cover_badge_max_chars", 6),
        ("highlight", "cover_highlight_count", 2),
    ):
        try:
            value = int(config.get(key))
        except (TypeError, ValueError):
            value = int(DEFAULT_PROCESSING_CONFIG[key])
        value = max(value, 1)
        limits[f"{name}_max"] = value
        limits[f"{name}_guard"] = max(value, floor)
    return limits


def with_prompt_defaults(config: dict[str, Any]) -> dict[str, Any]:
    """附上内置默认值与只读清单，供高级设置当编辑起点。

    模板留空 = 跟随代码默认，所以库里存的可能是 null —— 光看 null 管理员不知道
    该写什么。把内置原文一起下发，前端铺进编辑框；提交时若与内置原文一致仍回传
    null，这样「没动过」的模板会继续跟着代码默认走，不会被冻结成一份副本。
    数字上限同理，`*_default` 就是前端判断「是否已自定义」的依据。
    """
    return {
        **config,
        "cover_prompt_template_default": COVER_IMAGE_PROMPT_TEMPLATE,
        "planner_prompt_template_default": PLANNER_SYSTEM_PROMPT_TEMPLATE,
        "cover_plan_prompt_template_default": COVER_PLAN_PROMPT_TEMPLATE,
        "cover_plan_user_prompt_template_default": COVER_PLAN_USER_PROMPT_TEMPLATE,
        "cover_style_samples_default": COVER_STYLE_SAMPLES,
        # 数字上限同样要下发默认值：前端据此把「没动过」的字段回传成 null，
        # 否则管理员点一次保存就把默认值冻结成副本，以后改代码默认不再跟随。
        "cover_title_max_chars_default": DEFAULT_PROCESSING_CONFIG["cover_title_max_chars"],
        "cover_subtitle_max_chars_default": DEFAULT_PROCESSING_CONFIG["cover_subtitle_max_chars"],
        "cover_badge_max_chars_default": DEFAULT_PROCESSING_CONFIG["cover_badge_max_chars"],
        "cover_highlight_count_default": DEFAULT_PROCESSING_CONFIG["cover_highlight_count"],
        "subtitle_font_default": DEFAULT_PROCESSING_CONFIG["subtitle_font"],
        "subtitle_font_size_default": DEFAULT_PROCESSING_CONFIG["subtitle_font_size"],
        "subtitle_outline_width_default": DEFAULT_PROCESSING_CONFIG["subtitle_outline_width"],
        "subtitle_bold_default": DEFAULT_PROCESSING_CONFIG["subtitle_bold"],
        # 字体下拉的候选来自后端：名字写错阿里是静默回落，不能让前端自己维护一份。
        "subtitle_font_options": list(SUBTITLE_FONT_OPTIONS),
    }


# 配置项与默认值。加新字段只改这里 + schema，不用动表结构。
DEFAULT_PROCESSING_CONFIG: dict[str, Any] = {
    # 封面生图通道。用户界面已不再暴露，只在管理员高级设置里切换。
    "cover_image_provider": settings.VIDEO_COVER_IMAGE_PROVIDER,
    "relay_image_model": settings.COVER_RELAY_IMAGE_MODEL,
    "relay_image_size": settings.COVER_RELAY_IMAGE_SIZE,
    "cover_summary_model": settings.VIDEO_COVER_SUMMARY_MODEL,
    "creative_planner_model": settings.VIDEO_CREATIVE_PLANNER_MODEL,
    # 提示词留空（None）表示用代码里的内置模板；只有被显式改过才落库。
    "cover_prompt_template": None,
    "planner_prompt_template": None,
    # 封面策划拆两段：system 管角色与调性，user 管输入与 JSON 契约。
    "cover_plan_prompt_template": None,
    "cover_plan_user_prompt_template": None,
    # 标题风格样本，一行一条。
    "cover_style_samples": None,
    # 策划阶段的字数上限。默认值与改造前写死在代码里的提示词文案一致。
    "cover_title_max_chars": 16,
    "cover_subtitle_max_chars": 18,
    "cover_badge_max_chars": 4,
    "cover_highlight_count": 2,
    # 底部字幕样式。字号上限受装饰带几何约束，见 _SUBTITLE_FONT_SIZE_MAX。
    "subtitle_font": "HappyZcool-2016",
    "subtitle_font_size": 56,
    "subtitle_outline_width": 2,
    "subtitle_bold": True,
    "version": 1,
}


def merge_processing_config(stored: dict[str, Any] | None) -> dict[str, Any]:
    """把库里的值合并到默认值之上。

    `None` 视为「跟随默认」，所以清空某个字段 = 恢复默认，不需要额外接口。
    """
    merged = dict(DEFAULT_PROCESSING_CONFIG)
    for key, value in (stored or {}).items():
        if key in merged and value is not None:
            merged[key] = value
    return merged


async def read_processing_config(db: AsyncSession) -> dict[str, Any]:
    """在给定会话里读配置，附上更新人与更新时间。"""
    row = (
        await db.execute(
            select(VideoProcessingConfigModel).where(
                VideoProcessingConfigModel.id == CONFIG_ROW_ID
            )
        )
    ).scalars().first()
    merged = merge_processing_config(row.config if row is not None else None)
    merged["updated_time"] = row.updated_time if row is not None else None
    merged["updated_by"] = await _resolve_username(db, row.updated_id if row is not None else None)
    return merged


async def load_processing_config() -> dict[str, Any]:
    """自带会话读配置，供 worker 链路（封面、创意规划）调用。"""
    async with async_db_session() as db:
        return await read_processing_config(db)


async def save_processing_config(
    db: AsyncSession,
    payload: dict[str, Any],
    user_id: int | None,
) -> dict[str, Any]:
    """合并写入配置并递增版本号。

    只覆盖 payload 里显式给出的键：`None` 会落库成 null，读取时回落默认值，
    这就是「恢复默认」的实现方式。
    """
    row = (
        await db.execute(
            select(VideoProcessingConfigModel).where(
                VideoProcessingConfigModel.id == CONFIG_ROW_ID
            )
        )
    ).scalars().first()

    stored = dict(row.config) if row is not None and isinstance(row.config, dict) else {}
    stored.update(payload)
    # 每次保存都递增版本，任务落库时记录用的是哪一版，事后能对上。
    stored["version"] = int(stored.get("version") or 1) + 1

    if row is None:
        db.add(
            VideoProcessingConfigModel(
                id=CONFIG_ROW_ID,
                config=stored,
                updated_id=user_id,
            )
        )
    else:
        row.config = dict(stored)
        row.updated_id = user_id
    await db.flush()
    return await read_processing_config(db)


async def _resolve_username(db: AsyncSession, user_id: int | None) -> str | None:
    """只取用户名一个字段，避免把 UserModel 的关系一起拉出来。"""
    if not user_id:
        return None
    return await db.scalar(select(UserModel.username).where(UserModel.id == user_id))
