# -*- coding: utf-8 -*-

from fastapi import APIRouter, Depends, UploadFile, Body, Path, Query
from fastapi.responses import StreamingResponse, JSONResponse

from app.common.response import SuccessResponse, StreamResponse
from app.core.dependencies import AuthPermission
from app.api.v1.module_system.auth.schema import AuthSchema
from app.core.base_params import PaginationQueryParam
from app.utils.common_util import bytes2file_response
from app.core.logger import log
from app.core.base_schema import BatchSetAvailable

from .service import AiImageAutoStrategyService
from .schema import (
    AiImageAutoStrategyCreateSchema,
    AiImageAutoStrategyUpdateSchema,
    AiImageAutoStrategyQueryParam,
)

AiImageAutoStrategyRouter = APIRouter(
    prefix="/auto_strategy", tags=["AI 24小时自动化生图策略模块"]
)


@AiImageAutoStrategyRouter.get(
    "/detail/{id}",
    summary="获取AI 24小时自动化生图策略详情",
    description="获取AI 24小时自动化生图策略详情",
)
async def get_ai_image_auto_strategy_detail_controller(
    id: int = Path(..., description="ID"),
    auth: AuthSchema = Depends(
        AuthPermission(["module_ai_image:ai_image_auto_strategy:query"])
    ),
) -> JSONResponse:
    """
    获取AI 24小时自动化生图策略详情接口

    参数:
    - id: int - 数据ID
    - auth: AuthSchema - 认证信息

    返回:
    - JSONResponse - 包含AI 24小时自动化生图策略详情的JSON响应
    """
    result_dict = (
        await AiImageAutoStrategyService.detail_ai_image_auto_strategy_service(
            auth=auth, id=id
        )
    )
    log.info(f"获取AI 24小时自动化生图策略详情成功 {id}")
    return SuccessResponse(data=result_dict, msg="获取AI 24小时自动化生图策略详情成功")


@AiImageAutoStrategyRouter.get(
    "/list",
    summary="查询AI 24小时自动化生图策略列表",
    description="查询AI 24小时自动化生图策略列表",
)
async def get_ai_image_auto_strategy_list_controller(
    page: PaginationQueryParam = Depends(),
    search: AiImageAutoStrategyQueryParam = Depends(),
    auth: AuthSchema = Depends(
        AuthPermission(["module_ai_image:ai_image_auto_strategy:query"])
    ),
) -> JSONResponse:
    """
    查询AI 24小时自动化生图策略列表接口（数据库分页）

    参数:
    - page: PaginationQueryParam - 分页参数
    - search: AiImageAutoStrategyQueryParam - 查询参数
    - auth: AuthSchema - 认证信息

    返回:
    - JSONResponse - 包含AI 24小时自动化生图策略列表的JSON响应
    """
    result_dict = await AiImageAutoStrategyService.page_ai_image_auto_strategy_service(
        auth=auth,
        page_no=page.page_no if page.page_no is not None else 1,
        page_size=page.page_size if page.page_size is not None else 10,
        search=search,
        order_by=page.order_by,
    )
    log.info("查询AI 24小时自动化生图策略列表成功")
    return SuccessResponse(data=result_dict, msg="查询AI 24小时自动化生图策略列表成功")


@AiImageAutoStrategyRouter.post(
    "/create",
    summary="创建AI 24小时自动化生图策略",
    description="创建AI 24小时自动化生图策略",
)
async def create_ai_image_auto_strategy_controller(
    data: AiImageAutoStrategyCreateSchema,
    auth: AuthSchema = Depends(
        AuthPermission(["module_ai_image:ai_image_auto_strategy:create"])
    ),
) -> JSONResponse:
    """
    创建AI 24小时自动化生图策略接口

    参数:
    - data: AiImageAutoStrategyCreateSchema - 创建数据
    - auth: AuthSchema - 认证信息

    返回:
    - JSONResponse - 包含创建AI 24小时自动化生图策略结果的JSON响应
    """
    result_dict = (
        await AiImageAutoStrategyService.create_ai_image_auto_strategy_service(
            auth=auth, data=data
        )
    )
    log.info("创建AI 24小时自动化生图策略成功")
    return SuccessResponse(data=result_dict, msg="创建AI 24小时自动化生图策略成功")


@AiImageAutoStrategyRouter.put(
    "/update/{id}",
    summary="修改AI 24小时自动化生图策略",
    description="修改AI 24小时自动化生图策略",
)
async def update_ai_image_auto_strategy_controller(
    data: AiImageAutoStrategyUpdateSchema,
    id: int = Path(..., description="ID"),
    auth: AuthSchema = Depends(
        AuthPermission(["module_ai_image:ai_image_auto_strategy:update"])
    ),
) -> JSONResponse:
    """
    修改AI 24小时自动化生图策略接口

    参数:
    - id: int - 数据ID
    - data: AiImageAutoStrategyUpdateSchema - 更新数据
    - auth: AuthSchema - 认证信息

    返回:
    - JSONResponse - 包含修改AI 24小时自动化生图策略结果的JSON响应
    """
    result_dict = (
        await AiImageAutoStrategyService.update_ai_image_auto_strategy_service(
            auth=auth, id=id, data=data
        )
    )
    log.info("修改AI 24小时自动化生图策略成功")
    return SuccessResponse(data=result_dict, msg="修改AI 24小时自动化生图策略成功")


