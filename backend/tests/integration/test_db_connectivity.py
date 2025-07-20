#!/usr/bin/env python3
"""Test database connectivity and CRUD operations."""

import asyncio
import os
from datetime import UTC, datetime

from sqlalchemy import text

from app.core.database import async_session_factory, engine, init_db
from app.crud.document import crud_document
from app.crud.space import crud_space
from app.crud.user import crud_user
from app.schemas.documents import DocumentCreate
from app.schemas.spaces import SpaceCreate
from app.schemas.users import UserCreate


async def test_basic_connection():
    """Test basic database connection."""
    print("🔌 Testing basic database connection...")
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


async def test_database_schema():
    """Test database schema creation."""
    print("🏗️  Testing database schema...")
    try:
        await init_db()
        print("✅ Database schema initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Database schema initialization failed: {e}")
        return False


async def test_crud_operations():
    """Test CRUD operations with real database."""
    print("🔧 Testing CRUD operations...")

    async with async_session_factory() as db:
        try:
            # Test User CRUD
            print("  📝 Testing User CRUD...")

            # Try to use existing user first, or create new one with unique timestamp
            import time

            timestamp = str(int(time.time()))
            username = f"test_integration_user_{timestamp}"

            user_data = UserCreate(
                username=username,
                email=f"test_integration_{timestamp}@example.com",
                full_name="Test Integration User",
                password="test_password123",
            )
            user = await crud_user.create(db, obj_in=user_data)
            assert user.id is not None
            assert user.username == username
            print("    ✅ User creation successful")

            # Test Space CRUD
            print("  📂 Testing Space CRUD...")
            space_data = SpaceCreate(
                name="Test Integration Space",
                description="A test space for integration testing",
                color="#FF5733",
                icon="test",
                is_public=False,
                tags=["integration", "test"],
                meta_data={"test": True},
            )
            space = await crud_space.create(db, obj_in=space_data, user_id=user.id)
            assert space.id is not None
            assert space.name == "Test Integration Space"
            print("    ✅ Space creation successful")

            # Test Document CRUD
            print("  📄 Testing Document CRUD...")
            document_data = DocumentCreate(
                filename="test_integration.txt",
                content_type="text/plain",
                size=1024,
                space_id=space.id,
                description="A test document",
                tags=["integration", "test"],
                meta_data={
                    "source": "integration_test",
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )
            document = await crud_document.create(
                db,
                obj_in=document_data,
                user_id=user.id,
                file_path="/tmp/test_integration.txt",
                file_hash="test_hash_123",
                original_filename="test_integration.txt",
            )
            assert document.id is not None
            assert document.filename == "test_integration.txt"
            assert (
                document.meta_data
                and document.meta_data["source"] == "integration_test"
            )
            print("    ✅ Document creation successful")

            # Test relationships
            print("  🔗 Testing relationships...")
            user_spaces = await crud_space.get_user_spaces(db, user_id=user.id)
            assert len(user_spaces) >= 1
            assert any(s.id == space.id for s in user_spaces)

            space_documents = await crud_document.get_by_space(db, space_id=space.id)
            assert len(space_documents) >= 1
            assert any(d.id == document.id for d in space_documents)
            print("    ✅ Relationships working correctly")

            print("✅ All CRUD operations successful")
            return True

        except Exception as e:
            print(f"❌ CRUD operations failed: {e}")
            import traceback

            traceback.print_exc()
            return False


async def test_complex_queries():
    """Test complex queries and joins."""
    print("🔍 Testing complex queries...")

    async with async_session_factory() as db:
        try:
            # Test user with spaces count
            users = await crud_user.get_multi(db, limit=10)
            if users:
                user = users[0]
                user_spaces = await crud_space.get_user_spaces(db, user_id=user.id)
                print(f"    📊 User {user.username} has {len(user_spaces)} spaces")

            # Test search functionality
            if users and user_spaces:
                documents = await crud_document.search(
                    db, space_id=user_spaces[0].id, query="test", limit=5
                )
                print(f"    🔎 Found {len(documents)} documents matching 'test'")
            else:
                print("    📝 No spaces found for search test")

            print("✅ Complex queries successful")
            return True

        except Exception as e:
            print(f"❌ Complex queries failed: {e}")
            return False


async def cleanup_test_data():
    """Clean up test data."""
    print("🧹 Cleaning up test data...")
    async with async_session_factory() as db:
        try:
            # Find and delete test users (cascading will handle related data)
            users = await crud_user.get_multi(db, limit=100)
            deleted_count = 0
            for user in users:
                if user.username.startswith("test_integration_user_"):
                    await crud_user.remove(db, id=user.id)
                    deleted_count += 1
            if deleted_count > 0:
                print(f"✅ Test data cleaned up ({deleted_count} test users)")
        except Exception as e:
            print(f"⚠️  Cleanup failed (this is usually okay): {e}")


async def main():
    """Run all connectivity tests."""
    print("🚀 Starting CRUD to Database Connectivity Tests")
    print("=" * 50)

    # Update DATABASE_URL for local testing if needed
    current_db_url = os.getenv("DATABASE_URL", "")
    if "postgres:5432" in current_db_url:
        local_db_url = current_db_url.replace("postgres:5432", "localhost:5432")
        os.environ["DATABASE_URL"] = local_db_url
        print(f"📝 Updated DATABASE_URL to: {local_db_url}")

    tests = [
        ("Basic Connection", test_basic_connection),
        ("Database Schema", test_database_schema),
        ("CRUD Operations", test_crud_operations),
        ("Complex Queries", test_complex_queries),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        result = await test_func()
        results.append((test_name, result))

    # Cleanup
    await cleanup_test_data()

    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1

    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print(
            "🎉 All connectivity tests passed! CRUD layer is properly connected to the database."
        )
    else:
        print(
            "⚠️  Some tests failed. Please check the database configuration and connections."
        )

    # Close database connections
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
