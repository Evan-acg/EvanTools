"""MD5 哈希计算结果类。

该模块提供 HashResult 数据类，用于表示 MD5 哈希计算的结果。
"""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class HashResult:
    """MD5 哈希计算结果。
    
    表示一个文件的 MD5 哈希计算结果，包含文件路径、哈希值、计算状态
    和相关元数据。
    
    Attributes:
        path: 文件路径
        hash_value: 哈希值（十六进制字符串）
        status: 计算是否成功
        message: 状态或错误消息
        file_size: 文件大小（人类可读格式）
        algorithm: 算法名称
        is_sparse: 是否为稀疏计算
        computed_at: 计算完成时间（默认为当前时间）
    """
    
    path: Path
    hash_value: str
    status: bool
    message: str
    file_size: str
    algorithm: str
    is_sparse: bool
    computed_at: datetime = field(default_factory=datetime.now)
    
    def __repr__(self) -> str:
        """返回友好的字符串表示。
        
        根据计算状态返回不同的格式：
        - 成功：显示文件路径、哈希值前缀、文件大小、计算模式和成功状态
        - 失败：显示文件路径、失败状态和错误消息
        
        Returns:
            格式化的字符串表示
        """
        filename = self.path.name
        status_icon = "✓" if self.status else "✗"
        status_text = "成功" if self.status else "失败"
        
        if self.status:
            # 成功的情况：显示完整信息
            hash_preview = (
                f"{self.hash_value[:8]}..." 
                if len(self.hash_value) > 8 
                else self.hash_value
            )
            mode = "稀疏" if self.is_sparse else "完整"
            return (
                f"HashResult(path={filename}, hash={hash_preview}, "
                f"size={self.file_size}, mode={mode}, status={status_icon} {status_text})"
            )
        else:
            # 失败的情况：显示错误信息
            return (
                f"HashResult(path={filename}, status={status_icon} {status_text}, "
                f"error={self.message})"
            )
