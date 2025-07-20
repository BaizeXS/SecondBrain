"""密码处理模块，解决 bcrypt 版本兼容性问题."""

import sys
import warnings
from io import StringIO

from passlib.context import CryptContext

# 临时捕获并忽略 bcrypt 警告
_original_stderr = sys.stderr
sys.stderr = StringIO()

try:
    # 忽略所有警告
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
finally:
    # 恢复 stderr
    sys.stderr = _original_stderr


def get_password_hash(password: str) -> str:
    """生成密码哈希."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码."""
    return pwd_context.verify(plain_password, hashed_password)
