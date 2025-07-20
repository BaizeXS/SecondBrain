#!/usr/bin/env python3
"""
SecondBrain 数据库清理工具
用于清理测试数据或重置数据库到干净状态
"""

import asyncio
import os
import sys
from datetime import datetime

import asyncpg
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker

# 数据库配置
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://secondbrain:secondbrain123@localhost:5432/secondbrain"
)


class DatabaseCleaner:
    """数据库清理器"""

    def __init__(self):
        self.engine = None
        self.async_session = None
        self.cleaned_stats = {
            "users": 0,
            "spaces": 0,
            "documents": 0,
            "notes": 0,
            "conversations": 0,
            "messages": 0,
            "annotations": 0,
            "citations": 0,
        }

    async def __aenter__(self):
        self.engine = create_async_engine(DATABASE_URL, echo=False)
        self.async_session = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.engine:
            await self.engine.dispose()

    def log(self, message: str, level: str = "INFO"):
        """打印日志信息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        symbol = "✅" if level == "SUCCESS" else "❌" if level == "ERROR" else "ℹ️"
        print(f"[{timestamp}] {symbol} {message}")

    async def get_table_stats(self):
        """获取各表的数据统计"""
        async with self.async_session() as session:
            stats = {}
            tables = [
                "users",
                "spaces",
                "documents",
                "notes",
                "conversations",
                "messages",
                "annotations",
                "citations",
            ]

            for table in tables:
                result = await session.execute(
                    text(f"SELECT COUNT(*) FROM {table}")
                )
                count = result.scalar()
                stats[table] = count

            return stats

    async def clean_test_data(self, preserve_demo: bool = True):
        """清理测试数据"""
        self.log("开始清理测试数据...")

        async with self.async_session() as session:
            try:
                # 保留演示用户的条件
                demo_user_condition = ""
                if preserve_demo:
                    demo_user_condition = "AND username NOT IN ('demo_user', 'teacher_demo')"
                    self.log("保留演示账号数据")

                # 1. 获取要删除的用户ID
                result = await session.execute(
                    text(f"""
                        SELECT id FROM users 
                        WHERE username LIKE 'test_user_%' 
                        {demo_user_condition}
                    """)
                )
                test_user_ids = [row[0] for row in result]

                if test_user_ids:
                    user_ids_str = ",".join(map(str, test_user_ids))

                    # 2. 删除相关数据（按依赖关系顺序）
                    # 删除消息
                    result = await session.execute(
                        text(f"""
                            DELETE FROM messages 
                            WHERE conversation_id IN (
                                SELECT id FROM conversations 
                                WHERE user_id IN ({user_ids_str})
                            )
                        """)
                    )
                    self.cleaned_stats["messages"] = result.rowcount

                    # 删除对话
                    result = await session.execute(
                        text(f"DELETE FROM conversations WHERE user_id IN ({user_ids_str})")
                    )
                    self.cleaned_stats["conversations"] = result.rowcount

                    # 删除标注
                    result = await session.execute(
                        text(f"DELETE FROM annotations WHERE user_id IN ({user_ids_str})")
                    )
                    self.cleaned_stats["annotations"] = result.rowcount

                    # 删除引用
                    result = await session.execute(
                        text(f"""
                            DELETE FROM citations 
                            WHERE document_id IN (
                                SELECT id FROM documents 
                                WHERE space_id IN (
                                    SELECT id FROM spaces 
                                    WHERE user_id IN ({user_ids_str})
                                )
                            )
                        """)
                    )
                    self.cleaned_stats["citations"] = result.rowcount

                    # 删除笔记
                    result = await session.execute(
                        text(f"""
                            DELETE FROM notes 
                            WHERE space_id IN (
                                SELECT id FROM spaces 
                                WHERE user_id IN ({user_ids_str})
                            )
                        """)
                    )
                    self.cleaned_stats["notes"] = result.rowcount

                    # 删除文档
                    result = await session.execute(
                        text(f"""
                            DELETE FROM documents 
                            WHERE space_id IN (
                                SELECT id FROM spaces 
                                WHERE user_id IN ({user_ids_str})
                            )
                        """)
                    )
                    self.cleaned_stats["documents"] = result.rowcount

                    # 删除空间
                    result = await session.execute(
                        text(f"DELETE FROM spaces WHERE user_id IN ({user_ids_str})")
                    )
                    self.cleaned_stats["spaces"] = result.rowcount

                    # 删除用户
                    result = await session.execute(
                        text(f"DELETE FROM users WHERE id IN ({user_ids_str})")
                    )
                    self.cleaned_stats["users"] = result.rowcount

                    await session.commit()
                    self.log("测试数据清理成功", "SUCCESS")
                else:
                    self.log("没有找到测试数据")

            except Exception as e:
                await session.rollback()
                self.log(f"清理失败: {str(e)}", "ERROR")
                raise

    async def reset_demo_data(self):
        """重置演示数据（删除演示用户的所有数据但保留账号）"""
        self.log("开始重置演示数据...")

        async with self.async_session() as session:
            try:
                # 获取演示用户ID
                result = await session.execute(
                    text("SELECT id FROM users WHERE username IN ('demo_user', 'teacher_demo')")
                )
                demo_user_ids = [row[0] for row in result]

                if demo_user_ids:
                    user_ids_str = ",".join(map(str, demo_user_ids))

                    # 删除演示用户的数据（保留用户账号）
                    tables_to_clean = [
                        ("messages", "conversation_id IN (SELECT id FROM conversations WHERE user_id IN ({}))", ),
                        ("conversations", "user_id IN ({})", ),
                        ("annotations", "user_id IN ({})", ),
                        ("citations", "document_id IN (SELECT id FROM documents WHERE space_id IN (SELECT id FROM spaces WHERE user_id IN ({})))", ),
                        ("notes", "space_id IN (SELECT id FROM spaces WHERE user_id IN ({}))", ),
                        ("documents", "space_id IN (SELECT id FROM spaces WHERE user_id IN ({}))", ),
                        ("spaces", "user_id IN ({})", ),
                    ]

                    for table, condition in tables_to_clean:
                        query = f"DELETE FROM {table} WHERE {condition.format(user_ids_str)}"
                        result = await session.execute(text(query))
                        self.log(f"删除 {table}: {result.rowcount} 条记录")

                    await session.commit()
                    self.log("演示数据重置成功", "SUCCESS")
                else:
                    self.log("没有找到演示用户")

            except Exception as e:
                await session.rollback()
                self.log(f"重置失败: {str(e)}", "ERROR")
                raise

    async def full_reset(self):
        """完全重置数据库（危险操作）"""
        self.log("⚠️  警告：即将执行完全重置，这将删除所有数据！", "ERROR")
        
        confirm = input("确认要删除所有数据吗？输入 'YES' 继续: ")
        if confirm != "YES":
            self.log("操作已取消")
            return

        async with self.async_session() as session:
            try:
                # 按依赖关系顺序删除所有表数据
                tables = [
                    "messages",
                    "conversation_branches",
                    "conversations",
                    "annotations",
                    "citations",
                    "note_versions",
                    "notes",
                    "documents",
                    "spaces",
                    "agent_executions",
                    "agents",
                    "users",
                ]

                for table in tables:
                    result = await session.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
                    self.log(f"清空表 {table}")

                await session.commit()
                self.log("数据库完全重置成功", "SUCCESS")

            except Exception as e:
                await session.rollback()
                self.log(f"重置失败: {str(e)}", "ERROR")
                raise

    def print_summary(self):
        """打印清理总结"""
        print("\n" + "=" * 70)
        print("📊 数据库清理总结")
        print("=" * 70)

        print("\n✅ 清理的数据统计：")
        for table, count in self.cleaned_stats.items():
            if count > 0:
                print(f"  - {table}: {count} 条记录")

        print("\n💡 提示：")
        print("  - 使用 --preserve-demo 保留演示账号")
        print("  - 使用 --reset-demo 重置演示数据")
        print("  - 使用 --full-reset 完全重置数据库（危险）")


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="SecondBrain 数据库清理工具")
    parser.add_argument(
        "--preserve-demo",
        action="store_true",
        default=True,
        help="保留演示账号（默认开启）",
    )
    parser.add_argument(
        "--reset-demo",
        action="store_true",
        help="重置演示数据（删除内容但保留账号）",
    )
    parser.add_argument(
        "--full-reset",
        action="store_true",
        help="完全重置数据库（危险操作）",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="仅显示数据库统计信息",
    )

    args = parser.parse_args()

    print("🧹 SecondBrain 数据库清理工具")
    print("⏰ 开始时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("🔗 数据库:", DATABASE_URL.split("@")[1] if "@" in DATABASE_URL else "localhost")
    print("=" * 70)

    async with DatabaseCleaner() as cleaner:
        # 显示当前统计
        stats = await cleaner.get_table_stats()
        print("\n📈 当前数据库状态：")
        for table, count in stats.items():
            print(f"  - {table}: {count} 条记录")

        if args.stats:
            return

        # 执行清理操作
        if args.full_reset:
            await cleaner.full_reset()
        elif args.reset_demo:
            await cleaner.reset_demo_data()
        else:
            await cleaner.clean_test_data(preserve_demo=args.preserve_demo)

        # 打印总结
        cleaner.print_summary()

    print("\n✅ 操作完成！")


if __name__ == "__main__":
    asyncio.run(main())