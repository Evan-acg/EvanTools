# Registry 模块增强 实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** 为 registry 模块添加命令发现、执行审计和性能监控功能，提供 CLI 仪表板支持。

**架构:** 采用四层分离架构（发现层、追踪层、存储层、可视化层），通过可选的 `RegistryManager` 提供增强功能，原有 API 完全保持不变。核心采用内存存储，支持后续扩展到持久化存储。

**技术栈:** Python 3.8+, dataclasses, inspect, datetime, typer (现有依赖)

---

## Phase 1: 核心基础设施

### Task 1: 创建发现层目录结构和元数据数据类

**文件:**

- Create: `src/evan_tools/registry/discovery/__init__.py`
- Create: `src/evan_tools/registry/discovery/metadata.py`
- Test: `tests/registry/discovery/__init__.py`
- Test: `tests/registry/test_discovery_metadata.py`

**Step 1: 编写元数据数据类的单元测试**

```python
# tests/registry/test_discovery_metadata.py
import inspect
from dataclasses import dataclass
from src.evan_tools.registry.discovery.metadata import CommandMetadata


def test_command_metadata_creation():
    """测试 CommandMetadata 创建"""
    def sample_func(x: int, y: str) -> str:
        """Sample function."""
        return str(x) + y
    
    sig = inspect.signature(sample_func)
    metadata = CommandMetadata(
        name="sample",
        group="test",
        func=sample_func,
        docstring="Sample function.",
        module="test_module",
        signature=sig
    )
    
    assert metadata.name == "sample"
    assert metadata.group == "test"
    assert metadata.func is sample_func
    assert metadata.docstring == "Sample function."
    assert metadata.module == "test_module"
    assert isinstance(metadata.signature, inspect.Signature)


def test_command_metadata_without_group():
    """测试没有分组的元数据"""
    def func():
        pass
    
    sig = inspect.signature(func)
    metadata = CommandMetadata(
        name="cmd",
        group=None,
        func=func,
        docstring=None,
        module="mod",
        signature=sig
    )
    
    assert metadata.group is None
```

**Step 2: 运行测试，验证失败**

```bash
cd d:\Work\Spaces\Common\CommonPython\EvanTools
python -m pytest tests/registry/test_discovery_metadata.py -v
```

预期: FAIL - "No module named 'src.evan_tools.registry.discovery'"

**Step 3: 实现元数据数据类**

```python
# src/evan_tools/registry/discovery/metadata.py
import inspect
import typing as t
from dataclasses import dataclass


@dataclass
class CommandMetadata:
    """命令元数据信息"""
    name: str
    group: str | None
    func: t.Callable[..., None]
    docstring: str | None
    module: str
    signature: inspect.Signature
    
    def __post_init__(self) -> None:
        """验证数据有效性"""
        if not self.name:
            raise ValueError("Command name cannot be empty")
        if not self.module:
            raise ValueError("Module cannot be empty")
```

```python
# src/evan_tools/registry/discovery/__init__.py
from .metadata import CommandMetadata

__all__ = ["CommandMetadata"]
```

```python
# tests/registry/discovery/__init__.py
# 空文件
```

**Step 4: 运行测试，验证通过**

```bash
cd d:\Work\Spaces\Common\CommonPython\EvanTools
python -m pytest tests/registry/test_discovery_metadata.py -v
```

预期: PASS

**Step 5: 提交**

```bash
git add -A && git commit -m "feat(registry/discovery): 添加命令元数据数据类"
```

---

### Task 2: 实现 CommandInspector（命令检查器）

**文件:**

- Create: `src/evan_tools/registry/discovery/inspector.py`
- Test: `tests/registry/test_discovery_inspector.py`

**Step 1: 编写 CommandInspector 的单元测试**

```python
# tests/registry/test_discovery_inspector.py
import inspect
from src.evan_tools.registry.discovery.inspector import CommandInspector


def test_extract_metadata_from_function():
    """测试从函数提取元数据"""
    def test_command(x: int, y: str) -> None:
        """Test command."""
        pass
    
    inspector = CommandInspector()
    metadata = inspector.extract_metadata(
        name="test_cmd",
        func=test_command,
        group="test_group",
        module="test_module"
    )
    
    assert metadata.name == "test_cmd"
    assert metadata.group == "test_group"
    assert metadata.func is test_command
    assert metadata.docstring == "Test command."
    assert metadata.module == "test_module"
    assert isinstance(metadata.signature, inspect.Signature)


def test_extract_metadata_without_docstring():
    """测试提取没有文档字符串的函数"""
    def cmd():
        pass
    
    inspector = CommandInspector()
    metadata = inspector.extract_metadata("cmd", cmd, None, "mod")
    
    assert metadata.docstring is None


def test_extract_docstring_single_line():
    """测试提取单行文档字符串"""
    def cmd():
        """Single line."""
        pass
    
    inspector = CommandInspector()
    metadata = inspector.extract_metadata("cmd", cmd, None, "mod")
    
    assert metadata.docstring == "Single line."


def test_extract_docstring_multiline():
    """测试提取多行文档字符串（取第一行）"""
    def cmd():
        """First line.
        
        More details here.
        """
        pass
    
    inspector = CommandInspector()
    metadata = inspector.extract_metadata("cmd", cmd, None, "mod")
    
    assert metadata.docstring == "First line."
```

**Step 2: 运行测试，验证失败**

```bash
cd d:\Work\Spaces\Common\CommonPython\EvanTools
python -m pytest tests/registry/test_discovery_inspector.py -v
```

预期: FAIL - "No module named 'src.evan_tools.registry.discovery.inspector'"

**Step 3: 实现 CommandInspector**

```python
# src/evan_tools/registry/discovery/inspector.py
import inspect
import typing as t
from .metadata import CommandMetadata


class CommandInspector:
    """提取和分析命令元数据的检查器"""
    
    def extract_metadata(
        self,
        name: str,
        func: t.Callable[..., None],
        group: str | None,
        module: str,
    ) -> CommandMetadata:
        """从函数提取元数据"""
        signature = inspect.signature(func)
        docstring = self._extract_first_line_of_docstring(func)
        
        return CommandMetadata(
            name=name,
            group=group,
            func=func,
            docstring=docstring,
            module=module,
            signature=signature,
        )
    
    @staticmethod
    def _extract_first_line_of_docstring(func: t.Callable[..., None]) -> str | None:
        """提取函数文档字符串的第一行"""
        doc = inspect.getdoc(func)
        if not doc:
            return None
        
        first_line = doc.split('\n')[0].strip()
        return first_line if first_line else None
```

更新 `__init__.py`:

```python
# src/evan_tools/registry/discovery/__init__.py
from .metadata import CommandMetadata
from .inspector import CommandInspector

__all__ = ["CommandMetadata", "CommandInspector"]
```

**Step 4: 运行测试，验证通过**

```bash
cd d:\Work\Spaces\Common\CommonPython\EvanTools
python -m pytest tests/registry/test_discovery_inspector.py -v
```

预期: PASS

**Step 5: 提交**

```bash
git add -A && git commit -m "feat(registry/discovery): 实现命令检查器 CommandInspector"
```

---

