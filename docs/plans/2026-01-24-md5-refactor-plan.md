# MD5 模块重构 实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** 将 MD5 模块从过程式设计重构为基于策略模式和配置对象的架构，提高可维护性、可测试性和可扩展性。

**Architecture:** 采用策略模式分离计算算法（Full/Sparse），通过 HashConfig 对象管理参数，统一通过 calculate_hash() 入口函数暴露 API，保持向后兼容性。

**Tech Stack:** Python 3.9+，dataclass，typing，pytest，hashlib

---

## 任务总览

| 任务 | 说明 | 优先级 |
|------|------|--------|
| T1 | 创建异常类体系 | P1 |
| T2 | 创建 HashConfig 配置类 | P1 |
| T3 | 创建改进的 HashResult 类 | P1 |
| T4 | 创建 HashCalculator 基类 | P1 |
| T5 | 实现 FullHashCalculator | P1 |
| T6 | 实现 SparseHashCalculator | P1 |
| T7 | 创建 calculate_hash() 主入口 | P1 |
| T8 | 保持向后兼容性 | P1 |
| T9 | 编写完整单元测试 | P2 |
| T10 | 性能基准测试 | P3 |

---

## Task 1: 创建异常类体系

**Files:**
- Create: `src/evan_tools/md5/exceptions.py`
- Test: `tests/md5/test_exceptions.py`

### Step 1: 编写异常类测试

Create `tests/md5/test_exceptions.py`:

```python
import pytest
from evan_tools.md5.exceptions import (
    HashCalculationError,
    FileAccessError,
    FileReadError,
    InvalidConfigError,
)


def test_hash_calculation_error_is_exception():
    """异常基类应是 Exception 的子类"""
    error = HashCalculationError("test error")
    assert isinstance(error, Exception)
    assert str(error) == "test error"


def test_file_access_error_is_hash_calculation_error():
    """FileAccessError 应是 HashCalculationError 的子类"""
    error = FileAccessError("file not found")
    assert isinstance(error, HashCalculationError)
    assert isinstance(error, Exception)


def test_file_read_error_is_hash_calculation_error():
    """FileReadError 应是 HashCalculationError 的子类"""
    error = FileReadError("disk error")
    assert isinstance(error, HashCalculationError)
    assert isinstance(error, Exception)


def test_invalid_config_error_is_hash_calculation_error():
    """InvalidConfigError 应是 HashCalculationError 的子类"""
    error = InvalidConfigError("bad config")
    assert isinstance(error, HashCalculationError)
    assert isinstance(error, Exception)
```

### Step 2: 运行测试确认失败

```bash
cd d:\Work\Spaces\Common\CommonPython\EvanTools
python -m pytest tests/md5/test_exceptions.py -v
```

Expected: FAIL with "No module named 'evan_tools.md5.exceptions'"

### Step 3: 创建异常类模块

Create `src/evan_tools/md5/exceptions.py`:

```python
"""
MD5 模块异常定义

这个模块定义了 MD5 计算过程中可能发生的所有异常。
"""


class HashCalculationError(Exception):
    """哈希计算异常基类
    
    所有与哈希计算相关的异常都应继承此类。
    """
    pass


class FileAccessError(HashCalculationError):
    """文件访问异常
    
    当文件不存在、无读取权限或其他访问问题时抛出。
    """
    pass


class FileReadError(HashCalculationError):
    """文件读取异常
    
    当读取文件内容时发生磁盘错误、I/O 中断等问题时抛出。
    """
    pass


class InvalidConfigError(HashCalculationError):
    """无效配置异常
    
    当配置参数无效或不合理时抛出。
    """
    pass
```

### Step 4: 运行测试确认通过

```bash
python -m pytest tests/md5/test_exceptions.py -v
```

Expected: PASS (4 passed)

### Step 5: 提交

```bash
git add src/evan_tools/md5/exceptions.py tests/md5/test_exceptions.py
git commit -m "feat(md5): 添加异常类体系定义"
```

---

## Task 2: 创建 HashConfig 配置类

**Files:**
- Create: `src/evan_tools/md5/config.py`
- Test: `tests/md5/test_config.py`

### Step 1: 编写配置类测试

Create `tests/md5/test_config.py`:

