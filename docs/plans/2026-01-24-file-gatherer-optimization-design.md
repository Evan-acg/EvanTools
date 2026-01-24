# 文件收集模块优化设计

**日期**: 2026-01-24  
**模块**: `evan_tools.file`  
**目标**: 全面优化 `gather_paths` 功能，增强性能、功能和可用性

## 背景

现有的 `gather_paths` 函数提供基本的文件/目录收集功能，但在处理大型目录树、复杂过滤需求时存在以下限制：
- 性能瓶颈：扫描大量文件时速度较慢
- 功能受限：缺乏模式匹配、排除规则、排序等高级功能
- 错误处理：静默跳过错误，用户无法感知问题
- 进度反馈：无法在长时间扫描时提供进度信息

## 设计目标

1. **性能优化**: 提升大目录扫描速度
2. **功能增强**: 添加模式匹配、排序、属性过滤、进度回调
3. **改进可用性**: 更好的错误处理和API设计
4. **代码质量**: 重构内部实现，提高可维护性
5. **向后兼容**: 不破坏现有代码

## 架构方案：渐进式扩展

### 设计原则

- 保留现有 `gather_paths()` 函数作为简单接口
- 添加 `PathGatherer` 类处理复杂场景
- 简单场景用函数，复杂场景用类
- 性能优化集中在关键路径

### 模块结构

```
file/main.py
├── 现有函数（向后兼容）
│   ├── gather_paths()  # 保持API不变
│   └── 辅助函数 (_process_depth, _handle_root_path 等)
│
├── 新增：PathGatherer 类（核心）
│   ├── __init__()      # 配置初始化
│   ├── pattern()       # 设置匹配模式（链式）
│   ├── exclude()       # 设置排除规则（链式）
│   ├── sort_by()       # 设置排序（链式）
│   ├── filter_by()     # 文件属性过滤（链式）
│   ├── on_progress()   # 进度回调（链式）
│   └── gather()        # 执行收集
│
└── 新增：辅助类和类型
    ├── GatherConfig    # 配置数据类
    ├── SortBy (Enum)   # 排序选项枚举
    └── errors 属性     # 错误列表访问
```

## 核心设计

### 1. 类型定义

```python
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

class SortBy(Enum):
    """排序方式枚举"""
    NAME = "name"          # 按文件名
    SIZE = "size"          # 按大小
    MTIME = "mtime"        # 按修改时间
    CTIME = "ctime"        # 按创建时间
    EXTENSION = "ext"      # 按扩展名

@dataclass
class GatherConfig:
    """收集配置"""
    deep: bool | int = False
    dir_only: bool = False
    patterns: list[str] = field(default_factory=list)
    excludes: list[str] = field(default_factory=list)
    filter_func: Callable[[Path], bool] | None = None
    sort_by: SortBy | None = None
    sort_reverse: bool = False
    # 文件属性过滤
    size_min: int | None = None
    size_max: int | None = None
    mtime_after: float | None = None
    mtime_before: float | None = None
    # 回调
    progress_callback: Callable[[int], None] | None = None
    error_handler: Callable[[Path, Exception], None] | None = None
```

### 2. PathGatherer 类

```python
class PathGatherer:
    """路径收集器 - 链式调用构建器"""
    
    def __init__(self, paths: Iterable[Path | str], *, deep: bool | int = False):
        """初始化收集器"""
        self._paths = [Path(p) for p in paths]
        self._config = GatherConfig(deep=deep)
        self._errors: list[tuple[Path, Exception]] = []
    
    # 链式配置方法
    def pattern(self, *patterns: str) -> "PathGatherer":
        """添加匹配模式，支持 glob 语法 (如 *.py, test_*.txt)"""
        
    def exclude(self, *patterns: str) -> "PathGatherer":
        """添加排除模式，支持 glob 语法 (如 *.pyc, __pycache__)"""
        
    def sort_by(self, key: SortBy, *, reverse: bool = False) -> "PathGatherer":
        """设置排序方式"""
        
    def filter_by(self, *, size_min=None, size_max=None, 
                  mtime_after=None, mtime_before=None) -> "PathGatherer":
        """按文件属性过滤"""
        
    def on_progress(self, callback: Callable[[int], None]) -> "PathGatherer":
        """设置进度回调，参数为已找到的文件数"""
        
    # 执行方法
    def gather(self) -> Iterable[Path]:
        """执行路径收集"""
        
    # 属性访问
    @property
    def errors(self) -> list[tuple[Path, Exception]]:
        """获取收集过程中遇到的错误"""
```

### 3. 过滤处理流程

采用**先过滤后排序**策略，优化性能：

```
遍历文件系统
    ↓
模式匹配（快速字符串操作）
    ↓
排除规则（快速字符串操作）
    ↓
属性过滤（需要 stat，较慢）
    ↓
自定义过滤器（用户逻辑）
    ↓
排序（如果需要，物化为列表）
    ↓
返回结果
```

**优化点**：
1. 过滤顺序：先快速的字符串匹配，再慢的文件系统操作
2. 懒惰求值：只有通过前面检查才执行 `stat()`
3. 短路逻辑：任一条件不满足立即返回

### 4. 性能优化

#### scandir 优化
```python
# 使用 entry.is_dir() 而不是 Path.is_dir()
with os.scandir(path) as entries:
    for entry in entries:
        if entry.is_dir(follow_symlinks=False):  # 避免额外系统调用
            ...
```

