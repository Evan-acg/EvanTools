"""
稀疏 MD5 哈希计算器

提供快速的文件哈希计算实现。通过采样文件的头部、中间和尾部
来快速生成文件的哈希值，适合大文件的快速去重检测。
"""

import hashlib
from pathlib import Path
from typing import BinaryIO

from .calculator_base import HashCalculator
from .exceptions import FileAccessError, FileReadError
from .result import HashResult


class SparseHashCalculator(HashCalculator):
    """稀疏哈希计算器

    通过采样文件的特定部分（头部、中间采样点、尾部）来快速计算
    文件哈希值，而不是读取整个文件。适合大文件的快速去重检测。

    Attributes:
        config: 哈希计算配置对象
    """

    def calculate(self, path: Path) -> HashResult:
        """计算文件的稀疏 MD5 哈希值

        对于较小文件（≤ buffer_size * sparse_segments），使用完整计算。
        对于较大文件，采样头部、中间和尾部来快速计算哈希值。

        Args:
            path: 要计算哈希值的文件路径

        Returns:
            包含计算结果的 HashResult 对象，status 为 True 表示成功，
            为 False 表示失败。is_sparse 表示是否使用了稀疏采样。
        """
        try:
            # 验证文件存在性和可读性
            self._validate_file(path)

            # 打开文件并计算哈希
            with open(path, "rb") as f:
                hash_value = self._calculate_hash(f)

            # 获取文件大小
            file_size = self._get_file_size_humanized(path)

            # 获取文件实际大小（字节）
            actual_size = path.stat().st_size
            threshold = self.config.buffer_size * self.config.sparse_segments
            is_sparse = actual_size > threshold

            # 返回成功的结果
            return HashResult(
                path=path,
                hash_value=hash_value,
                status=True,
                message="Success",
                file_size=file_size,
                algorithm=self.config.algorithm,
                is_sparse=is_sparse,
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
        """计算文件的稀疏 MD5 哈希值

        算法步骤：
        1. 获取文件大小
        2. 计算阈值：buffer_size * sparse_segments
        3. 如果文件大小 ≤ 阈值，执行完整计算
        4. 否则，采样：
           - 读取头部 buffer_size 字节
           - 计算中间采样点，均匀分布在中间部分
           - 读取尾部 buffer_size 字节
        5. 返回十六进制哈希值

        Args:
            f: 已打开的二进制文件对象

        Returns:
            十六进制格式的 MD5 哈希值字符串（32 个字符）
        """
        md5_hash = hashlib.md5()

        # 获取文件大小
        f.seek(0, 2)  # 移动到文件末尾
        file_size = f.tell()
        f.seek(0)  # 移动回文件开头

        # 计算阈值
        threshold = self.config.buffer_size * self.config.sparse_segments

        # 如果文件较小，执行完整计算
        if file_size <= threshold:
            while True:
                chunk = self._read_file_chunk(f, self.config.buffer_size)
                if not chunk:
                    break
                md5_hash.update(chunk)
            return md5_hash.hexdigest()

        # 稀疏采样模式
        segments = self.config.sparse_segments
        buffer_size = self.config.buffer_size

        # 1. 读取头部
        head_data = self._read_file_chunk(f, buffer_size)
        md5_hash.update(head_data)

        # 2. 计算中间采样点
        # effective_size = 除了头尾的中间部分大小
        effective_size = file_size - buffer_size * 2

        # 在中间部分均匀采样 (segments - 2) 个点
        # 第一个采样点在 buffer_size 之后，最后一个采样点在距离尾部 buffer_size 之前
        if segments > 2 and effective_size > 0:
            # 计算采样步长
            step = effective_size // (segments - 2)

            # 采样 (segments - 2) 个中间点
            for i in range(segments - 2):
                # 计算采样点位置
                position = buffer_size + step * i
                f.seek(position)
                sample_data = self._read_file_chunk(f, buffer_size)
                md5_hash.update(sample_data)

        # 3. 读取尾部
        f.seek(file_size - buffer_size)
        tail_data = self._read_file_chunk(f, buffer_size)
        md5_hash.update(tail_data)

        # 返回十六进制哈希值
        return md5_hash.hexdigest()
