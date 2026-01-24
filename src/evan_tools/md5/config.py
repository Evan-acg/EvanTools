"""
MD5 模块配置管理

这个模块定义了 MD5 计算的配置类，用于管理和验证配置参数。
"""

from dataclasses import dataclass

from .exceptions import InvalidConfigError

# 支持的哈希算法集合
SUPPORTED_ALGORITHMS = {"md5"}


@dataclass
class HashConfig:
    """哈希计算配置类
    
    管理 MD5 计算过程中的各种配置参数，包括算法选择、缓冲区大小、
    稀疏采样段数和缓存配置。
    
    Attributes:
        algorithm: 哈希算法名称，目前只支持 "md5"
        buffer_size: 文件读取缓冲区大小（字节），默认 8MB
        sparse_segments: 稀疏采样段数，用于快速计算，默认 10
        enable_cache: 是否启用缓存功能，默认禁用
    """
    
    algorithm: str = "md5"
    buffer_size: int = 8 * 1024 * 1024  # 8MB
    sparse_segments: int = 10
    enable_cache: bool = False
    
    def __post_init__(self) -> None:
        """初始化后验证所有配置参数"""
        self._validate()
    
    def _validate(self) -> None:
        """验证配置参数的有效性
        
        Raises:
            InvalidConfigError: 当任何参数无效时抛出
        """
        # 验证 algorithm
        if self.algorithm not in SUPPORTED_ALGORITHMS:
            raise InvalidConfigError(
                f"不支持的算法: {self.algorithm}。支持的算法: {SUPPORTED_ALGORITHMS}"
            )
        
        # 验证 buffer_size
        if self.buffer_size <= 0:
            raise InvalidConfigError(
                f"buffer_size 必须为正数，得到: {self.buffer_size}"
            )
        
        # 验证 sparse_segments
        if self.sparse_segments < 2:
            raise InvalidConfigError(
                f"sparse_segments 必须至少为 2，得到: {self.sparse_segments}"
            )
