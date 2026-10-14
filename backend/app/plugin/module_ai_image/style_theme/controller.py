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

from .service import AiStyleThemeService
from .schema import (
    AiStyleThemeCreateSchema,
    AiStyleThemeGenerateRequest,
    AiStyleThemeUpdateSchema,
    AiStyleThemeQueryParam,
)
from app.plugin.module_ai_image.utils.llm_generator import llm_action_engine

AiStyleThemeRouter = APIRouter(prefix="/style_theme", tags=["AI写真样式主题模块"])


@AiStyleThemeRouter.get(
    "/detail/{id}",
    summary="获取AI写真样式主题详情",
    description="获取AI写真样式主题详情",
)
async def get_style_theme_detail_controller(
    id: int = Path(..., description="ID"),
    auth: AuthSchema = Depends(AuthPermission(["module_ai_image:style_theme:query"])),
) -> JSONResponse:
    """
    获取AI写真样式主题详情接口

    参数:
    - id: int - 数据ID
    - auth: AuthSchema - 认证信息

    返回:
    - JSONResponse - 包含AI写真样式主题详情的JSON响应
    """
    result_dict = await AiStyleThemeService.detail_style_theme_service(auth=auth, id=id)
    log.info(f"获取AI写真样式主题详情成功 {id}")
    return SuccessResponse(data=result_dict, msg="获取AI写真样式主题详情成功")


@AiStyleThemeRouter.get(
    "/list", summary="查询AI写真样式主题列表", description="查询AI写真样式主题列表"
)
async def get_style_theme_list_controller(
    page: PaginationQueryParam = Depends(),
    search: AiStyleThemeQueryParam = Depends(),
    auth: AuthSchema = Depends(AuthPermission(["module_ai_image:style_theme:query"])),
) -> JSONResponse:
    """
    查询AI写真样式主题列表接口（数据库分页）

    参数:
    - page: PaginationQueryParam - 分页参数
    - search: AiStyleThemeQueryParam - 查询参数
    - auth: AuthSchema - 认证信息

    返回:
    - JSONResponse - 包含AI写真样式主题列表的JSON响应
    """
    result_dict = await AiStyleThemeService.page_style_theme_service(
        auth=auth,
        page_no=page.page_no if page.page_no is not None else 1,
        page_size=page.page_size if page.page_size is not None else 10,
        search=search,
        order_by=page.order_by,
    )
    log.info("查询AI写真样式主题列表成功")
    return SuccessResponse(data=result_dict, msg="查询AI写真样式主题列表成功")


@AiStyleThemeRouter.post(
    "/create", summary="创建AI写真样式主题", description="创建AI写真样式主题"
)
async def create_style_theme_controller(
    data: AiStyleThemeCreateSchema,
    auth: AuthSchema = Depends(AuthPermission(["module_ai_image:style_theme:create"])),
) -> JSONResponse:
    """
    创建AI写真样式主题接口

    参数:
    - data: AiStyleThemeCreateSchema - 创建数据
    - auth: AuthSchema - 认证信息

    返回:
    - JSONResponse - 包含创建AI写真样式主题结果的JSON响应
    """
    result_dict = await AiStyleThemeService.create_style_theme_service(
        auth=auth, data=data
    )
    log.info("创建AI写真样式主题成功")
    return SuccessResponse(data=result_dict, msg="创建AI写真样式主题成功")


@AiStyleThemeRouter.put(
    "/update/{id}", summary="修改AI写真样式主题", description="修改AI写真样式主题"
)
async def update_style_theme_controller(
    data: AiStyleThemeUpdateSchema,
    id: int = Path(..., description="ID"),
    auth: AuthSchema = Depends(AuthPermission(["module_ai_image:style_theme:update"])),
) -> JSONResponse:
    """
    修改AI写真样式主题接口

    参数:
    - id: int - 数据ID
    - data: AiStyleThemeUpdateSchema - 更新数据
    - auth: AuthSchema - 认证信息

    返回:
    - JSONResponse - 包含修改AI写真样式主题结果的JSON响应
    """
    result_dict = await AiStyleThemeService.update_style_theme_service(
        auth=auth, id=id, data=data
    )
    log.info("修改AI写真样式主题成功")
    return SuccessResponse(data=result_dict, msg="修改AI写真样式主题成功")


@AiStyleThemeRouter.delete(
    "/delete", summary="删除AI写真样式主题", description="删除AI写真样式主题"
)
async def delete_style_theme_controller(
    ids: list[int] = Body(..., description="ID列表"),
    auth: AuthSchema = Depends(AuthPermission(["module_ai_image:style_theme:delete"])),
) -> JSONResponse:
    """
    删除AI写真样式主题接口

    参数:
    - ids: list[int] - 数据ID列表
    - auth: AuthSchema - 认证信息

    返回:
    - JSONResponse - 包含删除AI写真样式主题结果的JSON响应
    """
    await AiStyleThemeService.delete_style_theme_service(auth=auth, ids=ids)
    log.info(f"删除AI写真样式主题成功: {ids}")
    return SuccessResponse(msg="删除AI写真样式主题成功")


