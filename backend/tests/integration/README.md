# 集成测试指南

本目录包含 Second Brain 后端的集成测试，用于验证各个组件协同工作的正确性。

## 测试结构

```
tests/integration/
├── conftest.py              # 测试配置和通用 fixtures
├── test_db_connectivity.py  # 数据库连接测试
├── test_auth_flow.py        # 认证流程测试
├── test_user_workflow.py    # 用户工作流测试
└── test_api_e2e.py         # API 端到端测试
```

## 运行测试

### 前置条件

1. 确保所有服务正在运行：

```bash
docker-compose up -d
```

2. 创建测试数据库（如果不存在）：

```bash
docker-compose exec postgres psql -U secondbrain -c "CREATE DATABASE secondbrain_test;"
```

### 运行所有集成测试

```bash
# 在 backend 目录下
uv run pytest tests/integration -v
```

### 运行特定测试文件

```bash
# 测试数据库连接
uv run pytest tests/integration/test_db_connectivity.py -v

# 测试认证流程
uv run pytest tests/integration/test_auth_flow.py -v

# 测试用户工作流
uv run pytest tests/integration/test_user_workflow.py -v

# 测试 API 端到端
uv run pytest tests/integration/test_api_e2e.py -v
```

### 运行特定测试类或方法

```bash
# 运行特定测试类
uv run pytest tests/integration/test_auth_flow.py::TestAuthenticationFlow -v

# 运行特定测试方法
uv run pytest tests/integration/test_auth_flow.py::TestAuthenticationFlow::test_user_registration_flow -v
```

### 带覆盖率运行

```bash
uv run pytest tests/integration --cov=app --cov-report=term-missing --cov-report=html
```

### 调试模式

```bash
# 显示详细输出
uv run pytest tests/integration -vv

# 在第一个失败时停止
uv run pytest tests/integration -x

# 显示打印输出
uv run pytest tests/integration -s

# 显示完整的错误追踪
uv run pytest tests/integration --tb=long
```

## 测试覆盖范围

### 1. 数据库连接测试 (test_db_connectivity.py)

- ✅ 基础数据库连接
- ✅ 数据库模式初始化
- ✅ CRUD 操作（用户、空间、文档）
- ✅ 关系查询
- ✅ 复杂查询和连接

### 2. 认证流程测试 (test_auth_flow.py)

- ✅ 用户注册
- ✅ 用户登录（用户名和邮箱）
- ✅ 令牌刷新
- ✅ 受保护端点访问
- ✅ 登出功能
- ✅ 修改密码
- ✅ 高级用户权限

### 3. 用户工作流测试 (test_user_workflow.py)

- ✅ 知识管理工作流（空间、文档、笔记）
- ✅ AI 聊天工作流
- ✅ 协作工作流
- ✅ AI 代理工作流

### 4. API 端到端测试 (test_api_e2e.py)

- ✅ API 健康检查
- ✅ 速率限制
- ✅ 并发操作
- ✅ 错误处理
- ✅ 数据一致性
- ✅ 搜索集成
- ✅ 流式响应
- ✅ 文件处理

## 环境变量

测试使用以下环境变量：

```bash
# 测试数据库 URL
TEST_DATABASE_URL=postgresql+asyncpg://secondbrain:secondbrain123@localhost:5432/secondbrain_test

# 标记为测试环境
TESTING=1
```

## 故障排除

### 1. 数据库连接失败

确保 PostgreSQL 正在运行：

```bash
docker-compose ps postgres
```

确保测试数据库存在：

```bash
docker-compose exec postgres psql -U secondbrain -l | grep secondbrain_test
```

### 2. 服务不可用

检查所有服务状态：

```bash
docker-compose ps
```

重启服务：

```bash
docker-compose restart
```

### 3. 权限问题

确保用户有正确的数据库权限：

```bash
docker-compose exec postgres psql -U secondbrain -d secondbrain_test -c "SELECT current_user;"
```

### 4. 测试数据污染

清理测试数据库：

```bash
docker-compose exec postgres psql -U secondbrain -c "DROP DATABASE IF EXISTS secondbrain_test;"
docker-compose exec postgres psql -U secondbrain -c "CREATE DATABASE secondbrain_test;"
```

## 最佳实践

1. **隔离性**：每个测试应该是独立的，不依赖其他测试的状态
2. **清理**：测试结束后清理创建的数据
3. **Mock 外部服务**：使用 `mock_ai_service` fixture 避免调用真实的 AI API
4. **使用 fixtures**：利用 conftest.py 中的 fixtures 避免重复代码
5. **异步测试**：使用 `@pytest.mark.asyncio` 标记异步测试

## 添加新测试

1. 在适当的测试文件中添加测试方法
2. 使用描述性的测试名称
3. 添加文档字符串说明测试目的
4. 确保测试独立且可重复运行
5. 在测试后清理数据

示例：

```python
@pytest.mark.asyncio
async def test_new_feature(client: AsyncClient, auth_headers: dict):
    """测试新功能的描述。"""
    # 准备测试数据
    test_data = {"key": "value"}

    # 执行测试
    response = await client.post(
        "/api/v1/new-endpoint",
        json=test_data,
        headers=auth_headers
    )

    # 验证结果
    assert response.status_code == 200
    assert response.json()["success"] is True

    # 清理数据
    # ...
```