### Task 3: 实现 CommandIndex（命令索引）

**文件:**

- Create: `src/evan_tools/registry/discovery/index.py`
- Test: `tests/registry/test_discovery_index.py`

**Step 1: 编写 CommandIndex 的单元测试**

```python
# tests/registry/test_discovery_index.py
from src.evan_tools.registry.discovery.index import CommandIndex
from src.evan_tools.registry.discovery.metadata import CommandMetadata
from src.evan_tools.registry.main import get_registry
import inspect


def test_command_index_initialization():
    """测试索引初始化"""
    index = CommandIndex()
    assert index is not None


def test_get_all_commands():
    """测试获取所有命令"""
    index = CommandIndex()
    # 这个测试需要有已注册的命令
    # 暂时直接检查返回类型
    commands = index.get_all_commands()
    assert isinstance(commands, list)


def test_get_commands_by_group():
    """测试按组获取命令"""
    index = CommandIndex()
    commands = index.get_commands_by_group("file")
    assert isinstance(commands, list)


def test_search_commands():
    """测试搜索命令"""
    index = CommandIndex()
    results = index.search_commands("file")
    assert isinstance(results, list)


def test_get_command_tree():
    """测试获取命令树"""
    index = CommandIndex()
    tree = index.get_command_tree()
    assert isinstance(tree, dict)


def test_get_command_docs():
    """测试获取命令文档"""
    index = CommandIndex()
    docs = index.get_command_docs()
    assert isinstance(docs, str)
```

**Step 2: 运行测试，验证失败**

```bash
cd d:\Work\Spaces\Common\CommonPython\EvanTools
python -m pytest tests/registry/test_discovery_index.py -v
```

预期: FAIL - "No module named 'src.evan_tools.registry.discovery.index'"

**Step 3: 实现 CommandIndex**

```python
# src/evan_tools/registry/discovery/index.py
import typing as t
from .metadata import CommandMetadata
from .inspector import CommandInspector
from ..main import get_registry


class CommandIndex:
    """构建和查询命令索引"""
    
    def __init__(self) -> None:
        """初始化索引"""
        self._inspector = CommandInspector()
        self._metadata_cache: list[CommandMetadata] | None = None
    
    def get_all_commands(self) -> list[CommandMetadata]:
        """获取所有已注册的命令"""
        if self._metadata_cache is None:
            self._rebuild_cache()
        return list(self._metadata_cache)
    
    def get_commands_by_group(self, group: str) -> list[CommandMetadata]:
        """按组名获取命令"""
        all_commands = self.get_all_commands()
        return [cmd for cmd in all_commands if cmd.group == group]
    
    def get_command_tree(self) -> dict[str | None, list[str]]:
        """获取命令树结构（按组组织）"""
        tree: dict[str | None, list[str]] = {}
        for cmd in self.get_all_commands():
            group = cmd.group or "_ungrouped"
            if group not in tree:
                tree[group] = []
            tree[group].append(cmd.name)
        return tree
    
    def search_commands(self, query: str) -> list[CommandMetadata]:
        """搜索命令（按名称或文档）"""
        query_lower = query.lower()
        all_commands = self.get_all_commands()
        results = []
        
        for cmd in all_commands:
            if query_lower in cmd.name.lower():
                results.append(cmd)
            elif cmd.docstring and query_lower in cmd.docstring.lower():
                results.append(cmd)
        
        return results
    
    def get_command_docs(self) -> str:
        """生成命令文档（Markdown 格式）"""
        lines = ["# 命令列表\n"]
        
        tree = self.get_command_tree()
        for group in sorted(tree.keys()):
            if group == "_ungrouped":
                lines.append("## 全局命令\n")
            else:
                lines.append(f"## 组: {group}\n")
            
            for cmd_name in sorted(tree[group]):
                cmd = next(c for c in self.get_all_commands() if c.name == cmd_name)
                doc = cmd.docstring or "无文档"
                lines.append(f"- **{cmd_name}**: {doc}\n")
            
            lines.append("")
        
        return "".join(lines)
    
    def _rebuild_cache(self) -> None:
        """重建元数据缓存"""
        self._metadata_cache = []
        registry = get_registry()
        
        for group, name, func in registry:
            metadata = self._inspector.extract_metadata(
                name=name,
                func=func,
                group=group,
                module=func.__module__,
            )
            self._metadata_cache.append(metadata)
```

更新 `__init__.py`:

```python
# src/evan_tools/registry/discovery/__init__.py
from .metadata import CommandMetadata
from .inspector import CommandInspector
from .index import CommandIndex

__all__ = ["CommandMetadata", "CommandInspector", "CommandIndex"]
```

**Step 4: 运行测试，验证通过**

```bash
cd d:\Work\Spaces\Common\CommonPython\EvanTools
python -m pytest tests/registry/test_discovery_index.py -v
```

预期: PASS

**Step 5: 提交**

```bash
git add -A && git commit -m "feat(registry/discovery): 实现命令索引 CommandIndex"
```

---

### Task 4: 创建追踪层和存储层数据类

**文件:**

- Create: `src/evan_tools/registry/tracking/__init__.py`
- Create: `src/evan_tools/registry/tracking/models.py`
- Create: `src/evan_tools/registry/storage/__init__.py`
- Test: `tests/registry/test_tracking_models.py`

**Step 1: 编写追踪数据类的单元测试**

```python
# tests/registry/test_tracking_models.py
from datetime import datetime
from src.evan_tools.registry.tracking.models import ExecutionRecord, PerformanceStats


def test_execution_record_creation():
    """测试执行记录创建"""
    now = datetime.now()
    record = ExecutionRecord(
        command_name="test_cmd",
        group="test",
        timestamp=now,
        duration_ms=123.45,
        success=True,
        error=None,
        args=("arg1", "arg2"),
        kwargs={"key": "value"},
    )
    
    assert record.command_name == "test_cmd"
    assert record.group == "test"
    assert record.timestamp == now
    assert record.duration_ms == 123.45
    assert record.success is True
    assert record.error is None
    assert record.args == ("arg1", "arg2")
    assert record.kwargs == {"key": "value"}


def test_execution_record_with_error():
    """测试包含错误的执行记录"""
    now = datetime.now()
    record = ExecutionRecord(
        command_name="fail_cmd",
        group=None,
        timestamp=now,
        duration_ms=50.0,
        success=False,
        error="ValueError: invalid input",
        args=(),
        kwargs={},
    )
    
    assert record.success is False
    assert record.error == "ValueError: invalid input"


def test_performance_stats_creation():
    """测试性能统计创建"""
    stats = PerformanceStats(
        command_name="cmd",
        call_count=10,
        total_duration_ms=1000.0,
        avg_duration_ms=100.0,
        min_duration_ms=50.0,
        max_duration_ms=200.0,
        error_count=1,
    )
    
    assert stats.command_name == "cmd"
    assert stats.call_count == 10
    assert stats.avg_duration_ms == 100.0
```

**Step 2: 运行测试，验证失败**

```bash
cd d:\Work\Spaces\Common\CommonPython\EvanTools
python -m pytest tests/registry/test_tracking_models.py -v
```

预期: FAIL

