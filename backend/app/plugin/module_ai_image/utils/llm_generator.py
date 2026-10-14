from datetime import datetime
import os
import uuid
import aiohttp
import asyncio
import base64
import hashlib
import io
import json
import random
from typing import Dict, Any
from fastapi import HTTPException, UploadFile
import httpx
from openai import AsyncOpenAI, APIError, APIStatusError
from app.core.exceptions import CustomException
from loguru import logger
from app.config.setting import settings
from app.plugin.module_ai_image.utils.image_utils import ImageUtil
from app.utils.upload_util import UploadUtil
from app.plugin.module_ai_image.utils.themes import (
    GENDER_PORTRAIT_CONFIG,
)
from app.api.v1.module_system.auth.schema import AuthSchema
from app.plugin.module_ai_image.style_theme.schema import AiStyleThemeQueryParam
from app.plugin.module_ai_image.style_theme.service import AiStyleThemeService


class LLMActionEngine:
    """
    AI 摄影策划引擎 - 升级版：黄金模板执行器
    """

    VISUAL_PROMPT_TEMPLATE_CACHE_TTL_SECONDS = 24 * 60 * 60
    VISUAL_PROMPT_TEMPLATE_CACHE_MAX_ITEMS = 256
    _visual_prompt_template_cache: dict[str, dict[str, Any]] = {}
    _visual_prompt_template_inflight: dict[str, asyncio.Future] = {}

    def __init__(self):
        openai_client_kwargs = {"api_key": settings.OPENAI_API_KEY}
        if settings.OPENAI_BASE_URL:
            openai_client_kwargs["base_url"] = settings.OPENAI_BASE_URL

        self.openai_client = AsyncOpenAI(**openai_client_kwargs)
        self.openai_image_model = settings.OPENAI_MODEL or "gpt-image-2"
        self.client = AsyncOpenAI(
            api_key=settings.DOUBAO_API_KEY, base_url=settings.DOUBAO_API_URL
        )
        self.lz_client = AsyncOpenAI(
            api_key=settings.LZ_API_KEY, base_url=settings.LZ_API_URL
        )
        self.gpt5_client = AsyncOpenAI(**openai_client_kwargs)
        self.model = (
            "doubao-seed-2-0-pro-260215"  # 推荐使用 4o 或 Claude 3.5 以精准遵循复杂指令
        )

        self.ark_client = AsyncOpenAI(
            api_key=settings.DOUBAO_API_KEY, base_url=settings.DOUBAO_API_URL
        )

        self.qwen_client = AsyncOpenAI(
            api_key=settings.QWEN_API_KEY,
            base_url=settings.QWEN_API_URL,
        )

    @classmethod
    def _get_cached_visual_prompt_template(cls, image_hash: str) -> str | None:
        cached = cls._visual_prompt_template_cache.get(image_hash)
        if not cached:
            logger.info(
                "🧩 视觉模板缓存未命中 | pid={} | hash={} | cache_size={}",
                os.getpid(),
                image_hash[:16],
                len(cls._visual_prompt_template_cache),
            )
            return None

        now_ts = datetime.now().timestamp()
        if now_ts - cached["created_at"] > cls.VISUAL_PROMPT_TEMPLATE_CACHE_TTL_SECONDS:
            cls._visual_prompt_template_cache.pop(image_hash, None)
            logger.info(
                "⌛ 视觉模板缓存已过期 | pid={} | hash={} | cache_size={}",
                os.getpid(),
                image_hash[:16],
                len(cls._visual_prompt_template_cache),
            )
            return None

        cached["last_accessed_at"] = now_ts
        logger.info(
            "🎯 视觉模板缓存命中 | pid={} | hash={} | cache_size={}",
            os.getpid(),
            image_hash[:16],
            len(cls._visual_prompt_template_cache),
        )
        return cached["content"]

    @classmethod
    def _set_cached_visual_prompt_template(
        cls, image_hash: str, content: str
    ) -> None:
        now_ts = datetime.now().timestamp()
        cls._visual_prompt_template_cache[image_hash] = {
            "content": content,
            "created_at": now_ts,
            "last_accessed_at": now_ts,
        }
        logger.info(
            "💾 写入视觉模板缓存 | pid={} | hash={} | content_length={} | cache_size={}",
            os.getpid(),
            image_hash[:16],
            len(content),
            len(cls._visual_prompt_template_cache),
        )

        if len(cls._visual_prompt_template_cache) <= cls.VISUAL_PROMPT_TEMPLATE_CACHE_MAX_ITEMS:
            return

        oldest_key = min(
            cls._visual_prompt_template_cache,
            key=lambda key: cls._visual_prompt_template_cache[key]["last_accessed_at"],
        )
        cls._visual_prompt_template_cache.pop(oldest_key, None)
        logger.info(
            "🧹 视觉模板缓存触发淘汰 | pid={} | evicted_hash={} | cache_size={}",
            os.getpid(),
            oldest_key[:16],
            len(cls._visual_prompt_template_cache),
        )

    async def run_fission_pipeline(
        self,
        auth: AuthSchema,
        location: str,
        gender: str,
        age: int,
        extra_command: str = None,
        current_theme: dict = None,
        theme_ids: list[int] = None,
    ) -> Dict[str, Any]:
        # 1. 定义黄金模板（作为 LLM 的参考背景，不让它直接填充）
        # 建议将所有现代风和年代感风合并，古风独立
        # 在调用函数内部随机选择一个
        if current_theme is None:
            # 映射数据库性别标签

            # 🚀 核心逻辑变更：
            # 如果指定了 theme_ids，则忽略性别在大池子里的搜索，只查这几个 ID
            # 如果没有 theme_ids，则按性别查大池子
            search = AiStyleThemeQueryParam(gender=gender, status=0)

            # 如果 Service 里的 CRUD 支持 ids 过滤，直接传进去
            # 如果不支持，我们可以拿到 list 后在 Python 层过滤
            result_dict = await AiStyleThemeService.page_style_theme_service(
                auth=auth, page_no=1, page_size=1000, search=search
            )

            themes = result_dict.get("items", [])

            # 🚀 如果传了 theme_ids，从查出的结果里二次过滤出这几个 ID 的数据
            if theme_ids:
                themes = [t for t in themes if t.get("id") in theme_ids]

            if themes:
                target = random.choice(themes)
                current_theme = {
                    "theme": target.get("theme_name"),
                    "material": target.get("material"),
                    "clothing_style": target.get("clothing_style"),
                    "colors": target.get("colors"),
                    "vibe": target.get("vibe"),
                }
        golden_template = (
            "写实摄影风格，{style}，{lighting_detail}。主场景位于{scene_detail}。"
            "一位{age}岁中国汉族面孔{gender}。{face_description}。"
            "眼神自然清澈，灵动有神。眼波流转，眼底眼神光温润而不刺眼。"
            "虹膜纹理自然呈现，深邃且富有层次感。睫毛浓密清晰，不突变。"
            "{hairstyle}。身着{clothing}。{action}，{view}。"
            "画面呈现极致的真实质感，{skin_texture}，{atmosphere_detail}，8k超高清分辨率。"  # 👈 动态环境氛围
            "相机参数：Canon EOS R5, 50mm f/1.2, 1/250s, ISO 400，比例9：16。"
        )
        print(f"🚀 性别：{gender}")
        selected_portrait = GENDER_PORTRAIT_CONFIG.get(gender)

        # 构造 System Prompt 的描述块
        # 这样 LLM 就不需要自己思考，只需把这段话根据场景微调或直接复用即可
        people_directive = f"""
                - **身材体态 (body_height)**：{selected_portrait['height']}
                - **面部骨相 (facial_feature)**：{selected_portrait['facial_feature']}
                - **面部神韵 (face_description)**：{selected_portrait['face']}
                - **皮肤质感 (skin_texture)**：{selected_portrait['skin']}
        """
        if extra_command and extra_command.strip():
            # 存在附加指令：直接覆盖原有的场景逻辑，强制执行导演特殊定制
            scene_section = f"""
        1. 【场景深度解构 (scene_detail) - 🚨 导演特别定制场景 (强制执行)】：
            - 导演最高优指令：必须彻底摒弃常规的地点认知，严格根据以下附加要求进行场景重构：
            【 {extra_command.strip()} 】
            - 场景描述必须具备极强的画面感、物理材质与微观细节。拒绝空泛废话，必须写出能被镜头捕捉到的具体物件与质感。
            """
        else:
            # 不存在附加指令：走默认的基于 location 的高级地理特征挖掘逻辑
            scene_section = f"""
        1. 【场景深度解构 (scene_detail) - 拒绝悬浮感与打卡照】：
            - 导演指令：必须对“{location}”进行真实的地理风貌与物理材质解构。严禁使用通用废话（如“风景如画、美丽的地方”），必须聚焦于【微观材质与物理特征】。
            - 🚨 绝对黑名单：无论地点在哪，严禁无脑输出“苔藓、露珠、桃花、油纸伞”这类泛滥的古风元素，除非该地质极度吻合。
            
            - 必须从以下三个维度提取该地点的特征进行组合，确保画面具有顶级时尚杂志的“高定感”与“电影级质感”：
            - 维度 A [高级感背景与地表肌理 (High-end Textures)]：
                - 古典与沉淀：带有哑光光泽的青石板阶梯、微泛金光的斑驳暗墙、带有古典雕花的深色木质结构、铺满金黄落叶的静谧小径。
                - 旷野与自然：极具雕塑感的天然岩壁肌理、风吹过带有律动感的草海/芦苇荡、波光粼粼的水面高光反射、冷峻利落的冰雪边缘。
                - 现代与极简：极简主义的清水混凝土墙面、被光影锐利切割的几何建筑边缘、高透光的玻璃折射、带有高级丝绒质感的暗调背景。

            - 维度 B [唯美微观风物 (Cinematic Micro-Elements)] (必须具体，能被镜头捕捉并提升画面仙气/氛围的元素)：
                - 光影与流体：丁达尔光柱中清晰跃动的细腻微尘、叶片尖端清透的露珠折射（克制使用）、水面泛起的柔和涟漪、随风翻滚的云隙光。
                - 动态与生命：随风扬起的轻柔纱幔/布料边缘、光影在植物枝叶上打出的利落剪影、被风卷起的几片落叶或飞花。
                - 质感点缀：精致且带有复古光泽的黄铜门环、栏杆上残留的细微冰晶、阳光下散发光泽的钢琴烤漆面或高级皮质纹理。
            """

        # 2. 构造 System Prompt
        # 注意：这里我们明确告知 LLM 它的角色是“素材提供方”
        system_prompt = f"""
        # 角色
        你是一位深耕中国传统美学、精通全球地理特征与顶级写实摄影的视觉导演。你擅长避开“游客打卡照”的平庸感，通过微观视角和电影级光影，挖掘“{location}”不为人知的高级美。

        # 核心参考模板
        生成的变量将嵌入此黄金架构："{golden_template}"

        # 导演策划流程
        {scene_section}


        2. 【光影与氛围 (atmosphere_detail) - 极致空气感构建】：
            - 导演指令：必须结合你输出的场景的地理海拔与气候，从以下三个维度进行【组合混编】，写出能让人“闻到空气味道”的细腻描述。严禁干瘪的词汇。
            
            - 维度 A [气候与颗粒感]：
                - 极度干燥/大漠：炽热扭曲的空气、粗粝的沙尘悬浮、风化质感、高反差的明暗切割。
                - 尘埃悬浮/复古：老电影般的颗粒感（Film Grain）、丁达尔光柱中清晰跃动的细腻微尘。
                - 潮湿氤氲/江南：黏腻的湿润空气、镜头边缘微弱的水汽凝结、被雾气柔化和散射的漫反射光。
                - 凛冽清透/高海拔：如同玻璃般透明的冷空气、极高的能见度与锐度、呼吸可见的微小冰晶感。

            - 维度 B [时间与色温] (必须明确指定一种时间段)：
                - 破晓薄雾：冷暖交织，清冷蓝调的环境光夹杂着一丝初升太阳的暖金。
                - 黄金时刻 (Golden Hour)：浓郁的琥珀色/橘红色夕阳、极长的拖影、温暖包裹的电影感色调。
                - 蓝调时刻 (Blue Hour)：太阳落山后深邃的克莱因蓝、静谧无声、带有路灯/冷光源的冷暖对比。
                - 阴雨/冷灰：无直射光，阴天特有的低反差漫射柔光，极其平缓的阴影，呈现高级的低饱和度。

            - 维度 C [光影形态]：
                - 斑驳碎光：穿过树叶或建筑缝隙的细碎光斑，在人物脸上或衣服上形成摇曳的明暗纹理。
                - 极致轮廓 (Rim Light)：强烈的侧逆光，在发丝和衣物边缘勾勒出闪亮的金色/银色光晕，将人物从背景中立体剥离。
                - 局部顶光：一束神圣的顶光穿透幽暗空间（如溶洞、密林）直射而下，四周陷入深邃的暗调。

        3. 【定向人物画像 (核心)】：（{age}岁）与性别（{gender}）：
           {people_directive}
           - 🚨 拒绝千篇一律的AI网红脸！必须明确定义人物的【骨相与脸型】（如：清冷的骨感菱形脸、温婉的鹅蛋脸、带点原生质感的方圆脸、下颌线清晰的高级脸等），
           结合年龄赋予人物真实的故事感。
           - 🚨 肤色防爆红死命令：无论是男孩还是女孩，严禁在描述中使用“红晕”、“粉晕”、“高原红”、“腮红”等词汇，无论什么场景面部和头发都不能有潮湿感
           。必须强调“肤色均匀”、“清爽干净”、“自然健康的哑光质感”。
           - 🚨 拒绝 带有汗毛等关键字， 生图工作流会以为有出汗的感觉
        4. 【极致光影设计】：匹配一种能增强画面深度的写实光影。
           - 方案：(如：侧逆光勾勒的轮廓线、穿过竹林的丁达尔效应、蓝调时刻的清冷寂静)。注意这里只是示例，你需要根据给出的地点来构思出与之匹配的方案
           - 🚨 防爆白补丁：必须包含“环境散落光”或“斑驳影纹”，严禁强光直射面部，追求温润的阴影过渡。

        5. 【🧥 本组服饰套系锁定（🚨核心修复衣品）】：
        - **本组风格锚点**：【{current_theme['theme']}】
        - **指定主材质**：【{current_theme['material']}】
        - **指定款式与色系**：【{current_theme['clothing_style']}】，配色方案选用【{current_theme['colors']}】。
        
        - **导演要求**：
            - **高度统一性**：本组 15 张图中的模特必须穿着【完全相同】的这一套衣服，严禁改变材质和基本款式。
            - **高级感约束**：色彩搭配必须符合摄影美学（同色系或经典对比色），严禁出现高饱和度亮色乱搭。强调【{current_theme['vibe']}】。
        6. 【🚨 情绪、镜头与动作裂变 (拒绝AI假笑)】：策划 15 个具有叙事感的动作。
           - 情绪死命令：严禁所有动作都是“微笑”！必须在动作中融合不同的【自然微表情】（如：清冷疏离、微微蹙眉、嘴唇微抿、专注出神、慵懒随性、闭眼感受风等），配合前面设定的脸型彻底消除假笑的诡异感。
           - 严格分配景别为了后续换脸，尽量都是正面形象或者微侧20度左右即可（view_type）：
            - **【站立全身组】(5个动作)**：
                - **强制要求**：view_type 必须为“全景”。
                - **构图命令**：必须明确描述【露出完整的双脚必须要穿着鞋子】和【全身线条】，严禁出现蹲姿、坐姿或膝盖以上的裁剪 
                    根据当前场景可以上拿一些东西,小饰品比如将军则是拿武器，古风拿折扇,女生拿圆扇，根据当前场景自由发挥但是并不需要每一张都拿）。
                    展现“{location}”的宏大氛围与环境深度。
            - **【互动中景组】(7个动作)**：
                - **要求**：view_type 为“中景”。
                - **逻辑**：允许弯腰或半身互动（如：指尖碰水、拂过芦苇、低头看花）。
                - **重点**：强调人物与环境的局部交互。
                
            - **【情绪特写组】(3个动作)**：
                - **要求**：view_type 为“特写”。
                - **重点**：专注于面部神韵、别发簪、整理领口等微小动作，充分展现你策划的皮肤质感。

        # 任务要求
        1. 🚨 **全中文输出**：严禁出现英文描述。
        2. **禁止拼装**：只需输出 JSON 变量，严禁在 JSON 中返回拼好的 prompt。
        3. **画质加持**：在描述环境和光影时，多用“晶莹、锐利、丝丝入扣、通透”等能暗示高画质的词。

        # ⚠️ 输出格式 (严格遵循以下 JSON 结构)
        {{
            "selected_scene": "场景简练名称（如：烟雨石阶）",
            "scene_detail": "细腻的场景细节描述（强调前中后景与材质）", 
            "selected_style": "光影风格名称",
            "lighting_detail": "具体的光效细节描述（必须包含斑驳感与温润过渡）",
            "face_description": "针对{age}岁定制的面部神韵描述",
            "skin_texture": "针对{age}岁定制的皮肤质感描述",
            "hairstyle": "发型与发饰的精细描述",
            "clothing": "针对【{current_theme['material']}】的细节描写（必须体现面料纹理与光泽）",
            "actions": [
                {{ "desc": "具体动作描述", "view_type": "特写/中景/全景" }}
            ]
        }}
        """
        if extra_command and extra_command.strip():
            injection = f"""
        # 🚨 导演最高优特别指令 (强制执行)
        请你务必严格遵守以下附加要求，并将其自然地融入到场景、光影、氛围或服饰的策划中：
        【 {extra_command.strip()} 】
            """
            # 巧妙地把它插在“# 任务要求”的正上方
            system_prompt = system_prompt.replace(
                "# 任务要求", injection + "\n\n        # 任务要求"
            )
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个只输出 JSON 的摄影导演。"},
                    {"role": "user", "content": system_prompt},
                ],
                temperature=0.85,  # 👈 提高到 0.85 增加随机性和发散性
                top_p=0.9,
            )
            content = response.choices[0].message.content
            if content:
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                elif content.startswith("```"):
                    content = content[3:]

                if content.endswith("```"):
                    content = content[:-3]

                content = content.strip()

            # 3. 再次尝试解析
            try:
                result = json.loads(content)
                logger.info(
                    f"导演决策完成 -> 场景: {result.get('scene')}, 风格: {result.get('style')}"
                )
                result["current_theme"] = current_theme
                return result
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析彻底失败，清洗后的内容为: {content}")
                raise CustomException(msg="AI 导演给出的剧本格式乱码了，请重试")

        except Exception as e:
            logger.error(f"LLM 裂变引擎故障: {str(e)}")
            raise CustomException(msg="AI 导演正在休息，请稍后再试")

    # 在 llm_action_engine 类中新增
    async def infer_visual_context(self, image_url: str = None, location: str = None):
        """
        🎭 视觉导演 V3.0：多模态决策引擎
        有图用图（视觉反推），无图用地点（地理脑暴）
        """

        # 1. 判定当前执行模式
        has_image = bool(image_url and image_url.startswith("http"))
        has_location = bool(location and location.strip())

        # 2. 构建针对性的 System Prompt
        if has_image:
            # 视觉反推模式
            mode_prefix = "【模式：视觉深度反推】请解析上传的图片内容。"
            context_hint = f"参考地理位置：{location}" if has_location else ""
        else:
            # 地理脑暴模式
            mode_prefix = f"【模式：地理视觉脑暴】目前没有参考图，请基于地点“{location}”进行脑暴。"
            context_hint = "请挖掘该地点最具代表性的高级感视觉特征。"

        vision_system_prompt = f"""
        你是一位顶级的 AI 摄影导演。{mode_prefix} {context_hint}
        请遵循以下逻辑进行视觉策划，确保产出具有“高级写真大片”质感：

        1. 【场景/地貌解构 (scene_detail)】：
           - 严禁平庸废话。聚焦物理材质（如：哑光青石板、微泛金光的夯土、丝绸般的水面）。
           - 运营死命令：拒绝杂草、老旧自行车、生锈栏杆等破败元素，追求极致美感。

        2. 【极致光影设计 (lighting_detail)】：
           - 策划一种“增强画面深度”的写实方案（如：侧逆光边缘勾勒、林间斑驳碎光）。
           - 必须包含“环境散落光”或“斑驳影纹”，严禁强光直射面部。

        3. 【空气氛围重构 (atmosphere_detail)】：
           - 根据地理/画面判定干湿度。干燥则写出“通透、尘埃在丁达尔光柱中跃动”；湿润则写出“空气氤氲、光线被湿度散射”。

        请严格以 JSON 格式输出：
        {{
          "scene_detail": "...",
          "lighting_detail": "...",
          "atmosphere_detail": "..."
        }}
        """

        try:
            messages = [
                {
                    "role": "system",
                    "content": "你是一个只输出 JSON 的视觉导演，严禁废话。",
                }
            ]

            # 3. 构造不同的 Payload
            if has_image:
                # 调用多模态模型 (VLM)
                raw_b64 = await ImageUtil.fetch_to_base64(image_url)
                base64_image_data = f"data:image/jpeg;base64,{raw_b64}"

                user_content = [
                    {"type": "text", "text": vision_system_prompt},
                    {"type": "image_url", "image_url": {"url": base64_image_data}},
                ]
            elif has_location:
                # 调用纯文本模型 (LLM)
                user_content = vision_system_prompt
            else:
                # 双无情况，直接返回兜底
                return self._get_default_visual_context()

            messages.append({"role": "user", "content": user_content})

            # 4. 发起请求
            # 如果没有图片，可以使用更便宜/快速的纯文本模型 ID

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.4,
            )

            content = response.choices[0].message.content

            # --- 清洗与解析逻辑保持不变 ---
            return self._parse_json_content(content)

        except Exception as e:
            logger.error(f"视觉导演决策引擎故障: {str(e)}")
            return self._get_default_visual_context()

    def _parse_json_content(self, content: str) -> dict:
        """
        🧹 专属清洁工：处理大模型返回的 JSON 字符串，剥离 Markdown 伪装
        """
        if not content:
            logger.warning("大模型返回内容为空，使用默认视觉配置")
            return self._get_default_visual_context()

        # 1. 基础清理
        content = content.strip()

        # 2. 剥离可能存在的 markdown 代码块包裹 (```json ... ```)
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]

        if content.endswith("```"):
            content = content[:-3]

        content = content.strip()

        # 3. 尝试解析
        try:
            result = json.loads(content)
            # 简单校验一下字段是否都存在，不存在的给个空字符串兜底
            return {
                "scene_detail": result.get("scene_detail", ""),
                "lighting_detail": result.get("lighting_detail", ""),
                "atmosphere_detail": result.get("atmosphere_detail", ""),
            }
        except json.JSONDecodeError as e:
            logger.error(f"视觉 JSON 解析失败: {content} | Error: {str(e)}")
            # 解析失败时，优雅降级，返回兜底数据
            return self._get_default_visual_context()

    def _get_default_visual_context(self):
        """兜底默认值"""
        return {
            "scene_detail": "高级感户外写实背景，具有丰富的环境层次",
            "lighting_detail": "温润的自然漫反射光，带有斑驳的树影纹理",
            "atmosphere_detail": "通透自然，具有极佳的空气感",
        }

    async def generate_image_by_doubao_with_images(
        self, prompt: str, image_urls: list[str]
    ) -> str:
        """
        🎨 调用豆包 Seedream 生图大模型：支持多图参考 (异步版本)
        """
        if not image_urls or len(image_urls) < 1:
            raise CustomException(msg="图像编辑模式必须传参参考图URL")

        logger.info(f"🎨 正在唤醒豆包画师(多图模式)，Prompt: {prompt[:30]}...")

        try:
            # 🚀 官方示例的异步改写版
            response = await self.ark_client.images.generate(
                model="doubao-seedream-5-0-260128",
                prompt=prompt,
                size="2K",
                response_format="url",
                # 🛠️ 塞入多图参考
                extra_body={
                    "image": image_urls,  # 👈 直接甩给豆包服务器
                    "watermark": False,
                    "send": 1111,
                    "sequential_image_generation": "disabled",
                },
                # 生图+融合比较慢，设长一点超时
                timeout=120.0,
            )

            # 提取图片 URL
            if response.data and len(response.data) > 0:
                img_url = response.data[0].url
                logger.info(f"✅ 豆包融合成功")
                async with httpx.AsyncClient() as client:
                    img_res = await client.get(img_url)
                    img_res.raise_for_status()  # 确保下载成功
                    image_bytes = img_res.content

                # 🚀 2. 伪装成 FastAPI 的 UploadFile 对象
                file_name = f"doubao_fusion_{uuid.uuid4().hex[:8]}.png"
                file_like = io.BytesIO(image_bytes)
                mock_upload_file = UploadFile(filename=file_name, file=file_like)
                _, _, file_url = await UploadUtil.upload_to_minio(file=mock_upload_file)
                return file_url
            else:
                raise CustomException(msg="接口请求成功，但未返回图片地址")

        except Exception as e:
            logger.error(f"豆包生图引擎故障: {str(e)}")
            raise CustomException(msg="AI 绘图正在拼合场景，请稍后再试")

    async def generate_image_by_qwen_edit(
        self, prompt: str, image_urls: list[str]
    ) -> str:
        """
        🚀 使用 Qwen-Image-2.0-Pro 进行多图写实融合
        bg_url: 千家洞背景图
        person_url: 抠好的人物图
        """
        url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.QWEN_API_KEY}",
        }

        # 🛠️ 构造多图输入结构
        payload = {
            "model": "wan2.7-image",
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"image": image_urls[0]},  # 图 1：人物
                            {"image": image_urls[1]},  # 图 2：背景板
                            {"text": prompt},  # 指令：如何融合
                        ],
                    }
                ]
            },
            "parameters": {
                "size": "2K",
                "n": 1,
                "size": "1216*1760",  # 建议匹配你 9:16 的比例
                "prompt_extend": False,  # 既然咱们的提示词已经够细节了，关闭自动扩写防止它乱画
                "watermark": False,
                "thinking_mode": True,
            },
        }

        logger.info("🎨 Qwen-2.0-Pro 正在进行多图深度融合...")

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    url, headers=headers, json=payload, timeout=120
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.error(f"❌ Qwen API 报错: {error_text}")
                        raise CustomException(msg="千问画师罢工了，请稍后再试")

                    result = await resp.json()

                    # 提取生成图片的 URL
                    # 注意：Qwen-2.0-Pro 的返回结构通常在 output.choices[0].message.content
                    choices = result.get("output", {}).get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content", [])
                        # 寻找 content 里的 image 类型
                        for item in content:
                            if "image" in item:
                                img_url = item["image"]
                                logger.info(f"✅ 融合成功: {img_url[:50]}")
                                async with httpx.AsyncClient() as client:
                                    img_res = await client.get(img_url)
                                    img_res.raise_for_status()  # 确保下载成功
                                    image_bytes = img_res.content

                                # 🚀 2. 伪装成 FastAPI 的 UploadFile 对象
                                file_name = f"Qwen_fusion_{uuid.uuid4().hex[:8]}.png"
                                file_like = io.BytesIO(image_bytes)
                                mock_upload_file = UploadFile(
                                    filename=file_name, file=file_like
                                )
                                _, _, file_url = await UploadUtil.upload_to_minio(
                                    file=mock_upload_file
                                )
                                return file_url

                    raise CustomException(msg="接口请求成功，但未解析到图片地址")

            except Exception as e:
                logger.error(f"❌ Qwen-2.0-Pro 调用异常: {str(e)}")
                raise CustomException(msg="AI 正在玩命修图，请稍后")

    async def infer_visual_prompt_template(self, image_url: str) -> str:
        """
        👁️ 视觉导演 V3.0：基于背景环境深度反推，直出包含占位符的完整长文本提示词
        """
        vision_system_prompt = """You are a world-class commercial photo retoucher and AI spatial perspective expert.
Your task: Deeply analyze the provided [Background Scene Image] and generate a professional prompt for "Seamless Human-Scene Integration." 

Analyze the image based on these principles:
1. **Spatial Perspective (Critical for Proportions)**: Determine camera height (Eye-level, High-angle, Low-angle) and the Horizon Line position. Identify scale references (doors, stairs, furniture) to suggest the correct human height percentage in the frame.
2. **Structural Lock-in**: Extract architectural details and textures. **MANDATORY: Any text, signage, or plaques must be listed as "Text 'XXX' must be clear, accurate, and follow physical perspective."**
3. **Lighting Physics**: Analyze real color temperature (Cold/Warm/Neutral), light direction, and hardness. Do NOT invent "God rays" if they don't exist.
4. **Interaction Interface**: Define how the background color bleeds onto the subject (Light Wrapping) and the Ambient Occlusion (AO) shadows at the contact points.

---Output ONLY the prompt in the following format (No explanations):---

Photorealistic, environment lighting consistency, seamless subject integration, 8k UHD, physical perspective alignment, crystal clear quality.

**Spatial Structure & Composition:**
[1. Camera Angle: (e.g., Eye-level/Slightly high angle); 2. Horizon Line: (e.g., At the lower 1/3 of the frame); 3. Human Scale Suggestion: (e.g., Subject should be mid-ground, proportional to the height of [Reference Object]); 4. Detailed description of physical structures. If text exists, specify: "Text 'XXX' must be perfectly rendered without distortion."]

**Native Lighting & Atmosphere:**
[1. Weather: (e.g., Overcast with highly diffused light); 2. Color Temperature: (e.g., 5500K Neutral White); 3. Lighting Logic: (Specify main light direction and shadow softness. Avoid cinematic exaggerations).]

**Physical Level Integration:**
1. **Light Wrapping**: [Describe how the [Specific Color] from the background forms a subtle glow around the subject's edges for color balance].
2. **Grounding & AO**: [Describe the subtle Ambient Occlusion shadows where the subject's feet touch the [Specific Material] ground. Shadows must follow the perspective of the scene].
3. **Depth of Field (DoF)**: [Describe the blur relationship between the background and the subject's focal plane to ensure spatial depth].

**Camera Settings:**
[e.g., Sony A7R IV, 35mm lens, F/4.0, Realistic exposure, Accurate color rendition]."""

        image_hash = ""
        try:
            processed_image_bytes = await ImageUtil.fetch_processed_bytes(image_url)
            image_hash = hashlib.sha256(processed_image_bytes).hexdigest()
            logger.info(
                "🖼️ 视觉模板图片预处理完成 | pid={} | hash={} | bytes={} | url={}",
                os.getpid(),
                image_hash[:16],
                len(processed_image_bytes),
                image_url[:120],
            )
            cached_prompt = self._get_cached_visual_prompt_template(image_hash)
            if cached_prompt:
                logger.info(
                    "🎯 命中视觉导演模板缓存并直接返回 | pid={} | hash={} | url={}",
                    os.getpid(),
                    image_hash[:16],
                    image_url[:120],
                )
                return cached_prompt

            raw_b64 = base64.b64encode(processed_image_bytes).decode("utf-8")
            base64_image_data = f"data:image/jpeg;base64,{raw_b64}"
        except Exception as e:
            logger.error(f"反推前处理图片失败: {str(e)}")
            raise CustomException(msg="导演还没戴眼镜，看不清图，请重试")

        inflight_future = self._visual_prompt_template_inflight.get(image_hash)
        if inflight_future:
            logger.info(
                "⏳ 等待同图视觉模板结果复用 | hash={} | url={}",
                image_hash[:16],
                image_url[:120],
            )
            return await inflight_future

        loop = asyncio.get_running_loop()
        current_future = loop.create_future()
        self._visual_prompt_template_inflight[image_hash] = current_future

        try:
            messages = [
                {
                    "role": "system",
                    "content": "你是一个严谨的视觉导演。严格按照给定模板输出，严禁输出任何寒暄、前言或总结等废话。",
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": vision_system_prompt},
                        {"type": "image_url", "image_url": {"url": base64_image_data}},
                    ],
                },
            ]

            response = await self.gpt5_client.chat.completions.create(
                model="gpt-5.4",
                messages=messages,
                temperature=0.4,
                max_completion_tokens=2000,
                timeout=180.0,
            )

            content = response.choices[0].message.content

            # --- 🚀 极简清理逻辑 ---
            # 有些大模型依然喜欢在外面套一层 ```markdown 或 ```text
            if content:
                content = content.strip()
                if content.startswith("```"):
                    # 去掉第一行的 ``` 及标记
                    parts = content.split("\n", 1)
                    if len(parts) > 1:
                        content = parts[1]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

            self._set_cached_visual_prompt_template(image_hash, content)
            current_future.set_result(content)
            logger.info("🎭 视觉导演长文本模板反推完成！")

            # 直接返回长文本
            return content

        except Exception as e:
            if not current_future.done():
                current_future.set_exception(e)
                current_future.exception()
            logger.exception(
                f"VLM 引擎故障: {type(e).__name__}: {e!s}"
            )
            raise CustomException(
                msg="AI 导演正在看图构思，请稍后再试",
                data={
                    "origin_error_type": type(e).__name__,
                    "origin_error": repr(e),
                },
            )
        finally:
            self._visual_prompt_template_inflight.pop(image_hash, None)

    async def generate_image_by_banana_edit(
        self, prompt: str, image_urls: list[str]
    ) -> str:
        """
        🍌 使用 Banana (Gemini) 模型进行多图艺术构图与融合
        image_urls: 包含需要融合的图片URL列表 (例如: [人物图, 背景图])
        """
        if not image_urls or len(image_urls) < 1:
            raise CustomException(msg="Banana 图像融合必须提供参考图 URL")

        # 从配置获取密钥和地址，建议写在 settings 里
        api_key = settings.BANANA_API_KEY  # 你的 sk-YOUR_API_KEY
        api_url = "https://api.laozhang.ai/v1beta/models/gemini-3.1-flash-image:generateContent"

        headers = {
            "x-goog-api-key": api_key,
            "Content-Type": "application/json",
        }

        logger.info("🍌 Banana 引擎正在提取多图特征并准备融合...")

        try:
            # 1. 构建 parts 结构：先放 Prompt
            parts = [{"text": prompt}]

            # 2. 异步下载图片并转换为 Base64
            for raw_b64 in image_urls:
                parts.append(
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",  # 这里视具体情况可动态判断，jpeg通用性较好
                            "data": raw_b64,
                        }
                    }
                )

            # 3. 构造请求 Payload
            payload = {
                "contents": [{"parts": parts}],
                "generationConfig": {
                    "temperature": 0.2,  # 🚀 [新增] 控制发散程度 (0.0 - 1.0)
                    "seed": 42,
                    "responseModalities": ["IMAGE"],
                    "imageConfig": {
                        "aspectRatio": "3:4",  # 这里改成了适配你手机竖屏旅拍的 9:16
                        "imageSize": "2K",
                    },
                },
            }

            # 4. 异步发起生图请求
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    api_url, headers=headers, json=payload, timeout=180.0
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.error(f"❌ Banana API 报错: {error_text}")
                        raise CustomException(msg="Banana 画师罢工了，请稍后再试")

                    result = await resp.json()

                    # 5. 提取生成的 Base64 图片数据
                    candidates = result.get("candidates", [])
                    if candidates:
                        content_parts = (
                            candidates[0].get("content", {}).get("parts", [])
                        )
                        for part in content_parts:
                            if "inlineData" in part and "data" in part["inlineData"]:
                                output_base64 = part["inlineData"]["data"]
                                logger.info(
                                    "✅ Banana 融合成功，获取到 Base64 图像流！"
                                )

                                # 🚀 ---------- 核心：Base64 落地 MinIO ---------- 🚀
                                # 1. 将 Base64 字符串解码为真实的二进制字节流
                                file_content = base64.b64decode(output_base64)

                                # 2. 用 BytesIO 将字节流放进内存，伪装成一个文件
                                timestamp = int(datetime.now().timestamp())
                                fake_file = UploadFile(
                                    file=io.BytesIO(file_content),
                                    filename=f"banana_mix_{timestamp}.png",
                                )

                                # 3. 完美对接你的工具类，上传并拿到公网 URL
                                _, _, file_url = await UploadUtil.upload_to_minio(
                                    file=fake_file
                                )

                                logger.info(
                                    f"🎉 融合图已成功挂载 CDN/MinIO: {file_url[:60]}..."
                                )
                                return file_url

                    raise CustomException(msg="接口请求成功，但未解析到图像数据")

        except CustomException:
            raise
        except Exception as e:
            logger.error(f"❌ Banana 调用异常: {str(e)}")
            raise CustomException(msg="AI 正在玩命修图，请稍后")

    async def generate_image_by_gpt_edit(
        self, prompt: str, image_urls: list[str]
    ) -> str:
        """
        使用 OpenAI GPT Image 模型进行多图融合。
        image_urls 支持 data URI 或纯 Base64 字符串。
        """
        if not image_urls:
            raise CustomException(msg="GPT 图像融合必须提供参考图")

        if not settings.OPENAI_API_KEY:
            raise CustomException(msg="未配置 OPENAI_API_KEY，无法使用 GPT 融图")

        image_debug_infos = []
        try:
            image_files = []
            for index, image_data in enumerate(image_urls, start=1):
                mime_type = "image/jpeg"
                raw_b64 = image_data

                if image_data.startswith("data:"):
                    header, raw_b64 = image_data.split(",", 1)
                    mime_type = header.split(";", 1)[0].split(":", 1)[1]

                image_bytes = base64.b64decode(raw_b64)
                extension = mime_type.split("/")[-1] or "jpg"
                image_debug_infos.append(
                    {
                        "index": index,
                        "mime_type": mime_type,
                        "extension": extension,
                        "byte_size": len(image_bytes),
                    }
                )
                image_files.append(
                    (f"gpt_edit_{index}.{extension}", image_bytes, mime_type)
                )

            request_context = {
                "model": self.openai_image_model,
                "image_count": len(image_files),
                "images": image_debug_infos,
                "size": "1024x1536",
                "quality": "high",
                "output_format": "png",
                "response_format": "b64_json",
                "timeout_seconds": 180.0,
                "prompt_length": len(prompt),
                "prompt_preview": prompt,
            }
            logger.info(
                "🧠 GPT Image 正在进行多图融合 | context={}",
                json.dumps(request_context, ensure_ascii=False, default=str),
            )
            response = await self.lz_client.images.edit(
                model=self.openai_image_model,
                image=image_files,
                prompt=prompt,
                size="1024x1536",
                quality="high",
                output_format="png",
                response_format="b64_json",
                timeout=180.0,
            )

            if response.data and len(response.data) > 0:
                result = response.data[0]

                if getattr(result, "b64_json", None):
                    image_bytes = base64.b64decode(result.b64_json)
                elif getattr(result, "url", None):
                    async with httpx.AsyncClient() as client:
                        img_res = await client.get(result.url)
                        img_res.raise_for_status()
                        image_bytes = img_res.content
                else:
                    raise CustomException(msg="GPT 融图成功，但未返回可用图像数据")

                fake_file = UploadFile(
                    file=io.BytesIO(image_bytes),
                    filename=f"gpt_mix_{uuid.uuid4().hex[:8]}.png",
                )
                _, _, file_url = await UploadUtil.upload_to_minio(file=fake_file)
                logger.info(f"🎉 GPT 融合图已上传 MinIO: {file_url[:60]}...")
                return file_url

            raise CustomException(msg="GPT 融图接口未返回图片结果")

        except CustomException:
            raise
        except Exception as e:
            error_context = {
                "model": self.openai_image_model,
                "base_url": str(getattr(self.openai_client, "base_url", "")),
                "image_count": len(image_urls),
                "images": image_debug_infos,
                "prompt_length": len(prompt),
                "prompt_preview": prompt[:300],
                "exception_type": type(e).__name__,
                "exception_message": str(e),
                "exception_repr": repr(e),
            }

            if isinstance(e, APIError):
                error_context.update(
                    {
                        "openai_code": e.code,
                        "openai_param": e.param,
                        "openai_type": getattr(e, "type", None),
                        "openai_body": e.body,
                        "request_method": getattr(e.request, "method", None),
                        "request_url": str(getattr(e.request, "url", "")),
                    }
                )

            if isinstance(e, APIStatusError):
                error_context.update(
                    {
                        "status_code": e.status_code,
                        "request_id": e.request_id,
                        "response_text": e.response.text,
                    }
                )

            logger.exception(
                "❌ GPT Image 调用异常 | context={}",
                json.dumps(error_context, ensure_ascii=False, default=str),
            )
            raise CustomException(msg="GPT 正在玩命修图，请稍后")

    async def generate_style_theme(
        self, gender: str, theme_name: str, remark: str | None = None
    ) -> dict:
        """
        调用大模型生成完整的 AI 摄影风格参数

        :param gender: 性别 (如: male, female)
        :param theme_name: 主题名称 (如: 井冈山小红军)
        :param remark: 用户补充的备注要求 (可选)
        :return: 包含各项风格参数的字典
        """
        system_prompt = """
        你是一个资深的AI摄影美术指导与Prompt专家。你的任务是根据用户提供的【性别】和【拍摄主题】，
        发散并设计出用于AI生图的具体视觉参数。
        
        必须以纯JSON对象格式返回，包含以下5个字段（严禁输出任何Markdown标记如```json，直接输出JSON主体即可）：
        {
            "material": "材质描述(如: 水洗粗棉布, 丝绸, 亚麻等，需符合主题年代与风格)",
            "clothing_style": "穿着风格描述(如: 军装复古风, 宽松版型, 赛博朋克机能风等)",
            "colors": "配色方案(如: 军绿与褪色红, 高对比度黑白等)",
            "vibe": "氛围感关键词(如: 历史厚重感, 阳光明媚, 电影感胶片等，用逗号分隔)",
            "remark": "根据你生成的设计，给生图系统或摄影师的一句简短建议"
        }
        """

        user_content = f"性别: {gender}\n主题名称: {theme_name}\n"
        if remark:
            user_content += f"补充要求: {remark}\n"

        try:
            # 发起异步调用
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.7,  # 0.7 能保证一定的创意发散，又不至于太离谱
            )

            # 提取文本内容
            result_text = response.choices[0].message.content.strip()

            # 防御性编程：清理偶尔出现的 Markdown 代码块包裹
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            elif result_text.startswith("```"):
                result_text = result_text[3:]

            if result_text.endswith("```"):
                result_text = result_text[:-3]

            # 解析为字典
            style_params = json.loads(result_text.strip())
            return style_params

        except json.JSONDecodeError as e:
            print(f"引擎解析风格JSON失败. 原始内容: {result_text}")
            # 解析失败时返回安全兜底数据，防止整个链路中断
            return {
                "material": "",
                "clothing_style": "",
                "colors": "",
                "vibe": "",
                "remark": "AI解析异常，已降级处理",
            }
        except Exception as e:
            print(f"LLMActionEngine调用大模型失败: {str(e)}")
            raise e  # 将异常抛出，由外层的 Controller (Service) 进行捕获和 HTTP 500 处理


llm_action_engine = LLMActionEngine()
