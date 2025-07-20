#!/usr/bin/env python3
"""
运行所有集成测试的脚本。

使用方法：
    python tests/integration/run_integration_tests.py
"""

import os
import subprocess
import sys
from pathlib import Path


def run_tests():
    """运行集成测试。"""
    # 确保在正确的目录
    backend_dir = Path(__file__).parent.parent.parent
    os.chdir(backend_dir)

    print("🚀 Starting Integration Tests")
    print("=" * 60)

    # 设置测试环境变量
    test_env = os.environ.copy()
    test_env["TESTING"] = "1"
    test_env["DATABASE_URL"] = (
        "postgresql+asyncpg://secondbrain:secondbrain123@localhost:5432/secondbrain_test"
    )

    # 运行测试
    cmd = [
        "uv",
        "run",
        "pytest",
        "-v",  # 详细输出
        "--tb=short",  # 简短的错误追踪
        "--maxfail=3",  # 最多失败3个测试后停止
        "-x",  # 第一个失败后停止
    ]

    # 添加覆盖率选项（可选）
    if "--coverage" in sys.argv:
        cmd.extend(
            [
                "--cov=app",
                "--cov-report=term-missing",
                "--cov-report=html",
            ]
        )

    # 添加具体的测试文件
    cmd.extend(
        [
            "tests/integration/test_db_connectivity.py",
            "tests/integration/test_auth_flow.py",
            "tests/integration/test_user_workflow.py",
            "tests/integration/test_api_e2e.py",
            "tests/integration/test_spaces_workflow.py",
            "tests/integration/test_documents_workflow.py",
            "tests/integration/test_notes_workflow.py",
            "tests/integration/test_chat_workflow.py",
            "tests/integration/test_export_workflow.py",
            "tests/integration/test_error_handling.py",
        ]
    )

    print(f"📝 Running command: {' '.join(cmd)}")
    print("-" * 60)

    # 运行测试
    result = subprocess.run(cmd, env=test_env)

    if result.returncode == 0:
        print("\n✅ All integration tests passed!")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


def check_services():
    """检查必要的服务是否运行。"""
    print("🔍 Checking required services...")

    services = {
        "PostgreSQL": "docker exec secondbrain-postgres pg_isready -U secondbrain",
        "Redis": "redis-cli ping",
        "MinIO": "curl -s http://localhost:9000/minio/health/live",
    }

    all_good = True
    for service, check_cmd in services.items():
        result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✅ {service} is running")
        else:
            print(f"  ❌ {service} is not running")
            all_good = False

    if not all_good:
        print("\n⚠️  Some services are not running!")
        print("Please start all services with: docker-compose up -d")
        sys.exit(1)

    print()


def create_test_database():
    """创建测试数据库（如果不存在）。"""
    print("🗄️  Setting up test database...")

    # 检查测试数据库是否存在
    check_cmd = [
        "docker",
        "exec",
        "secondbrain-postgres",
        "psql",
        "-U",
        "secondbrain",
        "-lqt",
    ]

    result = subprocess.run(check_cmd, capture_output=True, text=True)

    if "secondbrain_test" not in result.stdout:
        # 创建测试数据库
        create_cmd = [
            "docker",
            "exec",
            "secondbrain-postgres",
            "psql",
            "-U",
            "secondbrain",
            "-c",
            "CREATE DATABASE secondbrain_test;",
        ]

        result = subprocess.run(create_cmd)

        if result.returncode == 0:
            print("  ✅ Test database created")
        else:
            print("  ❌ Failed to create test database")
            sys.exit(1)
    else:
        print("  ✅ Test database already exists")

    print()


if __name__ == "__main__":
    try:
        # 检查服务
        check_services()

        # 创建测试数据库
        create_test_database()

        # 运行测试
        run_tests()

    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        sys.exit(1)
