from datetime import datetime
from typing import Any
from sqlalchemy import delete, func, select
from app.api.v1.module_system.auth.schema import AuthSchema
from app.core.base_crud import CRUDBase

# 导入你的 Model
from .model import AIImageBatch, AIImageTask
from .schema import FissionCreateSchema, BatchUpdateSchema
from .schema import TaskCallbackSchema


class FissionBatchCRUD(CRUDBase[AIImageBatch, FissionCreateSchema, BatchUpdateSchema]):
    """AI 自动化裂变数据层"""

    def __init__(self, auth: AuthSchema) -> None:
        """初始化 CRUD"""
        super().__init__(model=AIImageBatch, auth=auth)

    async def delete_fission_bundle_crud(self, batch_id: int) -> bool:
        """
        原子化物理删除：销毁 1个批次 + 关联的所有生图任务
        """
        # 1. 先把底下的“子兵”全部干掉 (AIImageTask)
        # 使用 delete 语句比循环删除效率高得多
        task_delete_stmt = delete(AIImageTask).where(AIImageTask.batch_id == batch_id)
        await self.auth.db.execute(task_delete_stmt)

        # 2. 再把“司令部”端了 (AIImageBatch)
        batch_delete_stmt = delete(AIImageBatch).where(AIImageBatch.id == batch_id)
        result = await self.auth.db.execute(batch_delete_stmt)

        # 3. 检查受影响的行数，看看是不是真的删掉了
        if result.rowcount == 0:
            return False

        # 4. Flush 进事务流，同样不写 commit，等框架管家最后拍板
        await self.auth.db.flush()

        return True

    async def get_distinct_column_values(
        self, column_name: str, gender: str = None
    ) -> list[str]:
        """
        🚀 核心魔法增强版：获取某个字段去重后的所有有效值 (支持按性别联动过滤)
        """
        # 1. 获取模型对应的列
        column = getattr(self.model, column_name, None)
        if column is None:
            return []

        # 2. 构建基础查询：SELECT DISTINCT 且排除空值
        query = select(column).where(column.isnot(None)).where(column != "")

        # 3. --- 联动核心：如果传了 gender，则精准过滤 ---
        if gender:
            # 注意：这里假设 self.model 必须有 gender 字段
            query = query.where(self.model.gender == gender)

        # 4. 执行去重
        query = query.distinct()

        # 5. 执行并返回结果
        result = await self.auth.db.execute(query)
        return list(result.scalars().all())

    # ==========================================
    # 核心函数 1：多表联动原子化入库 (保留并修复 db 调用)
    # ==========================================
    async def create_fission_bundle_crud(
        self, batch_data: dict, tasks_data: list[dict]
    ) -> AIImageBatch:
        """
        原子化创建：1个批次 + 10个生图任务
        """
        if batch_data.get("status") is None:  # 👈 添加默认值
            batch_data["status"] = 1
        # 不用写 try...except 捕获回滚了，把异常抛给外层的框架管家去 Rollback
        user_id = self.auth.user.id if self.auth.user else None

        # 1. 创建批次实例
        batch_obj = AIImageBatch(**batch_data, created_id=user_id, updated_id=user_id)
        self.auth.db.add(batch_obj)

        # 2. 预提交以获取 batch_obj.id (关键步骤，千万不能删)
        await self.auth.db.flush()

        # 3. 批量创建任务明细
        task_objs = [
            AIImageTask(
                **t, batch_id=batch_obj.id, created_id=user_id, updated_id=user_id
            )
            for t in tasks_data
        ]
        self.auth.db.add_all(task_objs)

        # 4. 再次 flush 把 10 个任务推入当前事务流，并刷新 batch_obj 的返回数据
        await self.auth.db.flush()
        await self.auth.db.refresh(batch_obj)

        # 直接返回，把 commit 的大权交还给 FastapiAdmin 框架！
        return batch_obj

    # ==========================================
    # 核心函数 3：获取批次列表 (恢复并修复 list_crud 报错)
    # ==========================================
    async def list_fission_batches(
        self, search: dict, offset: int, limit: int, out_schema
    ):
        """
        调用父类 CRUDBase 强大的 page 方法，实现完美分页和过滤
        """
        # ⚠️ 修复：不再调用不存在的 list_crud，而是调用父类原生的 page 方法
        return await self.page(
            offset=offset,
            limit=limit,
            order_by=[
                {"created_time": "desc"},
            ],
            search=search,
            out_schema=out_schema,
        )

        # 在 FissionBatchCRUD 类中

    async def get_today_batch_count_by_strategy_crud(self, strategy_id: int) -> int:
        """统计指定策略今日已生成的批次数量"""
        from datetime import datetime, date

        today_start = datetime.combine(date.today(), datetime.min.time())

        # 使用 self.auth.db 保持会话一致
        stmt = (
            select(func.count(self.model.id))
            .where(self.model.strategy_id == strategy_id)
            .where(self.model.created_time >= today_start)
        )
        result = await self.auth.db.execute(stmt)
        return result.scalar() or 0