```python
import pytest
from evan_tools.md5.config import HashConfig
from evan_tools.md5.exceptions import InvalidConfigError


def test_hash_config_default_values():
    """HashConfig 应有合理的默认值"""
    config = HashConfig()
    assert config.algorithm == "md5"
    assert config.buffer_size == 8 * 1024 * 1024  # 8MB
    assert config.sparse_segments == 10
    assert config.enable_cache is False


def test_hash_config_custom_values():
    """HashConfig 应支持自定义值"""
    config = HashConfig(
        algorithm="sha256",
        buffer_size=16 * 1024 * 1024,
        sparse_segments=5,
        enable_cache=True,
    )
    assert config.algorithm == "sha256"
    assert config.buffer_size == 16 * 1024 * 1024
    assert config.sparse_segments == 5
    assert config.enable_cache is True


def test_hash_config_validate_invalid_buffer_size():
    """buffer_size 必须为正数"""
    with pytest.raises(InvalidConfigError):
        HashConfig(buffer_size=0)
    
    with pytest.raises(InvalidConfigError):
        HashConfig(buffer_size=-1024)


def test_hash_config_validate_invalid_sparse_segments():
    """sparse_segments 必须至少为 2"""
    with pytest.raises(InvalidConfigError):
        HashConfig(sparse_segments=1)
    
    with pytest.raises(InvalidConfigError):
        HashConfig(sparse_segments=0)


def test_hash_config_validate_algorithm():
    """algorithm 必须是支持的类型"""
    # 目前只支持 md5
    config = HashConfig(algorithm="md5")
    assert config.algorithm == "md5"
    
    # 暂时不支持其他算法
    with pytest.raises(InvalidConfigError):
        HashConfig(algorithm="sha256")
```

### Step 2: 运行测试确认失败

```bash
python -m pytest tests/md5/test_config.py -v
```

Expected: FAIL

### Step 3: 创建配置类

Create `src/evan_tools/md5/config.py`:

```python
"""
MD5 模块配置

这个模块定义了哈希计算的配置对象。
"""

from dataclasses import dataclass
from evan_tools.md5.exceptions import InvalidConfigError


SUPPORTED_ALGORITHMS = {"md5"}  # 未来可扩展


@dataclass
class HashConfig:
    """哈希计算配置
    
    Attributes:
        algorithm: 哈希算法，目前支持 "md5"
        buffer_size: 文件读取缓冲区大小（字节），默认 8MB
        sparse_segments: 稀疏计算的段数，默认 10
        enable_cache: 是否启用缓存（未来功能），默认 False
    """
    
    algorithm: str = "md5"
    buffer_size: int = 8 * 1024 * 1024
    sparse_segments: int = 10
    enable_cache: bool = False
    
    def __post_init__(self):
        """验证配置参数"""
        self._validate()
    
    def _validate(self):
        """验证所有参数"""
        if self.algorithm not in SUPPORTED_ALGORITHMS:
            raise InvalidConfigError(
                f"不支持的算法: {self.algorithm}. "
                f"支持的算法: {SUPPORTED_ALGORITHMS}"
            )
        
        if self.buffer_size <= 0:
            raise InvalidConfigError(
                f"buffer_size 必须为正数，收到: {self.buffer_size}"
            )
        
        if self.sparse_segments < 2:
            raise InvalidConfigError(
                f"sparse_segments 必须至少为 2，收到: {self.sparse_segments}"
            )
```

### Step 4: 运行测试确认通过

```bash
python -m pytest tests/md5/test_config.py -v
```

Expected: PASS (6 passed)

### Step 5: 提交

```bash
git add src/evan_tools/md5/config.py tests/md5/test_config.py
git commit -m "feat(md5): 创建 HashConfig 配置类和验证"
```

---

## Task 3: 创建改进的 HashResult 类

**Files:**
- Create: `src/evan_tools/md5/result.py`
- Test: `tests/md5/test_result.py`

### Step 1: 编写 HashResult 测试

Create `tests/md5/test_result.py`:

```python
from datetime import datetime
from pathlib import Path
import pytest
from evan_tools.md5.result import HashResult


def test_hash_result_creation_success():
    """创建成功的 HashResult"""
    path = Path("/tmp/test.bin")
    result = HashResult(
        path=path,
        hash_value="abc123",
        status=True,
        message="Success",
        file_size="10 MB",
        algorithm="md5",
        is_sparse=False,
    )
    
    assert result.path == path
    assert result.hash_value == "abc123"
    assert result.status is True
    assert result.message == "Success"
    assert result.file_size == "10 MB"
    assert result.algorithm == "md5"
    assert result.is_sparse is False
    assert isinstance(result.computed_at, datetime)


def test_hash_result_creation_failure():
    """创建失败的 HashResult"""
    path = Path("/tmp/nonexistent.bin")
    result = HashResult(
        path=path,
        hash_value="",
        status=False,
        message="File not found",
        file_size="0 B",
        algorithm="md5",
        is_sparse=False,
    )
    
    assert result.status is False
    assert result.hash_value == ""
    assert "File not found" in result.message


def test_hash_result_sparse_flag():
    """HashResult 应正确标识是否为稀疏计算"""
    path = Path("/tmp/test.bin")
    
    sparse_result = HashResult(
        path=path,
        hash_value="abc123",
        status=True,
        message="Success",
        file_size="1 GB",
        algorithm="md5",
        is_sparse=True,
    )
    
    full_result = HashResult(
        path=path,
        hash_value="abc123",
        status=True,
        message="Success",
        file_size="1 GB",
        algorithm="md5",
        is_sparse=False,
    )
    
    assert sparse_result.is_sparse is True
    assert full_result.is_sparse is False
```

### Step 2: 运行测试确认失败

