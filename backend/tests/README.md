# Tests Structure

测试文件结构应该镜像app目录的结构，使测试文件易于查找和管理。

```
tests/
├── conftest.py                    # 共享的测试fixtures
├── README.md                      # 测试文档
│
├── unit/                          # 单元测试
│   ├── crud/                      # CRUD层测试
│   │   ├── test_base.py          # 基础CRUD测试
│   │   ├── test_user.py          # 用户CRUD测试
│   │   ├── test_space.py         # Space CRUD测试
│   │   ├── test_document.py      # 文档CRUD测试
│   │   ├── test_conversation.py  # 对话CRUD测试
│   │   ├── test_message.py       # 消息CRUD测试
│   │   ├── test_note.py          # 笔记CRUD测试
│   │   ├── test_annotation.py    # 标注CRUD测试
│   │   └── test_citation.py      # 引用CRUD测试
│   │
│   ├── schemas/                   # Schema验证测试
│   │   ├── test_user_schemas.py
│   │   ├── test_space_schemas.py
│   │   ├── test_document_schemas.py
│   │   └── ...
│   │
│   ├── services/                  # 服务层测试
│   │   ├── test_ai_service.py
│   │   ├── test_document_service.py
│   │   ├── test_note_service.py
│   │   └── ...
│   │
│   └── core/                      # 核心功能测试
│       ├── test_config.py
│       ├── test_database.py
│       └── test_security.py
│
├── integration/                   # 集成测试
│   ├── test_auth_flow.py         # 认证流程测试
│   ├── test_document_upload.py   # 文档上传流程测试
│   ├── test_ai_chat.py          # AI对话流程测试
│   └── test_note_management.py   # 笔记管理流程测试
│
├── api/                          # API端点测试
│   ├── v1/
│   │   ├── test_auth_endpoints.py
│   │   ├── test_user_endpoints.py
│   │   ├── test_space_endpoints.py
│   │   ├── test_document_endpoints.py
│   │   └── ...
│   │
│   └── test_api_integration.py  # API集成测试
│
└── e2e/                          # 端到端测试（可选）
    ├── test_user_journey.py
    └── test_scenarios.py
```

## 测试命名约定

1. 测试文件名：`test_<module_name>.py`
2. 测试类名：`Test<ClassName>`
3. 测试方法名：`test_<method_name>_<scenario>`

## 测试运行命令

```bash
# 运行所有测试
uv run pytest

# 运行特定目录的测试
uv run pytest tests/unit/crud/

# 运行特定文件的测试
uv run pytest tests/unit/crud/test_base.py

# 运行带覆盖率的测试
uv run pytest --cov=app --cov-report=html

# 运行特定标记的测试
uv run pytest -m "not slow"
```