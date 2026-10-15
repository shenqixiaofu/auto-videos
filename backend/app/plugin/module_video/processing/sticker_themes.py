from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from typing import Any

from app.core.exceptions import CustomException
from app.core.logger import log


@dataclass(frozen=True, slots=True)
class StickerEffectLayer:
    """贴纸花字的一层描边或阴影。

    `XBord/YBord/XShift/YShift` 取 0~1 小数时按 FontSize 相对缩放，换字号后观感一致。
    """

    kind: str
    color: str
    x_bord: float
    y_bord: float
    blur: float = 0.0
    x_shift: float = 0.0
    y_shift: float = 0.0
    opacity: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        """序列化为阿里 SubtitleEffects 的一层。"""
        return {
            "Type": self.kind,
            "Color": self.color,
            "Blur": self.blur,
            "XBord": self.x_bord,
            "YBord": self.y_bord,
            "XShift": self.x_shift,
            "YShift": self.y_shift,
            "Opacity": self.opacity,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> StickerEffectLayer:
        """从时间线资产的样式字典还原一层效果。"""
        return cls(
            kind=str(payload["Type"]),
            color=str(payload["Color"]),
            x_bord=float(payload["XBord"]),
            y_bord=float(payload["YBord"]),
            blur=float(payload.get("Blur") or 0.0),
            x_shift=float(payload.get("XShift") or 0.0),
            y_shift=float(payload.get("YShift") or 0.0),
            opacity=float(payload.get("Opacity") or 1.0),
        )


# 阿里内置字体里挑的「不显老」一批，逐主题错开，避免 8 套主题只换色值。
# 字体名必须与官方字体列表逐字一致，写错会静默回落到默认字体。
DEFAULT_STICKER_FONT = "HappyZcool-2016"

# 官方花字（EffectColorStyle）白名单，逐个对着官方预览图挑过：
#   https://help.aliyun.com/zh/ims/developer-reference/flower-effect-example
# 只看「浅底 + 粗描边」这一档 —— 白/亮色字身 + 饱和色厚描边，缩到 58pt 也还认得出。
# **别用「淡彩渐变字身 + 细描边」那一档**（CS0001 大部分、CS0005/CS0007~CS0010 几乎全部）：
# 官方预览里就已经糊在白底上，投到真实画面基本看不清，之前 cobalt_spark 用的
# CS0001-000001 就是这一类。CS0003 系列是白底 + 纯色厚描边，CS0006 系列是饱和渐变字身，
# 这两族里挑出来的下面这几个才进白名单。
_WORD_ART_WHITELIST = (
    "CS0003-000001",  # 白底 + 暗红描边
    "CS0003-000008",  # 白底 + 蓝描边
    "CS0003-000013",  # 白底 + 青绿描边
    "CS0006-000001",  # 白底 + 蓝描边
    "CS0006-000005",  # 暖黄渐变字身 + 橙描边
)


@dataclass(frozen=True, slots=True)
class StickerThemeStyle:
    """单个贴纸模板的视觉样式。

    只保留真正会下发到阿里 Timeline 的字段：字体、字色、透明度和 SubtitleEffects 多层描边。
    历史字段（背景色、圆角、气泡模板）没有消费方，留着只会让人误以为可调。
    """

    font_size: int
    font_color: str
    opacity: str
    effects: tuple[StickerEffectLayer, ...]
    # 末位带默认值：历史任务的 visual_style 里没有这个键，重放时要能兜底。
    font: str = DEFAULT_STICKER_FONT
    # 官方花字预设（EffectColorStyle）。设了就下发预设花字，并且**不再**下发自绘三层
    # 描边 —— 官方花字自带描边，两层叠起来是描边套描边，发脏。取值只能在
    # _WORD_ART_WHITELIST 里挑，白名单外的会被 style_for_template 丢掉。
    word_art_style: str | None = None

    def to_dict(self) -> dict[str, object]:
        """序列化为可写入时间线资产的样式字典。"""
        return {
            "font": self.font,
            "font_size": self.font_size,
            "font_color": self.font_color,
            "opacity": self.opacity,
            "effects": [layer.to_dict() for layer in self.effects],
            "word_art_style": self.word_art_style,
        }


def sticker_effects(
    *,
    deep: str,
    ring: str,
    glow: str,
) -> tuple[StickerEffectLayer, ...]:
    """构造「发光 + 深色压边 + 亮色内圈」三层描边。

    单层 Outline 在复杂背景上几乎看不见，多层堆叠才有花字的体积感。
    数组越靠前越在底层，底层 Bord 必须更大，否则会被上层完全遮住。
    """
    return (
        StickerEffectLayer(kind="Shadow", color=glow, x_bord=0.13, y_bord=0.13, blur=0.24),
        StickerEffectLayer(kind="Outline", color=deep, x_bord=0.10, y_bord=0.10),
        StickerEffectLayer(kind="Outline", color=ring, x_bord=0.045, y_bord=0.045),
    )


@dataclass(frozen=True, slots=True)
class StickerTheme:
    """一组口播视频贴纸主题。

    `font` / `word_art_style` 挂在主题上而不是单个模板上：同一任务内所有贴纸共用
    一套字体与花字口径，主题之间才靠字体 + 配色 + 花字一起区分。
    """

    id: str
    label: str
    font: str
    opinion_card: StickerThemeStyle
    micro_sticker: StickerThemeStyle
    highlight_box: StickerThemeStyle
    # 官方花字预设，取值见 _WORD_ART_WHITELIST；None 表示这套主题走自绘三层描边。
    word_art_style: str | None = None

    def style_for_template(self, template_id: str) -> StickerThemeStyle:
        """按贴纸模板读取对应的视觉样式，并把主题字体与花字预设注入进去。"""
        style = {
            "opinion_card": self.opinion_card,
            "micro_sticker": self.micro_sticker,
            "highlight_box": self.highlight_box,
        }.get(template_id)
        if style is None:
            raise CustomException(msg=f"未知贴纸模板: {template_id}")
        word_art = self.word_art_style
        if word_art is not None and word_art not in _WORD_ART_WHITELIST:
            # 白名单外一律不发官方花字，回落到自绘三层描边。发一个没挑过的 id
            # 要么是淡彩细描边那种糊字，要么 id 写错被阿里静默回落，两种都很难查。
            log.warning(f"官方花字不在白名单内，已回落到自绘描边: theme={self.id}, id={word_art}")
            word_art = None
        return replace(style, font=self.font, word_art_style=word_art)


@dataclass(frozen=True, slots=True)
class StickerMotionVariant:
    """单个贴纸的入场/出场/动效组合。"""

    id: str
    motion_in: str
    motion_out: str
    motion_effect: str | None = None


_THEME_POOL: tuple[StickerTheme, ...] = (
    StickerTheme(
        id="citrus_pop",
        label="Citrus Pop",
        font="HappyZcool-2016",
        opinion_card=StickerThemeStyle(
            font_size=54,
            font_color="#FFE066",
            opacity="0.94",
            effects=sticker_effects(deep="#3B2408", ring="#FFF6D6", glow="#FFB703"),
        ),
        micro_sticker=StickerThemeStyle(
            font_size=36,
            font_color="#FFD452",
            opacity="0.96",
            effects=sticker_effects(deep="#3B2408", ring="#FFF6D6", glow="#FFB703"),
        ),
        highlight_box=StickerThemeStyle(
            font_size=46,
            font_color="#FFFFFF",
            opacity="0.9",
            effects=sticker_effects(deep="#3B2408", ring="#FFB703", glow="#FFB703"),
        ),
        word_art_style="CS0006-000005",
    ),
    StickerTheme(
        id="mint_lift",
        label="Mint Lift",
        font="Alibaba PuHuiTi",
        opinion_card=StickerThemeStyle(
            font_size=54,
            font_color="#6EE7B7",
            opacity="0.94",
            effects=sticker_effects(deep="#04372A", ring="#E6FFF6", glow="#34D399"),
        ),
        micro_sticker=StickerThemeStyle(
            font_size=36,
            font_color="#6EE7B7",
            opacity="0.94",
            effects=sticker_effects(deep="#04372A", ring="#E6FFF6", glow="#34D399"),
        ),
        highlight_box=StickerThemeStyle(
            font_size=46,
            font_color="#FFFFFF",
            opacity="0.9",
            effects=sticker_effects(deep="#04372A", ring="#34D399", glow="#34D399"),
        ),
        word_art_style="CS0003-000013",
    ),
    StickerTheme(
        id="peach_energy",
        label="Peach Energy",
        font="Yuanti SC",
        opinion_card=StickerThemeStyle(
            font_size=54,
            font_color="#FFB3A7",
            opacity="0.95",
            effects=sticker_effects(deep="#4A1512", ring="#FFEDE8", glow="#FB7185"),
        ),
        micro_sticker=StickerThemeStyle(
            font_size=36,
            font_color="#FFB3A7",
            opacity="0.94",
            effects=sticker_effects(deep="#4A1512", ring="#FFEDE8", glow="#FB7185"),
        ),
        highlight_box=StickerThemeStyle(
            font_size=46,
            font_color="#FFFFFF",
            opacity="0.9",
            effects=sticker_effects(deep="#4A1512", ring="#FB7185", glow="#FB7185"),
        ),
    ),
    StickerTheme(
        id="cobalt_spark",
        label="Cobalt Spark",
        font="Source Han Sans CN",
        opinion_card=StickerThemeStyle(
            font_size=56,
            font_color="#9DC4FF",
            opacity="0.93",
            effects=sticker_effects(deep="#10264D", ring="#EAF2FF", glow="#60A5FA"),
        ),
        micro_sticker=StickerThemeStyle(
            font_size=35,
            font_color="#9DC4FF",
            opacity="0.96",
            effects=sticker_effects(deep="#10264D", ring="#EAF2FF", glow="#60A5FA"),
        ),
        highlight_box=StickerThemeStyle(
            font_size=46,
            font_color="#FFFFFF",
            opacity="0.9",
            effects=sticker_effects(deep="#10264D", ring="#60A5FA", glow="#60A5FA"),
        ),
        word_art_style="CS0006-000001",
    ),
    StickerTheme(
        id="cream_marker",
        label="Cream Marker",
        font="FZKai-Z03S",
        opinion_card=StickerThemeStyle(
            font_size=54,
            font_color="#FFF0B8",
            opacity="0.95",
            effects=sticker_effects(deep="#3D2E1B", ring="#FFFDF0", glow="#FCD34D"),
        ),
        micro_sticker=StickerThemeStyle(
            font_size=35,
            font_color="#FFF0B8",
            opacity="0.95",
            effects=sticker_effects(deep="#3D2E1B", ring="#FFFDF0", glow="#FCD34D"),
        ),
        highlight_box=StickerThemeStyle(
            font_size=46,
            font_color="#FFFFFF",
            opacity="0.92",
            effects=sticker_effects(deep="#3D2E1B", ring="#FCD34D", glow="#FCD34D"),
        ),
    ),
    StickerTheme(
        id="electric_punch",
        label="Electric Punch",
        font="FZHei-B01S",
        opinion_card=StickerThemeStyle(
            font_size=56,
            font_color="#F5B8FF",
            opacity="0.92",
            effects=sticker_effects(deep="#3B0A45", ring="#FDEBFF", glow="#E879F9"),
        ),
        micro_sticker=StickerThemeStyle(
            font_size=36,
            font_color="#F5B8FF",
            opacity="0.95",
            effects=sticker_effects(deep="#3B0A45", ring="#FDEBFF", glow="#E879F9"),
        ),
        highlight_box=StickerThemeStyle(
            font_size=46,
            font_color="#FFFFFF",
            opacity="0.9",
            effects=sticker_effects(deep="#3B0A45", ring="#E879F9", glow="#E879F9"),
        ),
    ),
    StickerTheme(
        id="sunset_flash",
        label="Sunset Flash",
        font="Source Han Serif CN",
        opinion_card=StickerThemeStyle(
            font_size=55,
            font_color="#FFC98B",
            opacity="0.95",
            effects=sticker_effects(deep="#4A1D07", ring="#FFF3E4", glow="#FB923C"),
        ),
        micro_sticker=StickerThemeStyle(
            font_size=36,
            font_color="#FFC98B",
            opacity="0.95",
            effects=sticker_effects(deep="#4A1D07", ring="#FFF3E4", glow="#FB923C"),
        ),
        highlight_box=StickerThemeStyle(
            font_size=46,
            font_color="#FFFFFF",
            opacity="0.9",
            effects=sticker_effects(deep="#4A1D07", ring="#FB923C", glow="#FB923C"),
        ),
        word_art_style="CS0003-000001",
    ),
    StickerTheme(
        id="neon_night",
        label="Neon Night",
        font="WenQuanYi Zen Hei Sharp",
        opinion_card=StickerThemeStyle(
            font_size=54,
            font_color="#8BE0FF",
            opacity="0.9",
            effects=sticker_effects(deep="#0B2E42", ring="#E6F9FF", glow="#22D3EE"),
        ),
        micro_sticker=StickerThemeStyle(
            font_size=35,
            font_color="#8BE0FF",
            opacity="0.95",
            effects=sticker_effects(deep="#0B2E42", ring="#E6F9FF", glow="#22D3EE"),
        ),
        highlight_box=StickerThemeStyle(
            font_size=46,
            font_color="#FFFFFF",
            opacity="0.9",
            effects=sticker_effects(deep="#0B2E42", ring="#22D3EE", glow="#22D3EE"),
        ),
    ),
)

# 剪辑风格 -> 精选主题 id。抽哪一套仍只看 seed，所以同风格成片有统一调性、
# 又不会每条都一样。
#
# vlog 刻意不入表：它是默认风格，走 _THEME_POOL 全池回落，主题选取与改造前逐字一致。
# 别把 vlog 也塞进来 —— 内网产品只跑 vlog，一收窄就会静默换掉现有成片的贴纸风格。
# 主题 id 写错会在 import 时就 KeyError，别改成 `get` 静默跳过。
_STYLE_THEME_IDS: dict[str, tuple[str, ...]] = {
    # 旅行记录：天空蓝 / 日落橙 / 夜景青 / 薄荷
    "travel": ("cobalt_spark", "sunset_flash", "neon_night", "mint_lift"),
    # 美食探店：暖色为主，加一套高饱和撞色
    "food": ("citrus_pop", "sunset_flash", "peach_energy", "electric_punch"),
    # 清爽简约：低饱和冷色
    "clean": ("mint_lift", "cobalt_spark", "neon_night"),
}

_THEME_BY_ID: dict[str, StickerTheme] = {theme.id: theme for theme in _THEME_POOL}
_STYLE_THEME_POOLS: dict[str, tuple[StickerTheme, ...]] = {
    style: tuple(_THEME_BY_ID[theme_id] for theme_id in theme_ids)
    for style, theme_ids in _STYLE_THEME_IDS.items()
}

_MOTION_VARIANTS: dict[str, tuple[StickerMotionVariant, ...]] = {
    "opinion_card": (
        StickerMotionVariant("card_fade_pop", "dissolve_in", "dissolve_out", "soft_pop"),
        StickerMotionVariant("card_lift", "wipe_up_in", "dissolve_out", "slide_up"),
        StickerMotionVariant("card_wipe", "wipe_up_in", "fade_out"),
        StickerMotionVariant("card_zoom", "zoomin_i", "dissolve_out", "subtle_zoom"),
    ),
    "micro_sticker": (
        StickerMotionVariant("chip_pop", "zoomin_i", "fade_out", "soft_pop"),
        StickerMotionVariant("chip_spring", "dissolve_in", "dissolve_out", "soft_pop"),
        StickerMotionVariant("chip_swipe", "wipe_up_in", "fade_out"),
        StickerMotionVariant("chip_zoom", "zoomin_i", "dissolve_out", "subtle_zoom"),
    ),
    "highlight_box": (
        StickerMotionVariant("box_focus", "dissolve_in", "dissolve_out", "subtle_zoom"),
        StickerMotionVariant("box_lift", "wipe_up_in", "dissolve_out", "slide_up"),
        StickerMotionVariant("box_wipe", "wipe_up_in", "fade_out"),
        StickerMotionVariant("box_zoom", "zoomin_i", "fade_out", "soft_pop"),
    ),
}


def pick_sticker_theme(seed: str, style_preset: str | None = None) -> StickerTheme:
    """按任务种子在风格对应的主题池里稳定抽一套贴纸主题。

    风格只决定**候选池**，具体抽哪一套仍然只看 seed —— 所以同一任务重跑结果不变，
    可重放性没变。风格缺省或不在表里（老任务 config 里可能没有 style_preset）时
    回落到全池，行为与改造前一致。
    """
    pool = _STYLE_THEME_POOLS.get(style_preset or "") or _THEME_POOL
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()
    return pool[int(digest[:8], 16) % len(pool)]


def pick_sticker_motion(
    seed: str,
    template_id: str,
    event_id: str,
) -> StickerMotionVariant:
    """按任务种子和事件 ID 稳定抽取动画组合。"""
    variants = _MOTION_VARIANTS.get(template_id)
    if not variants:
        raise CustomException(msg=f"未知贴纸模板动画池: {template_id}")
    digest = hashlib.sha1(f"{seed}:{template_id}:{event_id}".encode()).hexdigest()
    return variants[int(digest[:8], 16) % len(variants)]
