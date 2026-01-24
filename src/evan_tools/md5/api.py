"""MD5 模块主入口 API

提供用户友好的主入口函数 calculate_hash()，隐藏计算器选择的复杂性。
用户只需指定计算模式（full 或 sparse）就能快速计算文件哈希值。

示例:
    使用默认配置计算哈希值（稀疏模式）:
    
    >>> from pathlib import Path
    >>> from evan_tools.md5.api import calculate_hash
    >>> result = calculate_hash(Path("file.txt"))
    >>> print(f"Hash: {result.hash_value}")
    Hash: a1b2c3d4e5f6...
    
    使用完整计算模式:
    
    >>> result = calculate_hash(Path("file.txt"), mode="full")
    >>> print(f"Is sparse: {result.is_sparse}")
    Is sparse: False
    
    使用自定义配置:
    
    >>> from evan_tools.md5.config import HashConfig
    >>> config = HashConfig(buffer_size=16 * 1024 * 1024)
    >>> result = calculate_hash(Path("file.txt"), config=config)
"""

from pathlib import Path
from typing import Literal, Optional

from evan_tools.md5.config import HashConfig
from evan_tools.md5.result import HashResult
from evan_tools.md5.calculator_full import FullHashCalculator
from evan_tools.md5.calculator_sparse import SparseHashCalculator


def calculate_hash(
    path: Path,
    mode: Literal["full", "sparse"] = "sparse",
    config: Optional[HashConfig] = None,
) -> HashResult:
    """计算文件的哈希值
    
    这是 MD5 模块的主入口函数，提供简洁的 API 接口。
    根据指定的模式选择合适的计算器，并返回计算结果。
    
    Args:
        path: 要计算哈希值的文件路径
        mode: 计算模式，支持 "full" (完整计算) 或 "sparse" (稀疏计算)，
              默认为 "sparse" 以获得更快的速度
        config: 可选的哈希配置对象。如果不提供，使用默认配置
                (buffer_size=8MB, sparse_segments=10)
    
    Returns:
        HashResult 对象，包含：
        - status: True 表示计算成功，False 表示失败
        - hash_value: 计算成功时的十六进制哈希值
        - message: 计算失败时的错误消息
        - is_sparse: 是否使用了稀疏计算模式
        - 其他元数据（文件大小、算法名称等）
    
    Raises:
        无直接异常。所有错误都被捕获并返回为失败的 HashResult。
    
    示例:
        >>> from pathlib import Path
        >>> result = calculate_hash(Path("myfile.txt"))
        >>> if result.status:
        ...     print(f"MD5: {result.hash_value}")
        ... else:
        ...     print(f"错误: {result.message}")
    """
    # 如果没有提供配置，使用默认配置
    if config is None:
        config = HashConfig()
    
    # 验证 mode 参数
    if mode not in ("full", "sparse"):
        return HashResult(
            path=path,
            hash_value="",
            status=False,
            message=f"无效的计算模式: {mode}。支持的模式: 'full', 'sparse'",
            file_size="",
            algorithm=config.algorithm,
            is_sparse=False,
        )
    
    # 根据 mode 选择合适的计算器
    if mode == "full":
        calculator = FullHashCalculator(config)
    else:  # mode == "sparse"
        calculator = SparseHashCalculator(config)
    
    # 调用计算器计算哈希值
    result = calculator.calculate(path)
    
    return result