**Step 3: 实现数据类**

```python
# src/evan_tools/registry/tracking/models.py
import typing as t
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ExecutionRecord:
    """命令执行审计记录"""
    command_name: str
    group: str | None
    timestamp: datetime
    duration_ms: float
    success: bool
    error: str | None
    args: tuple[t.Any, ...]
    kwargs: dict[str, t.Any]


@dataclass
class PerformanceStats:
    """命令性能统计"""
    command_name: str
    call_count: int
    total_duration_ms: float
    avg_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    error_count: int
```

```python
# src/evan_tools/registry/tracking/__init__.py
from .models import ExecutionRecord, PerformanceStats

__all__ = ["ExecutionRecord", "PerformanceStats"]
```

```python
# src/evan_tools/registry/storage/__init__.py
# 暂时为空，后续添加存储类
```

**Step 4: 运行测试，验证通过**

```bash
cd d:\Work\Spaces\Common\CommonPython\EvanTools
python -m pytest tests/registry/test_tracking_models.py -v
```

预期: PASS

**Step 5: 提交**

```bash
git add -A && git commit -m "feat(registry): 添加执行记录和性能统计数据类"
```

---

## Phase 2: 执行追踪和监控

### Task 5: 实现内存存储

**文件:**

- Create: `src/evan_tools/registry/storage/memory_store.py`
- Test: `tests/registry/test_storage_memory.py`

**Step 1: 编写内存存储的单元测试**

```python
# tests/registry/test_storage_memory.py
from src.evan_tools.registry.storage.memory_store import InMemoryStore
from src.evan_tools.registry.tracking.models import ExecutionRecord, PerformanceStats
from datetime import datetime


def test_memory_store_add_record():
    """测试添加执行记录"""
    store = InMemoryStore()
    record = ExecutionRecord(
        command_name="cmd",
        group=None,
        timestamp=datetime.now(),
        duration_ms=100.0,
        success=True,
        error=None,
        args=(),
        kwargs={},
    )
    
    store.add_record(record)
    records = store.get_all_records()
    
    assert len(records) == 1
    assert records[0].command_name == "cmd"


def test_memory_store_get_recent_records():
    """测试获取最近的记录"""
    store = InMemoryStore()
    
    for i in range(5):
        record = ExecutionRecord(
            command_name=f"cmd{i}",
            group=None,
            timestamp=datetime.now(),
            duration_ms=100.0,
            success=True,
            error=None,
            args=(),
            kwargs={},
        )
        store.add_record(record)
    
    recent = store.get_recent_records(limit=3)
    assert len(recent) == 3


def test_memory_store_clear():
    """测试清空存储"""
    store = InMemoryStore()
    record = ExecutionRecord(
        command_name="cmd",
        group=None,
        timestamp=datetime.now(),
        duration_ms=100.0,
        success=True,
        error=None,
        args=(),
        kwargs={},
    )
    
    store.add_record(record)
    assert len(store.get_all_records()) == 1
    
    store.clear()
    assert len(store.get_all_records()) == 0


def test_memory_store_calculate_stats():
    """测试计算性能统计"""
    store = InMemoryStore()
    
    for duration in [50.0, 100.0, 150.0]:
        record = ExecutionRecord(
            command_name="cmd",
            group=None,
            timestamp=datetime.now(),
            duration_ms=duration,
            success=True,
            error=None,
            args=(),
            kwargs={},
        )
        store.add_record(record)
    
    stats = store.calculate_stats("cmd")
    
    assert stats.command_name == "cmd"
    assert stats.call_count == 3
    assert stats.total_duration_ms == 300.0
    assert stats.avg_duration_ms == 100.0
    assert stats.min_duration_ms == 50.0
    assert stats.max_duration_ms == 150.0
```

**Step 2: 运行测试，验证失败**

```bash
cd d:\Work\Spaces\Common\CommonPython\EvanTools
python -m pytest tests/registry/test_storage_memory.py -v
```

预期: FAIL

**Step 3: 实现内存存储**

```python
# src/evan_tools/registry/storage/memory_store.py
import typing as t
from collections import defaultdict
from ..tracking.models import ExecutionRecord, PerformanceStats


class InMemoryStore:
    """内存存储实现"""
    
    def __init__(self, max_records: int = 10000) -> None:
        """初始化存储"""
        self._records: list[ExecutionRecord] = []
        self._max_records = max_records
        self._stats_cache: dict[str, PerformanceStats] = {}
    
    def add_record(self, record: ExecutionRecord) -> None:
        """添加执行记录"""
        self._records.append(record)
        
        # 限制记录数量，防止内存溢出
        if len(self._records) > self._max_records:
            self._records = self._records[-self._max_records:]
        
        # 更新统计缓存
        self._update_stats_cache(record)
    
    def get_all_records(self) -> list[ExecutionRecord]:
        """获取所有记录"""
        return list(self._records)
    
    def get_recent_records(self, limit: int = 100) -> list[ExecutionRecord]:
        """获取最近的记录"""
        return list(self._records[-limit:])
    
    def get_records_by_command(self, command_name: str) -> list[ExecutionRecord]:
        """按命令名获取记录"""
        return [r for r in self._records if r.command_name == command_name]
    
    def clear(self) -> None:
        """清空存储"""
        self._records.clear()
        self._stats_cache.clear()
    
    def calculate_stats(self, command_name: str) -> PerformanceStats | None:
        """计算命令的性能统计"""
        records = self.get_records_by_command(command_name)
        
        if not records:
            return None
        
        durations = [r.duration_ms for r in records]
        error_count = sum(1 for r in records if not r.success)
        
        return PerformanceStats(
            command_name=command_name,
            call_count=len(records),
            total_duration_ms=sum(durations),
            avg_duration_ms=sum(durations) / len(durations),
            min_duration_ms=min(durations),
            max_duration_ms=max(durations),
            error_count=error_count,
        )
    
    def get_all_stats(self) -> dict[str, PerformanceStats]:
        """获取所有命令的统计"""
        command_names = set(r.command_name for r in self._records)
        return {
            cmd: self.calculate_stats(cmd)
            for cmd in command_names
            if self.calculate_stats(cmd) is not None
        }
    
    def _update_stats_cache(self, record: ExecutionRecord) -> None:
        """更新统计缓存"""
        stats = self.calculate_stats(record.command_name)
        if stats:
            self._stats_cache[record.command_name] = stats
```

更新 `__init__.py`:

```python
# src/evan_tools/registry/storage/__init__.py
from .memory_store import InMemoryStore

__all__ = ["InMemoryStore"]
```

**Step 4: 运行测试，验证通过**

```bash
cd d:\Work\Spaces\Common\CommonPython\EvanTools
python -m pytest tests/registry/test_storage_memory.py -v
```

预期: PASS

**Step 5: 提交**

```bash
git add -A && git commit -m "feat(registry/storage): 实现内存存储 InMemoryStore"
```

---

### Task 6: 实现 ExecutionTracker（执行追踪器）

**文件:**

- Create: `src/evan_tools/registry/tracking/tracker.py`
- Test: `tests/registry/test_tracking_tracker.py`

**Step 1: 编写 ExecutionTracker 的单元测试**

