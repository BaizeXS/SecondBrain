#!/usr/bin/env python3
"""
演示数据管理工具
用法: uv run python tools/demo_data.py [create|clean]
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import delete, select

from app.core.database import async_session_factory
from app.core.password import get_password_hash
from app.models.models import Conversation, Note, Space, User


async def create_demo_data():
    """创建演示数据"""
    async with async_session_factory() as db:
        # 检查是否已存在演示用户
        result = await db.execute(select(User).where(User.username == "demo_user"))
        if result.scalar_one_or_none():
            print("✅ 演示数据已存在")
            return

        print("🔨 创建演示数据...")

        # 创建演示用户
        demo_user = User(
            username="demo_user",
            email="demo@example.com",
            full_name="演示用户",
            hashed_password=get_password_hash("Demo123456!"),
            is_active=True,
        )
        db.add(demo_user)
        await db.flush()

        # 创建演示空间
        demo_space = Space(
            name="我的第一个知识空间",
            description="这是一个演示知识空间，你可以在这里上传文档、做笔记、与AI对话",
            user_id=demo_user.id,
        )
        db.add(demo_space)
        await db.flush()

        # 创建演示笔记
        demo_note = Note(
            title="欢迎使用 Second Brain",
            content="""# 欢迎使用 Second Brain！

这是一个AI驱动的个人知识管理系统。

## 主要功能

1. **知识空间** - 组织你的文档和笔记
2. **AI对话** - 与100+AI模型对话
3. **文档管理** - 支持PDF、Word、PPT等格式
4. **智能笔记** - Markdown格式，支持AI增强

## 快速开始

- 点击左侧创建新的空间
- 上传文档开始管理知识
- 与AI对话获得智能助手支持

祝你使用愉快！""",
            space_id=demo_space.id,
            user_id=demo_user.id,
            note_type="manual",
        )
        db.add(demo_note)

        # 创建演示对话
        demo_conversation = Conversation(
            title="AI助手对话",
            space_id=demo_space.id,
            user_id=demo_user.id,
            mode="chat",  # 必填字段
            model="openrouter/auto",  # 设置默认模型
        )
        db.add(demo_conversation)

        await db.commit()
        print("✅ 演示数据创建成功！")
        print("📧 用户名: demo_user")
        print("🔑 密码: Demo123456!")


async def clean_demo_data():
    """清除演示数据"""
    async with async_session_factory() as db:
        # 查找演示用户
        result = await db.execute(select(User).where(User.username == "demo_user"))
        demo_user = result.scalar_one_or_none()

        if not demo_user:
            print("❌ 未找到演示数据")
            return

        print("🧹 清除演示数据...")

        try:
            # 先删除相关的对话
            await db.execute(delete(Conversation).where(Conversation.user_id == demo_user.id))
            # 删除相关的笔记
            await db.execute(delete(Note).where(Note.user_id == demo_user.id))
            # 删除相关的空间
            await db.execute(delete(Space).where(Space.user_id == demo_user.id))
            # 最后删除用户
            await db.execute(delete(User).where(User.id == demo_user.id))

            await db.commit()
            print("✅ 演示数据已清除")
        except Exception as e:
            print(f"❌ 清除失败: {e}")
            await db.rollback()


async def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: uv run python tools/demo_data.py [create|clean]")
        print("  create - 创建演示数据")
        print("  clean  - 清除演示数据")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "create":
        await create_demo_data()
    elif command == "clean":
        await clean_demo_data()
    else:
        print(f"❌ 未知命令: {command}")
        print("请使用 'create' 或 'clean'")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
