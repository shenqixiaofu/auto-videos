from app.core.database import async_db_session
from app.api.v1.module_system.auth.schema import AuthSchema
from app.api.v1.module_system.user.model import UserModel

# 如果需要真的 UserModel，从你的 model 导入
# from app.models.user import UserModel


async def get_system_auth(db_session) -> AuthSchema:
    """
    🛠️ 构造系统级 Auth (用于定时任务、后台脚本等无用户上下文的场景)
    """

    from sqlalchemy import select

    stmt = select(UserModel).where(
        UserModel.username == "admin"
    )  # 假设你有个叫 admin 的号
    sys_user = (await db_session.execute(stmt)).scalars().first()

    return AuthSchema(user=sys_user, check_data_scope=False, db=db_session)
