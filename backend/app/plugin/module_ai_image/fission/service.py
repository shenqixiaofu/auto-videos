import asyncio
import base64
import copy
import time
from datetime import datetime
from io import BytesIO
import io
import json
from PIL import Image

from fastapi import UploadFile
import httpx
from loguru import logger
from app.api.v1.module_system.auth.schema import AuthSchema
from app.core.exceptions import CustomException
from volcengine.visual.VisualService import VisualService
from app.config.setting import settings
from app.api.v1.module_common.file.service import FileService
from app.utils.upload_util import UploadUtil
from app.plugin.module_ai_image.utils.image_utils import ImageUtil
from sqlalchemy.orm.attributes import flag_modified

# 导入咱们自己的组件
from .crud import FissionBatchCRUD, FissionTaskCRUD
from .schema import (
    FissionCreateSchema,
    BatchOutSchema,
    FissionManualCreateSchema,
    SubmitExpertBatchRequest,
    TaskCallbackSchema,
    TaskOutSchema,
    FissionQueryParam,
    UpscaleCreateSchema,
)

# LLM 模块
from app.plugin.module_ai_image.utils.llm_generator import llm_action_engine


class FissionService:
    """
    AI 自动化裂变服务层 - 实现 1 进 10 的核心逻辑
    """

    @classmethod
    async def get_filter_options_service(cls, auth: any, field_name: str) -> list[str]:
        return await FissionBatchCRUD(auth).get_distinct_column_values(field_name)

    @classmethod
    async def manual_create_batch_service(
        cls, auth: any, obj_in: FissionManualCreateSchema
    ) -> any:
        """
        🚀 业务逻辑：手动将 MinIO 图片链接转化为一个完整的生图批次
        """
        crud = FissionBatchCRUD(auth)

        # 1. 生成唯一的批次编号 (手动前缀标识)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        batch_sn = f"MANUAL_{timestamp}"

        # 2. 构造 Batch（主表）数据
        # 状态设为 2 (已完成)，因为图片已经上传好了
        batch_data = {
            "batch_sn": batch_sn,
            "input_location": obj_in.input_location,
            "theme": obj_in.theme,
            "gender": obj_in.gender,
            "age": obj_in.age,
            "selected_scene": obj_in.selected_scene,
            "selected_style": obj_in.selected_style,
            "task_count": len(obj_in.image_urls),
            "status": 2,
        }

        # 3. 构造 Tasks（明细表）数据列表
        tasks_data = []
        for index, url in enumerate(obj_in.image_urls):
            tasks_data.append(
                {
                    "task_sn": f"TSN_{batch_sn}_{index + 1}",
                    "location": obj_in.input_location,  # 冗余同步
                    "gender": obj_in.gender,  # 冗余同步
                    "age": obj_in.age,  # 冗余同步
                    "image_url": url,
                    "process_status": 2,  # 2 代表：执行成功
                    "view_type": "手动补录",
                    "action_desc": f"补录图片_{index + 1}",
                    "positive_prompt": "Manual upload by administrator",  # 填补必填项
                    "completed_at": datetime.now(),
                }
            )

        # 4. 调用 CRUD 层执行原子化保存（内部会处理 flush 和 refresh）
        # 这里会一次性把 1个 Batch 和 N个 Task 塞进数据库
        new_batch = await crud.create_fission_bundle_crud(batch_data, tasks_data)

        return new_batch

    @classmethod
    async def delete_fission_batch_service(cls, auth: any, batch_id: int) -> bool:
        """
        业务逻辑：安全删除一个裂变批次及其关联任务
        """
        # 1. 初始化 CRUD 实例
        crud = FissionBatchCRUD(auth)

        # 2. 调用原子化删除逻辑
        # 内部已经包含了先删 Task 再删 Batch 的顺序逻辑
        success = await crud.delete_fission_bundle_crud(batch_id)

        # 3. 结果校验
        if not success:
            # 如果 rowcount 为 0，说明这个 ID 根本不存在，或者已经被删过了
            raise CustomException(
                status_code=404, msg="删除失败：该批次不存在或已被销毁！"
            )

        return True

    @classmethod
    async def get_all_filter_options_service(
        cls, auth: any, gender: str = None
    ) -> dict:
        """
        🚀 聚合并发查询：支持性别联动的全量/过滤下拉选项
        """
        crud = FissionBatchCRUD(auth)

        # 将 gender 参数传给每一个查询任务
        # 这里的 crud.get_distinct_column_values 需要同步修改以支持 gender 过滤
        location, scene, style, theme = await asyncio.gather(
            crud.get_distinct_column_values("input_location", gender=gender),
            crud.get_distinct_column_values("selected_scene", gender=gender),
            crud.get_distinct_column_values("selected_style", gender=gender),
            crud.get_distinct_column_values("theme", gender=gender),
        )

        # 打包返回，变量名对齐前端
        return {
            "locations": location,
            "scenes": scene,
            "styles": style,
            "themes": theme,
        }

    @classmethod
    async def build_fission_data_payload(
        cls,
        auth: AuthSchema,
        location: str,
        gender: str,
        age: int,
        theme_ids: list[int] = None,
        extra_command: str = None,
    ) -> tuple[dict, list[dict]]:
        """
        🚀 纯业务逻辑层：调LLM -> 组装黄金模板 -> 生成待入库的数据字典
        自动化调用生图任务
        (不碰数据库，不依赖 Auth)
        """
        GOLDEN_TEMPLATE = (
            "写实摄影风格，{style}，{lighting_detail}。主场景位于{scene_detail}。"
            "一位{age}岁中国汉族面孔{gender}。{face_description}。"  # 👈 注意这里是 face_description
            "眼神自然清澈，灵动有神。眼波流转，眼底眼神光（catchlight）温润而不刺眼。"
            "虹膜纹理自然呈现，深邃且富有层次感。睫毛浓密清晰，不突变。"
            "{hairstyle}。身着{clothing}。{action}，{view}。"
            "画面呈现极致的真实质感，{skin_texture}，{atmosphere_detail}，8k超高清分辨率。"
            "相机参数：Canon EOS R5, 50mm f/1.2, 1/250s, ISO 400，比例9：16。Do not change the background."
        )

        # 1. 调起 AI 摄影导演获取策划素材
        llm_result = await llm_action_engine.run_fission_pipeline(
            auth,
            location=location,
            gender=gender,
            age=age,
            theme_ids=theme_ids,
            extra_command=extra_command,
        )

        # 3. 准备批次主表数据 (增加 strategy_id 支持自动化)
        style = llm_result.get("selected_style", "写实摄影")
        lighting_detail = llm_result.get("lighting_detail", "")
        scene_detail = llm_result.get("scene_detail", "")
        hairstyle = llm_result.get("hairstyle", "")
        clothing = llm_result.get("clothing", "")
        # 👇 提取豆包生成的人物画像与皮肤质感
        face_description = llm_result.get("face_description", "面部轮廓清晰，神态自然")
        skin_texture = llm_result.get("skin_texture", "皮肤纹理真实细腻")
        atmosphere_detail = llm_result.get("atmosphere_detail", "空气感通透")
        current_theme = llm_result.get("current_theme", {})
        # 3. 准备批次主表数据
        batch_sn = f"B{datetime.now().strftime('%Y%m%d%H%M%S')}"
        batch_data = {
            "batch_sn": batch_sn,
            "input_location": location,
            "gender": gender,
            "theme": current_theme.get("theme", "未分类主题"),
            "age": age,
            "selected_scene": llm_result.get("selected_scene", ""),
            "selected_style": style,
            "task_count": 15,
        }

        # 4. 准备 10 个动作子任务数据
        tasks_data = []
        for i, action in enumerate(llm_result.get("actions", [])):

            # --- 🚀 核心逻辑 B：在 Python 层进行 Prompt 动态渲染 ---
            try:
                # 每一个 action 会替换模板中的 {action} 和 {view}
                rendered_prompt = GOLDEN_TEMPLATE.format(
                    style=style,
                    lighting_detail=lighting_detail,
                    scene_detail=scene_detail,
                    age=age,
                    gender=gender,
                    face_description=face_description,  # 👈 填入神韵
                    atmosphere_detail=atmosphere_detail,
                    skin_texture=skin_texture,  # 👈 填入皮肤
                    hairstyle=hairstyle,
                    clothing=clothing,
                    action=action.get("desc", ""),
                    view=action.get("view_type", "中景"),
                )
            except KeyError as e:
                # 容错处理：如果模板变量对不上，至少保证能入库不报错
                rendered_prompt = f"渲染失败，模板缺失字段: {str(e)}"

            tasks_data.append(
                {
                    "task_sn": f"T{batch_sn[1:]}{i:02d}",
                    "location": location,
                    "style_tag": style,
                    "gender": gender,
                    "age": age,
                    "view_type": action.get("view_type", ""),
                    "action_desc": action.get("desc", ""),
                    "positive_prompt": rendered_prompt,
                    "process_status": 0,
                    # 🚀 核心：初始化版本历史
                    "current_version": 1,
                    "version_history": [
                        {
                            "v": 1,
                            "url": "",  # 初始为空，生图回调后再填入
                            "positive_prompt": rendered_prompt,
                            "status": "waiting",
                            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "seed": None,
                            # 👈 存入当前这张图的核心参数快照，下次“换背景”就改这里
                            "params_snapshot": {
                                "style": style,
                                "lighting_detail": lighting_detail,
                                "scene_detail": scene_detail,
                                "face_description": face_description,
                                "skin_texture": skin_texture,
                                "atmosphere_detail": atmosphere_detail,
                                "hairstyle": hairstyle,
                                "clothing": clothing,
                                "action": action.get("desc", ""),
                                "view": action.get("view_type", "中景"),
                            },
                        }
                    ],
                }
            )

        return batch_data, tasks_data

    @classmethod
    async def create_fission_service(
        cls,
        auth: AuthSchema,
        data: FissionCreateSchema,
        strategy_id: int = None,
        theme_ids: list[int] = None,
        extra_command: str = None,
    ) -> dict:
        """
        核心逻辑：自动化生成 LLM 提供变量素材 -> Python 完成黄金模板组装 -> 原子化入库
        """

        batch_data, tasks_data = await cls.build_fission_data_payload(
            auth, data.location, data.gender, data.age, theme_ids, extra_command
        )

        if strategy_id:  # 👈 添加策略 ID 支持
            batch_data["strategy_id"] = strategy_id

        # 5. 原子化入库
        new_batch = await FissionBatchCRUD(auth).create_fission_bundle_crud(
            batch_data, tasks_data
        )

        return {"id": new_batch.id}

    @classmethod
    async def get_batch_list_service(
        cls, auth: AuthSchema, search: FissionQueryParam
    ) -> dict:
        """
        查看历史裂变批次 (完美对齐 CRUDBase 原生分页)
        """
        # 1. 提取分页参数
        page_no = getattr(search, "page", 1) or 1
        page_size = getattr(search, "page_size", 10) or 10
        offset = (page_no - 1) * page_size

        # 2. 剥离分页字段，生成纯净的 search 字典 (过滤掉 None 的查询条件)
        search_dict = {}
        if search:
            # 定义哪些字段需要用模糊搜索 (LIKE)
            fuzzy_fields = [
                "input_location",
                "selected_scene",
                "selected_style",
                "theme",
            ]

            for k, v in search.model_dump(exclude={"page", "page_size"}).items():
                if v is not None and str(v).strip() != "":
                    # 🚀 魔法在这里：如果是文本字段，包装成元组触发 LIKE 搜索
                    if k in fuzzy_fields:
                        search_dict[k] = ("like", str(v).strip())
                    else:
                        search_dict[k] = v
        if "status" in search_dict:
            frontend_status = search_dict.pop("status")  # 取出前端传的字符串
            if frontend_status == "done":
                search_dict["status"] = 2  # 映射为数据库里的整型状态
            elif frontend_status == "processing":
                search_dict["status"] = 1
        # 3. 调用我们在 CRUD 封装的核心分页函数
        result_dict = await FissionBatchCRUD(auth).list_fission_batches(
            search=search_dict,
            offset=offset,
            limit=page_size,
            out_schema=BatchOutSchema,
        )

        return result_dict

    @classmethod
    async def get_task_batch_service(
        cls, auth: AuthSchema, batch_id: int
    ) -> list[dict]:
        """
        查看某个批次下的 10 个生图任务详情
        """
        # 直接调用核心函数 2
        tasks = await FissionTaskCRUD(auth).get_tasks_by_batch_id(batch_id)
        return [TaskOutSchema.model_validate(t).model_dump() for t in tasks]

    @classmethod
    async def get_batch_detail_service(cls, auth: AuthSchema, batch_id: int) -> dict:
        """
        获取批次完整详情：包含主表表单基础信息 + 子表任务列表 (专供工作台回显)
        """
        # 1. 查询批次主表 (为了恢复前端左侧的 form)
        batch = await FissionBatchCRUD(auth).get(id=batch_id)
        if not batch:
            raise CustomException(status_code=404, msg="批次不存在")

        # 2. 直接复用你原有的查询核心：获取该批次下的所有子任务
        tasks = await FissionTaskCRUD(auth).get_tasks_by_batch_id(batch_id)

        # 3. 将 tasks 转成你定义好的 Schema 字典列表
        task_list = [TaskOutSchema.model_validate(t).model_dump() for t in tasks]

        # 4. 🚀 组合成一个大字典，完美契合前端的 Object.assign
        return {
            "id": batch.id,
            "location": getattr(
                batch, "input_location", ""
            ),  # 注意对齐你数据库的实际字段名
            "gender": getattr(batch, "gender", "女孩"),
            "age": getattr(batch, "age", 20),
            "theme": getattr(batch, "theme", ""),
            "selected_scene": getattr(batch, "selected_scene", ""),
            "selected_style": getattr(batch, "selected_style", ""),
            # 把转好的子任务列表塞进来，对应前端的 promptList
            "tasks": task_list,
        }

    @classmethod
    async def get_task_detail_service(cls, auth: any, task_id: int) -> dict:
        """
        获取单张任务详情
        """
        # 直接用咱们刚刚剥离出来的 FissionTaskCRUD 查库
        task = await FissionTaskCRUD(auth).get(id=task_id)

        if not task:
            raise CustomException(msg=f"找不到指定的任务记录 (ID: {task_id})")

        # 假设你有一个 Pydantic schema 用于序列化输出，如果没有可以直接转 dict
        # 这里为了演示，直接返回其字典形式
        return TaskOutSchema.model_validate(task).model_dump(mode="json")

    @classmethod
    async def claim_task_service(cls, auth: AuthSchema, agent_id: str) -> dict | None:
        """
        Agent 抢单服务
        """
        task = await FissionTaskCRUD(auth).claim_pending_task_crud(agent_id=agent_id)
        if not task:
            return None
        return TaskOutSchema.model_validate(task).model_dump()

    import copy  # 🚀 必须在文件顶部引入这个

    @classmethod
    async def task_callback_service(
        cls, auth: any, payload: TaskCallbackSchema
    ) -> bool:
        """
        Agent 结果回传服务 - 防弹重构版
        """
        task_crud = FissionTaskCRUD(auth)
        task = await task_crud.get(id=payload.task_id)
        batch_crud = FissionBatchCRUD(auth)

        if not task:
            raise CustomException(msg=f"回传失败：未找到该任务 ID ({payload.task_id})")

        # ==========================================
        # 🚀 必杀技 1：深拷贝 (Deep Copy)
        # 强制生成一个新的内存对象，打破 SQLAlchemy 的脏检查免疫！
        # ==========================================
        new_history = copy.deepcopy(task.version_history or [])

        # 标记是否成功匹配并修改了数据
        is_updated = False

        for item in new_history:
            # ==========================================
            # 🚀 必杀技 2：强制转为 int 比较，消灭 1 != "1" 的隐患！
            # ==========================================
            if int(item.get("v", 0)) == int(task.current_version):
                item["url"] = payload.image_url
                item["seed"] = payload.seed
                item["status"] = "success" if payload.process_status == 2 else "failed"

                if payload.process_status != 2 and hasattr(payload, "error_msg"):
                    item["error_msg"] = payload.error_msg

                is_updated = True
                break

        if not is_updated:
            print(
                f"⚠️ [警告] 任务 {task.id} 回传时未能匹配到版本 v{task.current_version}"
            )

        # 3. 组装更新数据
        update_data = {
            "version_history": new_history,
            "process_status": payload.process_status,
            # 🚀 必杀技 3：顺手把外层展示用的图片 URL 也给更新了，方便前端瀑布流直接读！
            "image_url": payload.image_url,
        }

        # 4. 提交给数据库
        await task_crud.update(id=task.id, data=update_data)

        pending_count = await task_crud.count(
            search={"batch_id": task.batch_id, "process_status__in": [0, 1]}
        )

        # 如果未完成的任务数量为 0，说明 15 张图全画完了（不管成功还是失败）
        if pending_count == 0:
            logger.info(f"🎉 批次 {task.batch_id} 所有任务执行完毕，更新批次状态！")
            # 这里的状态 2 代表 Batch 已完成 (需跟你上面选的第一条路对应)
            await batch_crud.update(id=task.batch_id, data={"status": 2})

        return True

    @classmethod
    async def update_task_callback_crud(
        cls, auth: AuthSchema, payload: TaskCallbackSchema
    ):
        # 🚀 复用框架的 get: 按照 task_sn 查出对象 (框架支持 **kwargs 查询)
        task = await FissionTaskCRUD(auth).get(id=payload.task_id)

        if not task:
            return None

        # --- 核心逻辑：在内存中准备好新的 JSON 列表 ---
        new_history = list(task.version_history or [])
        for item in new_history:
            if item.get("v") == task.current_version:
                item["url"] = payload.image_url
                item["seed"] = payload.seed
                item["status"] = "success" if payload.status == "success" else "failed"
                break

        # 🚀 复用框架的 update: 传入 ID 和我们要更新的字典
        # 注意：这里我们传入整个 new_history，setattr 会触发 SQLAlchemy 的变更追踪
        update_data = {
            "version_history": new_history,
            "process_status": payload.process_status,
        }

        # 调用 self.update，它会自动帮你 handle：updated_id、flush、refresh 和权限校验
        return await FissionTaskCRUD(auth).update(id=task.id, data=update_data)

    @classmethod
    async def create_upscale_service(cls, auth: any, data: UpscaleCreateSchema) -> dict:
        """
        一键高清：调用火山引擎视觉 API (CVProcess) 进行图像超分
        """
        # 1. 这里你需要写一段查库逻辑：通过 data.task_id 拿到原图 URL
        task = await FissionTaskCRUD(auth).get(id=data.task_id)
        if not task or not task.image_url:
            raise CustomException(msg="任务不存在或原图尚未生成")

        # 假设我们查到了原图 URL
        original_image_url = data.target_url

        # 2. 初始化火山引擎视觉服务客户端
        visual_service = VisualService()

        try:
            # 使用 httpx 异步拉取图片，绝不阻塞 FastAPI 主线程
            async with httpx.AsyncClient() as client:
                img_response = await client.get(original_image_url, timeout=10.0)
                img_response.raise_for_status()  # 如果不是 200 就抛出异常

                # 读取二进制流并转为 Base64 字符串
                img_bytes = img_response.content
                img_base64_str = base64.b64encode(img_bytes).decode("utf-8")
        except Exception as e:
            print(f"❌ 从 MinIO 读取图片失败: {str(e)}")
            raise CustomException(msg=f"读取原图失败，无法进行高清处理: {str(e)}")

        # 🚨 替换为你火山引擎的真实 AK / SK (强烈建议写在 .env 环境变量里)
        visual_service.set_ak(settings.VOLC_AK)
        visual_service.set_sk(settings.VOLC_SK)

        # 3. 严格按照你给的 Body 参数构造请求载荷
        form_data = {
            "req_key": "lens_lqir",  # 👈 换成了这个智能增强算法
            "binary_data_base64": [img_base64_str],
            # 假设你希望 720p 以上的图就不放大了，只做去模糊和去噪
            "resolution_boundary": "1080p",
            "enable_hdr": True,  # 👈 开启 HDR，让景区的光影和人物更通透
            "enable_wb": False,  # 白平衡看情况，如果怕破坏原图氛围可以先关掉
            "result_format": 0,
            "jpg_quality": 95,
            "return_url": True,
        }

        try:
            # 4. 发起同步请求 (火山底层的 cv_process)
            print(f"🚀 开始调用火山视觉超分，目标图片: {original_image_url}")
            resp_json = visual_service.cv_process(form_data)
            # 5. 解析返回结果
            # 火山的 SDK 通常返回一个 JSON 字符串，我们需要 loads 一下

            # 检查火山是否报错 (通常看 code 字段，10000 才是成功，具体以官方文档为准)
            if "code" in resp_json and resp_json["code"] != 10000:
                raise Exception(f"火山超分接口报错: {resp_json.get('message')}")
            # 2. 安全校验

            # 3. 按照你提供的结构精准抠出高清 URL
            # 路径是: data -> image_urls -> [0]
            volc_data = resp_json.get("data", {})
            upscaled_list = volc_data.get("image_urls", [])

            if not upscaled_list:
                raise CustomException(msg="火山引擎未返回高清图片地址")

            upscaled_url = upscaled_list[0]
            return {
                "task_id": data.task_id,
                "status": "success",
                "upscaled_url": upscaled_url,  # 先全量返回给前端看看，调通了再精简
            }

        except Exception as e:
            print(f"❌ 火山引擎调用失败: {str(e)}")
            # raise CustomException(msg=f"图像超分失败: {str(e)}")
            raise e

    @classmethod
    async def update_task_detail_service(cls, task_id: int, data: dict, auth: any):
        """
        更新任务记录
        """
        # 这里的 FissionTaskCRUD 是你之前定义的数据库操作类
        # 确保它有 update 方法
        target_url = data.get("image_url")

        # 如果检测到是火山引擎的域名，自动执行“洗白”入库操作
        if target_url and "byteimg.com" in target_url:
            # 自动转存并替换为 MinIO 永久链接
            permanent_url = await cls.transfer_volc_to_minio(target_url)
            data["image_url"] = permanent_url

        affected_rows = await FissionTaskCRUD(auth).update(id=task_id, data=data)

        if affected_rows == 0:
            raise CustomException(msg="更新失败，记录可能不存在")

        return True

    @staticmethod
    async def transfer_volc_to_minio(volc_url: str) -> str:
        """
        核心中转逻辑：抓取火山引擎图片 -> 伪造 UploadFile -> 存入私有 MinIO
        """
        async with httpx.AsyncClient() as client:
            try:
                # 1. 抓取火山引擎生成的临时高清图
                # 设置 30s 超时，防止大图下载过慢导致请求挂掉
                resp = await client.get(volc_url, timeout=30.0)
                resp.raise_for_status()  # 如果火山返回 403 或 500 直接抛出异常

                file_content = resp.content

                # 2. 🚀 关键步骤：伪造一个 FastAPI/Starlette 兼容的 UploadFile 对象
                # 这样可以直接“骗过”你原有的 UploadUtil.upload_to_minio 逻辑
                timestamp = int(datetime.now().timestamp())
                fake_file = UploadFile(
                    file=BytesIO(file_content), filename=f"upscale_{timestamp}.png"
                )

                # 3. 完美对接原有工具类
                # filename: 文件名, filepath: 相对路径, file_url: MinIO 访问全路径
                _, _, file_url = await UploadUtil.upload_to_minio(file=fake_file)

                print(f"✅ 图片已成功从火山转存至 MinIO: {file_url}")
                return file_url

            except httpx.HTTPStatusError as e:
                print(f"❌ 抓取火山图片失败，状态码: {e.response.status_code}")
                raise CustomException(msg="高清图抓取失败，请稍后重试")
            except Exception as e:
                print(f"❌ 转存 MinIO 过程中发生未知异常: {str(e)}")
                raise e

    @classmethod
    async def regenerate_task_v2_service(cls, auth: any, data: dict) -> dict:
        """
        单图微调重绘：继承旧版本的 Seed，基于新参数生成 V2/V3，并放回任务池等 Agent 抢单
        """
        task_id = data.get("task_id")
        user_params = data.get("params", {})  # 前端传过来的最新全量参数

        # 1. 校验与查库
        task = await FissionTaskCRUD(auth).get(id=task_id)
        if not task:
            raise CustomException(msg=f"找不到指定的任务记录 (ID: {task_id})")

        history = list(task.version_history or [])
        if not history:
            raise CustomException(msg="任务版本历史数据异常，无法重绘")

        # 2. 🎯 提取“传家宝”：找到当前版本的 Seed
        current_v_data = next(
            (h for h in history if h.get("v") == task.current_version), history[-1]
        )
        inherited_seed = current_v_data.get("seed", -1)

        # 3. 🎨 重新组装提示词 (Prompt)
        # 🚀 必须与 create_fission_service 里的模板一模一样！
        GOLDEN_TEMPLATE = (
            "写实摄影风格，{style}，{lighting_detail}。主场景位于{scene_detail}。"
            "一位{age}岁{gender}性，中国汉族面孔。{face_description}。"
            "眼神自然清澈，灵动有神。眼波流转，眼底眼神光（catchlight）温润而不刺眼。"
            "虹膜纹理自然呈现，深邃且富有层次感。睫毛浓密清晰，不突变。"
            "{hairstyle}。身着{clothing}。{action}，{view}。"
            "画面呈现极致的真实质感，{skin_texture}，{atmosphere_detail}，8k超高清分辨率。"
            "相机参数：Canon EOS R5, 50mm f/1.2, 1/250s, ISO 400，比例9：16。Do not change the background."
        )

        try:
            # 用前端传来的新参数填充，核心属性(age/gender)坚决从外层取，防止被篡改
            new_prompt = GOLDEN_TEMPLATE.format(
                style=user_params.get("style", "写实摄影"),
                lighting_detail=user_params.get("lighting_detail", ""),
                scene_detail=user_params.get("scene_detail", ""),
                age=task.age,
                gender=task.gender,
                face_description=user_params.get("face_description", ""),
                atmosphere_detail=user_params.get("atmosphere_detail", ""),
                skin_texture=user_params.get("skin_texture", ""),
                hairstyle=user_params.get("hairstyle", ""),
                clothing=user_params.get("clothing", ""),
                action=user_params.get("action", ""),
                view=user_params.get("view", "中景"),
            )
        except KeyError as e:
            raise CustomException(msg=f"重绘提示词组装失败，缺失参数: {str(e)}")

        # 4. 📦 组装新版本的 JSON 快照
        new_v_num = task.current_version + 1
        new_version_record = {
            "v": new_v_num,
            "url": "",  # 等待 Agent 回传
            "seed": inherited_seed,  # 🚀 核心：强行注入历史 Seed！
            "status": "waiting",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "params_snapshot": user_params,  # 存入这一版的参数快照
            "positive_prompt": new_prompt,
        }

        history.append(new_version_record)

        # 5. 🚦 更新数据库，点亮“接单”信号灯
        update_data = {
            "version_history": history,
            "current_version": new_v_num,
            "positive_prompt": new_prompt,  # 覆盖外层，方便 Agent SQL 直接 Select
            "process_status": 0,  # 🚀 核心：置为 0，重新进入任务池！
        }

        # 调用你框架的 update 方法，它会自动 flush 和 commit
        await FissionTaskCRUD(auth).update(id=task.id, data=update_data)

        return {
            "task_id": task.id,
            "new_version": new_v_num,
            "inherited_seed": inherited_seed,
            "msg": f"新版本 v{new_v_num} 已加入生成队列",
        }

    @classmethod
    async def regenerate_expert_task_service(cls, auth: any, data: dict) -> dict:
        """
        专家模式-单图自由重绘：完全由前端控制 Prompt，后端仅负责版本管理、Seed 继承和任务入池
        """
        task_id = data.get("task_id")
        # 🚀 核心：直接接收用户在前端修改好的完整提示词
        custom_prompt = data.get("positive_prompt")
        # 用户可能也微调了快照参数(用于界面回显)
        user_params = data.get("params", {})

        if not custom_prompt:
            raise CustomException(msg="重绘指令 (Prompt) 不能为空")

        # 1. 查库
        task = await FissionTaskCRUD(auth).get(id=task_id)
        if not task:
            raise CustomException(msg=f"找不到任务记录 (ID: {task_id})")

        history = list(task.version_history or [])
        if not history:
            raise CustomException(msg="任务版本历史异常，无法重绘")

        # 2. 🎯 继承“传家宝” Seed：维持人物一致性的关键
        current_v_data = next(
            (h for h in history if h.get("v") == task.current_version), history[-1]
        )
        inherited_seed = current_v_data.get("seed", -1)

        # 3. 📦 组装 V+1 版本记录
        new_v_num = task.current_version + 1
        new_version_record = {
            "v": new_v_num,
            "url": "",  # 等待 Agent 执行后回调
            "seed": inherited_seed,  # 🚀 核心：强制使用历史 Seed
            "status": "waiting",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "params_snapshot": user_params,  # 这里的快照存用户最新的修改
            "positive_prompt": custom_prompt,  # 🚀 使用用户自由输入的指令
        }

        history.append(new_version_record)

        # 4. 🚦 更新任务状态，送回公海池
        update_data = {
            "version_history": history,
            "current_version": new_v_num,
            "positive_prompt": custom_prompt,  # 覆盖外层，Agent 拿到的是最新版
            "process_status": 0,  # 🚀 置为 0，让 ComfyUI Agent 重新抢单
        }

        # 执行更新
        await FissionTaskCRUD(auth).update(id=task.id, data=update_data)

        return {
            "task_id": task.id,
            "new_version": new_v_num,
            "inherited_seed": inherited_seed,
            "msg": f"专家重绘任务 v{new_v_num} 已加入队列",
        }

    @classmethod
    async def volcengine_face_swap(cls, face_url: str, base_image_url: str) -> str:
        """
        使用火山官方 SDK 调用 faceswap_ai 换脸 (全 Base64 传输版)
        """
        # 1. 初始化视觉服务
        visual_service = VisualService()
        visual_service.set_ak(settings.VOLC_AK)
        visual_service.set_sk(settings.VOLC_SK)

        try:
            # 🚀 核心改动：并发下载两张图片，效率翻倍！
            # 绝不一个一个等，两个一起下
            face_b64, base_b64 = await asyncio.gather(
                ImageUtil.fetch_to_base64(face_url),
                ImageUtil.fetch_to_base64(base_image_url),
            )
            print(
                f"📊 Base64 Size Check - Face: {len(face_b64)/1024/1024:.2f}MB, Base: {len(base_b64)/1024/1024:.2f}MB"
            )

            if len(face_b64) < 100 or len(base_b64) < 100:
                raise Exception("Base64 数据过短，疑似下载到了空文件")
        except Exception as e:
            print(f"❌ 资源下载或转换 Base64 失败: {str(e)}")
            raise CustomException(msg=f"资源预处理失败: {str(e)}")

        # 2. 组装请求 Body
        # 注意：当使用 Base64 时，字段名变为 binary_data_base64
        body = {
            "req_key": "faceswap_ai",
            "binary_data_base64": [
                base_b64,  # 索引 1: 底片模板
                face_b64,  # 索引 0: 真人脸
            ],
            "do_risk": False,
            "gpen": 0,
            "skin": 0,
            "return_url": True,  # 🚀 依然保留这个，让它回传 URL 而不是又吐回一个大 Base64
        }

        # 3. 🚀 呼叫官方 SDK
        try:
            # SDK 会自动处理签名，由于我们传的是 Body 里的 Base64，它会自动算 Hash
            resp = visual_service.cv_process(body)

            if resp.get("code") == 10000:
                final_url = resp["data"]["image_urls"][0]
                print(f"✨ 火山换脸成功，回传预览 URL: {final_url}")
                return final_url
            else:
                error_msg = resp.get("message", "未知错误")
                print(f"❌ 火山接口报错: {error_msg}")
                raise Exception(error_msg)

        except Exception as e:
            raise Exception(f"火山引擎服务交互异常: {str(e)}")

    @classmethod
    async def face_swap_volcengine_service(
        cls, auth: any, task_id: int, target_face_url: str, target_url: str
    ) -> dict:
        """
        火山换脸并持久化入库：结果存入 swapped_url
        """
        crud = FissionTaskCRUD(auth)
        task = await crud.get(id=task_id)
        if not task:
            raise CustomException(msg="任务不存在")

        # 1. 准备底图 (必须是已经生成的 image_url)

        # 2. 🚀 调用火山引擎 SDK (此处为逻辑流程)
        temp_swapped_url = await cls.volcengine_face_swap(target_url, target_face_url)
        print(f"🚀 换脸结果临时 URL: {temp_swapped_url}")
        # 3. 🚀 关键步骤：转存自家 MinIO (防止火山临时链接过期)
        # 这里的 upload_from_url 是咱们之前写好的工具方法
        final_minio_url = await cls.transfer_volc_to_minio(temp_swapped_url)

        # 4. 写入新字段，不覆盖原有的 image_url（保留底片）
        update_data = {
            "swapped_url": final_minio_url,
            "swapped_time": datetime.now(),
            "process_status": 2,  # 确保状态是成功
        }

        await crud.update(id=task.id, data=update_data)

        return {
            "task_id": task.id,
            "swapped_url": final_minio_url,
            "msg": "换脸成功并已持久化存档",
        }

    @classmethod
    async def infer_background_service(
        cls, auth: any, image_url: str, location: str = None
    ) -> dict:
        """
        多模态背景反推服务：将图片转为文本描述
        """

        # 2. 调起多模态引擎进行反推
        # 这里引用你上面的引擎实例
        try:

            visual_params = await llm_action_engine.infer_visual_context(
                image_url, location
            )

            # 🚀 核心：如果你想在反推的同时，也更新一下这个任务的当前参数，可以执行一次静默保存
            # 但通常建议只返回给前端，让用户在界面上确认后再点击“生成新版本”

            return {
                "scene_detail": visual_params.get("scene_detail", ""),
                "lighting_detail": visual_params.get("lighting_detail", ""),
                "atmosphere_detail": visual_params.get("atmosphere_detail", ""),
                "msg": "视觉特征反推完成",
            }

        except Exception as e:
            print(f"❌ 多模态分析失败: {str(e)}")
            raise CustomException(msg=f"图片分析失败: {str(e)}")

    @classmethod
    async def prepare_background_task_service(
        cls, auth: any, task_id: int, bg_image_url: str, custom_prompt: str | None = None
    ) -> dict:
        """
        第一步：在数据库里预先插一条版本记录
        """
        crud = FissionTaskCRUD(auth)
        task = await crud.get(id=task_id)
        if not task:
            raise CustomException(msg="找不到指定的任务")

        # 使用深拷贝打破 SQLAlchemy 脏检查免疫
        new_history = copy.deepcopy(task.bg_version_history or [])
        new_v = len(new_history) + 1
        started_at_ts = time.time()

        new_entry = {
            "v": new_v,
            "status": "processing",
            "target_bg_image": bg_image_url,
            "custom_prompt": custom_prompt,
            "final_prompt": None,
            "duration_seconds": None,
            "result_url": None,
            "error_msg": None,
            "created_at": datetime.fromtimestamp(started_at_ts).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "started_at_ts": started_at_ts,
        }
        new_history.append(new_entry)

        # 更新任务表，标记当前背景版本正在处理
        await crud.update(
            id=task.id,
            data={"bg_version_history": new_history, "current_bg_version": new_v},
        )

        return {"v": new_v, "task_id": task_id}

    # ==========================================
    # 2. 🚀 核心后台任务：把你的旧逻辑塞进这里
    # ==========================================
    @classmethod
    async def execute_volcengine_fusion_task(
        cls,
        auth: any,
        task_id: int,
        model: str,
        bg_image_url: str,
        custom_prompt: str,
        version: int,
    ):
        """
        真实的后台干活逻辑：转圈、拉取、反推、生图
        """
        final_prompt = None
        try:
            # 1. 查数据库拿到人物底片
            task = await FissionTaskCRUD(auth).get(id=task_id)
            if not task:
                raise Exception("找不到精修任务主体")
            person_image_url = task.image_url

            # 2. VLM 视觉反推背景光影（这一步耗时，放在后台正合适）
            visual_params = await llm_action_engine.infer_visual_prompt_template(
                bg_image_url
            )

            # 3. 并发下载本地 MinIO 图片 -> 压缩 -> 转 Base64
            person_raw_b64, bg_raw_b64 = await asyncio.gather(
                ImageUtil.fetch_to_base64(person_image_url),
                ImageUtil.fetch_to_base64(bg_image_url),
            )
            person_data_uri = f"data:image/jpeg;base64,{person_raw_b64}"
            bg_data_uri = f"data:image/jpeg;base64,{bg_raw_b64}"

            # 4. 调用大模型引擎进行融合
            final_prompt = (custom_prompt or "") + visual_params
            logger.info(f"🚀 [后台任务] 启动融合任务 v{version}... {final_prompt}")
            if model == "seedream":
                fused_url = (
                    await llm_action_engine.generate_image_by_doubao_with_images(
                        prompt=final_prompt,
                        image_urls=[person_data_uri, bg_data_uri],
                    )
                )
            elif model == "wan2.7-image":
                fused_url = await llm_action_engine.generate_image_by_qwen_edit(
                    prompt=final_prompt,
                    image_urls=[person_data_uri, bg_data_uri],
                )
            elif model == "banana_2":
                fused_url = await llm_action_engine.generate_image_by_banana_edit(
                    prompt=final_prompt,
                    image_urls=[person_data_uri, bg_data_uri],
                )
            elif model in {"gpt", "gpt-image-2"}:
                fused_url = await llm_action_engine.generate_image_by_gpt_edit(
                    prompt=final_prompt,
                    image_urls=[person_data_uri, bg_data_uri],
                )
            else:
                raise CustomException(msg=f"暂不支持的背景融合模型: {model}")

            # 5. 🎉 成功：回填数据库，将状态改为 success
            await cls.update_bg_task_status(
                auth=auth,
                task_id=task_id,
                version=version,
                status="success",
                result_url=fused_url,
                final_prompt=final_prompt,
            )

        except Exception as e:
            # 6. 🚨 失败：捕获所有异常，回填 error_msg 避免任务一直卡在 processing
            if isinstance(e, CustomException):
                logger.error(
                    f"后台融合任务异常 [TaskID: {task_id}]: {e.msg} | detail: {e.data}"
                )
            else:
                logger.exception(
                    f"后台融合任务异常 [TaskID: {task_id}]: {type(e).__name__}: {e!s}"
                )
            await cls.update_bg_task_status(
                auth=auth,
                task_id=task_id,
                version=version,
                status="failed",
                error_msg=str(e),
                final_prompt=final_prompt,
            )

    # ==========================================
    # 3. 状态更新工具 (你之前复制的那个)
    # ==========================================
    @classmethod
    async def update_bg_task_status(
        cls,
        auth: any,
        task_id: int,
        version: int,
        status: str,
        result_url: str = None,
        error_msg: str = None,
        final_prompt: str = None,
    ):
        crud = FissionTaskCRUD(auth)
        task = await crud.get(id=task_id)
        if not task:
            return

        # 1. 深拷贝修改数据
        new_history = copy.deepcopy(task.bg_version_history or [])
        for item in new_history:
            if int(item.get("v", 0)) == int(version):
                item["status"] = status
                if result_url:
                    item["result_url"] = result_url
                if error_msg:
                    item["error_msg"] = error_msg
                if final_prompt:
                    item["final_prompt"] = final_prompt
                started_at_ts = item.get("started_at_ts")
                if status != "processing" and started_at_ts:
                    item["duration_seconds"] = round(
                        max(time.time() - float(started_at_ts), 0), 1
                    )
                break

        # 2. 🚀 直接修改对象属性
        task.bg_version_history = new_history
        if status == "success" and result_url:
            task.current_bg_url = result_url

        # 3. 🚀 核武器：明确告诉 SQLAlchemy，这个 JSON 字段被改了，不要偷懒！
        flag_modified(task, "bg_version_history")

        # 4. 把对象塞回 session 并强行提交
        try:
            await auth.db.flush()
            await auth.db.refresh(task)

            # 🚀 救命神药：在后台任务里，必须显式调用 commit！
            await auth.db.commit()
            logger.info(f"✅ 任务 {task_id} 版本 v{version} 状态已强制回填为: {status}")
        except Exception as e:
            logger.error(f"❌ 强制 Commit 失败: {str(e)}")

    @classmethod
    async def brainstorm_expert_prompts(
        cls,
        auth: AuthSchema,
        location: str,
        gender: str,
        age: int,
        extra_command: str = "",
        theme: dict = None,
    ) -> list[dict]:
        """
        🚀 专家创作台专属：调 LLM -> 组装黄金模板 -> 返回给前端的 15 条提示词数组
        (绝对不碰数据库，纯内存操作)
        """
        # 1. 你的黄金模板 (和原来保持一致)
        GOLDEN_TEMPLATE = (
            "写实摄影风格，{style}，{lighting_detail}。主场景位于{scene_detail}。"
            "一位{age}岁中国汉族面孔{gender}。{face_description}。"
            "眼神自然清澈，灵动有神。眼波流转，眼底眼神光温润而不刺眼。"
            "虹膜纹理自然呈现，深邃且富有层次感。睫毛浓密清晰，不突变。"
            "{hairstyle}。身着{clothing}。{action}，{view}。"
            "画面呈现极致的真实质感，{skin_texture}，{atmosphere_detail}，8k超高清分辨率。"
            "相机参数：Canon EOS R5, 50mm f/1.2, 1/250s, ISO 400，比例9：16。Do not change the background."
        )

        # 2. 调起 AI 摄影导演获取策划素材
        # 🚀 注意：这里多传了一个 extra_command 进去！
        llm_result = await llm_action_engine.run_fission_pipeline(
            auth,
            location=location,
            gender=gender,
            age=age,
            extra_command=extra_command,
            current_theme=theme,
        )

        # 3. 提取全局通用属性 (让 15 张图的环境和服装保持一致)
        style = llm_result.get("selected_style", "写实摄影")
        lighting_detail = llm_result.get("lighting_detail", "")
        scene_detail = llm_result.get("scene_detail", "")
        hairstyle = llm_result.get("hairstyle", "")
        clothing = llm_result.get("clothing", "")
        face_description = llm_result.get("face_description", "面部轮廓清晰，神态自然")
        skin_texture = llm_result.get("skin_texture", "皮肤纹理真实细腻").replace(
            "汗毛孔", "毛孔"
        )
        atmosphere_detail = llm_result.get("atmosphere_detail", "空气感通透")

        # 4. 🚀 组装返回给前端的数据结构
        prompt_list = []
        for action in llm_result.get("actions", []):
            try:
                # 把动作和景别塞进模板
                rendered_prompt = GOLDEN_TEMPLATE.format(
                    style=style,
                    lighting_detail=lighting_detail,
                    scene_detail=scene_detail,
                    age=age,
                    gender=gender,
                    face_description=face_description,
                    atmosphere_detail=atmosphere_detail,
                    skin_texture=skin_texture,
                    hairstyle=hairstyle,
                    clothing=clothing,
                    action=action.get("desc", ""),
                    view=action.get("view_type", "中景"),
                )
            except KeyError as e:
                rendered_prompt = f"渲染失败，模板缺失字段: {str(e)}"

            # 严格对齐前端要求的字段名
            prompt_list.append(
                {
                    "view_type": action.get("view_type", "中景"),
                    "action_desc": action.get("desc", ""),
                    "positive_prompt": rendered_prompt.replace("汗毛孔", "毛孔"),
                    "selected_scene": llm_result.get("selected_scene", ""),
                    "selected_style": llm_result.get("selected_style", "写实摄影"),
                }
            )

        # 直接把这 15 条组装好的数据丢回给前端
        return prompt_list

    @classmethod
    async def submit_expert_fission_data(
        cls, auth: any, payload: SubmitExpertBatchRequest
    ) -> tuple[dict, list[dict]]:
        """
        🚀 专家模式提交入库：直接接收前端拼装好的 15 个 prompt，构建入库数据字典
        """
        batch_sn = f"B{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # 1. 准备批次主表数据
        batch_data = {
            "batch_sn": batch_sn,
            "input_location": payload.location,
            "gender": payload.gender,
            "age": payload.age,
            "theme": payload.theme,
            "selected_scene": payload.selected_scene,  # 🚀 完美闭环
            "selected_style": payload.selected_style,  # 🚀 完美闭环
            "task_count": len(payload.tasks),
        }

        # 2. 准备子任务数据
        tasks_data = []
        for i, task in enumerate(payload.tasks):
            tasks_data.append(
                {
                    "task_sn": f"T{batch_sn[1:]}{i:02d}",
                    "location": payload.location,
                    "style_tag": "专家高定",
                    "gender": payload.gender,
                    "age": payload.age,
                    "view_type": task.view_type,
                    "action_desc": task.action_desc,
                    "positive_prompt": task.positive_prompt,  # 👈 直接拿前端传来的！
                    "process_status": 0,  # 等待 ComfyUI 机器拉取
                    # 🚀 初始化版本历史
                    "current_version": 1,
                    "version_history": [
                        {
                            "v": 1,
                            "url": "",
                            "positive_prompt": task.positive_prompt,
                            "status": "waiting",
                            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "seed": None,
                            # 👈 专家模式因为是手写的，没有细碎的 params 拆解，可以直接存一个标识
                            "params_snapshot": {
                                "mode": "expert_custom",
                                "raw_prompt": task.positive_prompt,
                            },
                        }
                    ],
                }
            )
        crud = FissionBatchCRUD(auth)
        new_batch = await crud.create_fission_bundle_crud(batch_data, tasks_data)
        # 接下来你就可以拿着 batch_data 和 tasks_data 去执行数据库 INSERT 操作了
        return new_batch
