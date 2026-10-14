import io
import base64
import httpx
import logging
from PIL import Image

from app.core.exceptions import CustomException

logger = logging.getLogger(__name__)


class ImageUtil:
    # 🚀 5MB 阈值常量
    SIZE_THRESHOLD = 5 * 1024 * 1024

    @staticmethod
    async def fetch_processed_bytes(url: str, quality: int = 90) -> bytes:
        """
        全能型图片预处理：下载 -> 智能压缩(>5MB) -> RGBA转RGB
        :param url: 图片远程地址
        :param quality: 压缩质量 (默认90，兼顾画质与体积)
        :return: 处理后的图片字节
        """
        async with httpx.AsyncClient() as client:
            try:
                logger.info(f"📥 正在拉取资源: {url[:50]}...")
                response = await client.get(url, timeout=20.0)
                response.raise_for_status()

                img_bytes = response.content
                img_size = len(img_bytes)

                # 🚀 判定逻辑：如果文件大于 5MB，进行“脱水”处理
                if img_size > ImageUtil.SIZE_THRESHOLD:
                    logger.warning(
                        f"⚠️ 图片体积({img_size / 1024 / 1024:.2f}MB) 超过阈值，启动 JPEG 压缩..."
                    )

                    # 使用 with 语句自动管理内存对象
                    with Image.open(io.BytesIO(img_bytes)) as img:
                        # 兼容性处理：如果是 RGBA (PNG) 转为 RGB，否则 JPEG 无法保存
                        if img.mode in ("RGBA", "P"):
                            img = img.convert("RGB")

                        # 在内存中进行压缩
                        with io.BytesIO() as output_buffer:
                            # optimize=True 会进行额外的霍夫曼编码优化，减小体积
                            img.save(
                                output_buffer,
                                format="JPEG",
                                quality=quality,
                                optimize=True,
                            )
                            final_bytes = output_buffer.getvalue()

                    logger.info(
                        f"✅ 压缩完成：{img_size/1024/1024:.2f}MB -> {len(final_bytes)/1024/1024:.2f}MB"
                    )
                else:
                    final_bytes = img_bytes

                # 显式手动清理大字节块引用，加速 GC
                del img_bytes
                return final_bytes

            except httpx.HTTPStatusError as e:
                logger.error(f"图片下载失败，状态码: {e.response.status_code}")
                raise CustomException(msg="无法从远程获取素材图，请检查链接")
            except Exception as e:
                logger.error(f"图片预处理异常: {str(e)}")
                raise CustomException(msg=f"资源预处理失败: {str(e)}")

    @staticmethod
    async def fetch_to_base64(url: str, quality: int = 90) -> str:
        """
        全能型图片预处理：下载 -> 智能压缩(>5MB) -> RGBA转RGB -> Base64
        :param url: 图片远程地址
        :param quality: 压缩质量 (默认90，兼顾画质与体积)
        :return: 纯净的 Base64 字符串
        """
        final_bytes = await ImageUtil.fetch_processed_bytes(url, quality=quality)
        return base64.b64encode(final_bytes).decode("utf-8")