```bash
python -m pytest tests/md5/test_result.py -v
```

Expected: FAIL

### Step 3: 创建 HashResult 类

Create `src/evan_tools/md5/result.py`:

```python
"""
MD5 模块结果对象

这个模块定义了哈希计算的结果对象。
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class HashResult:
    """哈希计算结果
    
    Attributes:
        path: 被计算的文件路径
        hash_value: 计算得到的哈希值 (十六进制字符串)
        status: 计算是否成功
        message: 状态信息或错误消息
        file_size: 文件大小 (人类可读格式，如 "10 MB")
        algorithm: 使用的算法 (如 "md5")
        is_sparse: 是否为稀疏计算（True 表示只读取了部分文件）
        computed_at: 计算完成的时间
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
        """自定义字符串表示"""
        mode = "稀疏" if self.is_sparse else "完整"
        status_str = "✓ 成功" if self.status else "✗ 失败"
        
        if self.status:
            return (
                f"HashResult("
                f"path={self.path.name}, "
                f"hash={self.hash_value[:8]}..., "
                f"size={self.file_size}, "
                f"mode={mode}, "
                f"status={status_str})"
            )
        else:
            return (
                f"HashResult("
                f"path={self.path.name}, "
                f"status={status_str}, "
                f"error={self.message})"
            )
```

### Step 4: 运行测试确认通过

```bash
python -m pytest tests/md5/test_result.py -v
```

Expected: PASS (3 passed)

### Step 5: 提交

```bash
git add src/evan_tools/md5/result.py tests/md5/test_result.py
git commit -m "feat(md5): 创建改进的 HashResult 类"
```

---

## Task 4: 创建 HashCalculator 基类

**Files:**
- Create: `src/evan_tools/md5/calculator_base.py`
- Test: `tests/md5/test_calculator_base.py`

### Step 1: 编写基类测试

Create `tests/md5/test_calculator_base.py`:

```python
from pathlib import Path
import pytest
from unittest.mock import patch, mock_open
from evan_tools.md5.config import HashConfig
from evan_tools.md5.calculator_base import HashCalculator
from evan_tools.md5.exceptions import FileAccessError


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
    """validate_file 应检查文件是否可读"""
    config = HashConfig()
    calc = ConcreteCalculator(config)
    
    test_file = tmp_path / "test.bin"
    test_file.write_bytes(b"test")
    
    # 移除读权限
    import os
    os.chmod(test_file, 0o000)
    
    try:
        with pytest.raises(FileAccessError):
            calc._validate_file(test_file)
    finally:
        # 恢复权限以便清理
        os.chmod(test_file, 0o644)
```

### Step 2: 运行测试确认失败

```bash
python -m pytest tests/md5/test_calculator_base.py -v
```

Expected: FAIL

### Step 3: 创建基类

Create `src/evan_tools/md5/calculator_base.py`:

```python
"""
MD5 计算器基类

这个模块定义了所有哈希计算器的基类。
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO
import os

from evan_tools.md5.config import HashConfig
from evan_tools.md5.result import HashResult
from evan_tools.md5.exceptions import FileAccessError, FileReadError


class HashCalculator(ABC):
    """哈希计算器基类
    
    定义了所有具体计算器必须实现的接口和共享的验证逻辑。
    """
    
    def __init__(self, config: HashConfig):
        """初始化计算器
        
        Args:
            config: HashConfig 配置对象
        """
        self.config = config
    
    @abstractmethod
    def _calculate_hash(self, f: BinaryIO) -> str:
        """计算文件的哈希值（由子类实现）
        
        Args:
            f: 打开的二进制文件对象
            
        Returns:
            十六进制哈希值字符串
        """
        pass
    
    def _validate_file(self, path: Path) -> None:
        """验证文件的存在性和可读性
        
        Args:
            path: 文件路径
            
        Raises:
            FileAccessError: 如果文件不存在或不可读
        """
        if not path.exists():
            raise FileAccessError(f"文件不存在: {path}")
        
        if not path.is_file():
            raise FileAccessError(f"路径不是文件: {path}")
        
        if not os.access(path, os.R_OK):
            raise FileAccessError(f"没有读取权限: {path}")
    
    def _read_file_chunk(self, f: BinaryIO, size: int) -> bytes:
        """从文件中读取数据块
        
        Args:
            f: 打开的二进制文件对象
            size: 要读取的字节数
            
        Returns:
            读取到的数据
            
        Raises:
            FileReadError: 如果读取出错
        """
        try:
            data = f.read(size)
            return data
        except IOError as e:
            raise FileReadError(f"读取文件失败: {e}")
    
    def _get_file_size_humanized(self, path: Path) -> str:
        """获取文件大小的人类可读格式
        
        Args:
            path: 文件路径
            
        Returns:
            人类可读的文件大小字符串
        """
        try:
            import humanize
            size_bytes = path.stat().st_size
            return humanize.naturalsize(size_bytes)
        except Exception:
            # 如果 humanize 不可用或出错，回退到简单格式
            size_bytes = path.stat().st_size
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if size_bytes < 1024:
                    return f"{size_bytes:.1f} {unit}"
                size_bytes /= 1024
            return f"{size_bytes:.1f} PB"
```