```python
# tests/registry/test_tracking_tracker.py
from src.evan_tools.registry.tracking.tracker import ExecutionTracker
from src.evan_tools.registry.storage.memory_store import InMemoryStore
from datetime import datetime


def test_tracker_initialization():
    """测试追踪器初始化"""
    tracker = ExecutionTracker()
    assert tracker is not None
    assert not tracker.is_tracking()


def test_tracker_enable_disable():
    """测试启用和禁用追踪"""
    tracker = ExecutionTracker()
    
    tracker.start_tracking()
    assert tracker.is_tracking()
    
    tracker.stop_tracking()
    assert not tracker.is_tracking()


def test_tracker_record_execution():
    """测试记录执行"""
    tracker = ExecutionTracker()
    tracker.start_tracking()
    
    tracker.record_execution(
        command_name="test_cmd",
        group="test",
        duration_ms=100.0,
        success=True,
        error=None,
        args=(),
        kwargs={},
    )
    
    history = tracker.get_execution_history()
    assert len(history) == 1
    assert history[0].command_name == "test_cmd"


def test_tracker_get_history():
    """测试获取执行历史"""
    tracker = ExecutionTracker()
    tracker.start_tracking()
    
    for i in range(5):
        tracker.record_execution(
            command_name=f"cmd{i}",
            group=None,
            duration_ms=100.0,
            success=True,
            error=None,
            args=(),
            kwargs={},
        )
    
    history = tracker.get_execution_history(limit=3)
    assert len(history) == 3


def test_tracker_clear_history():
    """测试清空历史"""
    tracker = ExecutionTracker()
    tracker.start_tracking()
    
    tracker.record_execution(
        command_name="cmd",
        group=None,
        duration_ms=100.0,
        success=True,
        error=None,
        args=(),
        kwargs={},
    )
    
    assert len(tracker.get_execution_history()) == 1
    
    tracker.clear_history()
    assert len(tracker.get_execution_history()) == 0
```

**Step 2: 运行测试，验证失败**

```bash
cd d:\Work\Spaces\Common\CommonPython\EvanTools
python -m pytest tests/registry/test_tracking_tracker.py -v
```

预期: FAIL

**Step 3: 实现 ExecutionTracker**

```python
# src/evan_tools/registry/tracking/tracker.py
import typing as t
from datetime import datetime
from ..storage.memory_store import InMemoryStore
from .models import ExecutionRecord


class ExecutionTracker:
    """命令执行追踪器"""
    
    def __init__(self, store: InMemoryStore | None = None) -> None:
        """初始化追踪器"""
        self._store = store or InMemoryStore()
        self._is_tracking = False
    
    def start_tracking(self) -> None:
        """启用追踪"""
        self._is_tracking = True
    
    def stop_tracking(self) -> None:
        """禁用追踪"""
        self._is_tracking = False
    
    def is_tracking(self) -> bool:
        """检查是否启用追踪"""
        return self._is_tracking
    
    def record_execution(
        self,
        command_name: str,
        group: str | None,
        duration_ms: float,
        success: bool,
        error: str | None,
        args: tuple[t.Any, ...],
        kwargs: dict[str, t.Any],
    ) -> None:
        """记录命令执行"""
        if not self._is_tracking:
            return
        
        record = ExecutionRecord(
            command_name=command_name,
            group=group,
            timestamp=datetime.now(),
            duration_ms=duration_ms,
            success=success,
            error=error,
            args=args,
            kwargs=kwargs,
        )
        
        self._store.add_record(record)
    
    def get_execution_history(self, limit: int = 100) -> list[ExecutionRecord]:
        """获取执行历史"""
        return self._store.get_recent_records(limit=limit)
    
    def clear_history(self) -> None:
        """清空历史"""
        self._store.clear()
    
    def get_store(self) -> InMemoryStore:
        """获取存储实例"""
        return self._store
```

更新 `__init__.py`:

```python
# src/evan_tools/registry/tracking/__init__.py
from .models import ExecutionRecord, PerformanceStats
from .tracker import ExecutionTracker

__all__ = ["ExecutionRecord", "PerformanceStats", "ExecutionTracker"]
```

**Step 4: 运行测试，验证通过**

```bash
cd d:\Work\Spaces\Common\CommonPython\EvanTools
python -m pytest tests/registry/test_tracking_tracker.py -v
```

预期: PASS

**Step 5: 提交**

```bash
git add -A && git commit -m "feat(registry/tracking): 实现执行追踪器 ExecutionTracker"
```

---

### Task 7: 实现 PerformanceMonitor（性能监控器）

**文件:**

- Create: `src/evan_tools/registry/tracking/monitor.py`
- Test: `tests/registry/test_tracking_monitor.py`

**Step 1: 编写 PerformanceMonitor 的单元测试**

```python
# tests/registry/test_tracking_monitor.py
from src.evan_tools.registry.tracking.monitor import PerformanceMonitor
from src.evan_tools.registry.tracking.tracker import ExecutionTracker


def test_monitor_get_stats():
    """测试获取性能统计"""
    tracker = ExecutionTracker()
    monitor = PerformanceMonitor(tracker)
    
    tracker.start_tracking()
    for i in range(3):
        tracker.record_execution(
            command_name="cmd",
            group=None,
            duration_ms=100.0 + i * 10,
            success=True,
            error=None,
            args=(),
            kwargs={},
        )
    
    stats = monitor.get_stats("cmd")
    assert stats is not None
    assert stats.call_count == 3
    assert stats.command_name == "cmd"


def test_monitor_get_stats_not_found():
    """测试获取不存在的命令统计"""
    tracker = ExecutionTracker()
    monitor = PerformanceMonitor(tracker)
    
    stats = monitor.get_stats("nonexistent")
    assert stats is None


def test_monitor_get_all_stats():
    """测试获取所有统计"""
    tracker = ExecutionTracker()
    monitor = PerformanceMonitor(tracker)
    
    tracker.start_tracking()
    for cmd_idx in range(2):
        for i in range(3):
            tracker.record_execution(
                command_name=f"cmd{cmd_idx}",
                group=None,
                duration_ms=100.0,
                success=True,
                error=None,
                args=(),
                kwargs={},
            )
    
    all_stats = monitor.get_all_stats()
    assert len(all_stats) == 2
    assert "cmd0" in all_stats
    assert "cmd1" in all_stats
```

**Step 2: 运行测试，验证失败**

```bash
cd d:\Work\Spaces\Common\CommonPython\EvanTools
python -m pytest tests/registry/test_tracking_monitor.py -v
```

预期: FAIL

**Step 3: 实现 PerformanceMonitor**

```python
# src/evan_tools/registry/tracking/monitor.py
from .tracker import ExecutionTracker
from .models import PerformanceStats


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, tracker: ExecutionTracker) -> None:
        """初始化监控器"""
        self._tracker = tracker
    
    def get_stats(self, command_name: str) -> PerformanceStats | None:
        """获取指定命令的性能统计"""
        return self._tracker.get_store().calculate_stats(command_name)
    
    def get_all_stats(self) -> dict[str, PerformanceStats]:
        """获取所有命令的性能统计"""
        return self._tracker.get_store().get_all_stats()
    
    def reset_stats(self) -> None:
        """重置所有统计"""
        self._tracker.clear_history()
```

