from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Path, Query
from fastapi.responses import JSONResponse

from app.api.v1.module_system.auth.schema import AuthSchema
from app.common.response import ResponseSchema, SuccessResponse
from app.core.base_params import PaginationQueryParam
from app.core.dependencies import AuthPermission
from app.core.router_class import OperationLogRoute

from .schema import (
    VideoAssetDownloadOutSchema,
    VideoAssetMetadataOutSchema,
    VideoAssetOutSchema,
    VideoAssetUploadInitOutSchema,
    VideoAssetUploadInitSchema,
    VideoCoverImageModelOutSchema,
    VideoMultipartCompleteSchema,
    VideoMultipartPresignSchema,
    VideoMultipartUploadPartSchema,
    VideoProcessingConfigOutSchema,
    VideoProcessingConfigUpdateSchema,
    VideoTaskBatchCreateSchema,
    VideoTaskBatchDetailOutSchema,
    VideoTaskBatchQueryParam,
    VideoTaskCreateSchema,
    VideoTaskDebugOutSchema,
    VideoTaskDetailOutSchema,
    VideoTaskQueryParam,
    VideoTaskReviewSchema,
)
from .service import VideoProcessingService

VideoProcessingRouter = APIRouter(
    route_class=OperationLogRoute,
    prefix="/processing",
    tags=["智能视频"],
)


@VideoProcessingRouter.post(
    "/tasks",
    summary="创建自动剪辑任务",
    response_model=ResponseSchema[VideoTaskDetailOutSchema],
)
async def create_video_task_controller(
    data: Annotated[VideoTaskCreateSchema, Body(description="自动剪辑任务参数")],
    auth: Annotated[
        AuthSchema,
        Depends(AuthPermission(["module_video:processing:create"])),
    ],
) -> JSONResponse:
    """创建等待素材上传的自动剪辑任务。"""
    result = await VideoProcessingService.create_task_service(auth, data)
    return SuccessResponse(data=result, msg="自动剪辑任务创建成功")


@VideoProcessingRouter.post(
    "/batches",
    summary="创建自动剪辑批次",
    response_model=ResponseSchema[VideoTaskBatchDetailOutSchema],
)
async def create_video_batch_controller(
    data: Annotated[VideoTaskBatchCreateSchema, Body(description="自动剪辑批次参数")],
    auth: Annotated[
        AuthSchema,
        Depends(AuthPermission(["module_video:processing:create"])),
    ],
) -> JSONResponse:
    """创建文件夹导入批次。"""
    result = await VideoProcessingService.create_batch_service(auth, data)
    return SuccessResponse(data=result, msg="自动剪辑批次创建成功")


@VideoProcessingRouter.get(
    "/tasks",
    summary="分页查询自动剪辑任务",
    response_model=ResponseSchema[dict[str, Any]],
)
async def list_video_tasks_controller(
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[VideoTaskQueryParam, Depends()],
    auth: Annotated[
        AuthSchema,
        Depends(AuthPermission(["module_video:processing:query"])),
    ],
) -> JSONResponse:
    """分页查询当前用户的自动剪辑任务。"""
    result = await VideoProcessingService.list_tasks_service(
        auth=auth,
        page_no=page.page_no,
        page_size=page.page_size,
        search=search,
    )
    return SuccessResponse(data=result, msg="自动剪辑任务查询成功")


@VideoProcessingRouter.get(
    "/batches",
    summary="分页查询自动剪辑批次",
    response_model=ResponseSchema[dict[str, Any]],
)
async def list_video_batches_controller(
    page: Annotated[PaginationQueryParam, Depends()],
    search: Annotated[VideoTaskBatchQueryParam, Depends()],
    auth: Annotated[
        AuthSchema,
        Depends(AuthPermission(["module_video:processing:query"])),
    ],
) -> JSONResponse:
    """分页查询当前用户的自动剪辑批次。"""
    result = await VideoProcessingService.list_batches_service(
        auth=auth,
        page_no=page.page_no,
        page_size=page.page_size,
        search=search,
    )
    return SuccessResponse(data=result, msg="自动剪辑批次查询成功")


