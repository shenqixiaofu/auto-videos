from typing import Annotated
from fastapi import APIRouter, Depends, Path, Query, Body
from fastapi.responses import JSONResponse

from app.api.v1.module_system.auth.schema import AuthSchema
from app.common.response import ResponseSchema, SuccessResponse
from app.core.dependencies import AuthPermission
from app.core.logger import log
from app.core.router_class import OperationLogRoute
from fastapi.encoders import jsonable_encoder  # 👈 加上这句导入
from fastapi import BackgroundTasks

# 导入咱们新区的组件
from .schema import (
    BackgroundFusionSchema,
    BrainstormExpertRequest,
    FaceSwapSchema,
    FissionCreateSchema,
    BatchOutSchema,
    FissionManualCreateSchema,
    InferBackgroundSchema,
    RegenerateTaskSchema,
    SubmitExpertBatchRequest,
    TaskOutSchema,
    FissionQueryParam,
    ClaimTaskSchema,
    TaskCallbackSchema,
    UpscaleCreateSchema,
)
from .service import FissionService

# 定义路由：prefix 会自动映射到 /ai_image/fission
FissionRouter = APIRouter(
    route_class=OperationLogRoute, prefix="/fission", tags=["AI 自动化裂变"]
)


@FissionRouter.post(
    "/generate",
    summary="触发 1 进 10 自动化裂变",
    description="输入地点/人像，执行 Action A/B/C 逻辑，全自动产出 10 组黄金提示词任务",
)
async def trigger_fission_controller(
    data: Annotated[FissionCreateSchema, Body(description="JSON请求体")],
    auth: Annotated[
        AuthSchema, Depends(AuthPermission(["module_ai_image:fission:generate"]))
    ],
) -> JSONResponse:
    """
    触发自动化裂变

    逻辑：
    1. 接收地点、性别、年龄
    2. 调起 AI 摄影导演 (LLM) 进行场景/风格/动作策划
    3. 原子化入库 1 个 Batch 和 10 个 Task
    """
    # 为了极度安全，咱们先拿一下 user_id
    user_id = auth.user.id if auth.user else "System"
    log.info(f"用户 {user_id} 发起裂变请求: {data.location}")

    result = await FissionService.create_fission_service(auth=auth, data=data)

    return SuccessResponse(
        data=jsonable_encoder(result),
        msg=f"AI 导演策划完成！已成功下发 {result.get('batch_sn')} 批次的 10 组生图任务",
    )


@FissionRouter.get(
    "/batch/list",
    summary="获取裂变批次列表",
    response_model=ResponseSchema[list[BatchOutSchema]],
)
async def get_fission_batches_controller(
    search: Annotated[FissionQueryParam, Query()],
    auth: Annotated[
        AuthSchema, Depends(AuthPermission(["module_ai_image:fission:list"]))
    ],
) -> JSONResponse:
    """
    获取历史裂变批次，方便查看 Action A 和 Action B 的决策结果
    """
    result_list = await FissionService.get_batch_list_service(auth=auth, search=search)
    return SuccessResponse(data=jsonable_encoder(result_list))


from fastapi import Query
from typing import Optional


@FissionRouter.get("/batch/filter-options", summary="获取所有聚合检索下拉选项")
async def get_all_batch_filter_options(
    # 新增 gender 参数，Query(None) 表示可选，默认值为 None
    gender: Optional[str] = Query(None, description="性别/人群标签筛选"),
    auth: Annotated[
        AuthSchema, Depends(AuthPermission(["module_ai_image:fission:list"]))
    ] = None,
) -> JSONResponse:
    """
    支持联动：如果传了 gender，则返回该人群下的去重选项；否则返回全量选项。
    """
    # 将 gender 透传给 Service 层
    data = await FissionService.get_all_filter_options_service(auth, gender=gender)
    return SuccessResponse(data=data)


@FissionRouter.get(
    "/batch/{id}/tasks",
    summary="获取批次下的任务详情",
    response_model=ResponseSchema[list[TaskOutSchema]],
)
async def get_batch_tasks_controller(
    id: Annotated[int, Path(description="批次主键ID")],
    auth: Annotated[
        AuthSchema, Depends(AuthPermission(["module_ai_image:fission:detail"]))
    ],
) -> JSONResponse:
    """
    查看某个批次裂变出的 10 个具体动作描述、提示词及其生成状态
    """
    result_list = await FissionService.get_task_batch_service(auth=auth, batch_id=id)
    return SuccessResponse(data=jsonable_encoder(result_list))


