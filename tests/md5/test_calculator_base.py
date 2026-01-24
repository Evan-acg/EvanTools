"""
MD5 计算器基类的单元测试

测试 HashCalculator 抽象基类的初始化、文件验证和文件读取功能。
"""

from pathlib import Path
import pytest
from unittest.mock import patch, mock_open
from evan_tools.md5.config import HashConfig
from evan_tools.md5.calculator_base import HashCalculator
from evan_tools.md5.exceptions import FileAccessError, FileReadError


class ConcreteCalculator(HashCalculator):
    """用于测试的具体实现"""
    
    def _calculate_hash(self, f) -> str:
        return "test_hash_value"


def test_hash_calculator_init():
    """HashCalculator 应接受配置"""
    config = HashConfig()
    calc = ConcreteCalculator(config)
    assert calc.config == config


def test_hash_calculator_validate_file_exists(tmp_path):
    """validate_file 应检查文件存在性"""
    config = HashConfig()
    calc = ConcreteCalculator(config)
    
    # 存在的文件应通过验证
    test_file = tmp_path / "test.bin"
    test_file.write_bytes(b"test")
    calc._validate_file(test_file)  # 不应抛出异常
    
    # 不存在的文件应抛出异常
    nonexistent = tmp_path / "nonexistent.bin"
    with pytest.raises(FileAccessError):
        calc._validate_file(nonexistent)


def test_hash_calculator_validate_file_readable(tmp_path):
    """validate_file 应检查目录时拒绝访问"""
    config = HashConfig()
    calc = ConcreteCalculator(config)
    
    # 使用目录而不是文件来测试无读权限的情况
    # （因为在 Windows 上 chmod 的行为与 Unix 不同）
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    
    # 目录应该被识别为非文件
    with pytest.raises(FileAccessError):
        calc._validate_file(test_dir)