@VideoProcessingRouter.get(
    "/tasks/{task_id}",
    summary="查询自动剪辑任务详情",
    response_model=ResponseSchema[VideoTaskDetailOutSchema],
)
async def get_video_task_controller(
    task_id: Annotated[int, Path(description="自动剪辑任务ID")],
    auth: Annotated[
        AuthSchema,
        Depends(AuthPermission(["module_video:processing:query"])),
    ],
) -> JSONResponse:
    """查询任务、输入素材和输出产物。"""
    result = await VideoProcessingService.get_task_service(auth, task_id)
    return SuccessResponse(data=result, msg="自动剪辑任务详情查询成功")


@VideoProcessingRouter.get(
    "/tasks/{task_id}/debug",
    summary="查询自动剪辑任务调试信息",
    response_model=ResponseSchema[VideoTaskDebugOutSchema],
)
async def get_video_task_debug_controller(
    task_id: Annotated[int, Path(description="自动剪辑任务ID")],
    auth: Annotated[
        AuthSchema,
        Depends(AuthPermission(["module_video:processing:query"])),
    ],
) -> JSONResponse:
    """返回本次任务实际用到的提示词与生图参考帧。"""
    result = await VideoProcessingService.get_task_debug_service(auth, task_id)
    return SuccessResponse(data=result, msg="自动剪辑任务调试信息查询成功")


@VideoProcessingRouter.get(
    "/batches/{batch_id}",
    summary="查询自动剪辑批次详情",
    response_model=ResponseSchema[VideoTaskBatchDetailOutSchema],
)
async def get_video_batch_controller(
    batch_id: Annotated[int, Path(description="自动剪辑批次ID")],
    auth: Annotated[
        AuthSchema,
        Depends(AuthPermission(["module_video:processing:query"])),
    ],
) -> JSONResponse:
    """查询批次、子任务和全部素材。"""
    result = await VideoProcessingService.get_batch_service(auth, batch_id)
    return SuccessResponse(data=result, msg="自动剪辑批次详情查询成功")


@VideoProcessingRouter.get(
    "/config",
    summary="查询自动剪辑全局配置",
    response_model=ResponseSchema[VideoProcessingConfigOutSchema],
)
async def get_video_processing_config_controller(
    auth: Annotated[
        AuthSchema,
        Depends(AuthPermission(["module_video:processing:config"])),
    ],
) -> JSONResponse:
    """读取封面生图通道、模型名与提示词模板。"""
    result = await VideoProcessingService.get_processing_config_service(auth)
    return SuccessResponse(data=result, msg="自动剪辑全局配置查询成功")


@VideoProcessingRouter.get(
    "/config/image-models",
    summary="查询中转站生图模型清单",
    response_model=ResponseSchema[list[VideoCoverImageModelOutSchema]],
)
async def list_video_cover_image_models_controller(
    auth: Annotated[
        AuthSchema,
        Depends(AuthPermission(["module_video:processing:config"])),
    ],
) -> JSONResponse:
    """返回中转站支持生图的模型名，供高级设置下拉选择。"""
    result = await VideoProcessingService.list_cover_image_models_service(auth)
    return SuccessResponse(data=result, msg="生图模型清单查询成功")


@VideoProcessingRouter.put(
    "/config",
    summary="更新自动剪辑全局配置",
    response_model=ResponseSchema[VideoProcessingConfigOutSchema],
)
async def update_video_processing_config_controller(
    data: Annotated[VideoProcessingConfigUpdateSchema, Body(description="全局配置")],
    auth: Annotated[
        AuthSchema,
        Depends(AuthPermission(["module_video:processing:config"])),
    ],
) -> JSONResponse:
    """保存模型名与提示词模板，字段传 null 表示恢复默认。"""
    result = await VideoProcessingService.update_processing_config_service(auth, data)
    return SuccessResponse(data=result, msg="自动剪辑全局配置保存成功")