#### 深度优化的递归遍历
```python
# 及早剪枝，避免遍历超深度的子树
if depth >= max_depth:
    dirs.clear()  # 停止深入
```

#### 迭代器特性保持
```python
# 不排序时保持生成器，节省内存
if self._config.sort_by:
    yield from sorted(collected)  # 需要时才物化
else:
    yield from collected  # 保持惰性
```

### 5. 错误处理策略

**记录但继续**模式：
- 收集所有错误到 `_errors` 列表
- 不中断整体处理流程
- 可选的用户错误回调
- 通过 `.errors` 属性访问错误列表

```python
try:
    # 处理路径
except OSError as e:
    self._errors.append((path, e))
    if self._config.error_handler:
        self._config.error_handler(path, e)
    # 继续处理下一个
```

### 6. 向后兼容

保留原有 `gather_paths` 函数：
```python
def gather_paths(
    paths: Iterable[Path | str],
    *,
    deep: bool | int = False,
    dir_only: bool = False,
    filter: Callable[[Path], bool] | None = None,
) -> Iterable[Path]:
    """原有函数保持不变"""
    # 简单场景使用原实现（最优性能）
    # 复杂场景内部调用 PathGatherer
```

## 使用示例

### 简单场景（向后兼容）

```python
from evan_tools.file import gather_paths

# 现有代码继续工作
paths = gather_paths(["."], deep=True)
files = gather_paths(["."], deep=2, dir_only=False)
```

### 复杂场景（新增功能）

```python
from evan_tools.file import PathGatherer, SortBy

# 查找所有 Python 文件，按大小排序
gatherer = (PathGatherer(["."])
    .pattern("*.py")
    .exclude("*.pyc", "__pycache__")
    .sort_by(SortBy.SIZE, reverse=True)
    .filter_by(size_min=1024)  # 至少 1KB
)

for path in gatherer.gather():
    print(f"{path}: {path.stat().st_size} bytes")

# 检查错误
if gatherer.errors:
    print(f"遇到 {len(gatherer.errors)} 个错误")
```

### 带进度的大目录扫描

```python
def show_progress(count):
    if count % 1000 == 0:
        print(f"已找到 {count} 个文件...")

gatherer = (PathGatherer(["/large/directory"])
    .pattern("*.log")
    .on_progress(show_progress)
)

logs = list(gatherer.gather())
```

### 按时间过滤

```python
import time

# 查找最近7天修改的文件
week_ago = time.time() - 7 * 24 * 3600

gatherer = (PathGatherer(["."])
    .filter_by(mtime_after=week_ago)
    .sort_by(SortBy.MTIME, reverse=True)
)

for path in gatherer.gather():
    print(f"{path} - {time.ctime(path.stat().st_mtime)}")
```

## 实现计划

### 阶段 1：核心类实现
1. 实现 `SortBy` 枚举和 `GatherConfig` 数据类
2. 实现 `PathGatherer` 基本框架和链式方法
3. 实现 `_should_include()` 过滤逻辑

### 阶段 2：收集逻辑
1. 实现 `gather()` 主方法
2. 优化 `_gather_flat()` 使用 scandir
3. 优化 `_gather_recursive()` 添加错误处理和进度

### 阶段 3：向后兼容
1. 调整原有 `gather_paths()` 函数
2. 确保所有现有测试通过
3. 更新 `__init__.py` 导出

### 阶段 4：测试和文档
1. 编写单元测试覆盖所有新功能
2. 性能基准测试
3. 更新文档和示例

## 测试策略

### 单元测试
- 模式匹配测试（各种 glob 模式）
- 排除规则测试
- 排序功能测试（所有排序键）
- 属性过滤测试
- 深度控制测试
- 错误处理测试

### 性能测试
- 对比新旧实现在大目录树（10,000+ 文件）上的性能
- 测试不同过滤器组合的性能影响
- 内存使用测试（迭代器 vs 列表）

### 集成测试
- 混合使用多种功能的复杂场景
- 边界情况（空目录、权限错误、符号链接等）
- 向后兼容性测试（确保现有代码不受影响）

## 风险和缓解

### 风险 1：性能回退
- **缓解**: 保持原函数的快速路径，仅在需要高级功能时使用新类
- **验证**: 性能基准测试确保简单场景不变慢

### 风险 2：API 复杂度
- **缓解**: 提供清晰的文档和示例，简单场景仍然简单
- **验证**: 代码审查确保 API 直观易用

### 风险 3：向后兼容性破坏
- **缓解**: 保持原有函数签名完全不变
- **验证**: 运行所有现有测试，确保通过

## 成功标准

1. ✅ 所有现有测试通过（向后兼容）
2. ✅ 新功能单元测试覆盖率 > 90%
3. ✅ 大目录扫描性能提升 > 20%
4. ✅ 支持所有计划的功能（模式、排序、过滤、进度）
5. ✅ 文档和示例完整清晰

## 未来扩展

可能的未来增强（不在本次范围内）：
- 并行扫描支持（使用多线程/进程）
- 缓存机制（记住已扫描的目录）
- 更高级的模式匹配（正则表达式）
- 符号链接循环检测
- 排除规则文件支持（如读取 .gitignore）