### Step 4: 运行测试确认通过

```bash
python -m pytest tests/md5/test_calculator_base.py -v
```

Expected: PASS (3 passed)

### Step 5: 提交

```bash
git add src/evan_tools/md5/calculator_base.py tests/md5/test_calculator_base.py
git commit -m "feat(md5): 创建 HashCalculator 基类"
```

---

## Task 5: 实现 FullHashCalculator

**Files:**
- Create: `src/evan_tools/md5/calculator_full.py`
- Test: `tests/md5/test_calculator_full.py`

### Step 1: 编写完整计算器测试

Create `tests/md5/test_calculator_full.py`:

```python
from pathlib import Path
import pytest
from evan_tools.md5.config import HashConfig
from evan_tools.md5.calculator_full import FullHashCalculator


@pytest.fixture
def test_file(tmp_path):
    """创建测试文件"""
    content = b"The quick brown fox jumps over the lazy dog"
    test_file = tmp_path / "test.bin"
    test_file.write_bytes(content)
    return test_file, content


def test_full_calculator_calculate_small_file(test_file):
    """FullHashCalculator 应正确计算小文件"""
    path, content = test_file
    config = HashConfig()
    calc = FullHashCalculator(config)
    result = calc.calculate(path)
    
    assert result.status is True
    assert result.is_sparse is False
    assert len(result.hash_value) == 32  # MD5 是 32 位十六进制
    assert result.message == "Success"


def test_full_calculator_calculate_large_file(tmp_path):
    """FullHashCalculator 应正确计算大文件"""
    # 创建 20MB 文件
    test_file = tmp_path / "large.bin"
    with open(test_file, "wb") as f:
        f.write(b"A" * (20 * 1024 * 1024))
    
    config = HashConfig()
    calc = FullHashCalculator(config)
    result = calc.calculate(test_file)
    
    assert result.status is True
    assert result.is_sparse is False
    assert len(result.hash_value) == 32


def test_full_calculator_same_content_same_hash(tmp_path):
    """相同内容的文件应有相同的哈希值"""
    content = b"test content"
    
    file1 = tmp_path / "file1.bin"
    file1.write_bytes(content)
    
    file2 = tmp_path / "file2.bin"
    file2.write_bytes(content)
    
    config = HashConfig()
    calc = FullHashCalculator(config)
    
    result1 = calc.calculate(file1)
    result2 = calc.calculate(file2)
    
    assert result1.hash_value == result2.hash_value


def test_full_calculator_different_content_different_hash(tmp_path):
    """不同内容的文件应有不同的哈希值"""
    file1 = tmp_path / "file1.bin"
    file1.write_bytes(b"content1")
    
    file2 = tmp_path / "file2.bin"
    file2.write_bytes(b"content2")
    
    config = HashConfig()
    calc = FullHashCalculator(config)
    
    result1 = calc.calculate(file1)
    result2 = calc.calculate(file2)
    
    assert result1.hash_value != result2.hash_value
```

### Step 2: 运行测试确认失败

```bash
python -m pytest tests/md5/test_calculator_full.py -v
```

Expected: FAIL

### Step 3: 实现完整计算器

Create `src/evan_tools/md5/calculator_full.py`:

```python
"""
完整 MD5 计算器

计算整个文件的 MD5 值，适合需要精确校验的场景。
"""

import hashlib
from pathlib import Path
from typing import BinaryIO

from evan_tools.md5.calculator_base import HashCalculator
from evan_tools.md5.config import HashConfig
from evan_tools.md5.result import HashResult
from evan_tools.md5.exceptions import FileReadError


class FullHashCalculator(HashCalculator):
    """完整文件 MD5 计算器
    
    逐块读取整个文件并计算 MD5 值。
    """
    
    def calculate(self, path: Path) -> HashResult:
        """计算文件的完整 MD5 值
        
        Args:
            path: 文件路径
            
        Returns:
            HashResult 对象
        """
        try:
            # 验证文件
            self._validate_file(path)
            
            # 计算哈希
            with open(path, "rb") as f:
                hash_value = self._calculate_hash(f)
            
            # 获取文件大小
            file_size = self._get_file_size_humanized(path)
            
            return HashResult(
                path=path,
                hash_value=hash_value,
                status=True,
                message="Success",
                file_size=file_size,
                algorithm=self.config.algorithm,
                is_sparse=False,
            )
        
        except Exception as e:
            return HashResult(
                path=path,
                hash_value="",
                status=False,
                message=str(e),
                file_size="0 B",
                algorithm=self.config.algorithm,
                is_sparse=False,
            )
    
    def _calculate_hash(self, f: BinaryIO) -> str:
        """计算文件的完整 MD5 值
        
        Args:
            f: 打开的二进制文件对象
            
        Returns:
            十六进制 MD5 值
        """
        md5_hash = hashlib.md5()
        
        while chunk := self._read_file_chunk(f, self.config.buffer_size):
            md5_hash.update(chunk)
        
        return md5_hash.hexdigest()
```