@AiImageAutoStrategyRouter.delete(
    "/delete",
    summary="删除AI 24小时自动化生图策略",
    description="删除AI 24小时自动化生图策略",
)
async def delete_ai_image_auto_strategy_controller(
    ids: list[int] = Body(..., description="ID列表"),
    auth: AuthSchema = Depends(
        AuthPermission(["module_ai_image:ai_image_auto_strategy:delete"])
    ),
) -> JSONResponse:
    """
    删除AI 24小时自动化生图策略接口

    参数:
    - ids: list[int] - 数据ID列表
    - auth: AuthSchema - 认证信息

    返回:
    - JSONResponse - 包含删除AI 24小时自动化生图策略结果的JSON响应
    """
    await AiImageAutoStrategyService.delete_ai_image_auto_strategy_service(
        auth=auth, ids=ids
    )
    log.info(f"删除AI 24小时自动化生图策略成功: {ids}")
    return SuccessResponse(msg="删除AI 24小时自动化生图策略成功")


@AiImageAutoStrategyRouter.patch(
    "/available/setting",
    summary="批量修改AI 24小时自动化生图策略状态",
    description="批量修改AI 24小时自动化生图策略状态",
)
async def batch_set_available_ai_image_auto_strategy_controller(
    data: BatchSetAvailable,
    auth: AuthSchema = Depends(
        AuthPermission(["module_ai_image:ai_image_auto_strategy:patch"])
    ),
) -> JSONResponse:
    """
    批量修改AI 24小时自动化生图策略状态接口

    参数:
    - data: BatchSetAvailable - 批量修改状态数据
    - auth: AuthSchema - 认证信息

    返回:
    - JSONResponse - 包含批量修改AI 24小时自动化生图策略状态结果的JSON响应
    """
    await AiImageAutoStrategyService.set_available_ai_image_auto_strategy_service(
        auth=auth, data=data
    )
    log.info(f"批量修改AI 24小时自动化生图策略状态成功: {data.ids}")
    return SuccessResponse(msg="批量修改AI 24小时自动化生图策略状态成功")


@AiImageAutoStrategyRouter.post(
    "/export",
    summary="导出AI 24小时自动化生图策略",
    description="导出AI 24小时自动化生图策略",
)
async def export_ai_image_auto_strategy_list_controller(
    search: AiImageAutoStrategyQueryParam = Depends(),
    auth: AuthSchema = Depends(
        AuthPermission(["module_ai_image:ai_image_auto_strategy:export"])
    ),
) -> StreamingResponse:
    """
    导出AI 24小时自动化生图策略接口

    参数:
    - search: AiImageAutoStrategyQueryParam - 查询参数
    - auth: AuthSchema - 认证信息

    返回:
    - StreamingResponse - 包含导出AI 24小时自动化生图策略数据的流式响应
    """
    result_dict_list = (
        await AiImageAutoStrategyService.list_ai_image_auto_strategy_service(
            search=search, auth=auth
        )
    )
    export_result = (
        await AiImageAutoStrategyService.batch_export_ai_image_auto_strategy_service(
            obj_list=result_dict_list
        )
    )
    log.info("导出AI 24小时自动化生图策略成功")
    return StreamResponse(
        data=bytes2file_response(export_result),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=ai_image_auto_strategy.xlsx"
        },
    )


@AiImageAutoStrategyRouter.post(
    "/import",
    summary="导入AI 24小时自动化生图策略",
    description="导入AI 24小时自动化生图策略",
)
async def import_ai_image_auto_strategy_list_controller(
    file: UploadFile,
    auth: AuthSchema = Depends(
        AuthPermission(["module_ai_image:ai_image_auto_strategy:import"])
    ),
) -> JSONResponse:
    """
    导入AI 24小时自动化生图策略接口

    参数:
    - file: UploadFile - 上传的Excel文件
    - auth: AuthSchema - 认证信息

    返回:
    - JSONResponse - 包含导入AI 24小时自动化生图策略结果的JSON响应
    """
    batch_import_result = (
        await AiImageAutoStrategyService.batch_import_ai_image_auto_strategy_service(
            file=file, auth=auth, update_support=True
        )
    )
    log.info("导入AI 24小时自动化生图策略成功")
    return SuccessResponse(
        data=batch_import_result, msg="导入AI 24小时自动化生图策略成功"
    )


@AiImageAutoStrategyRouter.post(
    "/download/template",
    summary="获取AI 24小时自动化生图策略导入模板",
    description="获取AI 24小时自动化生图策略导入模板",
    dependencies=[
        Depends(AuthPermission(["module_ai_image:ai_image_auto_strategy:download"]))
    ],
)
async def export_ai_image_auto_strategy_template_controller() -> StreamingResponse:
    """
    获取AI 24小时自动化生图策略导入模板接口

    返回:
    - StreamingResponse - 包含AI 24小时自动化生图策略导入模板的流式响应
    """
    import_template_result = (
        await AiImageAutoStrategyService.import_template_download_ai_image_auto_strategy_service()
    )
    log.info("获取AI 24小时自动化生图策略导入模板成功")
    return StreamResponse(
        data=bytes2file_response(import_template_result),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=ai_image_auto_strategy_template.xlsx"
        },
    )
