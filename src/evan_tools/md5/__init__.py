"""MD5 模块

提供文件哈希计算功能。
"""

# 导出主要 API
from evan_tools.md5.api import calculate_hash
from evan_tools.md5.config import HashConfig
from evan_tools.md5.result import HashResult
from evan_tools.md5.exceptions import (
    HashCalculationError,
    FileAccessError,
    FileReadError,
    InvalidConfigError,
)

# 导出旧 API 用于向后兼容
from evan_tools.md5.main import calc_full_md5, calc_sparse_md5, MD5Result

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
