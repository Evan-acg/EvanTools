from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class ConfigSource(ABC):
    """配置源抽象接口"""
    
    @abstractmethod
    def read(self, path: Path) -> dict[str, Any]:
        """
        读取配置文件
        
        Args:
            path: 配置文件路径
            
        Returns:
            配置字典
            
        Raises:
            OSError: 文件访问失败
            ValueError: 格式解析失败
        """
        pass
    
    @abstractmethod
    def write(self, path: Path, content: dict[str, Any]) -> None:
        """
        写入配置文件
        
        Args:
            path: 配置文件路径
            content: 配置字典
            
        Raises:
            OSError: 文件写入失败
            ValueError: 格式序列化失败
        """
        pass
    
    @abstractmethod
    def supports(self, path: Path) -> bool:
        """
        检查是否支持该文件格式
        
        Args:
            path: 配置文件路径
            
        Returns:
            是否支持
        """
        pass