更新 `__init__.py`:

```python
# src/evan_tools/registry/tracking/__init__.py
from .models import ExecutionRecord, PerformanceStats
from .tracker import ExecutionTracker
from .monitor import PerformanceMonitor

__all__ = ["ExecutionRecord", "PerformanceStats", "ExecutionTracker", "PerformanceMonitor"]
```

**Step 4: 运行测试，验证通过**

```bash
cd d:\Work\Spaces\Common\CommonPython\EvanTools
python -m pytest tests/registry/test_tracking_monitor.py -v
```

预期: PASS

**Step 5: 提交**

```bash
git add -A && git commit -m "feat(registry/tracking): 实现性能监控器 PerformanceMonitor"
```

---

## Phase 3: 可视化层

### Task 8: 实现仪表板（Dashboard）

**文件:**

- Create: `src/evan_tools/registry/dashboard/__init__.py`
- Create: `src/evan_tools/registry/dashboard/formatter.py`
- Create: `src/evan_tools/registry/dashboard/aggregator.py`
- Create: `src/evan_tools/registry/dashboard/dashboard.py`
- Test: `tests/registry/test_dashboard.py`

**Step 1: 编写仪表板的单元测试**

```python
# tests/registry/test_dashboard.py
from src.evan_tools.registry.dashboard.dashboard import RegistryDashboard
from src.evan_tools.registry.discovery.index import CommandIndex
from src.evan_tools.registry.tracking.tracker import ExecutionTracker


def test_dashboard_initialization():
    """测试仪表板初始化"""
    tracker = ExecutionTracker()
    index = CommandIndex()
    dashboard = RegistryDashboard(tracker, index)
    
    assert dashboard is not None


def test_dashboard_show_command_tree():
    """测试显示命令树"""
    tracker = ExecutionTracker()
    index = CommandIndex()
    dashboard = RegistryDashboard(tracker, index)
    
    output = dashboard.show_command_tree()
    assert isinstance(output, str)


def test_dashboard_show_execution_history():
    """测试显示执行历史"""
    tracker = ExecutionTracker()
    index = CommandIndex()
    dashboard = RegistryDashboard(tracker, index)
    
    tracker.start_tracking()
    tracker.record_execution(
        command_name="cmd",
        group="test",
        duration_ms=100.0,
        success=True,
        error=None,
        args=(),
        kwargs={},
    )
    
    output = dashboard.show_execution_history()
    assert isinstance(output, str)
    assert "cmd" in output


def test_dashboard_show_performance_stats():
    """测试显示性能统计"""
    tracker = ExecutionTracker()
    index = CommandIndex()
    dashboard = RegistryDashboard(tracker, index)
    
    tracker.start_tracking()
    for i in range(3):
        tracker.record_execution(
            command_name="cmd",
            group=None,
            duration_ms=100.0 + i * 10,
            success=True,
            error=None,
            args=(),
            kwargs={},
        )
    
    output = dashboard.show_performance_stats()
    assert isinstance(output, str)
```

**Step 2: 运行测试，验证失败**

```bash
cd d:\Work\Spaces\Common\CommonPython\EvanTools
python -m pytest tests/registry/test_dashboard.py -v
```

预期: FAIL

**Step 3: 实现表格格式化器**

```python
# src/evan_tools/registry/dashboard/formatter.py
import typing as t
from dataclasses import dataclass


@dataclass
class TableConfig:
    """表格配置"""
    padding: int = 2
    border_char: str = "-"
    col_sep: str = "|"


class TableFormatter:
    """表格格式化器"""
    
    def __init__(self, config: TableConfig | None = None) -> None:
        """初始化格式化器"""
        self.config = config or TableConfig()
    
    def format_table(
        self,
        headers: list[str],
        rows: list[list[str]],
    ) -> str:
        """格式化表格"""
        if not headers or not rows:
            return ""
        
        # 计算列宽
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # 添加填充
        col_widths = [w + self.config.padding * 2 for w in col_widths]
        
        # 构建表格
        lines = []
        
        # 顶部边界
        lines.append(self._build_border(col_widths))
        
        # 表头
        lines.append(self._build_row(headers, col_widths))
        
        # 表头下边界
        lines.append(self._build_border(col_widths))
        
        # 数据行
        for row in rows:
            lines.append(self._build_row(row, col_widths))
        
        # 底部边界
        lines.append(self._build_border(col_widths))
        
        return "\n".join(lines)
    
    def _build_border(self, col_widths: list[int]) -> str:
        """构建边界行"""
        parts = []
        for width in col_widths:
            parts.append(self.config.border_char * width)
        return self.config.col_sep.join(parts)
    
    def _build_row(self, cells: list[str], col_widths: list[int]) -> str:
        """构建数据行"""
        parts = []
        for i, cell in enumerate(cells):
            padding_left = self.config.padding
            padding_right = col_widths[i] - len(str(cell)) - padding_left
            padded = " " * padding_left + str(cell) + " " * padding_right
            parts.append(padded)
        return self.config.col_sep.join(parts)
```

**Step 4: 实现数据聚合器**

```python
# src/evan_tools/registry/dashboard/aggregator.py
import typing as t
from datetime import datetime
from ..tracking.tracker import ExecutionTracker
from ..tracking.models import ExecutionRecord, PerformanceStats


class StatsAggregator:
    """数据聚合和统计"""
    
    def __init__(self, tracker: ExecutionTracker) -> None:
        """初始化聚合器"""
        self._tracker = tracker
    
    def get_execution_records_formatted(self, limit: int = 20) -> list[list[str]]:
        """获取格式化的执行记录"""
        records = self._tracker.get_execution_history(limit=limit)
        rows = []
        
        for record in records:
            status = "✓" if record.success else "✗"
            timestamp = record.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            error = record.error or "-"
            
            rows.append([
                timestamp,
                record.group or "-",
                record.command_name,
                status,
                f"{record.duration_ms:.2f}ms",
                error if not record.success else "-",
            ])
        
        return rows
    
    def get_performance_stats_formatted(self) -> list[list[str]]:
        """获取格式化的性能统计"""
        store = self._tracker.get_store()
        all_stats = store.get_all_stats()
        rows = []
        
        for cmd_name in sorted(all_stats.keys()):
            stats = all_stats[cmd_name]
            rows.append([
                stats.command_name,
                str(stats.call_count),
                f"{stats.avg_duration_ms:.2f}ms",
                f"{stats.min_duration_ms:.2f}ms",
                f"{stats.max_duration_ms:.2f}ms",
                str(stats.error_count),
            ])
        
        return rows
    
    def get_command_tree_formatted(self, tree: dict[str | None, list[str]]) -> list[list[str]]:
        """获取格式化的命令树"""
        rows = []
        
        for group in sorted(tree.keys()):
            group_name = group if group != "_ungrouped" else "（全局）"
            commands = sorted(tree[group])
            
            for i, cmd in enumerate(commands):
                if i == 0:
                    rows.append([group_name, cmd])
                else:
                    rows.append(["", cmd])
        
        return rows
```

