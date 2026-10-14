from __future__ import annotations

import asyncio
import math
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import quote

import boto3
from botocore.client import BaseClient
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.config.setting import settings
from app.core.exceptions import CustomException
from app.utils.common_util import uuid4_str


class VideoObjectStorage:
    """为智能视频模块提供 MinIO Multipart 与短时下载签名。"""

    # 按用途缓存 client。boto3.client() 首次建连要 200ms 上下，而列表接口每个
    # 请求都要签一批预览地址，每次重建等于白等。
    _client_cache: dict[bool, BaseClient] = {}

    @classmethod
    def build_object_key(cls, task_no: str, asset_role: str, file_name: str) -> str:
        """生成不包含用户目录信息的唯一对象键。"""
        suffix = PurePosixPath(file_name).suffix.lower()
        return f"video/{asset_role}/{task_no}/{uuid4_str()}{suffix}"

    @classmethod
    async def download_object_to_file(cls, object_key: str, target_path: Path) -> None:
        """worker 将 MinIO 对象下载到本地临时文件，供云厂商 SDK 上传。"""
        client = cls._create_client()
        try:
            await asyncio.to_thread(
                client.download_file,
                settings.MINIO_BUCKET_NAME,
                object_key,
                str(target_path),
            )
        except (BotoCoreError, ClientError) as exc:
            raise CustomException(msg=f"下载视频素材失败: {exc}") from exc

    @classmethod
    async def upload_file(
        cls,
        object_key: str,
        file_path: Path,
        content_type: str,
    ) -> dict[str, Any]:
        """worker 将云端处理结果上传回 MinIO 并返回对象元数据。"""
        await cls.ensure_bucket()
        client = cls._create_client()
        try:
            await asyncio.to_thread(
                client.upload_file,
                str(file_path),
                settings.MINIO_BUCKET_NAME,
                object_key,
                ExtraArgs={"ContentType": content_type},
            )
        except (BotoCoreError, ClientError) as exc:
            raise CustomException(msg=f"上传视频产物失败: {exc}") from exc

        metadata = await cls.get_object_metadata(object_key)
        if metadata is None:
            raise CustomException(msg="视频产物上传后无法读取对象元数据")
        return metadata

    @classmethod
    async def initiate_multipart(
        cls,
        object_key: str,
        file_size: int,
        content_type: str,
    ) -> dict[str, Any]:
        """创建 Multipart 上传并为每个分片生成预签名 URL。"""
        part_size = settings.MINIO_MULTIPART_PART_SIZE
        part_count = math.ceil(file_size / part_size)
        if part_count > settings.MINIO_MULTIPART_MAX_PARTS:
            raise CustomException(msg="视频文件超过当前分片上传上限")

        await cls.ensure_bucket()
        client = cls._create_client()
        try:
            result = await asyncio.to_thread(
                client.create_multipart_upload,
                Bucket=settings.MINIO_BUCKET_NAME,
                Key=object_key,
                ContentType=content_type,
            )
            upload_id = result["UploadId"]
            parts = cls.presign_upload_parts(
                object_key=object_key,
                upload_id=upload_id,
                part_numbers=list(range(1, part_count + 1)),
            )
        except (BotoCoreError, ClientError) as exc:
            raise CustomException(msg=f"创建视频分片上传失败: {exc}") from exc

        return {
            "upload_id": upload_id,
            "part_size": part_size,
            "part_count": part_count,
            "expires_in": settings.MINIO_PRESIGNED_EXPIRE_SECONDS,
            "parts": parts,
        }

    @classmethod
    def presign_upload_parts(
        cls,
        object_key: str,
        upload_id: str,
        part_numbers: list[int],
    ) -> list[dict[str, Any]]:
        """为仍未开始上传的指定分片刷新短时签名。"""
        client = cls._create_client(public=True)
        return [
            {
                "part_number": part_number,
                "upload_url": client.generate_presigned_url(
                    "upload_part",
                    Params={
                        "Bucket": settings.MINIO_BUCKET_NAME,
                        "Key": object_key,
                        "UploadId": upload_id,
                        "PartNumber": part_number,
                    },
                    ExpiresIn=settings.MINIO_PRESIGNED_EXPIRE_SECONDS,
                ),
            }
            for part_number in part_numbers
        ]

    @classmethod
    async def list_multipart_parts(
        cls,
        object_key: str,
        upload_id: str,
    ) -> list[dict[str, Any]]:
        """读取 MinIO 已接收的真实分片，供合并前校验。"""
        client = cls._create_client()
        part_number_marker = 0
        uploaded_parts: list[dict[str, Any]] = []
        try:
            while True:
                result = await asyncio.to_thread(
                    client.list_parts,
                    Bucket=settings.MINIO_BUCKET_NAME,
                    Key=object_key,
                    UploadId=upload_id,
                    PartNumberMarker=part_number_marker,
                    MaxParts=1000,
                )
                uploaded_parts.extend(
                    {
                        "part_number": int(part["PartNumber"]),
                        "etag": str(part["ETag"]).strip('"'),
                        "size": int(part["Size"]),
                    }
                    for part in result.get("Parts", [])
                )
                if not result.get("IsTruncated"):
                    break
                part_number_marker = int(result["NextPartNumberMarker"])
        except (BotoCoreError, ClientError) as exc:
            raise CustomException(msg=f"读取视频分片失败: {exc}") from exc
        return uploaded_parts

    @classmethod
    async def ensure_bucket(cls) -> None:
        """确认视频存储桶可用，并按项目现有约定在缺失时创建。"""
        client = cls._create_client()
        try:
            await asyncio.to_thread(
                client.head_bucket,
                Bucket=settings.MINIO_BUCKET_NAME,
            )
        except ClientError as exc:
            error_code = str(exc.response.get("Error", {}).get("Code", ""))
            if error_code not in {"404", "NoSuchBucket", "NotFound"}:
                raise CustomException(msg=f"检查视频存储桶失败: {exc}") from exc
            try:
                await asyncio.to_thread(
                    client.create_bucket,
                    Bucket=settings.MINIO_BUCKET_NAME,
                )
            except ClientError as create_exc:
                create_error_code = str(create_exc.response.get("Error", {}).get("Code", ""))
                if create_error_code in {"BucketAlreadyOwnedByYou", "BucketAlreadyExists"}:
                    # 首次并发初始化时，另一个请求可能已经完成建桶，这里再次确认可访问性。
                    try:
                        await asyncio.to_thread(
                            client.head_bucket,
                            Bucket=settings.MINIO_BUCKET_NAME,
                        )
                    except (BotoCoreError, ClientError) as head_exc:
                        raise CustomException(msg=f"确认视频存储桶失败: {head_exc}") from head_exc
                    return
                raise CustomException(msg=f"创建视频存储桶失败: {create_exc}") from create_exc
            except BotoCoreError as create_exc:
                raise CustomException(msg=f"创建视频存储桶失败: {create_exc}") from create_exc
        except BotoCoreError as exc:
            raise CustomException(msg=f"检查视频存储桶失败: {exc}") from exc

    @classmethod
    async def get_object_metadata(cls, object_key: str) -> dict[str, Any] | None:
        """读取已完成对象的元数据，用于完成接口重试时做幂等对账。"""
        client = cls._create_client()
        try:
            metadata = await asyncio.to_thread(
                client.head_object,
                Bucket=settings.MINIO_BUCKET_NAME,
                Key=object_key,
            )
        except ClientError as exc:
            error_code = str(exc.response.get("Error", {}).get("Code", ""))
            if error_code in {"404", "NoSuchKey", "NotFound"}:
                return None
            raise CustomException(msg=f"读取视频对象元数据失败: {exc}") from exc
        except BotoCoreError as exc:
            raise CustomException(msg=f"读取视频对象元数据失败: {exc}") from exc

        return {
            "etag": str(metadata.get("ETag") or "").strip('"') or None,
            "file_size": int(metadata["ContentLength"]),
        }

    @classmethod
    async def complete_multipart(
        cls,
        object_key: str,
        upload_id: str,
        parts: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """合并已上传的分片并返回对象 ETag。"""
        client = cls._create_client()
        completed_parts = [
            {"PartNumber": part["part_number"], "ETag": part["etag"]}
            for part in sorted(parts, key=lambda item: item["part_number"])
        ]
        try:
            result = await asyncio.to_thread(
                client.complete_multipart_upload,
                Bucket=settings.MINIO_BUCKET_NAME,
                Key=object_key,
                UploadId=upload_id,
                MultipartUpload={"Parts": completed_parts},
            )
        except (BotoCoreError, ClientError) as exc:
            raise CustomException(msg=f"完成视频分片上传失败: {exc}") from exc

        return {
            "etag": str(result.get("ETag") or "").strip('"') or None,
        }

    @classmethod
    async def abort_multipart(cls, object_key: str, upload_id: str) -> None:
        """中止未完成的 Multipart 上传并释放 MinIO 分片。"""
        client = cls._create_client()
        try:
            await asyncio.to_thread(
                client.abort_multipart_upload,
                Bucket=settings.MINIO_BUCKET_NAME,
                Key=object_key,
                UploadId=upload_id,
            )
        except ClientError as exc:
            error_code = str(exc.response.get("Error", {}).get("Code", ""))
            if error_code == "NoSuchUpload":
                return
            raise CustomException(msg=f"中止视频分片上传失败: {exc}") from exc
        except BotoCoreError as exc:
            raise CustomException(msg=f"中止视频分片上传失败: {exc}") from exc

    @classmethod
    def presign_download(
        cls,
        object_key: str,
        file_name: str,
        attachment: bool,
    ) -> str:
        """生成仅在配置有效期内可用的对象预览或下载地址。"""
        client = cls._create_client(public=True)
        params = {"Bucket": settings.MINIO_BUCKET_NAME, "Key": object_key}
        if attachment:
            encoded_name = quote(PurePosixPath(file_name).name)
            params["ResponseContentDisposition"] = f"attachment; filename*=UTF-8''{encoded_name}"
        try:
            return str(
                client.generate_presigned_url(
                    "get_object",
                    Params=params,
                    ExpiresIn=settings.MINIO_PRESIGNED_EXPIRE_SECONDS,
                )
            )
        except (BotoCoreError, ClientError) as exc:
            raise CustomException(msg=f"生成视频下载地址失败: {exc}") from exc

    @staticmethod
    def _create_client(public: bool = False) -> BaseClient:
        """使用项目现有 MinIO 配置创建路径风格 S3 客户端，按用途复用。"""
        cached = VideoObjectStorage._client_cache.get(public)
        if cached is not None:
            return cached

        required_values = {
            "MINIO_ENDPOINT": settings.MINIO_ENDPOINT,
            "MINIO_PUBLIC_ENDPOINT": settings.MINIO_PUBLIC_ENDPOINT,
            "MINIO_ACCESS_KEY": settings.MINIO_ACCESS_KEY,
            "MINIO_SECRET_KEY": settings.MINIO_SECRET_KEY,
            "MINIO_BUCKET_NAME": settings.MINIO_BUCKET_NAME,
        }
        missing_names = [name for name, value in required_values.items() if not value]
        if missing_names:
            raise CustomException(msg=f"MinIO 配置缺失: {', '.join(missing_names)}")

        protocol = "https" if settings.MINIO_SECURE else "http"
        endpoint_url = (
            settings.MINIO_PUBLIC_ENDPOINT if public else f"{protocol}://{settings.MINIO_ENDPOINT}"
        )
        client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )
        VideoObjectStorage._client_cache[public] = client
        return client
