"""
SparseHashCalculator 的单元测试

测试稀疏哈希计算器的核心功能，包括大文件计算、
性能对比、segments 参数影响以及一致性验证。
"""

from pathlib import Path
import pytest
import time
from evan_tools.md5.config import HashConfig
from evan_tools.md5.calculator_sparse import SparseHashCalculator


@pytest.fixture
def large_test_file(tmp_path):
    """创建 100MB 测试文件
    
    创建一个 100MB 的测试文件，填充有规律的数据
    以便验证稀疏计算的正确性。
    
    Args:
        tmp_path: pytest 提供的临时目录
        
    Returns:
        测试文件的路径
    """
    test_file = tmp_path / "large.bin"
    size = 100 * 1024 * 1024  # 100MB
    with open(test_file, "wb") as f:
        # 写入有规律的数据以便验证
        chunk = b"A" * 1024
        for _ in range(size // 1024):
            f.write(chunk)
    return test_file


def test_sparse_calculator_calculate_large_file(large_test_file):
    """SparseHashCalculator 应能计算大文件
    
    验证：
    - 计算状态为成功
    - 是否为稀疏计算标志为 True
    - 哈希值为 32 位十六进制（MD5 格式）
    """
    config = HashConfig(sparse_segments=5)
    calc = SparseHashCalculator(config)
    result = calc.calculate(large_test_file)
    
    assert result.status is True
    assert result.is_sparse is True
    assert len(result.hash_value) == 32  # MD5 是 32 位十六进制


def test_sparse_calculator_faster_than_full(large_test_file):
    """稀疏计算应比完整计算快
    
    对比稀疏计算和完整计算的耗时，验证稀疏计算
    至少快 50% 以上。
    """
    from evan_tools.md5.calculator_full import FullHashCalculator
    
    config = HashConfig(sparse_segments=5)
    sparse_calc = SparseHashCalculator(config)
    full_calc = FullHashCalculator(config)
    
    # 测试稀疏计算速度
    start = time.time()
    sparse_result = sparse_calc.calculate(large_test_file)
    sparse_time = time.time() - start
    
    # 测试完整计算速度
    start = time.time()
    full_result = full_calc.calculate(large_test_file)
    full_time = time.time() - start
    
    # 稀疏计算应明显更快（至少快 50%）
    assert sparse_time < full_time * 0.5
    # 确保两个计算都成功
    assert sparse_result.status is True
    assert full_result.status is True


def test_sparse_calculator_segments_parameter(large_test_file):
    """不同的 segment 数量应产生不同结果
    
    验证：
    - 不同的 segments 参数产生不同的哈希值
    - 这是因为采样点位置不同
    """
    config1 = HashConfig(sparse_segments=5)
    config2 = HashConfig(sparse_segments=8)
    
    calc1 = SparseHashCalculator(config1)
    calc2 = SparseHashCalculator(config2)
    
    result1 = calc1.calculate(large_test_file)
    result2 = calc2.calculate(large_test_file)
    
    # 两个计算都应成功
    assert result1.status is True
    assert result2.status is True
    
    # 由于段数不同，哈希值应不同
    assert result1.hash_value != result2.hash_value


def test_sparse_calculator_same_file_same_hash(large_test_file):
    """相同配置计算同一文件应得到相同哈希
    
    验证：
    - 多次计算相同文件和配置得到相同结果
    - 这证明算法的确定性
    """
    config = HashConfig(sparse_segments=5)
    calc = SparseHashCalculator(config)
    
    result1 = calc.calculate(large_test_file)
    result2 = calc.calculate(large_test_file)
    
    assert result1.hash_value == result2.hash_value