@VideoProcessingRouter.post(
    "/tasks/{task_id}/assets/initiate",
    summary="初始化视频素材分片上传",
    response_model=ResponseSchema[VideoAssetUploadInitOutSchema],
)
async def initiate_video_asset_controller(
    task_id: Annotated[int, Path(description="自动剪辑任务ID")],
    data: Annotated[VideoAssetUploadInitSchema, Body(description="素材文件元数据")],
    auth: Annotated[
        AuthSchema,
        Depends(AuthPermission(["module_video:processing:create"])),
    ],
) -> JSONResponse:
    """创建 Multipart 会话并返回每个分片的预签名 URL。"""
    result = await VideoProcessingService.initiate_asset_service(auth, task_id, data)
    return SuccessResponse(data=result, msg="视频素材上传初始化成功")


@VideoProcessingRouter.post(
    "/tasks/{task_id}/assets/{asset_id}/complete",
    summary="完成视频素材分片上传",
    response_model=ResponseSchema[VideoAssetOutSchema],
)
async def complete_video_asset_controller(
    task_id: Annotated[int, Path(description="自动剪辑任务ID")],
    asset_id: Annotated[int, Path(description="视频素材ID")],
    data: Annotated[VideoMultipartCompleteSchema, Body(description="已上传分片列表")],
    auth: Annotated[
        AuthSchema,
        Depends(AuthPermission(["module_video:processing:create"])),
    ],
) -> JSONResponse:
    """合并全部分片并验证对象大小。"""
    result = await VideoProcessingService.complete_asset_service(auth, task_id, asset_id, data)
    return SuccessResponse(data=result, msg="视频素材上传完成")


@VideoProcessingRouter.post(
    "/tasks/{task_id}/assets/{asset_id}/parts/sign",
    summary="刷新视频分片上传签名",
    response_model=ResponseSchema[list[VideoMultipartUploadPartSchema]],
)
async def refresh_video_asset_parts_controller(
    task_id: Annotated[int, Path(description="自动剪辑任务ID")],
    asset_id: Annotated[int, Path(description="视频素材ID")],
    data: Annotated[VideoMultipartPresignSchema, Body(description="待刷新签名的分片")],
    auth: Annotated[
        AuthSchema,
        Depends(AuthPermission(["module_video:processing:create"])),
    ],
) -> JSONResponse:
    """为尚未开始上传的指定分片生成新的短时 URL。"""
    result = await VideoProcessingService.refresh_asset_parts_service(auth, task_id, asset_id, data)
    return SuccessResponse(data=result, msg="视频分片上传签名刷新成功")


@VideoProcessingRouter.post(
    "/tasks/{task_id}/assets/{asset_id}/abort",
    summary="中止视频素材分片上传",
    response_model=ResponseSchema[VideoAssetOutSchema],
)
async def abort_video_asset_controller(
    task_id: Annotated[int, Path(description="自动剪辑任务ID")],
    asset_id: Annotated[int, Path(description="视频素材ID")],
    auth: Annotated[
        AuthSchema,
        Depends(AuthPermission(["module_video:processing:create"])),
    ],
) -> JSONResponse:
    """中止失败素材的 Multipart 会话并释放 MinIO 分片。"""
    result = await VideoProcessingService.abort_asset_service(auth, task_id, asset_id)
    return SuccessResponse(data=result, msg="视频素材上传已中止")


@VideoProcessingRouter.post(
    "/tasks/{task_id}/submit",
    summary="提交自动剪辑任务",
    response_model=ResponseSchema[VideoTaskDetailOutSchema],
)
async def submit_video_task_controller(
    task_id: Annotated[int, Path(description="自动剪辑任务ID")],
    auth: Annotated[
        AuthSchema,
        Depends(AuthPermission(["module_video:processing:create"])),
    ],
) -> JSONResponse:
    """确认输入完整并将任务置为等待处理。"""
    result = await VideoProcessingService.submit_task_service(auth, task_id)
    return SuccessResponse(data=result, msg="自动剪辑任务已提交")