@AiStyleThemeRouter.patch(
    "/available/setting",
    summary="批量修改AI写真样式主题状态",
    description="批量修改AI写真样式主题状态",
)
async def batch_set_available_style_theme_controller(
    data: BatchSetAvailable,
    auth: AuthSchema = Depends(AuthPermission(["module_ai_image:style_theme:patch"])),
) -> JSONResponse:
    """
    批量修改AI写真样式主题状态接口

    参数:
    - data: BatchSetAvailable - 批量修改状态数据
    - auth: AuthSchema - 认证信息

    返回:
    - JSONResponse - 包含批量修改AI写真样式主题状态结果的JSON响应
    """
    await AiStyleThemeService.set_available_style_theme_service(auth=auth, data=data)
    log.info(f"批量修改AI写真样式主题状态成功: {data.ids}")
    return SuccessResponse(msg="批量修改AI写真样式主题状态成功")


@AiStyleThemeRouter.post(
    "/export", summary="导出AI写真样式主题", description="导出AI写真样式主题"
)
async def export_style_theme_list_controller(
    search: AiStyleThemeQueryParam = Depends(),
    auth: AuthSchema = Depends(AuthPermission(["module_ai_image:style_theme:export"])),
) -> StreamingResponse:
    """
    导出AI写真样式主题接口

    参数:
    - search: AiStyleThemeQueryParam - 查询参数
    - auth: AuthSchema - 认证信息

    返回:
    - StreamingResponse - 包含导出AI写真样式主题数据的流式响应
    """
    result_dict_list = await AiStyleThemeService.list_style_theme_service(
        search=search, auth=auth
    )
    export_result = await AiStyleThemeService.batch_export_style_theme_service(
        obj_list=result_dict_list
    )
    log.info("导出AI写真样式主题成功")
    return StreamResponse(
        data=bytes2file_response(export_result),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=ai_style_theme.xlsx"},
    )


@AiStyleThemeRouter.post(
    "/import", summary="导入AI写真样式主题", description="导入AI写真样式主题"
)
async def import_style_theme_list_controller(
    file: UploadFile,
    auth: AuthSchema = Depends(AuthPermission(["module_ai_image:style_theme:import"])),
) -> JSONResponse:
    """
    导入AI写真样式主题接口

    参数:
    - file: UploadFile - 上传的Excel文件
    - auth: AuthSchema - 认证信息

    返回:
    - JSONResponse - 包含导入AI写真样式主题结果的JSON响应
    """
    batch_import_result = await AiStyleThemeService.batch_import_style_theme_service(
        file=file, auth=auth, update_support=True
    )
    log.info("导入AI写真样式主题成功")
    return SuccessResponse(data=batch_import_result, msg="导入AI写真样式主题成功")


@AiStyleThemeRouter.post(
    "/download/template",
    summary="获取AI写真样式主题导入模板",
    description="获取AI写真样式主题导入模板",
    dependencies=[Depends(AuthPermission(["module_ai_image:style_theme:download"]))],
)
async def export_style_theme_template_controller() -> StreamingResponse:
    """
    获取AI写真样式主题导入模板接口

    返回:
    - StreamingResponse - 包含AI写真样式主题导入模板的流式响应
    """
    import_template_result = (
        await AiStyleThemeService.import_template_download_style_theme_service()
    )
    log.info("获取AI写真样式主题导入模板成功")
    return StreamResponse(
        data=bytes2file_response(import_template_result),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=ai_style_theme_template.xlsx"
        },
    )


@AiStyleThemeRouter.post(
    "/generate_params",
    summary="调用LLM生成AI写真样式参数",
    description="根据性别和主题名称，利用大模型自动扩写材质、穿着风格、配色、氛围感等参数",
)
async def generate_style_params_controller(
    request: AiStyleThemeGenerateRequest,
    auth: AuthSchema = Depends(
        AuthPermission(["module_ai_image:style_theme:generate"])
    ),
):
    """
    智能生成AI写真样式参数接口

    参数:
    - request: AiStyleThemeGenerateRequest - 包含性别、主题名称和备注
    - auth: AuthSchema - 认证信息

    返回:
    - JSONResponse - 包含生成的各维度描述参数
    """
    result_dict = await llm_action_engine.generate_style_theme(
        gender=request.gender, theme_name=request.theme_name, remark=request.remark
    )

    log.info(f"大模型生成样式主题参数成功: 主题{result_dict}")
    return SuccessResponse(data=result_dict, msg="样式参数生成成功")
