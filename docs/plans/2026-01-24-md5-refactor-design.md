# MD5 模块架构重构设计

**日期**: 2026-01-24  
**目标**: 全面优化 MD5 模块 - 性能、代码质量、可扩展性  
**使用场景**: 文件去重检测  

---

## 1. 整体架构

### 核心设计模式
采用 **策略模式** + **配置对象** 架构，分离关注点：

```
HashConfig (配置)
    ↓
HashCalculator (基类)
    ├─ FullHashCalculator (完整计算策略)
    └─ SparseHashCalculator (稀疏计算策略)
    
HashResult (结果对象)
```

### 关键类设计

#### 1. `HashConfig` 配置类
```python
@dataclass
class HashConfig:
    """哈希计算配置"""
    algorithm: str = "md5"                    # 算法类型
    buffer_size: int = 8 * 1024 * 1024        # 缓冲区大小（8MB）
    sparse_segments: int = 10                 # 稀疏计算段数
    enable_cache: bool = False                # 是否启用缓存
```

**作用**:
- 集中管理配置参数，提高可维护性
- 支持预设配置和自定义配置
- 便于未来扩展（如支持其他算法）

#### 2. `HashResult` 结果类（改进）
```python
@dataclass
class HashResult:
    path: Path                  # 文件路径
    hash_value: str             # 哈希值（改名以支持多算法）
    status: bool                # 计算是否成功
    message: str                # 状态信息/错误消息
    file_size: str              # 文件大小（人类可读）
    algorithm: str              # 算法类型
    is_sparse: bool             # 是否为稀疏计算
    computed_at: datetime       # 计算时间
```

**改进点**:
- 添加 `algorithm` 和 `is_sparse` 标识
- 添加时间戳便于缓存和追踪
- `hash_value` 字段名更通用，支持多算法

#### 3. `HashCalculator` 抽象基类
```python
from abc import ABC, abstractmethod

class HashCalculator(ABC):
    """哈希计算器基类"""
    
    def __init__(self, config: HashConfig):
        self.config = config
    
    @abstractmethod
    def calculate(self, path: Path) -> HashResult:
        """计算文件哈希值"""
        pass
    
    def _validate_file(self, path: Path) -> None:
        """文件校验"""
        # 检查文件存在性、可读性等
    
    def _read_file_chunk(self, f: BinaryIO, size: int) -> bytes:
        """统一的文件读取逻辑"""
        # 处理读取异常、重试等
```

**好处**:
- 定义统一的接口契约
- 共享通用逻辑
- 易于单元测试
- 后续支持 SHA256 等算法只需继承此类

---

## 2. API 设计与使用方式

### 用户入口函数

```python
def calculate_hash(
    path: Path, 
    mode: Literal["full", "sparse"] = "sparse",
    config: Optional[HashConfig] = None
) -> HashResult:
    """
    计算文件的哈希值
    
    Args:
        path: 文件路径
        mode: 计算模式
            - "full": 完整计算，精确但较慢
            - "sparse": 稀疏计算，快速适合去重比较
        config: 自定义配置，不提供时使用默认值
    
    Returns:
        HashResult: 计算结果
    """
```

### 使用示例

```python
from pathlib import Path
from evan_tools.md5 import calculate_hash, HashConfig

# 1. 快速去重检测（默认配置）
result = calculate_hash(Path("large_file.bin"), mode="sparse")
if result.status:
    print(f"稀疏哈希: {result.hash_value}")

# 2. 精确校验（完整计算）
result = calculate_hash(Path("important_file.bin"), mode="full")
if result.status:
    print(f"完整哈希: {result.hash_value}")
else:
    print(f"计算失败: {result.message}")

# 3. 自定义配置
config = HashConfig(
    buffer_size=16 * 1024 * 1024,  # 16MB 缓冲
    sparse_segments=8               # 8 段稀疏采样
)
result = calculate_hash(Path("file.bin"), mode="sparse", config=config)
```

### 数据流

```
Path 输入
  ↓
参数校验 (文件存在、可读、权限)
  ↓
构建计算器 (选择 Full 或 Sparse)
  ↓
读取文件数据
  ↓
增量计算哈希
  ↓
异常处理 (捕获所有错误)
  ↓
返回 HashResult
```

