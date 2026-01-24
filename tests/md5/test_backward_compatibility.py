"""
向后兼容性测试

验证旧的 API (calc_full_md5, calc_sparse_md5) 继续工作，
尽管它们现已基于新的计算器 API 实现。
"""

from pathlib import Path

import pytest

from evan_tools.md5.main import MD5Result, calc_full_md5, calc_sparse_md5


@pytest.fixture
def test_file(tmp_path):
    """创建测试文件"""
    path = tmp_path / "test.bin"
    path.write_bytes(b"test content for compatibility")
    return path


def test_calc_full_md5_still_works(test_file):
    """原有的 calc_full_md5 函数应继续工作"""
    result = calc_full_md5(test_file)

    # 应返回 MD5Result 对象
    assert isinstance(result, MD5Result)
    assert hasattr(result, "path")
    assert hasattr(result, "md5")
    assert hasattr(result, "status")
    assert hasattr(result, "message")
    assert hasattr(result, "file_size")

    assert result.status is True
    assert result.path == test_file
    assert len(result.md5) == 32  # MD5 哈希值长度


def test_calc_sparse_md5_still_works(test_file):
    """原有的 calc_sparse_md5 函数应继续工作"""
    result = calc_sparse_md5(test_file)

    # 应返回 MD5Result 对象
    assert isinstance(result, MD5Result)
    assert hasattr(result, "path")
    assert hasattr(result, "md5")
    assert hasattr(result, "status")
    assert hasattr(result, "message")
    assert hasattr(result, "file_size")

    assert result.status is True
    assert result.path == test_file


def test_full_md5_with_custom_parameters(test_file):
    """calc_full_md5 应支持原有的参数"""
    # 原有 API 支持 buffer_size 参数
    result = calc_full_md5(test_file, buffer_size=16 * 1024 * 1024)
    assert result.status is True


def test_sparse_md5_with_custom_parameters(test_file):
    """calc_sparse_md5 应支持原有的参数"""
    # 原有 API 支持 buffer_size 和 segments 参数
    result = calc_sparse_md5(
        test_file, buffer_size=16 * 1024 * 1024, segments=8
    )
    assert result.status is True


def test_calc_full_md5_nonexistent_file(tmp_path):
    """不存在的文件应返回失败状态"""
    nonexistent = tmp_path / "nonexistent.bin"
    result = calc_full_md5(nonexistent)

    assert result.status is False


def test_calc_sparse_md5_nonexistent_file(tmp_path):
    """不存在的文件应返回失败状态"""
    nonexistent = tmp_path / "nonexistent.bin"
    result = calc_sparse_md5(nonexistent)

    assert result.status is False
