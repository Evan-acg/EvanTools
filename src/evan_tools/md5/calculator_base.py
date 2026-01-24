"""
MD5 哈希计算器基类

提供用于计算文件哈希值的抽象基类，定义了计算器的接口和通用功能，
例如文件验证、文件读取和文件大小格式化。
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO
import os

from evan_tools.md5.config import HashConfig
from evan_tools.md5.exceptions import FileAccessError, FileReadError


class HashCalculator(ABC):
    """哈希计算器抽象基类
    
    为具体的哈希计算器提供共享的接口和通用逻辑。子类必须实现 _calculate_hash 方法。
    
    Attributes:
        config: 哈希计算配置对象
    """
    
    def __init__(self, config: HashConfig) -> None:
        """初始化哈希计算器
        
        Args:
            config: HashConfig 实例，包含算法选择、缓冲区大小等配置
        """
        self.config = config
    
    @abstractmethod
    def _calculate_hash(self, f: BinaryIO) -> str:
        """计算文件的哈希值（抽象方法）
        
        子类必须实现此方法来执行具体的哈希计算。
        
        Args:
            f: 已打开的二进制文件对象
            
        Returns:
            十六进制格式的哈希值字符串
        """
        pass
    
    def _validate_file(self, path: Path) -> None:
        """验证文件存在性和可读性
        
        检查文件是否存在、是否为常规文件以及是否可读。
        
        Args:
            path: 文件路径
            
        Raises:
            FileAccessError: 当文件不存在、不是常规文件或不可读时
        """
        # 检查文件是否存在
        if not path.exists():
            raise FileAccessError(f"文件不存在: {path}")
        
        # 检查是否为常规文件（不是目录等）
        if not path.is_file():
            raise FileAccessError(f"路径不是常规文件: {path}")
        
        # 检查文件是否可读
        if not os.access(path, os.R_OK):
            raise FileAccessError(f"文件无可读权限: {path}")
    
    def _read_file_chunk(self, f: BinaryIO, size: int) -> bytes:
        """读取文件块
        
        从已打开的文件对象读取指定大小的数据块。
        
        Args:
            f: 已打开的二进制文件对象
            size: 要读取的字节数
            
        Returns:
            读取的字节数据
            
        Raises:
            FileReadError: 当读取文件时发生 I/O 错误
        """
        try:
            return f.read(size)
        except IOError as e:
            raise FileReadError(f"读取文件时出错: {e}")
    
    def _get_file_size_humanized(self, path: Path) -> str:
        """获取人类可读的文件大小
        
        尝试使用 humanize 库格式化文件大小，如果不可用则使用简单实现。
        
        Args:
            path: 文件路径
            
        Returns:
            格式化的文件大小字符串（如 "1.5 MB"）
        """
        file_size = path.stat().st_size
        
        # 尝试使用 humanize 库
        try:
            import humanize
            return humanize.naturalsize(file_size)
        except ImportError:
            # 回退到简单实现
            return self._format_file_size_simple(file_size)
    
    @staticmethod
    def _format_file_size_simple(size_bytes: int) -> str:
        """简单的文件大小格式化实现
        
        将字节大小转换为更可读的格式。
        
        Args:
            size_bytes: 文件大小（字节）
            
        Returns:
            格式化的文件大小字符串
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                if unit == 'B':
                    return f"{size_bytes:.0f} {unit}"
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        
        return f"{size_bytes:.2f} PB"