**Step 5: 实现仪表板**

```python
# src/evan_tools/registry/dashboard/dashboard.py
from ..discovery.index import CommandIndex
from ..tracking.tracker import ExecutionTracker
from .formatter import TableFormatter
from .aggregator import StatsAggregator


class RegistryDashboard:
    """registry 仪表板"""
    
    def __init__(
        self,
        tracker: ExecutionTracker,
        index: CommandIndex,
    ) -> None:
        """初始化仪表板"""
        self._tracker = tracker
        self._index = index
        self._formatter = TableFormatter()
        self._aggregator = StatsAggregator(tracker)
    
    def show_command_tree(self) -> str:
        """显示命令树"""
        tree = self._index.get_command_tree()
        rows = self._aggregator.get_command_tree_formatted(tree)
        
        if not rows:
            return "【没有已注册的命令】"
        
        output = "命令树\n"
        output += self._formatter.format_table(["分组", "命令"], rows)
        return output
    
    def show_execution_history(self, limit: int = 20) -> str:
        """显示执行历史"""
        rows = self._aggregator.get_execution_records_formatted(limit=limit)
        
        if not rows:
            return "【没有执行记录】"
        
        output = f"执行历史 (最近 {limit} 条)\n"
        headers = ["时间", "分组", "命令", "结果", "耗时", "错误"]
        output += self._formatter.format_table(headers, rows)
        return output
    
    def show_performance_stats(self) -> str:
        """显示性能统计"""
        rows = self._aggregator.get_performance_stats_formatted()
        
        if not rows:
            return "【没有性能数据】"
        
        output = "性能统计\n"
        headers = ["命令", "调用次数", "平均耗时", "最小耗时", "最大耗时", "错误次数"]
        output += self._formatter.format_table(headers, rows)
        return output
    
    def show_summary(self) -> str:
        """显示综合统计概览"""
        lines = []
        
        lines.append("=" * 50)
        lines.append("Registry 仪表板概览")
        lines.append("=" * 50)
        lines.append("")
        
        # 命令统计
        all_commands = self._index.get_all_commands()
        lines.append(f"已注册命令数: {len(all_commands)}")
        
        # 执行统计
        all_records = self._tracker.get_execution_history(limit=10000)
        lines.append(f"总执行次数: {len(all_records)}")
        
        if all_records:
            successful = sum(1 for r in all_records if r.success)
            lines.append(f"成功次数: {successful}")
            lines.append(f"失败次数: {len(all_records) - successful}")
        
        lines.append("")
        return "\n".join(lines)
```

更新 `__init__.py`:

```python
# src/evan_tools/registry/dashboard/__init__.py
from .formatter import TableFormatter
from .aggregator import StatsAggregator
from .dashboard import RegistryDashboard

__all__ = ["TableFormatter", "StatsAggregator", "RegistryDashboard"]
```

**Step 6: 运行测试，验证通过**

```bash
cd d:\Work\Spaces\Common\CommonPython\EvanTools
python -m pytest tests/registry/test_dashboard.py -v
```

预期: PASS

**Step 7: 提交**

```bash
git add -A && git commit -m "feat(registry/dashboard): 实现仪表板和表格格式化"
```

---

## Phase 4: 顶层管理和集成

### Task 9: 实现 RegistryManager（注册管理器）

**文件:**

- Create: `src/evan_tools/registry/manager.py`
- Test: `tests/registry/test_registry_manager.py`

**Step 1: 编写 RegistryManager 的单元测试**

```python
# tests/registry/test_registry_manager.py
from src.evan_tools.registry.manager import RegistryManager


def test_manager_initialization_without_tracking():
    """测试初始化（不启用追踪）"""
    manager = RegistryManager(enable_tracking=False)
    
    assert not manager.is_tracking_enabled()
    assert manager.get_command_index() is not None
    assert manager.get_dashboard() is None


def test_manager_initialization_with_tracking():
    """测试初始化（启用追踪）"""
    manager = RegistryManager(enable_tracking=True)
    
    assert manager.is_tracking_enabled()
    assert manager.get_command_index() is not None
    assert manager.get_dashboard() is not None


def test_manager_enable_tracking():
    """测试启用追踪"""
    manager = RegistryManager(enable_tracking=False)
    
    assert not manager.is_tracking_enabled()
    
    manager.enable_tracking()
    assert manager.is_tracking_enabled()


def test_manager_disable_tracking():
    """测试禁用追踪"""
    manager = RegistryManager(enable_tracking=True)
    
    assert manager.is_tracking_enabled()
    
    manager.disable_tracking()
    assert not manager.is_tracking_enabled()
```

**Step 2: 运行测试，验证失败**

```bash
cd d:\Work\Spaces\Common\CommonPython\EvanTools
python -m pytest tests/registry/test_registry_manager.py -v
```

预期: FAIL

**Step 3: 实现 RegistryManager**

```python
# src/evan_tools/registry/manager.py
import typing as t
from .discovery.index import CommandIndex
from .tracking.tracker import ExecutionTracker
from .tracking.monitor import PerformanceMonitor
from .dashboard.dashboard import RegistryDashboard


class RegistryManager:
    """Registry 管理器（增强功能）"""
    
    def __init__(self, enable_tracking: bool = False) -> None:
        """初始化管理器"""
        self._enable_tracking = enable_tracking
        self._command_index = CommandIndex()
        
        if enable_tracking:
            self._tracker: ExecutionTracker | None = ExecutionTracker()
            self._tracker.start_tracking()
            self._monitor: PerformanceMonitor | None = PerformanceMonitor(self._tracker)
            self._dashboard: RegistryDashboard | None = RegistryDashboard(
                self._tracker,
                self._command_index,
            )
        else:
            self._tracker = None
            self._monitor = None
            self._dashboard = None
    
    def is_tracking_enabled(self) -> bool:
        """检查是否启用追踪"""
        return self._enable_tracking
    
    def enable_tracking(self) -> None:
        """启用追踪"""
        if not self._enable_tracking:
            self._enable_tracking = True
            self._tracker = ExecutionTracker()
            self._tracker.start_tracking()
            self._monitor = PerformanceMonitor(self._tracker)
            self._dashboard = RegistryDashboard(
                self._tracker,
                self._command_index,
            )
    
    def disable_tracking(self) -> None:
        """禁用追踪"""
        if self._enable_tracking:
            self._enable_tracking = False
            if self._tracker:
                self._tracker.stop_tracking()
            self._tracker = None
            self._monitor = None
            self._dashboard = None
    
    def get_command_index(self) -> CommandIndex:
        """获取命令索引"""
        return self._command_index
    
    def get_tracker(self) -> ExecutionTracker | None:
        """获取执行追踪器"""
        return self._tracker
    
    def get_monitor(self) -> PerformanceMonitor | None:
        """获取性能监控器"""
        return self._monitor
    
    def get_dashboard(self) -> RegistryDashboard | None:
        """获取仪表板"""
        return self._dashboard
```

**Step 4: 运行测试，验证通过**

```bash
cd d:\Work\Spaces\Common\CommonPython\EvanTools
python -m pytest tests/registry/test_registry_manager.py -v
```

预期: PASS

