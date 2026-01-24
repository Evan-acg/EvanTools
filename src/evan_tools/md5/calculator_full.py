"""
完整 MD5 哈希计算器

提供完整计算文件 MD5 哈希值的实现。此计算器读取整个文件
并计算其完整的 MD5 哈希值，返回 is_sparse=False 的结果。
"""

import hashlib
from pathlib import Path
from typing import BinaryIO

from evan_tools.md5.calculator_base import HashCalculator
from evan_tools.md5.config import HashConfig
from evan_tools.md5.result import HashResult
from evan_tools.md5.exceptions import FileAccessError, FileReadError


class FullHashCalculator(HashCalculator):
    """完整哈希计算器
    
    读取整个文件并计算完整的 MD5 哈希值。这是最准确的哈希计算方法，
    适合于所有文件大小，但可能较慢的超大文件。
    
    Attributes:
        config: 哈希计算配置对象
    """
    
    def calculate(self, path: Path) -> HashResult:
        """计算文件的完整 MD5 哈希值
        
        读取整个文件并计算其完整的 MD5 哈希值。过程中会进行文件验证，
        并将所有异常转换为失败的 HashResult 对象。
        
        Args:
            path: 要计算哈希值的文件路径
            
        Returns:
            包含计算结果的 HashResult 对象，status 为 True 表示成功，
            为 False 表示失败。is_sparse 总是 False，表示这是完整计算。
        """
        try:
            # 验证文件存在性和可读性
            self._validate_file(path)
            
            # 打开文件并计算哈希
            with open(path, "rb") as f:
                hash_value = self._calculate_hash(f)
            
            # 获取文件大小
            file_size = self._get_file_size_humanized(path)
            
            # 返回成功的结果
            return HashResult(
                path=path,
                hash_value=hash_value,
                status=True,
                message="Success",
                file_size=file_size,
                algorithm=self.config.algorithm,
                is_sparse=False,
            )
        
        except (FileAccessError, FileReadError) as e:
            # 处理文件访问和读取错误
            return HashResult(
                path=path,
                hash_value="",
                status=False,
                message=str(e),
                file_size="",
                algorithm=self.config.algorithm,
                is_sparse=False,
            )
        
        except Exception as e:
            # 捕获其他所有异常
            error_msg = f"计算哈希值时出错: {str(e)}"
            return HashResult(
                path=path,
                hash_value="",
                status=False,
                message=error_msg,
                file_size="",
                algorithm=self.config.algorithm,
                is_sparse=False,
            )
    
    def _calculate_hash(self, f: BinaryIO) -> str:
        """计算文件的 MD5 哈希值
        
        从文件对象逐块读取文件内容，并使用 MD5 算法计算哈希值。
        
        Args:
            f: 已打开的二进制文件对象
            
        Returns:
            十六进制格式的 MD5 哈希值字符串（32 个字符）
        """
        # 创建 MD5 哈希对象
        md5_hash = hashlib.md5()
        
        # 逐块读取文件并更新哈希
        while True:
            chunk = self._read_file_chunk(f, self.config.buffer_size)
            if not chunk:
                break
            md5_hash.update(chunk)
        
        # 返回十六进制哈希值
        return md5_hash.hexdigest()
