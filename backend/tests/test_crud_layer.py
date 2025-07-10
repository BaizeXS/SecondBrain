"""测试CRUD层是否正常工作."""

import asyncio

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

async def test_crud_layer():
    """测试CRUD层."""
    print("🔍 测试 CRUD 层...")

    try:
        # 测试导入
        print("\n1. 测试CRUD导入...")
        from app import crud
        from app.core.database import async_session_factory
        print("✅ CRUD模块导入成功")

        # 创建数据库会话
        async with async_session_factory() as db:
            print("\n2. 测试用户CRUD操作...")

            # 测试获取用户
            user = await crud.user.get_by_username(db, username="testuser_demo")
            if user:
                print(f"✅ 找到用户: {user.username} (ID: {user.id})")

                # 测试空间CRUD
                print("\n3. 测试空间CRUD操作...")
                spaces = await crud.space.get_user_spaces(db, user_id=user.id)
                print(f"✅ 用户有 {len(spaces)} 个空间")

                if spaces:
                    space = spaces[0]
                    print(f"   空间: {space.name} (ID: {space.id})")

                    # 测试文档CRUD
                    print("\n4. 测试文档CRUD操作...")
                    documents = await crud.document.get_by_space(
                        db, space_id=space.id, limit=5
                    )
                    print(f"✅ 空间中有 {len(documents)} 个文档")

                    # 测试对话CRUD
                    print("\n5. 测试对话CRUD操作...")
                    conversations = await crud.conversation.get_user_conversations(
                        db, user_id=user.id, limit=5
                    )
                    print(f"✅ 用户有 {len(conversations)} 个对话")
            else:
                print("❌ 未找到测试用户")

        print("\n✅ CRUD层测试完成！")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_crud_layer())