class FissionTaskCRUD(CRUDBase[AIImageTask, Any, Any]):
    """
    负责操作“裂变子任务表”（具体到每一张图、每一个 Prompt 和图片 URL）
    """

    def __init__(self, auth: Any):
        super().__init__(model=AIImageTask, auth=auth)

    async def count(self, search: dict) -> int:
        """
        🚀 动态条件统计总数
        支持精确匹配 (key: value) 和 IN 查询 (key__in: list)
        """
        # 1. 构造基础的 count 语句: SELECT count(1) FROM ai_image_task
        query = select(func.count()).select_from(self.model)

        # 2. 动态解析 search 字典
        if search:
            for key, value in search.items():
                # 处理 __in 语法 (例如: process_status__in: [0, 1])
                if key.endswith("__in"):
                    real_field = key.replace("__in", "")
                    column = getattr(self.model, real_field, None)
                    if column is not None and isinstance(value, (list, tuple)):
                        query = query.where(column.in_(value))

                # 处理普通的精确匹配 (例如: batch_id: 123)
                else:
                    column = getattr(self.model, key, None)
                    if column is not None:
                        query = query.where(column == value)

        # 3. 执行查询并返回标量结果
        result = await self.auth.db.execute(query)
        # scalar() 会取出第一行第一列的值，如果是 None 则兜底返回 0
        return result.scalar() or 0

    async def claim_pending_task_crud(self, agent_id: str) -> AIImageTask | None:
        """
        核心抢单逻辑：行级悲观锁 + 闪避并发
        """
        # 1. 查找最早的一条未处理任务 (process_status == 0)
        # ⚠️ 核心魔法：with_for_update(skip_locked=True)
        query = (
            select(AIImageTask)
            .where(AIImageTask.process_status == 0)
            .order_by(AIImageTask.id.asc())  # 先进先出，老的优先跑
            .limit(1)
            .with_for_update(skip_locked=True)
        )

        result = await self.auth.db.execute(query)
        task_obj = result.scalars().first()

        # 2. 如果没单子了，直接返回 None
        if not task_obj:
            return None

        # 3. 抢单成功！立刻修改状态为 1 (生图中)，并刻上 Agent 的名字
        task_obj.process_status = 1
        task_obj.agent_id = agent_id

        # 4. 遵守咱们之前定的铁律：只 flush 推入事务流，把 commit 留给框架管家！
        await self.auth.db.flush()
        await self.auth.db.refresh(task_obj)

        return task_obj

    async def update_task_callback_crud(
        self, payload: TaskCallbackSchema
    ) -> AIImageTask | None:
        """
        核心回传逻辑：更新任务状态、图片URL和完成时间
        """
        # 1. 查出这笔任务
        query = select(AIImageTask).where(AIImageTask.id == payload.task_id)
        result = await self.auth.db.execute(query)
        task_obj = result.scalars().first()

        if not task_obj:
            return None

        # 2. 注入结果数据
        task_obj.process_status = payload.process_status
        task_obj.completed_at = datetime.now()

        if payload.process_status == 2 and payload.image_url:
            task_obj.image_url = payload.image_url

        if payload.process_status == 3 and payload.error_msg:
            # 失败时，把错误信息写进 ModelMixin 自带的 description 字段里
            task_obj.description = payload.error_msg

        # 3. 刷入事务
        await self.auth.db.flush()
        await self.auth.db.refresh(task_obj)

        return task_obj

    # ==========================================
    # 核心函数 2：获取批次下的任务 (恢复并修复 db 调用)
    # ==========================================
    async def get_tasks_by_batch_id(self, batch_id: int) -> list[AIImageTask]:
        """
        查询某个批次下的所有任务明细
        因为当前类的泛型是 AIImageBatch，查 Task 表用原生 select 最合理
        """
        query = (
            select(AIImageTask)
            .where(AIImageTask.batch_id == batch_id)
            .order_by(AIImageTask.id.asc())
        )
        result = await self.auth.db.execute(query)  # ⚠️ 修复：必须用 self.auth.db
        return list(result.scalars().all())
