from pathlib import Path
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    Depends,
    Form,
    Request,
    UploadFile,
)
from fastapi.responses import FileResponse, JSONResponse

from app.common.response import ResponseSchema, SuccessResponse, UploadFileResponse
from app.core.dependencies import AuthPermission
from app.core.logger import log
from app.core.router_class import OperationLogRoute
from app.utils.upload_util import UploadUtil

from .service import FileService

FileRouter = APIRouter(route_class=OperationLogRoute, prefix="/file", tags=["文件管理"])


@FileRouter.post(
    "/upload",
    summary="上传文件",
    description="上传文件",
    response_model=ResponseSchema[dict],
    dependencies=[Depends(AuthPermission(["module_common:file:upload"]))],
)
async def upload_controller(
    request: Request,
    file: UploadFile,
    # 🚀 核心新增：接收表单里的 upload_type，默认直接走 minio
    upload_type: str = Form(default="minio", description="上传通道：local / minio"),
) -> JSONResponse:
    """
    上传文件
    """
    # 🚀 把 upload_type 传给底层的 service
    result_dict = await FileService.upload_service(
        base_url=str(request.base_url), file=file, upload_type=upload_type
    )

    log.info(f"上传文件成功 {result_dict}")
    return SuccessResponse(data=result_dict, msg="上传文件成功")


@FileRouter.post(
    "/download",
    summary="下载文件",
    description="下载文件",
    dependencies=[Depends(AuthPermission(["module_common:file:download"]))],
)
async def download_controller(
    background_tasks: BackgroundTasks,
    file_path: Annotated[str, Body(description="文件路径")],
    delete: Annotated[bool, Body(description="是否删除文件")] = False,
) -> FileResponse:
    """
    下载文件

    参数:
    - background_tasks (BackgroundTasks): 后台任务对象
    - file_path (str): 文件路径
    - delete (bool): 是否删除文件

    返回:
    - FileResponse: 包含下载文件的响应
    """
    result = await FileService.download_service(file_path=file_path)
    if delete:
        background_tasks.add_task(UploadUtil.delete_file, Path(result.file_path))
    log.info("下载文件成功")
    return UploadFileResponse(file_path=result.file_path, filename=result.file_name)