---

## 3. 错误处理与质量保证

### 异常体系

```python
# 异常基类
class HashCalculationError(Exception):
    """哈希计算异常基类"""
    pass

# 具体异常类
class FileAccessError(HashCalculationError):
    """文件访问异常（不存在、无权限等）"""
    pass

class FileReadError(HashCalculationError):
    """文件读取异常（磁盘错误、被占用等）"""
    pass

class InvalidConfigError(HashCalculationError):
    """无效配置异常"""
    pass
```

**处理原则**:
- 所有异常被**捕获并转换**为失败的 `HashResult`
- 程序不会因错误而中断（稳健性强）
- `message` 字段记录具体错误信息
- 便于日志记录和调试

### 单元测试覆盖

```
tests/md5/
├── test_config.py              # 配置类测试
├── test_full_calculator.py     # 完整计算器测试
├── test_sparse_calculator.py   # 稀疏计算器测试
├── test_error_handling.py      # 异常处理测试
│   ├── 文件不存在
│   ├── 权限不足
│   ├── 磁盘错误
│   └── 无效配置
├── test_edge_cases.py          # 边界情况
│   ├── 空文件
│   ├── 超小文件（< 缓冲区）
│   ├── 恰好等于缓冲区大小
│   └── 特大文件
└── test_api.py                 # 集成测试
    ├── 快速模式
    ├── 完整模式
    └── 自定义配置
```

**测试策略**:
- 单元测试覆盖率 ≥ 90%
- 模拟文件操作以加速测试
- 使用 pytest fixtures 共享测试数据
- 包含性能测试（benchmark）

---

## 4. 实现要点

### 代码组织

```
src/evan_tools/md5/
├── __init__.py              # 导出公开 API
├── main.py                  # 保持兼容性（包装旧函数）
├── config.py                # 配置类
├── result.py                # 结果类
├── exceptions.py            # 异常定义
├── calculator.py            # 计算器基类和具体实现
└── api.py                   # 用户入口函数
```

### 关键实现细节

1. **向后兼容性**：保留 `calc_full_md5()` 和 `calc_sparse_md5()`，但内部调用新 API
2. **参数验证**：在计算前验证文件和配置
3. **性能优化**：
   - 缓冲区大小根据系统内存动态调整（可选）
   - 使用 `mmap` 进行超大文件优化（可选）
4. **日志支持**：集成 `logging` 模块便于调试

---

## 5. 与现有代码的集成

### 外部使用不变

项目中其他模块使用 MD5 的方式保持不变：

```python
from evan_tools.md5 import calc_full_md5, calc_sparse_md5

# 现有代码继续工作
result = calc_sparse_md5(Path("file"))
```

### 内部实现升级

旧函数通过新 API 实现：

```python
# main.py
from .api import calculate_hash, HashConfig

def calc_sparse_md5(item: Path, buffer_size: int = ..., segments: int = ...) -> MD5Result:
    config = HashConfig(buffer_size=buffer_size, sparse_segments=segments)
    result = calculate_hash(item, mode="sparse", config=config)
    # 转换为旧格式返回
    return MD5Result(...)
```

---

## 6. 实现优先级

| 阶段 | 工作 | 优先级 |
|------|------|--------|
| P1 | 基础类设计和单元测试框架 | 必须 |
| P1 | 核心计算逻辑重构 | 必须 |
| P2 | 向后兼容性包装 | 必须 |
| P2 | 完整的单元测试套件 | 必须 |
| P3 | 性能基准测试 | 可选 |
| P4 | 文档和示例 | 可选 |

---

## 总结

这次重构通过引入**策略模式**和**配置对象**，实现了：
- ✅ **清晰的架构**：易于理解和维护
- ✅ **高度的灵活性**：支持不同的计算策略和配置
- ✅ **强大的扩展性**：未来支持其他哈希算法无需修改现有代码
- ✅ **可靠的质量**：完善的异常处理和测试覆盖
- ✅ **向后兼容**：现有代码无需修改即可升级
