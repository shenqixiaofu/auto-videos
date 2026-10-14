import asyncio
import random
from datetime import datetime, date
from typing import List
from loguru import logger
from sqlalchemy import select, func

# ================= 导入你工程中的依赖 =================
from app.core.database import async_db_session
from app.plugin.module_ai_image.fission.service import FissionService
from app.api.v1.module_system.auth.utils import get_system_auth
from app.plugin.module_ai_image.fission.crud import FissionBatchCRUD
from app.plugin.module_ai_image.auto_strategy.crud import AiImageAutoStrategyCRUD
from app.plugin.module_ai_image.auto_strategy.model import AiImageAutoStrategyModel
from app.config.setting import settings
from app.core.database import create_async_engine_and_session

# ⚠️ 注意：请替换为你项目中真实的模型路径
# from app.models.ai_image import AiImageAutoStrategy, AiImageBatch
# ======================================================


# ---------------------------------------------------------
# 【层级 4】核心业务创建：调LLM + 走CRUD入库
# ---------------------------------------------------------
async def create_auto_batch_and_tasks(
    location: str, gender: str, age: int, strategy_id: int, db_session
):
    """自动化引擎专属的创建链路"""
    try:
        # 1. 纯逻辑层：获取大模型生成的 Prompt 和任务数据
        batch_data, tasks_data = await FissionService.build_fission_data_payload(
            location=location, gender=gender, age=age, strategy_id=strategy_id
        )

        # 2. 获取系统超级权限 Auth (传入当前会话)
        system_auth = await get_system_auth(db_session)

        # 3. 复用现成的 CRUD 入库
        new_batch = await FissionBatchCRUD(system_auth).create_fission_bundle_crud(
            batch_data, tasks_data
        )
        logger.info(
            f"✅ 自动批次创建成功: [{batch_data['batch_sn']}]，包含 10 个衍生任务"
        )

    except Exception as e:
        logger.error(f"❌ 自动批次入库失败: {str(e)}")
        # 向上抛出异常，让引擎层决定是否继续跑下一个策略
        raise


# ---------------------------------------------------------
# 【层级 3】策略巡检引擎：扫表 + 额度校验 + 随机发牌
# ---------------------------------------------------------
async def auto_generation_engine(db_session):
    """
    ⚙️ 自动化生图引擎 (框架模式版)
    完全复用 CRUD 层逻辑，保持与 API 业务逻辑高度一致
    """
    logger.info("⚙️ 引擎启动：扫描 [ai_image_auto_strategy] 策略表...")

    # 1. 构造系统级 Auth 实例，这是进入“框架模式”的通行证
    system_auth = await get_system_auth(db_session)

    try:
        # 2. 使用 CRUD 类查询启用状态的策略 (框架模式)
        # 模拟前端分页查询，这里给一个较大的 limit 确保扫出所有启用策略
        strategy_result = await AiImageAutoStrategyCRUD(
            system_auth
        ).page_ai_image_auto_strategy_crud(
            offset=0,
            limit=100,
            order_by=[{"priority": "desc"}],
            search={"status": "0"},  # 只查启用的
        )

        logger.info(f"🚀 扫描到 {strategy_result} 个启用状态的策略")
        raw_strategies = strategy_result.get("items", [])
        strategies = [AiImageAutoStrategyModel(**item) for item in raw_strategies]
        if not strategies:
            logger.info("💤 当前无启用状态的生图策略。")
            return

        for strategy in strategies:
            try:
                # 3. 校验今日额度 (同样封装在 CRUD 内部)
                # 假设 FissionBatchCRUD 已经实现了按策略统计今日数量的方法
                today_batch_count = await FissionBatchCRUD(
                    system_auth
                ).get_today_batch_count_by_strategy_crud(strategy_id=strategy.id)
                logger.debug(
                    f"🚀 策略 [{strategy.strategy_name}] 今日已生成 {today_batch_count} 个批次"
                )
                if today_batch_count >= strategy.daily_batch_limit:
                    logger.debug(
                        f"🛑 策略 [{strategy.strategy_name}] 今日额度已满 ({today_batch_count}/{strategy.daily_batch_limit})"
                    )
                    continue

                # 4. 随机化参数
                target_age = random.randint(strategy.age_min, strategy.age_max)
                target_gender = (
                    random.choice(["女"])
                    if strategy.gender == "随机"
                    else strategy.gender
                )

                # 5. 调用业务 Service (也需要传入 auth)
                # 统一使用 FissionCreateSchema 包装数据，模拟前端提 交
                from app.plugin.module_ai_image.fission.schema import (
                    FissionCreateSchema,
                )

                fission_data = FissionCreateSchema(
                    location=strategy.location, gender=target_gender, age=target_age
                )

                # 这里的 create_fission_service 内部会自动调用 FissionBatchCRUD
                # 我们只需要额外传入 strategy_id (建议在 Service 逻辑中增加对该字段的可选支持)
                await FissionService.create_fission_service(
                    auth=system_auth,
                    data=fission_data,
                    strategy_id=strategy.id,  # 注入策略关联
                    theme_ids=strategy.theme_ids,
                    extra_command=strategy.background_strategy,
                )
                await db_session.commit()
                logger.info(
                    f"🚀 自动触发成功: {strategy.strategy_name} -> {strategy.location}"
                )

            except Exception as e:
                logger.error(f"⚠️ 策略 [{strategy.strategy_name}] 执行异常: {str(e)}")
                continue

    except Exception as e:
        logger.error(f"❌ 自动化引擎框架链路故障: {str(e)}")


# ---------------------------------------------------------
# 【层级 2】异步生命周期管理：开辟数据库事务
# ---------------------------------------------------------
async def async_main_runner():
    """异步包装器：在这个独立的事件循环中，建立专属的数据库连接"""

    # 1. 🚀 核心改动：在当前的 Loop 中，动态创建一个【全新的】引擎和 Session 工厂
    local_async_engine, LocalAsyncSession = create_async_engine_and_session(
        settings.ASYNC_DB_URI
    )

    try:
        # 2. 使用这个本地专属的 Session 跑业务
        async with LocalAsyncSession() as db_session:
            # 执行主引擎逻辑
            await auto_generation_engine(db_session)

            # 提交更改
            await db_session.commit()

    finally:
        # 3. 🚨 极其重要：任务跑完，必须显式地销毁这个临时引擎
        # 否则每次跑定时任务都会新建一个连接池，导致 MySQL 连接数被撑爆！
        await local_async_engine.dispose()


# ---------------------------------------------------------
# 【层级 1】框架同步入口：对接 APScheduler
# ---------------------------------------------------------
def handler(*args, **kwargs):
    """
    ⚙️ 24小时自动化生图引擎入口 (作为 APScheduler 定时任务被触发)
    """
    logger.info("=" * 50)
    logger.info("🤖 AI 生图自动化引擎被 APScheduler 唤醒")
    logger.info("=" * 50)

    try:
        # 强制在当前线程启动一个事件循环来跑异步逻辑
        asyncio.run(async_main_runner())

        logger.info("=" * 50)
        logger.info("✅ 自动化巡检圆满完成，数据库连接已释放")
        logger.info("=" * 50)

        return {"status": "success", "message": "生图引擎调度完成"}

    except Exception as e:
        logger.error(f"❌ 自动化引擎全局崩溃: {str(e)}")
        return {"status": "error", "message": str(e)}