### Step 4: 运行测试确认通过

```bash
python -m pytest tests/md5/test_calculator_full.py -v
```

Expected: PASS (5 passed)

### Step 5: 提交

```bash
git add src/evan_tools/md5/calculator_full.py tests/md5/test_calculator_full.py
git commit -m "feat(md5): 实现 FullHashCalculator"
```

---

## Task 6: 实现 SparseHashCalculator

**Files:**
- Create: `src/evan_tools/md5/calculator_sparse.py`
- Test: `tests/md5/test_calculator_sparse.py`

### Step 1: 编写稀疏计算器测试

Create `tests/md5/test_calculator_sparse.py`:

```python
from pathlib import Path
import pytest
from evan_tools.md5.config import HashConfig
from evan_tools.md5.calculator_sparse import SparseHashCalculator


@pytest.fixture
def large_test_file(tmp_path):
    """创建 100MB 测试文件"""
    test_file = tmp_path / "large.bin"
    size = 100 * 1024 * 1024  # 100MB
    with open(test_file, "wb") as f:
        # 写入有规律的数据以便验证
        chunk = b"A" * 1024
        for _ in range(size // 1024):
            f.write(chunk)
    return test_file


def test_sparse_calculator_calculate_large_file(large_test_file):
    """SparseHashCalculator 应能计算大文件"""
    config = HashConfig(sparse_segments=5)
    calc = SparseHashCalculator(config)
    result = calc.calculate(large_test_file)
    
    assert result.status is True
    assert result.is_sparse is True
    assert len(result.hash_value) == 32  # MD5 是 32 位


def test_sparse_calculator_faster_than_full(large_test_file):
    """稀疏计算应比完整计算快"""
    import time
    
    config = HashConfig(sparse_segments=5)
    sparse_calc = SparseHashCalculator(config)
    
    from evan_tools.md5.calculator_full import FullHashCalculator
    full_calc = FullHashCalculator(config)
    
    # 测试稀疏计算速度
    start = time.time()
    sparse_result = sparse_calc.calculate(large_test_file)
    sparse_time = time.time() - start
    
    # 测试完整计算速度
    start = time.time()
    full_result = full_calc.calculate(large_test_file)
    full_time = time.time() - start
    
    # 稀疏计算应明显更快
    assert sparse_time < full_time * 0.5


def test_sparse_calculator_segments_parameter(large_test_file):
    """不同的 segment 数量应产生不同结果"""
    config1 = HashConfig(sparse_segments=5)
    config2 = HashConfig(sparse_segments=8)
    
    calc1 = SparseHashCalculator(config1)
    calc2 = SparseHashCalculator(config2)
    
    result1 = calc1.calculate(large_test_file)
    result2 = calc2.calculate(large_test_file)
    
    # 由于段数不同，哈希值应不同
    assert result1.hash_value != result2.hash_value


def test_sparse_calculator_same_file_same_hash(large_test_file):
    """相同配置计算同一文件应得到相同哈希"""
    config = HashConfig(sparse_segments=5)
    calc = SparseHashCalculator(config)
    
    result1 = calc.calculate(large_test_file)
    result2 = calc.calculate(large_test_file)
    
    assert result1.hash_value == result2.hash_value
```

### Step 2: 运行测试确认失败

```bash
python -m pytest tests/md5/test_calculator_sparse.py -v
```

Expected: FAIL

### Step 3: 实现稀疏计算器

Create `src/evan_tools/md5/calculator_sparse.py`:

```python
"""
稀疏 MD5 计算器

通过只读取文件的头、尾和中间部分来快速估算 MD5，适合去重检测场景。
"""

import hashlib
from pathlib import Path
from typing import BinaryIO

from evan_tools.md5.calculator_base import HashCalculator
from evan_tools.md5.config import HashConfig
from evan_tools.md5.result import HashResult
from evan_tools.md5.exceptions import FileReadError


class SparseHashCalculator(HashCalculator):
    """稀疏 MD5 计算器
    
    快速计算文件的"指纹"，通过读取文件的头、尾和中间部分。
    """
    
    def calculate(self, path: Path) -> HashResult:
        """计算文件的稀疏 MD5 值
        
        Args:
            path: 文件路径
            
        Returns:
            HashResult 对象
        """
        try:
            # 验证文件
            self._validate_file(path)
            
            # 计算哈希
            with open(path, "rb") as f:
                hash_value = self._calculate_hash(f)
            
            # 获取文件大小
            file_size = self._get_file_size_humanized(path)
            
            return HashResult(
                path=path,
                hash_value=hash_value,
                status=True,
                message="Success",
                file_size=file_size,
                algorithm=self.config.algorithm,
                is_sparse=True,
            )
        
        except Exception as e:
            return HashResult(
                path=path,
                hash_value="",
                status=False,
                message=str(e),
                file_size="0 B",
                algorithm=self.config.algorithm,
                is_sparse=True,
            )
    
    def _calculate_hash(self, f: BinaryIO) -> str:
        """计算稀疏 MD5 值
        
        策略：
        1. 如果文件小于等于 buffer_size * sparse_segments，计算完整 MD5
        2. 否则，读取：头部 + 中间采样点 + 尾部
        
        Args:
            f: 打开的二进制文件对象
            
        Returns:
            十六进制 MD5 值
        """
        md5_hash = hashlib.md5()
        
        # 获取文件大小
        f.seek(0, 2)
        file_size = f.tell()
        f.seek(0)
        
        # 如果文件较小，直接计算完整 MD5
        threshold = self.config.buffer_size * self.config.sparse_segments
        if file_size <= threshold:
            while chunk := self._read_file_chunk(f, self.config.buffer_size):
                md5_hash.update(chunk)
            return md5_hash.hexdigest()
        
        # 稀疏计算：头 + 中间采样 + 尾
        buffer_size = self.config.buffer_size
        segments = self.config.sparse_segments
        
        # 1. 读取头部
        md5_hash.update(self._read_file_chunk(f, buffer_size))
        
        # 2. 计算中间采样点
        effective_size = file_size - buffer_size * 2
        step = effective_size // (segments - 2) if segments > 2 else 0
        
        # 3. 读取中间部分
        if step > 0:
            offset = buffer_size
            for i in range(segments - 2):
                offset += step
                if offset + buffer_size >= file_size:
                    break
                
                f.seek(offset)
                md5_hash.update(self._read_file_chunk(f, buffer_size))
        
        # 4. 读取尾部
        f.seek(file_size - buffer_size)
        md5_hash.update(self._read_file_chunk(f, buffer_size))
        
        return md5_hash.hexdigest()
```

### Step 4: 运行测试确认通过

```bash
python -m pytest tests/md5/test_calculator_sparse.py -v -s
```

Expected: PASS (5 passed)

### Step 5: 提交

```bash
git add src/evan_tools/md5/calculator_sparse.py tests/md5/test_calculator_sparse.py
git commit -m "feat(md5): 实现 SparseHashCalculator"
```

---

## Task 7: 创建 calculate_hash() 主入口函数

**Files:**
- Create: `src/evan_tools/md5/api.py`
- Test: `tests/md5/test_api.py`

### Step 1: 编写 API 测试

Create `tests/md5/test_api.py`:

```python
from pathlib import Path
import pytest
from evan_tools.md5.api import calculate_hash
from evan_tools.md5.config import HashConfig


@pytest.fixture
def test_file(tmp_path):
    """创建测试文件"""
    path = tmp_path / "test.bin"
    path.write_bytes(b"test content")
    return path


def test_calculate_hash_default_sparse_mode(test_file):
    """默认应使用稀疏模式"""
    result = calculate_hash(test_file)
    
    assert result.status is True
    assert result.is_sparse is True


def test_calculate_hash_full_mode(test_file):
    """指定 full 模式应使用完整计算"""
    result = calculate_hash(test_file, mode="full")
    
    assert result.status is True
    assert result.is_sparse is False


def test_calculate_hash_sparse_mode(test_file):
    """指定 sparse 模式应使用稀疏计算"""
    result = calculate_hash(test_file, mode="sparse")
    
    assert result.status is True
    assert result.is_sparse is True


def test_calculate_hash_custom_config(test_file):
    """应支持自定义配置"""
    config = HashConfig(buffer_size=16 * 1024 * 1024)
    result = calculate_hash(test_file, config=config)
    
    assert result.status is True


def test_calculate_hash_invalid_mode(test_file):
    """无效的模式应返回失败"""
    result = calculate_hash(test_file, mode="invalid")
    
    assert result.status is False
    assert "invalid" in result.message.lower()


def test_calculate_hash_nonexistent_file(tmp_path):
    """不存在的文件应返回失败结果"""
    nonexistent = tmp_path / "nonexistent.bin"
    result = calculate_hash(nonexistent)
    
    assert result.status is False
    assert "not found" in result.message.lower() or "不存在" in result.message
```

### Step 2: 运行测试确认失败

```bash
python -m pytest tests/md5/test_api.py -v
```

Expected: FAIL

### Step 3: 创建 API 模块

Create `src/evan_tools/md5/api.py`:

```python
"""
MD5 计算 API

提供用户友好的入口函数来计算文件哈希值。
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
    
    这是 MD5 模块的主入口函数，提供简洁的用户 API。
    
    Args:
        path: 要计算哈希值的文件路径
        mode: 计算模式
            - "full": 完整计算，精确但较慢，适合数据完整性验证
            - "sparse": 稀疏计算（默认），快速但估算，适合文件去重检测
        config: 自定义配置，默认为 None（使用 HashConfig 默认值）
    
    Returns:
        HashResult 对象，包含计算结果或错误信息
    
    Examples:
        >>> from pathlib import Path
        >>> from evan_tools.md5 import calculate_hash
        >>> 
        >>> # 快速去重检测
        >>> result = calculate_hash(Path("large_file.bin"), mode="sparse")
        >>> if result.status:
        ...     print(f"哈希值: {result.hash_value}")
        >>> 
        >>> # 精确校验
        >>> result = calculate_hash(Path("important_file.bin"), mode="full")
        >>> 
        >>> # 自定义配置
        >>> from evan_tools.md5 import HashConfig
        >>> config = HashConfig(buffer_size=16 * 1024 * 1024)
        >>> result = calculate_hash(Path("file.bin"), config=config)
    """
    # 使用默认配置如果未提供
    if config is None:
        config = HashConfig()
    
    # 选择合适的计算器
    if mode == "full":
        calculator = FullHashCalculator(config)
    elif mode == "sparse":
        calculator = SparseHashCalculator(config)
    else:
        # 无效的模式
        return HashResult(
            path=Path(path),
            hash_value="",
            status=False,
            message=f"无效的计算模式: {mode}. 支持的模式: 'full', 'sparse'",
            file_size="0 B",
            algorithm=config.algorithm,
            is_sparse=mode == "sparse",
        )
    
    # 执行计算
    return calculator.calculate(Path(path))
```

### Step 4: 运行测试确认通过

```bash
python -m pytest tests/md5/test_api.py -v
```

Expected: PASS (6 passed)

### Step 5: 提交

```bash
git add src/evan_tools/md5/api.py tests/md5/test_api.py
git commit -m "feat(md5): 创建 calculate_hash() 主 API 入口"
```

---

## Task 8: 保持向后兼容性

**Files:**
- Modify: `src/evan_tools/md5/main.py`
- Test: `tests/md5/test_backward_compatibility.py`

### Step 1: 编写向后兼容性测试

Create `tests/md5/test_backward_compatibility.py`:

```python
from pathlib import Path
import pytest
from evan_tools.md5.main import calc_full_md5, calc_sparse_md5


@pytest.fixture
def test_file(tmp_path):
    """创建测试文件"""
    path = tmp_path / "test.bin"
    path.write_bytes(b"test content for compatibility")
    return path


def test_calc_full_md5_still_works(test_file):
    """原有的 calc_full_md5 函数应继续工作"""
    result = calc_full_md5(test_file)
    
    # 应返回 MD5Result 对象
    assert hasattr(result, 'path')
    assert hasattr(result, 'md5')
    assert hasattr(result, 'status')
    assert hasattr(result, 'message')
    assert hasattr(result, 'file_size')
    
    assert result.status is True
    assert result.path == test_file
    assert len(result.md5) == 32  # MD5 哈希值


def test_calc_sparse_md5_still_works(test_file):
    """原有的 calc_sparse_md5 函数应继续工作"""
    result = calc_sparse_md5(test_file)
    
    # 应返回 MD5Result 对象
    assert hasattr(result, 'path')
    assert hasattr(result, 'md5')
    assert hasattr(result, 'status')
    assert hasattr(result, 'message')
    assert hasattr(result, 'file_size')
    
    assert result.status is True
    assert result.path == test_file


def test_full_md5_with_custom_parameters(test_file):
    """calc_full_md5 应支持原有的参数"""
    # 原有 API 支持 buffer_size 参数
    result = calc_full_md5(test_file, buffer_size=16 * 1024 * 1024)
    assert result.status is True


def test_sparse_md5_with_custom_parameters(test_file):
    """calc_sparse_md5 应支持原有的参数"""
    # 原有 API 支持 buffer_size 和 segments 参数
    result = calc_sparse_md5(
        test_file,
        buffer_size=16 * 1024 * 1024,
        segments=8
    )
    assert result.status is True


def test_calc_full_md5_nonexistent_file(tmp_path):
    """不存在的文件应返回失败状态"""
    nonexistent = tmp_path / "nonexistent.bin"
    result = calc_full_md5(nonexistent)
    
    assert result.status is False


def test_calc_sparse_md5_nonexistent_file(tmp_path):
    """不存在的文件应返回失败状态"""
    nonexistent = tmp_path / "nonexistent.bin"
    result = calc_sparse_md5(nonexistent)
    
    assert result.status is False
```

### Step 2: 运行测试确认失败

```bash
python -m pytest tests/md5/test_backward_compatibility.py -v
```

Expected: FAIL

### Step 3: 修改 main.py 保持兼容性

Modify `src/evan_tools/md5/main.py` - Replace the entire content:

