"""
MD5 哈希计算模块

这个模块提供文件 MD5 计算功能，支持完整计算和稀疏计算两种模式。

Note: 这个模块已经过重构，现在基于新的 API 实现。
旧的函数 (calc_full_md5, calc_sparse_md5) 被保留以保持向后兼容性。
"""

import typing as t
from pathlib import Path

from evan_tools.md5.api import calculate_hash
from evan_tools.md5.config import HashConfig


class MD5Result(t.NamedTuple):
    """MD5 计算结果（为了向后兼容性保留）"""

    path: Path
    md5: str
    status: bool
    message: str
    file_size: str


def calc_sparse_md5(
    item: Path, buffer_size: int = 8 * 1024 * 1024, segments: int = 10
) -> MD5Result:
    """计算文件的稀疏 MD5 值（快速模式）
    
    这个函数现已基于新的计算器 API 实现，但保留原有签名以保持兼容性。
    
    Args:
        item: 文件路径
        buffer_size: 缓冲区大小，默认 8MB
        segments: 稀疏采样段数，默认 10
    
    Returns:
        MD5Result: 包含计算结果的 NamedTuple
    """
    config = HashConfig(buffer_size=buffer_size, sparse_segments=segments)
    result = calculate_hash(item, mode="sparse", config=config)

    return MD5Result(
        path=result.path,
        md5=result.hash_value,
        status=result.status,
        message=result.message,
        file_size=result.file_size,
    )


def calc_full_md5(
    item: Path, buffer_size: int = 8 * 1024 * 1024
) -> MD5Result:
    """计算文件的完整 MD5 值
    
    这个函数现已基于新的计算器 API 实现，但保留原有签名以保持兼容性。
    
    Args:
        item: 文件路径
        buffer_size: 缓冲区大小，默认 8MB
    
    Returns:
        MD5Result: 包含计算结果的 NamedTuple
    """
    config = HashConfig(buffer_size=buffer_size)
    result = calculate_hash(item, mode="full", config=config)

    return MD5Result(
        path=result.path,
        md5=result.hash_value,
        status=result.status,
        message=result.message,
        file_size=result.file_size,
    )
