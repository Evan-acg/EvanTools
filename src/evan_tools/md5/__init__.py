"""MD5 模块

提供文件哈希计算功能。
"""

# 导出主要 API
# 导出旧 API 用于向后兼容
from .api import calculate_hash
from .config import HashConfig
from .exceptions import (
    FileAccessError,
    FileReadError,
    HashCalculationError,
    InvalidConfigError,
)
from .main import MD5Result, calc_full_md5, calc_sparse_md5
from .result import HashResult

__all__ = [
    # 新 API
    "calculate_hash",
    "HashConfig",
    "HashResult",
    # 异常类
    "HashCalculationError",
    "FileAccessError",
    "FileReadError",
    "InvalidConfigError",
    # 旧 API（向后兼容）
    "calc_full_md5",
    "calc_sparse_md5",
    "MD5Result",
]