**Step 5: 更新 registry 模块的 **init**.py**

```python
# src/evan_tools/registry/__init__.py
from .main import get_registry, load_commands, register_command, register_with_typer
from .manager import RegistryManager
from .discovery.index import CommandIndex
from .tracking.tracker import ExecutionTracker
from .tracking.monitor import PerformanceMonitor
from .dashboard.dashboard import RegistryDashboard

__all__ = [
    "register_command",
    "get_registry",
    "register_with_typer",
    "load_commands",
    "RegistryManager",
    "CommandIndex",
    "ExecutionTracker",
    "PerformanceMonitor",
    "RegistryDashboard",
]
```

**Step 6: 提交**

```bash
git add -A && git commit -m "feat(registry): 实现 RegistryManager 顶层管理接口"
```

---

## Phase 5: 集成测试和验证

### Task 10: 编写端到端集成测试

**文件:**

- Create: `tests/registry/test_integration.py`

**Step 1: 编写集成测试**

```python
# tests/registry/test_integration.py
"""Registry 增强功能的端到端集成测试"""

import time
from src.evan_tools.registry.manager import RegistryManager
from src.evan_tools.registry.main import register_command, get_registry, register_with_typer
import typer


def test_full_workflow():
    """测试完整工作流"""
    # 1. 注册一些测试命令
    @register_command(name="list_files", group="file")
    def cmd_list_files():
        """List files."""
        pass
    
    @register_command(name="upload", group="file")
    def cmd_upload():
        """Upload files."""
        pass
    
    @register_command(name="status")
    def cmd_status():
        """Show status."""
        pass
    
    # 2. 创建管理器并启用追踪
    manager = RegistryManager(enable_tracking=True)
    
    # 3. 验证命令被发现
    commands = manager.get_command_index().get_all_commands()
    assert len(commands) >= 3
    
    # 4. 记录一些执行
    tracker = manager.get_tracker()
    assert tracker is not None
    
    tracker.record_execution(
        command_name="list_files",
        group="file",
        duration_ms=50.0,
        success=True,
        error=None,
        args=(),
        kwargs={},
    )
    
    tracker.record_execution(
        command_name="upload",
        group="file",
        duration_ms=100.0,
        success=False,
        error="NetworkError",
        args=(),
        kwargs={},
    )
    
    tracker.record_execution(
        command_name="status",
        group=None,
        duration_ms=25.0,
        success=True,
        error=None,
        args=(),
        kwargs={},
    )
    
    # 5. 获取仪表板并验证输出
    dashboard = manager.get_dashboard()
    assert dashboard is not None
    
    tree_output = dashboard.show_command_tree()
    assert "file" in tree_output
    assert "list_files" in tree_output
    assert "upload" in tree_output
    
    history_output = dashboard.show_execution_history()
    assert "list_files" in history_output
    assert "upload" in history_output
    assert "✓" in history_output  # 成功标记
    assert "✗" in history_output  # 失败标记
    
    stats_output = dashboard.show_performance_stats()
    assert "list_files" in stats_output
    assert "upload" in stats_output
    assert "status" in stats_output
    
    # 6. 获取统计信息
    monitor = manager.get_monitor()
    assert monitor is not None
    
    stats = monitor.get_stats("list_files")
    assert stats is not None
    assert stats.call_count == 1
    assert stats.error_count == 0
    
    stats = monitor.get_stats("upload")
    assert stats is not None
    assert stats.call_count == 1
    assert stats.error_count == 1


def test_manager_without_tracking():
    """测试不启用追踪的管理器"""
    manager = RegistryManager(enable_tracking=False)
    
    assert not manager.is_tracking_enabled()
    assert manager.get_tracker() is None
    assert manager.get_dashboard() is None
    
    # 但命令发现仍然可用
    commands = manager.get_command_index().get_all_commands()
    assert isinstance(commands, list)
```

**Step 2: 运行集成测试，验证通过**

```bash
cd d:\Work\Spaces\Common\CommonPython\EvanTools
python -m pytest tests/registry/test_integration.py -v
```

预期: PASS

**Step 3: 提交**

```bash
git add -A && git commit -m "test(registry): 添加端到端集成测试"
```

---

### Task 11: 运行完整测试套件并验证覆盖率

**文件:**

- 无新文件

**Step 1: 运行所有 registry 测试**

```bash
cd d:\Work\Spaces\Common\CommonPython\EvanTools
python -m pytest tests/registry/ -v --cov=src/evan_tools/registry --cov-report=html
```

预期: 所有测试通过，覆盖率 >= 90%

**Step 2: 检查覆盖率报告**

```bash
# 生成的 HTML 报告在 htmlcov/index.html
# 打开浏览器查看
```

**Step 3: 提交**

```bash
git add -A && git commit -m "test(registry): 验证完整测试覆盖率"
```

---

### Task 12: 编写文档和示例

**文件:**

- Create: `src/evan_tools/registry/README.md`
- Create: `examples/registry_enhancement_usage.py`

**Step 1: 编写 README 文档**

```markdown
# Registry 模块增强

## 概述

Registry 模块提供了命令注册、发现、执行追踪和性能监控的完整解决方案。

### 功能

- **命令注册** - 通过装饰器注册命令
- **命令发现** - 自动发现和索引已注册的命令
- **执行追踪** - 记录命令的执行时间、结果和错误
- **性能监控** - 收集和统计性能指标
- **可视化仪表板** - CLI 表格形式展示命令和执行数据

### 快速开始

#### 基础用法（不启用追踪）

```python
from src.evan_tools.registry import register_command, load_commands, register_with_typer
import typer

# 注册命令
@register_command(name="list", group="file")
def cmd_list():
    """List files."""
    print("Listing files...")

# 注册更多命令...

# 加载命令
load_commands("evan_tools.file", verbose=True)

# 创建 Typer 应用
app = typer.Typer()
register_with_typer(app)

if __name__ == "__main__":
    app()
```

#### 启用追踪和监控

```python
from src.evan_tools.registry import RegistryManager, register_command
import typer

# 注册命令
@register_command(name="list", group="file")
def cmd_list():
    """List files."""
    print("Listing files...")

# 创建管理器并启用追踪
manager = RegistryManager(enable_tracking=True)

# 创建 Typer 应用
app = typer.Typer()
register_with_typer(app)

# 执行命令（会被自动追踪）
# 注意：需要在实际执行时包装命令调用

# 查看仪表板
dashboard = manager.get_dashboard()
print(dashboard.show_command_tree())
print(dashboard.show_execution_history())
print(dashboard.show_performance_stats())
```

### API 参考

#### CommandIndex

```python
from src.evan_tools.registry import CommandIndex

index = CommandIndex()

# 获取所有命令
all_commands = index.get_all_commands()

# 按组获取命令
file_commands = index.get_commands_by_group("file")

# 获取命令树
tree = index.get_command_tree()

# 搜索命令
results = index.search_commands("list")

# 生成文档
docs = index.get_command_docs()
print(docs)
```

#### RegistryManager

```python
from src.evan_tools.registry import RegistryManager

# 初始化管理器
manager = RegistryManager(enable_tracking=True)

# 获取命令索引
index = manager.get_command_index()