@VideoProcessingRouter.post(
    "/tasks/{task_id}/cancel",
    summary="取消自动剪辑任务",
    response_model=ResponseSchema[VideoTaskDetailOutSchema],
)
async def cancel_video_task_controller(
    task_id: Annotated[int, Path(description="自动剪辑任务ID")],
    auth: Annotated[
        AuthSchema,
        Depends(AuthPermission(["module_video:processing:cancel"])),
    ],
) -> JSONResponse:
    """取消任务并释放仍未完成的 MinIO 分片。"""
    result = await VideoProcessingService.cancel_task_service(auth, task_id)
    return SuccessResponse(data=result, msg="自动剪辑任务已取消")


@VideoProcessingRouter.post(
    "/tasks/{task_id}/retry",
    summary="重试自动剪辑任务",
    response_model=ResponseSchema[VideoTaskDetailOutSchema],
)
async def retry_video_task_controller(
    task_id: Annotated[int, Path(description="自动剪辑任务ID")],
    auth: Annotated[
        AuthSchema,
        Depends(AuthPermission(["module_video:processing:retry"])),
    ],
) -> JSONResponse:
    """使用已上传完成的原视频重新排队。"""
    result = await VideoProcessingService.retry_task_service(auth, task_id)
    return SuccessResponse(data=result, msg="自动剪辑任务已重新排队")


@VideoProcessingRouter.post(
    "/tasks/{task_id}/review",
    summary="审核自动剪辑待确认成片",
    response_model=ResponseSchema[VideoTaskDetailOutSchema],
)
async def review_video_task_controller(
    task_id: Annotated[int, Path(description="自动剪辑任务ID")],
    data: Annotated[VideoTaskReviewSchema, Body(description="审核动作")],
    auth: Annotated[
        AuthSchema,
        Depends(AuthPermission(["module_video:processing:create"])),
    ],
) -> JSONResponse:
    """确认待审核成片，或根据调整意见重新生成。"""
    result = await VideoProcessingService.review_task_service(auth, task_id, data)
    return SuccessResponse(data=result, msg="自动剪辑审核操作成功")


@VideoProcessingRouter.get(
    "/tasks/{task_id}/assets/{asset_id}/download",
    summary="获取视频产物短时访问地址",
    response_model=ResponseSchema[VideoAssetDownloadOutSchema],
)
async def download_video_asset_controller(
    task_id: Annotated[int, Path(description="自动剪辑任务ID")],
    asset_id: Annotated[int, Path(description="视频产物ID")],
    auth: Annotated[
        AuthSchema,
        Depends(AuthPermission(["module_video:processing:download"])),
    ],
    download: Annotated[bool, Query(description="是否强制下载文件")] = False,
) -> JSONResponse:
    """获取成片或字幕的短时读取地址。"""
    result = await VideoProcessingService.get_asset_download_service(
        auth, task_id, asset_id, download
    )
    return SuccessResponse(data=result, msg="视频产物访问地址生成成功")


@VideoProcessingRouter.get(
    "/tasks/{task_id}/assets/{asset_id}/metadata",
    summary="获取视频素材完整元数据",
    response_model=ResponseSchema[VideoAssetMetadataOutSchema],
)
async def get_video_asset_metadata_controller(
    task_id: Annotated[int, Path(description="自动剪辑任务ID")],
    asset_id: Annotated[int, Path(description="视频素材ID")],
    auth: Annotated[
        AuthSchema,
        Depends(AuthPermission(["module_video:processing:query"])),
    ],
) -> JSONResponse:
    """按需返回单个素材的完整媒体元数据。

    详情接口不下发 file_metadata（完整时间线 JSON 动辄 200KB），
    前端展开折叠区时再走这里单独取。
    """
    result = await VideoProcessingService.get_asset_metadata_service(auth, task_id, asset_id)
    return SuccessResponse(data=result, msg="视频素材元数据查询成功")
