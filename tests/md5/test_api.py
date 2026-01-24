"""MD5 模块 API 测试

测试主入口函数 calculate_hash() 的各种使用场景。
"""

from pathlib import Path
import pytest
from evan_tools.md5.api import calculate_hash
from evan_tools.md5.config import HashConfig


@pytest.fixture
def test_file(tmp_path):
    """创建测试文件（小文件）"""
    path = tmp_path / "test.bin"
    path.write_bytes(b"test content")
    return path


@pytest.fixture
def large_test_file(tmp_path):
    """创建大测试文件以触发稀疏计算
    
    文件大小需要大于 buffer_size * sparse_segments (default: 8MB * 10 = 80MB)
    这里创建 100MB 的文件来确保使用稀疏计算
    """
    path = tmp_path / "large_test.bin"
    # 创建 100MB 的文件
    chunk_size = 1024 * 1024  # 1MB
    num_chunks = 100
    with open(path, "wb") as f:
        for i in range(num_chunks):
            f.write(b"x" * chunk_size)
    return path


class TestCalculateHashBasic:
    """基础功能测试"""

    def test_calculate_hash_default_sparse_mode(self, large_test_file):
        """默认应使用稀疏模式"""
        result = calculate_hash(large_test_file)
        
        assert result.status is True
        assert result.is_sparse is True

    def test_calculate_hash_full_mode(self, test_file):
        """指定 full 模式应使用完整计算"""
        result = calculate_hash(test_file, mode="full")
        
        assert result.status is True
        assert result.is_sparse is False

    def test_calculate_hash_sparse_mode(self, large_test_file):
        """指定 sparse 模式应使用稀疏计算"""
        result = calculate_hash(large_test_file, mode="sparse")
        
        assert result.status is True
        assert result.is_sparse is True


class TestCalculateHashCustomConfig:
    """自定义配置测试"""

    def test_calculate_hash_custom_config(self, test_file):
        """应支持自定义配置"""
        config = HashConfig(buffer_size=16 * 1024 * 1024)
        result = calculate_hash(test_file, config=config)
        
        assert result.status is True


class TestCalculateHashErrorHandling:
    """错误处理测试"""

    def test_calculate_hash_invalid_mode(self, test_file):
        """无效的模式应返回失败"""
        result = calculate_hash(test_file, mode="invalid")
        
        assert result.status is False
        assert "invalid" in result.message.lower()

    def test_calculate_hash_nonexistent_file(self, tmp_path):
        """不存在的文件应返回失败结果"""
        nonexistent = tmp_path / "nonexistent.bin"
        result = calculate_hash(nonexistent)
        
        assert result.status is False
        assert "not found" in result.message.lower() or "不存在" in result.message
