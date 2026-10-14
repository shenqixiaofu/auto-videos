import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.common.enums import EnvironmentEnum
from app.config.path_conf import BASE_DIR, ENV_DIR

# 文件名在类定义时求值，而裸 alembic 之类的入口不会设置 ENVIRONMENT：不给默认值就会去读
# env/.env.None（不存在 → pydantic 静默忽略），字段全部回落类默认、静默连到 localhost。
_ENV_FILE = ENV_DIR / f".env.{os.getenv('ENVIRONMENT') or EnvironmentEnum.DEV.value}"

class Settings(BaseSettings):
    """系统配置类"""

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,  # 区分大小写
    )

    # ================================================= #
    # ******************* 项目环境 ****************** #
    # ================================================= #
    ENVIRONMENT: EnvironmentEnum = EnvironmentEnum.DEV

    # ================================================= #
    # ******************* 服务器配置 ****************** #
    # ================================================= #
    SERVER_HOST: str = "0.0.0.0"  # 允许访问的IP地址
    SERVER_PORT: int = 8001  # 服务端口

    # ================================================= #
    # ******************* API文档配置 ****************** #
    # ================================================= #
    DEBUG: bool = True  # 调试模式
    TITLE: str = "🎉 FastapiAdmin 🎉 "  # 文档标题
    VERSION: str = "0.1.0"  # 版本号
    DESCRIPTION: str = (
        "该项目是一个基于python的web服务框架，基于fastapi和sqlalchemy实现。"  # 文档描述
    )
    SUMMARY: str = "接口汇总"  # 文档概述
    DOCS_URL: str = "/docs"  # Swagger UI路径
    REDOC_URL: str = "/redoc"  # ReDoc路径
    LJDOC_URL: str = "/ljdoc"  # LangJin UI路径
    ROOT_PATH: str = "/api/v1"  # API路由前缀

    # ================================================= #
    # ******************** 日志配置 ******************** #
    # ================================================= #
    LOGGER_LEVEL: str = "DEBUG"  # 日志级别

    # ================================================= #
    # ******************** 跨域配置 ******************** #
    # ================================================= #
    CORS_ORIGIN_ENABLE: bool = True  # 是否启用跨域
    ALLOW_ORIGINS: list[str] = ["*"]  # 允许的域名列表
    ALLOW_METHODS: list[str] = ["*"]  # 允许的HTTP方法
    ALLOW_HEADERS: list[str] = ["*"]  # 允许的请求头
    ALLOW_CREDENTIALS: bool = True  # 是否允许携带cookie
    CORS_EXPOSE_HEADERS: list[str] = ["X-Request-ID"]

    # ================================================= #
    # ******************* 登录认证配置 ****************** #
    # ================================================= #
    SECRET_KEY: str = "vgb0tnl9d58+6n-6h-ea&u^1#s0ccp!794=krylxcjq75vzps$"  # JWT密钥
    ALGORITHM: str = "HS256"  # JWT算法
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 300  # access_token过期时间(秒)30 分钟
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 3000  # refresh_token过期时间(秒)30 分钟
    TOKEN_TYPE: str = "bearer"  # token类型
    TOKEN_REQUEST_PATH_EXCLUDE: list[str] = ["api/v1/auth/login"]  # JWT / RBAC 路由白名单
    TOKEN_SLIDING_EXPIRE: bool = True  # 是否启用滑动过期(用户操作时自动续期)

    # ================================================= #
    # ******************** 数据库配置 ******************* #
    # ================================================= #
    SQL_DB_ENABLE: bool = True  # 是否启用数据库
    DATABASE_ECHO: bool | Literal["debug"] = False  # 是否显示SQL日志
    ECHO_POOL: bool | Literal["debug"] = False  # 是否显示连接池日志
    POOL_SIZE: int = 10  # 连接池大小
    MAX_OVERFLOW: int = 20  # 最大溢出连接数
    POOL_TIMEOUT: int = 30  # 连接超时时间(秒)
    POOL_RECYCLE: int = 1800  # 连接回收时间(秒)
    POOL_USE_LIFO: bool = True  # 是否使用LIFO连接池
    POOL_PRE_PING: bool = True  # 是否开启连接预检
    FUTURE: bool = True  # 是否使用SQLAlchemy 2.0特性
    AUTOCOMMIT: bool = False  # 是否自动提交
    AUTOFETCH: bool = False  # 是否自动刷新
    EXPIRE_ON_COMMIT: bool = False  # 是否在提交时过期

    # MySQL/PostgreSQL数据库连接
    DATABASE_TYPE: Literal["mysql", "postgres", "sqlite"] = "mysql"
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 3306
    DATABASE_USER: str = "root"
    DATABASE_PASSWORD: str = "ServBay.dev"
    DATABASE_NAME: str = "fastapiadmin"

    # ================================================= #
    # ******************** Redis配置 ******************* #
    # ================================================= #
    REDIS_ENABLE: bool = True  # 是否启用Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB_NAME: int = 1
    REDIS_USER: str = ""
    REDIS_PASSWORD: str = ""

    # ================================================= #
    # ******************** 验证码配置 ******************* #
    # ================================================= #
    CAPTCHA_ENABLE: bool = True  # 是否启用验证码
    CAPTCHA_EXPIRE_SECONDS: int = 60 * 1  # 验证码过期时间(秒) 1分钟
    CAPTCHA_FONT_SIZE: int = 35  # 字体大小
    CAPTCHA_FONT_PATH: str = "static/assets/font/Arial.ttf"  # 字体路径

    # ================================================= #
    # ********************* 日志配置 ******************* #
    # ================================================= #
    OPERATION_LOG_RECORD: bool = True  # 是否记录操作日志
    IGNORE_OPERATION_FUNCTION: list[str] = ["get_captcha_for_login"]  # 忽略记录的函数
    OPERATION_RECORD_METHOD: list[str] = [
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "HEAD",
        "OPTIONS",
    ]  # 需要记录的请求方法

    # ================================================= #
    # ******************* Gzip压缩配置 ******************* #
    # ================================================= #
    GZIP_ENABLE: bool = True  # 是否启用Gzip
    GZIP_MIN_SIZE: int = 1000  # 最小压缩大小(字节)
    GZIP_COMPRESS_LEVEL: int = 9  # 压缩级别(1-9)

    # ================================================= #
    # ***************** 静态文件配置 ***************** #
    # ================================================= #
    STATIC_ENABLE: bool = True  # 是否启用静态文件
    STATIC_URL: str = "/static"  # 访问路由
    STATIC_DIR: str = "static"  # 目录名
    STATIC_ROOT: Path = BASE_DIR.joinpath(STATIC_DIR)  # 绝对路径

    # ================================================= #
    # ***************** 动态文件配置 ***************** #
    # ================================================= #
    UPLOAD_FILE_PATH: Path = Path("static/upload")  # 上传目录
    UPLOAD_MACHINE: str = "A"  # 上传机器标识
    ALLOWED_EXTENSIONS: list[str] = [  # 允许的文件类型
        ".gif",
        ".jpg",
        ".jpeg",
        ".png",
        ".ico",
        ".svg",
        ".xls",
        ".xlsx",
    ]
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 最大文件大小(10MB)

    # ================================================= #
    # ***************** Swagger配置 ***************** #
    # ================================================= #
    SWAGGER_CSS_URL: str = "static/swagger/swagger-ui/swagger-ui.css"
    SWAGGER_JS_URL: str = "static/swagger/swagger-ui/swagger-ui-bundle.js"
    REDOC_JS_URL: str = "static/swagger/redoc/bundles/redoc.standalone.js"
    CUSTOM_CSS_URL: str = "static/swagger/custom-ui/styles.css"
    CUSTOM_JS_URL: str = "static/swagger/custom-ui/scripts.js"
    FAVICON_URL: str = "static/swagger/favicon.png"

    # ================================================= #
    # ******************* AI大模型配置 ****************** #
    # ================================================= #
    OPENAI_BASE_URL: str = ""
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = ""

    # GLM 模型配置
    GLM_API_KEY: str = ""
    GLM_API_URL: str = ""
    GLM_API_MODEL: str = ""

    # lz
    LZ_API_KEY: str = ""
    LZ_API_URL: str = ""

    # DOUBAO
    DOUBAO_API_KEY: str = ""
    DOUBAO_API_URL: str = ""
    DOUBAO_API_MODEL: str = ""

    # QWEN
    QWEN_API_KEY: str = ""
    QWEN_API_URL: str = ""

    # gemini
    BANANA_API_KEY: str = ""

    # 🪣 MinIO 对象存储配置
    # ==========================================
    # MinIO API 地址 (注意不要带 http://，只需 IP:端口，如 127.0.0.1:9000)
    MINIO_ENDPOINT: str = ""

    # 浏览器直传使用的完整地址，必须是用户设备可访问的 MinIO API 地址。
    MINIO_PUBLIC_ENDPOINT: str = ""

    # 账号和密码
    MINIO_ACCESS_KEY: str = ""
    MINIO_SECRET_KEY: str = ""

    # 火山引擎：仅 module_ai_image 的人脸融合/换脸在用，智能视频模块已全面迁阿里。
    VOLC_AK: str = ""
    VOLC_SK: str = ""

    # 🎬 智能视频云端处理 Worker 配置
    # ==========================================
    # 是否启用视频处理 Worker（未启用时任务提交后停留在 queued）
    VIDEO_WORKER_ENABLED: bool = False
    # Worker 扫描 queued 任务的间隔（秒）
    VIDEO_WORKER_SCAN_INTERVAL_SECONDS: int = 10
    # 同时处理的任务数上限
    VIDEO_WORKER_CONCURRENCY: int = 2
    # 单个批次允许同时运行的子任务数上限
    VIDEO_BATCH_CONCURRENCY: int = 10
    # 阿里云 IMS 提交视频渲染作业的并发上限，和轮询分开控制。
    VIDEO_ALIYUN_RENDER_SUBMIT_CONCURRENCY: int = 2
    # 阿里云 IMS 查询视频渲染状态的并发上限，避免轮询把接口打满。
    VIDEO_ALIYUN_RENDER_POLL_CONCURRENCY: int = 4
    # 火山方舟大模型调用并发，创意规划和封面策划共用。
    VIDEO_VOLC_LLM_CONCURRENCY: int = 2
    # 火山方舟生图并发，避免封面批量生成挤爆图片接口。
    VIDEO_VOLC_IMAGE_CONCURRENCY: int = 2
    # 单个任务处理超时（秒），超时后标记失败
    VIDEO_WORKER_TASK_TIMEOUT_SECONDS: int = 60 * 60
    # 是否启用智能视频源视频预处理（preprocessor.py 只做方向规整，不做去静音）
    VIDEO_PREPROCESS_ENABLED: bool = True
    # 单次预处理超时（秒）；名字沿用历史误名，实际是 preprocessor.py 调 ffmpeg 的超时。
    VIDEO_AUTO_EDITOR_TIMEOUT_SECONDS: int = 30 * 60
    # 是否压缩口播里的长停顿；基于词级时间戳的间隙判断，不做音频能量分析。
    VIDEO_SPEECH_PAUSE_TRIM_ENABLED: bool = True
    # 词间停顿超过该秒数才压缩，两端各留余量，避免切口生硬。
    VIDEO_SPEECH_PAUSE_MIN_SECONDS: float = 0.8
    # 是否启用智能视频 AI 封面图，封面基于关键帧和字幕内容生成
    VIDEO_COVER_ENABLED: bool = True
    # AI 封面主体帧在视频时间线上的位置（0~1），0.5 为中段。
    # 只用这一帧：其余位置的帧既进不了生图，又要各跑一次 ffmpeg。
    VIDEO_COVER_SOURCE_FRAME_RATIO: float = 0.5
    # AI 封面策划请求超时（秒），用于控制封面标题与排版策划阶段的等待上限。
    VIDEO_COVER_PLAN_TIMEOUT_SECONDS: float = 180.0
    # AI 封面理解模型，使用方舟 OpenAI-compatible Chat 接口
    VIDEO_COVER_SUMMARY_MODEL: str = "doubao-seed-2-0-pro-260215"
    # AI 封面生图模型，当前真实帧封面方案暂不使用，保留给后续重绘方案评估。
    VIDEO_COVER_IMAGE_MODEL: str = "doubao-seedream-5-0-260128"
    # AI 封面生图尺寸，当前真实帧封面方案暂不使用。
    VIDEO_COVER_IMAGE_SIZE: str = "2K"
    # 封面生图 provider：seedream=火山方舟，relay=OpenAI 协议中转站。
    # 选 relay 但 COVER_RELAY_API_KEY 为空时会自动回退 seedream，避免密钥没填就整条失败。
    VIDEO_COVER_IMAGE_PROVIDER: Literal["seedream", "relay"] = "relay"
    # OpenAI 兼容中转站配置（封面生图专用）。
    COVER_RELAY_API_URL: str = "https://newapi.dragon3api.com/v1"
    COVER_RELAY_API_KEY: str = ""
    COVER_RELAY_IMAGE_MODEL: str = "gpt-image-2.5"
    # 中转站生图尺寸。基础款 gpt-image-2.5 是 1K 档，竖版取 1024x1536，
    # 落盘前会本地规整到封面画布 3:4，不用模型直接出目标比例。
    COVER_RELAY_IMAGE_SIZE: str = "1024x1536"
    # 是否启用云端创意剪辑阶段，用于贴纸、动画和轻特效。
    VIDEO_CREATIVE_EDITING_ENABLED: bool = True
    # 云端创意剪辑规划模型，负责把口播时间轴整理成贴纸和动画事件。
    VIDEO_CREATIVE_PLANNER_MODEL: str = "doubao-seed-2-0-pro-260215"
    # 时间线创意渲染 provider。
    VIDEO_RENDER_PROVIDER: Literal["aliyun_ims"] = "aliyun_ims"
    # 所有异步视频输出任务的统一轮询间隔。
    VIDEO_RENDER_POLL_INTERVAL_SECONDS: int = 10
    # 阿里云智能媒体服务和 OSS 配置。
    ALIYUN_ACCESS_KEY_ID: str = ""
    ALIYUN_ACCESS_KEY_SECRET: str = ""
    ALIYUN_ICE_REGION: str = "cn-shanghai"
    ALIYUN_ICE_ENDPOINT: str = "ice.cn-shanghai.aliyuncs.com"
    ALIYUN_OSS_ENDPOINT: str = "https://oss-cn-shanghai.aliyuncs.com"
    ALIYUN_OSS_BUCKET: str = ""
    ALIYUN_OSS_OBJECT_PREFIX: str = "auto-nexus/video-render"
    ALIYUN_OSS_PRESIGNED_EXPIRE_SECONDS: int = 3600
    # 阿里百炼非实时 ASR 配置。
    ALIYUN_DASHSCOPE_API_KEY: str = ""
    ALIYUN_DASHSCOPE_WORKSPACE_ID: str = ""
    ALIYUN_DASHSCOPE_REGION: str = "cn-beijing"
    ALIYUN_DASHSCOPE_ASR_MODEL: str = "qwen-audio-3.0-asr-flash-filetrans"
    ALIYUN_DASHSCOPE_ASR_LANGUAGE: str = "zh"
    ALIYUN_DASHSCOPE_ASR_ENABLE_ITN: bool = True
    ALIYUN_OSS_ASR_OBJECT_PREFIX: str = "auto-nexus/audio-asr"
    ALIYUN_OSS_ASR_PRESIGNED_EXPIRE_SECONDS: int = 48 * 3600
    # 云端源素材媒资保留天数，到期由清理任务删除（MinIO 为唯一长期存储）
    VIDEO_CLOUD_RETENTION_DAYS: int = 7
    # 存储桶名称
    MINIO_BUCKET_NAME: str = ""

    MINIO_SECURE: bool = False

    # 智能视频使用标准 S3 Multipart 上传，避免大文件经过 FastAPI 内存。
    MINIO_PRESIGNED_EXPIRE_SECONDS: int = 15 * 60
    MINIO_MULTIPART_PART_SIZE: int = 64 * 1024 * 1024
    MINIO_MULTIPART_MAX_PARTS: int = 10_000

    # ================================================= #
    # ******************* ChromaDB配置 ****************** #
    # ================================================= #
    CHROMA_PERSIST_DIR: str = str(BASE_DIR / "data" / "chroma")  # ChromaDB 持久化目录
    CHROMA_COLLECTION_NAME: str = "knowledge_base"  # ChromaDB 集合名称

    # ================================================= #
    # ******************* 请求限制配置 ****************** #
    # ================================================= #
    REQUEST_LIMITER_REDIS_PREFIX: str = "fastapiadmin:request_limiter:"

    # ================================================= #
    # ******************* 重构配置 ******************* #
    # ================================================= #
    @property
    def MIDDLEWARE_LIST(self) -> list[str | None]:
        """获取项目根目录"""
        # 中间件列表
        MIDDLEWARES: list[str | None] = [
            ("app.core.middlewares.CustomCORSMiddleware" if self.CORS_ORIGIN_ENABLE else None),
            ("app.core.middlewares.RequestLogMiddleware" if self.OPERATION_LOG_RECORD else None),
            "app.core.middlewares.CustomGZipMiddleware" if self.GZIP_ENABLE else None,
        ]
        return MIDDLEWARES

    @property
    def EVENT_LIST(self) -> list[str | None]:
        """获取事件列表"""
        EVENTS: list[str | None] = [
            "app.core.database.redis_connect" if self.REDIS_ENABLE else None,
        ]
        return EVENTS

    @property
    def ASYNC_DB_URI(self) -> str:
        """获取异步数据库连接"""
        if self.DATABASE_TYPE not in ("mysql", "postgres", "sqlite"):
            raise ValueError(
                f"数据库驱动不支持: {self.DATABASE_TYPE}, 异步数据库请选择 mysql、postgres、sqlite"
            )
        db_connect: str = ""
        if self.DATABASE_TYPE == "mysql":
            db_connect = f"mysql+asyncmy://{self.DATABASE_USER}:{quote_plus(self.DATABASE_PASSWORD)}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}?charset=utf8mb4"
        elif self.DATABASE_TYPE == "postgres":
            db_connect = f"postgresql+asyncpg://{self.DATABASE_USER}:{quote_plus(self.DATABASE_PASSWORD)}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        else:
            db_connect = f"sqlite+aiosqlite:///{self.DATABASE_NAME}.db"
        return db_connect

    @property
    def ALIYUN_DASHSCOPE_BASE_URL(self) -> str:
        """返回阿里百炼 DashScope API 基础地址。"""
        if not self.ALIYUN_DASHSCOPE_WORKSPACE_ID:
            return "https://dashscope.aliyuncs.com"
        return (
            f"https://{self.ALIYUN_DASHSCOPE_WORKSPACE_ID}."
            f"{self.ALIYUN_DASHSCOPE_REGION}.maas.aliyuncs.com"
        )

    @property
    def DB_URI(self) -> str:
        """获取同步数据库连接"""
        if self.DATABASE_TYPE not in ("mysql", "postgres", "sqlite"):
            raise ValueError(
                f"数据库驱动不支持: {self.DATABASE_TYPE}, 同步数据库请选择 mysql、postgres、sqlite"
            )
        db_connect: str = ""
        if self.DATABASE_TYPE == "mysql":
            db_connect = f"mysql+pymysql://{self.DATABASE_USER}:{quote_plus(self.DATABASE_PASSWORD)}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}?charset=utf8mb4"
        elif self.DATABASE_TYPE == "postgres":
            db_connect = f"postgresql+psycopg://{self.DATABASE_USER}:{quote_plus(self.DATABASE_PASSWORD)}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        else:
            db_connect = f"sqlite:///{self.DATABASE_NAME}.db"
        return db_connect

    @property
    def REDIS_URI(self) -> str:
        """获取Redis连接"""
        return f"redis://{self.REDIS_USER}:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB_NAME}"

    @property
    def FASTAPI_CONFIG(self) -> dict[str, Any]:
        """获取FastAPI应用属性"""
        return {
            "debug": self.DEBUG,
            "title": self.TITLE,
            "version": self.VERSION,
            "description": self.DESCRIPTION,
            "summary": self.SUMMARY,
            "docs_url": None,
            "redoc_url": None,
            "root_path": self.ROOT_PATH,
            "responses": {
                200: {"description": "成功"},
                400: {"description": "请求参数错误"},
                401: {"description": "未认证"},
                403: {"description": "未授权"},
                404: {"description": "资源不存在"},
                422: {"description": "请求参数验证错误"},
                500: {"description": "服务器内部错误"},
            },
        }

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """获取配置实例"""
    return Settings()

settings = get_settings()