@FissionRouter.delete("/batch/{batch_id}", summary="删除生图批次")
async def delete_fission_batch(
    batch_id: int,
    auth: Annotated[
        AuthSchema, Depends(AuthPermission(["module_ai_image:fission:delete"]))
    ],
):
    await FissionService.delete_fission_batch_service(auth, batch_id)
    return SuccessResponse(msg="销毁成功，数据已彻底清理")


@FissionRouter.get(
    "/batch/{batch_id}",
    summary="🔍 获取生图批次详情及任务列表",
    # 权限建议用 list 或 query，视你系统的权限字典而定
    dependencies=[Depends(AuthPermission(["module_ai_image:fission:list"]))],
)
async def get_batch_detail(
    batch_id: int,
    auth: Annotated[
        AuthSchema, Depends(AuthPermission(["module_ai_image:fission:list"]))
    ],
):
    """
    ### 业务逻辑：
    1. 根据 batch_id 获取批次主表信息（地点、性别、年龄等基础配置）。
    2. 关联查询该批次下的所有子任务 (Tasks)。
    3. 组装后返回给前端，用于通过 URL 参数 (batchId) 恢复工作台数据。
    """

    # 调用 Service 层查询主子表数据
    detail_data = await FissionService.get_batch_detail_service(auth, batch_id)
    safe_data = jsonable_encoder(detail_data)

    # 3. 再放进 Response 返回
    return SuccessResponse(msg="查询成功", data=safe_data)


@FissionRouter.post(
    "/task/claim",
    summary="Agent 节点高并发抢单接口",
)
async def claim_task_controller(
    data: Annotated[ClaimTaskSchema, Body(description="Agent 身份信息")],
    auth: Annotated[
        AuthSchema, Depends(AuthPermission(["module_ai_image:fission:generate"]))
    ],
) -> JSONResponse:
    """
    ComfyUI 脚本专属：轮询获取未处理的生图任务
    """
    task_dict = await FissionService.claim_task_service(
        auth=auth, agent_id=data.agent_id
    )

    if not task_dict:
        # code=0 表示请求成功，但 data=None 告诉脚本现在没活儿干，去睡几秒再来
        return SuccessResponse(data=None, msg="目前没有待处理的任务")

    return SuccessResponse(
        data=jsonable_encoder(task_dict),
        msg=f"节点 {data.agent_id} 抢单成功！任务号: {task_dict.get('task_sn')}",
    )


@FissionRouter.post(
    "/task/callback",
    summary="Agent 节点任务结果回传",
)
async def task_callback_controller(
    payload: Annotated[TaskCallbackSchema, Body(description="生图结果数据")],
    auth: Annotated[
        AuthSchema, Depends(AuthPermission(["module_ai_image:fission:generate"]))
    ],
) -> JSONResponse:
    """
    ComfyUI 脚本专属：交图/报错接口
    """
    await FissionService.task_callback_service(auth=auth, payload=payload)

    return SuccessResponse(msg="任务状态已闭环更新！")


@FissionRouter.get(
    "/task/{task_id}",
    summary="查询单张生图任务详情",
)
async def get_task_detail_controller(
    task_id: Annotated[int, Path(description="子任务 ID")],
    auth: Annotated[
        AuthSchema,
        Depends(AuthPermission(["module_ai_image:fission:list"])),  # 权限视你的字典而定
    ],
) -> JSONResponse:
    """
    提供给前端编辑页或预览弹窗，获取单张图片的详细信息（包含原 prompt 和图片 url）
    """
    # 这里调用 Service 层去查库 (我们在 Service 里顺手补一下这个方法)
    task_data = await FissionService.get_task_detail_service(auth=auth, task_id=task_id)

    return SuccessResponse(msg="获取任务详情成功", data=task_data)


@FissionRouter.post(
    "/task/upscale",
    summary="一键高清放大 (调用火山引擎 API)",
)
async def upscale_task_controller(
    payload: Annotated[UpscaleCreateSchema, Body(description="高清放大请求参数")],
    auth: Annotated[
        AuthSchema, Depends(AuthPermission(["module_ai_image:fission:generate"]))
    ],
) -> JSONResponse:
    """
    接收前端一键高清请求，将 MinIO 原图转 Base64 后推送至火山引擎进行画质超分
    """
    # 调用咱们刚才写好的、带 Base64 转换和火山请求的 Service
    result = await FissionService.create_upscale_service(auth=auth, data=payload)

    return SuccessResponse(msg="高清放大成功！", data=result)