# 获取执行追踪器
tracker = manager.get_tracker()

# 获取性能监控器
monitor = manager.get_monitor()

# 获取仪表板
dashboard = manager.get_dashboard()

# 禁用/启用追踪
manager.disable_tracking()
manager.enable_tracking()
```

#### ExecutionTracker

```python
from src.evan_tools.registry import ExecutionTracker

tracker = ExecutionTracker()

# 启用追踪
tracker.start_tracking()

# 记录执行
tracker.record_execution(
    command_name="list",
    group="file",
    duration_ms=100.0,
    success=True,
    error=None,
    args=(),
    kwargs={},
)

# 获取历史
history = tracker.get_execution_history(limit=20)

# 清空历史
tracker.clear_history()

# 禁用追踪
tracker.stop_tracking()
```

#### PerformanceMonitor

```python
from src.evan_tools.registry import PerformanceMonitor, ExecutionTracker

tracker = ExecutionTracker()
monitor = PerformanceMonitor(tracker)

# 获取单个命令的统计
stats = monitor.get_stats("list")
if stats:
    print(f"调用次数: {stats.call_count}")
    print(f"平均耗时: {stats.avg_duration_ms}ms")

# 获取所有统计
all_stats = monitor.get_all_stats()

# 重置统计
monitor.reset_stats()
```

#### RegistryDashboard

```python
from src.evan_tools.registry import RegistryDashboard, ExecutionTracker, CommandIndex

tracker = ExecutionTracker()
index = CommandIndex()
dashboard = RegistryDashboard(tracker, index)

# 显示命令树
print(dashboard.show_command_tree())

# 显示执行历史
print(dashboard.show_execution_history(limit=20))

# 显示性能统计
print(dashboard.show_performance_stats())

# 显示概览
print(dashboard.show_summary())
```

### 最佳实践

1. **内存管理** - 注意内存中存储的执行记录数量，使用 `limit` 参数控制
2. **性能影响** - 追踪会对性能有轻微影响，如果对性能敏感，关闭追踪
3. **错误处理** - 总是捕获命令执行中的异常，记录 `error` 字段
4. **定期清理** - 定期调用 `clear_history()` 防止内存溢出

### 扩展

#### 后续可能的改进

- 持久化存储（SQLite, MongoDB）
- 分布式追踪支持
- 性能分析和瓶颈检测
- Web 仪表板
- 命令执行权限控制

```

**Step 2: 编写使用示例**

```python
# examples/registry_enhancement_usage.py
"""Registry 模块增强功能的使用示例"""

from src.evan_tools.registry import (
    register_command,
    get_registry,
    register_with_typer,
    RegistryManager,
)
import typer
import time


# 注册一些示例命令
@register_command(name="sync", group="file")
def cmd_sync():
    """Sync files to remote."""
    time.sleep(0.1)
    print("Files synced!")


@register_command(name="list", group="file")
def cmd_list():
    """List files."""
    time.sleep(0.05)
    print("file1.txt")
    print("file2.txt")


@register_command(name="upload", group="file")
def cmd_upload(filename: str = "default.txt"):
    """Upload a file."""
    if "error" in filename:
        raise ValueError(f"Invalid filename: {filename}")
    time.sleep(0.2)
    print(f"Uploaded {filename}")


@register_command(name="status", group=None)
def cmd_status():
    """Show system status."""
    time.sleep(0.02)
    print("System OK")


def main_with_tracking():
    """使用追踪功能的示例"""
    print("=== Registry 增强功能演示 ===\n")
    
    # 创建管理器并启用追踪
    manager = RegistryManager(enable_tracking=True)
    tracker = manager.get_tracker()
    
    # 模拟命令执行并追踪
    commands_to_run = [
        ("list", "file", True, None),
        ("sync", "file", True, None),
        ("upload", "file", False, "ValueError: Invalid filename: error.txt"),
        ("status", None, True, None),
        ("list", "file", True, None),
    ]
    
    print("执行命令...\n")
    for cmd_name, group, success, error in commands_to_run:
        start = time.time()
        try:
            # 这里只是模拟，实际使用时需要真正执行命令
            time.sleep(0.05)
            print(f"✓ 执行 {cmd_name}")
        except Exception as e:
            print(f"✗ 执行 {cmd_name} 失败: {e}")
            success = False
            error = str(e)
        
        duration_ms = (time.time() - start) * 1000
        
        # 记录执行
        tracker.record_execution(
            command_name=cmd_name,
            group=group,
            duration_ms=duration_ms,
            success=success,
            error=error,
            args=(),
            kwargs={},
        )
    
    print("\n" + "=" * 60 + "\n")
    
    # 显示仪表板
    dashboard = manager.get_dashboard()
    
    print(dashboard.show_summary())
    print()
    print(dashboard.show_command_tree())
    print()
    print(dashboard.show_execution_history())
    print()
    print(dashboard.show_performance_stats())


def main_discovery_only():
    """仅使用命令发现功能的示例"""
    print("=== 命令发现功能演示 ===\n")
    
    # 创建管理器（不启用追踪）
    manager = RegistryManager(enable_tracking=False)
    
    # 获取命令索引
    index = manager.get_command_index()
    
    print("所有已注册的命令：")
    commands = index.get_all_commands()
    for cmd in commands:
        group = cmd.group or "（全局）"
        print(f"  - {group}: {cmd.name} - {cmd.docstring}")
    
    print("\nFile 组下的命令：")
    file_commands = index.get_commands_by_group("file")
    for cmd in file_commands:
        print(f"  - {cmd.name}")
    
    print("\n命令文档：")
    print(index.get_command_docs())


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--discovery":
        main_discovery_only()
    else:
        main_with_tracking()
```

**Step 3: 提交**

```bash
git add -A && git commit -m "docs(registry): 添加使用文档和示例代码"
```

---

## 实现完成检查

**所有任务完成后，执行以下检查：**

1. 运行完整测试：

```bash
cd d:\Work\Spaces\Common\CommonPython\EvanTools
python -m pytest tests/registry/ -v
```

1. 检查代码风格：

```bash
python -m pylint src/evan_tools/registry/
```

1. 生成覆盖率报告：

```bash
python -m pytest tests/registry/ --cov=src/evan_tools/registry --cov-report=term-missing
```

1. 运行示例：

```bash
python examples/registry_enhancement_usage.py
python examples/registry_enhancement_usage.py --discovery
```

1. 最终提交和合并：

```bash
# 验证所有提交
git log --oneline

# 返回主分支
cd d:\Work\Spaces\Common\CommonPython\EvanTools
git checkout main

# 合并功能分支
git merge feat/registry-enhancement

# 可选：删除工作树
git worktree remove .worktrees/registry-enhancement
```

---

## 成功标准

- [x] 所有代码已实现
- [ ] 单元测试覆盖率 >= 90%
- [ ] 集成测试全部通过
- [ ] 命令发现正常工作
- [ ] 执行审计准确记录
- [ ] 性能监控统计正确
- [ ] 仪表板能正确展示数据
- [ ] 向后兼容性已验证
- [ ] 文档和示例完整
- [ ] 代码风格符合 PEP 8