```python
"""
MD5 哈希计算模块

这个模块提供文件 MD5 计算功能，支持完整计算和稀疏计算两种模式。

Note: 这个模块已经过重构，现在基于新的 API 实现。
旧的函数 (calc_full_md5, calc_sparse_md5) 被保留以保持向后兼容性。
"""

import typing as t
from pathlib import Path

import humanize
from rich import print

# 导入新的 API
from evan_tools.md5.api import calculate_hash
from evan_tools.md5.config import HashConfig


class MD5Result(t.NamedTuple):
    """MD5 计算结果（为了向后兼容性保留）"""
    path: Path
    md5: str
    status: bool
    message: str
    file_size: str


def calc_sparse_md5(
    item: Path, buffer_size: int = 8 * 1024 * 1024, segments: int = 10
) -> MD5Result:
    """计算文件的稀疏 MD5 值（快速模式）
    
    通过只读取文件的头、尾和中间部分来快速估算 MD5 值。
    适合文件去重检测场景。
    
    Args:
        item: 文件路径
        buffer_size: 读取缓冲区大小（默认 8MB）
        segments: 稀疏采样段数（默认 10）
    
    Returns:
        MD5Result 对象
    
    Note:
        这个函数现已基于新的计算器 API 实现，保留原有签名以保持兼容性。
    """
    config = HashConfig(buffer_size=buffer_size, sparse_segments=segments)
    result = calculate_hash(item, mode="sparse", config=config)
    
    return MD5Result(
        path=result.path,
        md5=result.hash_value,
        status=result.status,
        message=result.message,
        file_size=result.file_size,
    )


def calc_full_md5(item: Path, buffer_size: int = 8 * 1024 * 1024) -> MD5Result:
    """计算文件的完整 MD5 值
    
    逐块读取整个文件并计算精确的 MD5 值。
    适合数据完整性验证场景。
    
    Args:
        item: 文件路径
        buffer_size: 读取缓冲区大小（默认 8MB）
    
    Returns:
        MD5Result 对象
    
    Note:
        这个函数现已基于新的计算器 API 实现，保留原有签名以保持兼容性。
    """
    config = HashConfig(buffer_size=buffer_size)
    result = calculate_hash(item, mode="full", config=config)
    
    return MD5Result(
        path=result.path,
        md5=result.hash_value,
        status=result.status,
        message=result.message,
        file_size=result.file_size,
    )
```

### Step 4: 运行测试确认通过

```bash
python -m pytest tests/md5/test_backward_compatibility.py -v
```

Expected: PASS (7 passed)

### Step 5: 提交

```bash
git add src/evan_tools/md5/main.py tests/md5/test_backward_compatibility.py
git commit -m "refactor(md5): 基于新 API 重新实现，保持向后兼容"
```

---

## Task 9: 更新 __init__.py 导出公开 API

**Files:**
- Modify: `src/evan_tools/md5/__init__.py`

### Step 1: 修改 __init__.py

Modify `src/evan_tools/md5/__init__.py`:

```python
"""MD5 模块

提供文件哈希计算功能。
"""

# 导出主要 API
from evan_tools.md5.api import calculate_hash
from evan_tools.md5.config import HashConfig
from evan_tools.md5.result import HashResult
from evan_tools.md5.exceptions import (
    HashCalculationError,
    FileAccessError,
    FileReadError,
    InvalidConfigError,
)

# 导出旧 API 用于向后兼容
from evan_tools.md5.main import calc_full_md5, calc_sparse_md5, MD5Result

__all__ = [
    # 新 API
    "calculate_hash",
    "HashConfig",
    "HashResult",
    # 异常类
    "HashCalculationError",
    "FileAccessError",
    "FileReadError",
    "InvalidConfigError",
    # 旧 API（向后兼容）
    "calc_full_md5",
    "calc_sparse_md5",
    "MD5Result",
]
```

### Step 2: 测试导入

```bash
python -c "from evan_tools.md5 import calculate_hash, HashConfig, HashResult, calc_full_md5, calc_sparse_md5; print('All imports successful')"
```

Expected: "All imports successful"

### Step 3: 提交

```bash
git add src/evan_tools/md5/__init__.py
git commit -m "refactor(md5): 更新模块导出，包括新旧 API"
```

---

## Task 10: 运行全部测试并验收

**Files:**
- Test: `tests/md5/`

### Step 1: 运行所有 MD5 相关测试

```bash
python -m pytest tests/md5/ -v --tb=short
```

Expected: 所有测试通过

### Step 2: 检查测试覆盖率

```bash
python -m pytest tests/md5/ --cov=src/evan_tools/md5 --cov-report=term-missing
```

Expected: 覆盖率 ≥ 90%

### Step 3: 运行整个项目的测试以确保无回归

```bash
python -m pytest tests/ -v --tb=short
```

Expected: 所有测试通过

### Step 4: 最终提交

```bash
git add .
git commit -m "test(md5): 全部测试通过，覆盖率验收"
```

---

## 总结

实现完成后：

1. ✅ 新的模块化架构完全就绪
2. ✅ 所有旧 API 继续工作
3. ✅ 新 API 提供更强大的功能
4. ✅ 单元测试覆盖率 ≥ 90%
5. ✅ 文档完整
6. ✅ 代码质量高

**下一步选项：**
- 性能基准测试（Task 10 - 可选）
- 撰写使用文档
- 合并到 master 分支