@FissionRouter.put(
    "/task/{task_id}",
    summary="更新子任务信息 (如回填高清图、修改Prompt)",
)
async def update_task_controller(
    task_id: Annotated[int, Path(description="子任务 ID")],
    payload: Annotated[dict, Body(description="需要更新的字段集")],  # 灵活起见先用 dict
    auth: Annotated[
        AuthSchema, Depends(AuthPermission(["module_ai_image:fission:edit"]))
    ],
) -> JSONResponse:
    """
    用于回填高清图 URL、持久化保存修改后的 Prompt 等
    """
    # 直接调用 CRUD 或 Service 更新
    await FissionService.update_task_detail_service(
        task_id=task_id, data=payload, auth=auth
    )

    return SuccessResponse(msg="数据已同步至数据库")


@FissionRouter.post(
    "/task/infer-background",
    summary="多模态反推：识图生成背景与光影参数",
)
async def infer_background_controller(
    payload: InferBackgroundSchema,
    auth: Annotated[
        AuthSchema, Depends(AuthPermission(["module_ai_image:fission:edit"]))
    ],
) -> JSONResponse:
    """
    前端上传风景图后，调用大模型分析其环境，并返回适配的 scene_detail、lighting_detail 等参数
    """
    # 调用 Service 层的多模态方法 (咱们之前写的 LLMActionEngine)
    infer_result = await FissionService.infer_background_service(
        auth=auth, image_url=payload.image_url, location=payload.location
    )

    # 这里的 infer_result 应该是一个字典，包含 scene_detail, lighting_detail, atmosphere_detail
    return SuccessResponse(msg="背景反推成功", data=infer_result)


@FissionRouter.post(
    "/task/regenerate",
    summary="进化重绘：基于参数快照生成新版本 (v2/v3)",
)
async def regenerate_task_controller(
    payload: RegenerateTaskSchema,
    auth: Annotated[
        AuthSchema, Depends(AuthPermission(["module_ai_image:fission:edit"]))
    ],
) -> JSONResponse:
    """
    接收用户在导演面板微调后的参数，锁定原 Seed，生成带版本号的新图
    """
    # 调用 Service 层的方法，生成新的 prompt 并塞入 version_history，最后派发给 Agent
    new_version_info = await FissionService.regenerate_task_v2_service(
        auth=auth, data=payload.model_dump()
    )

    return SuccessResponse(msg="重绘指令已成功下发", data=new_version_info)


@FissionRouter.post(
    "/task/regenerate-expert",
    summary="🎨 专家重绘：基于修改后的 Prompt 重新生成版本",
)
async def regenerate_expert_task_controller(
    payload: dict = Body(
        ...,
        example={
            "task_id": 123,
            "positive_prompt": "new prompt string...",
            "params": {"theme": "xxx", "vibe": "xxx"},
        },
    ),
    auth: Annotated[
        AuthSchema, Depends(AuthPermission(["module_ai_image:fission:edit"]))
    ] = None,
):
    """
    ### 业务逻辑：
    1. 接收前端修改后的单条任务 Prompt。
    2. 继承该任务当前版本的 Seed (保持人脸一致性)。
    3. 创建 V+1 版本记录并把任务状态重置为 0，让 ComfyUI 重新抓取生图。
    """

    # 直接调用刚才写好的 Service
    result = await FissionService.regenerate_expert_task_service(
        auth=auth, data=payload
    )

    return SuccessResponse(msg="重绘任务已提交至队列", data=result)


@FissionRouter.post(
    "/task/face-swap",
    summary="极速换脸：调用火山引擎 API 直接融合面部",
)
async def face_swap_controller(
    payload: FaceSwapSchema,
    auth: Annotated[
        AuthSchema, Depends(AuthPermission(["module_ai_image:fission:edit"]))
    ],
) -> JSONResponse:
    """
    不经过 Agent，直接读取底片 URL 和人脸 URL，调用火山引擎接口并返回新图片链接
    """
    swap_result = await FissionService.face_swap_volcengine_service(
        auth=auth,
        task_id=payload.task_id,
        target_face_url=payload.target_face_url,
        target_url=payload.target_url,
    )

    return SuccessResponse(msg="换脸处理成功", data=swap_result)


