#!/usr/bin/env python3
"""
测试模型字段
用法: uv run python tools/test_models.py
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.models.models import Space, Note, Conversation, User

print("检查模型字段...")
print("\nSpace 模型字段:")
for field in Space.__table__.columns:
    print(f"  - {field.name}: {field.type}")

print("\nNote 模型字段:")
for field in Note.__table__.columns:
    print(f"  - {field.name}: {field.type}")

print("\nConversation 模型字段:")
for field in Conversation.__table__.columns:
    print(f"  - {field.name}: {field.type}")

print("\nUser 模型字段:")
for field in User.__table__.columns:
    print(f"  - {field.name}: {field.type}")