@FissionRouter.post(
    "/expert/brainstorm",
    summary="专家创作台：脑暴 15 组生图剧本提示词",
)
async def brainstorm_expert_prompts_controller(
    payload: BrainstormExpertRequest,
    auth: Annotated[
        AuthSchema, Depends(AuthPermission(["module_ai_image:fission:edit"]))
    ],
) -> JSONResponse:
    """
    不碰数据库，接收专家面板参数，直接调取 LLM 脑暴出 15 组 ComfyUI 指令并返回给前端
    """
    # 直接调用咱们刚才写好的开环业务逻辑
    prompt_list = await FissionService.brainstorm_expert_prompts(
        auth,
        location=payload.location,
        gender=payload.gender,
        age=payload.age,
        theme=payload.theme,
        extra_command=payload.extra_command,
    )

    # 用你项目的统一成功响应体包裹返回
    return SuccessResponse(msg="脑暴成功", data=prompt_list)


@FissionRouter.post(
    "/task/background-fusion",
    summary="背景瞬移：异步提交融合任务",
)
async def background_fusion_controller(
    payload: BackgroundFusionSchema,
    background_tasks: BackgroundTasks,  # 🚀 引入 FastAPI 后台任务工具
    auth: Annotated[
        AuthSchema, Depends(AuthPermission(["module_ai_image:fission:edit"]))
    ],
) -> JSONResponse:
    # 1. 先在 Service 层创建一个“处理中”的记录，并拿到新的版本号
    new_version_info = await FissionService.prepare_background_task_service(
        auth=auth,
        task_id=payload.task_id,
        bg_image_url=payload.bg_image_url,
        custom_prompt=payload.custom_prompt,
    )

    # 2. 将耗时的火山引擎请求丢进后台任务队列
    background_tasks.add_task(
        FissionService.execute_volcengine_fusion_task,  # 真正干活的函数
        auth=auth,
        task_id=payload.task_id,
        bg_image_url=payload.bg_image_url,
        model=payload.model,
        custom_prompt=payload.custom_prompt,
        version=new_version_info["v"],
    )

    # 3. 立即返回，不让前端转圈等待
    return SuccessResponse(
        msg="背景融合任务已提交，正在排队施法中...", data=new_version_info
    )


@FissionRouter.post(
    "/batch/manual",
    summary="📸 手动补录裂变批次",
    dependencies=[Depends(AuthPermission(["ai:fission:manual"]))],  # 建议加上权限控制
)
async def manual_create_batch(
    auth: Annotated[
        AuthSchema, Depends(AuthPermission(["module_ai_image:fission:edit"]))
    ],
    obj_in: FissionManualCreateSchema = Body(...),
):
    """
    ### 业务逻辑：
    1. 接收前端传来的 MinIO URL 列表及元数据
    2. 调用 Service 层进行原子化写入 (Batch + Tasks)
    """
    # 直接调用我们之前准备好的 Service 方法
    await FissionService.manual_create_batch_service(auth, obj_in)

    return SuccessResponse(msg="手动批次创建成功，数据已同步至底片台")


@FissionRouter.post(
    "/expert/submit",
    summary="🚀 专家创作台：提交生图任务入库",
)
async def submit_expert_batch_controller(
    auth: Annotated[
        AuthSchema, Depends(AuthPermission(["module_ai_image:fission:edit"]))
    ],
    payload: SubmitExpertBatchRequest = Body(
        ..., description="专家模式的 15 组生图剧本参数"
    ),
):
    """
    ### 业务逻辑：
    1. 接收专家模式下前端确认好的 15 组底层指令。
    2. 调用 Service 层将前端 Payload 转换为数据库对应的 Batch 和 Task 字典格式。
    3. 存入数据库，任务状态默认为 0（等待 ComfyUI 拉取执行）。
    """
    # 1. 调用我们写好的 Service 方法，拿到组装好的主表和子表数据
    new_batch = await FissionService.submit_expert_fission_data(
        auth=auth, payload=payload
    )

    return SuccessResponse(
        msg="专家任务投递成功，已加入 ComfyUI 生成队列！",
        data={"batch_sn": new_batch.id},
    )
