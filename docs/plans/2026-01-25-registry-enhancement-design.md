# Registry 模块增强设计文档

**日期**: 2026-01-25  
**状态**: 已验证设计  
**目标**: 为 registry 模块添加命令发现、执行审计和性能监控功能

---

## 需求概览

### 功能需求
1. **命令发现和文档** - 自动生成命令索引、帮助文档、命令树可视化
2. **命令执行审计** - 记录谁执行了什么命令、何时执行、执行结果
3. **性能指标** - 收集命令执行时间、调用频率统计
4. **可视化仪表板** - 提供 CLI 表格形式的实时查看界面

### 非功能性需求
- **向后兼容** - 原有 API 保持不变
- **可选启用** - 追踪功能默认关闭
- **最小依赖** - 仅使用标准库和现有依赖
- **易于测试** - 分层设计，职责清晰

---

## 架构设计

### 四层增强架构

```
┌──────────────────────────────────────────────────────┐
│        命令发现层 (Discovery Layer)                  │
│  • CommandIndex: 构建命令索引树                      │
│  • CommandInspector: 提取命令元数据                  │
│  • DocumentGenerator: 生成文档                       │
└────────────────┬─────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────┐
│        执行追踪层 (Execution Tracking)               │
│  • ExecutionTracker: 记录审计日志                    │
│  • PerformanceMonitor: 收集性能数据                  │
│  • CommandWrapper: 包装命令执行                      │
└────────────────┬─────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────┐
│        数据存储层 (Data Storage)                     │
│  • ExecutionRecord: 执行记录数据类                   │
│  • PerformanceStats: 性能统计数据类                  │
│  • InMemoryStore: 内存存储实现                       │
└────────────────┬─────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────┐
│        可视化层 (Visualization)                      │
│  • RegistryDashboard: CLI 仪表板                     │
│  • TableFormatter: 表格格式化                        │
│  • StatsAggregator: 数据聚合和统计                   │
└──────────────────────────────────────────────────────┘
```

---

## 数据结构设计

### 命令元数据
```python
@dataclass
class CommandMetadata:
    name: str
    group: str | None
    func: Callable
    docstring: str | None
    module: str
    signature: inspect.Signature
```

### 执行审计记录
```python
@dataclass
class ExecutionRecord:
    command_name: str
    group: str | None
    timestamp: datetime
    duration_ms: float
    success: bool
    error: str | None
    args: tuple
    kwargs: dict
```

### 性能统计
```python
@dataclass
class PerformanceStats:
    command_name: str
    call_count: int
    total_duration_ms: float
    avg_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    error_count: int
```

---

## 公共 API 设计

### 命令发现 API
```python
class CommandIndex:
    def get_all_commands() -> list[CommandMetadata]
    def get_commands_by_group(group: str) -> list[CommandMetadata]
    def get_command_tree() -> dict  # 树结构表示
    def get_command_docs() -> str  # Markdown 格式文档
    def search_commands(query: str) -> list[CommandMetadata]
```

### 执行追踪 API
```python
class ExecutionTracker:
    def start_tracking() -> None  # 启用审计
    def stop_tracking() -> None   # 禁用审计
    def get_execution_history(limit: int = 100) -> list[ExecutionRecord]
    def clear_history() -> None
```

### 性能监控 API
```python
class PerformanceMonitor:
    def get_stats(command_name: str) -> PerformanceStats | None
    def get_all_stats() -> dict[str, PerformanceStats]
    def reset_stats() -> None
```

### 仪表板 API
```python
class RegistryDashboard:
    def show_command_tree() -> str  # 命令树表格
    def show_execution_history() -> str  # 审计日志表格
    def show_performance_stats() -> str  # 性能数据表格
    def show_summary() -> str  # 综合统计概览
```

### 顶层管理 API
```python
class RegistryManager:
    def __init__(self, enable_tracking: bool = False)
    def enable_tracking() -> None
    def disable_tracking() -> None
    def get_dashboard() -> RegistryDashboard
    def get_command_index() -> CommandIndex
```

### 使用示例
```python
# 初始化注册管理器（启用追踪）
registry_mgr = RegistryManager(enable_tracking=True)

# 获取命令索引
commands = registry_mgr.get_command_index()
print(commands.get_command_docs())  # 打印文档

# 执行命令后，查看仪表板
dashboard = registry_mgr.get_dashboard()
print(dashboard.show_execution_history())  # 查看审计日志
print(dashboard.show_performance_stats())  # 查看性能数据
```

---

## 文件结构设计

```
src/evan_tools/registry/
├── __init__.py
├── main.py (原有代码，保持不变)
├── discovery/
│   ├── __init__.py
│   ├── metadata.py (CommandMetadata 数据类)
│   ├── inspector.py (CommandInspector：提取命令信息)
│   └── index.py (CommandIndex：构建命令索引)
├── tracking/
│   ├── __init__.py
│   ├── models.py (ExecutionRecord, PerformanceStats)
│   ├── tracker.py (ExecutionTracker：记录审计日志)
│   ├── monitor.py (PerformanceMonitor：统计性能)
│   └── wrapper.py (命令执行包装器)
├── storage/
│   ├── __init__.py
│   └── memory_store.py (InMemoryStore：内存存储)
└── dashboard/
    ├── __init__.py
    ├── formatter.py (TableFormatter：表格格式化)
    ├── aggregator.py (StatsAggregator：数据聚合)
    └── dashboard.py (RegistryDashboard：仪表板)
```

---

## 实现策略

### 集成方式（非侵入式）
```python
# main.py 保持现状，新增可选的 RegistryManager
class RegistryManager:
    """可选的增强管理器，不影响原有功能"""
    def __init__(self, enable_tracking: bool = False):
        self._tracker = ExecutionTracker() if enable_tracking else None
        self._index = CommandIndex()
        self._dashboard = RegistryDashboard(self._tracker, self._index)
    
    # 在 register_with_typer 时包装命令
    def register_with_typer_enhanced(self, app: typer.Typer) -> None:
        # 先调用原始注册
        register_with_typer(app)
        # 然后包装命令以启用追踪
        if self._tracker:
            self._wrap_commands_for_tracking(app)
```

### 关键设计决策
1. ✅ **向后兼容** - 原有 API 完全不变，新功能通过 `RegistryManager` 提供
2. ✅ **可选启用** - 追踪功能默认关闭，用户按需启用
3. ✅ **最小化依赖** - 仅使用标准库（`dataclasses`, `inspect`, `datetime`）+ 现有的 `typer`
4. ✅ **易于测试** - 每个模块职责明确，可独立单元测试

---

## 测试计划

```
tests/registry/
├── test_discovery.py (命令发现功能)
├── test_tracking.py (审计和性能追踪)
├── test_dashboard.py (仪表板展示)
└── test_integration.py (端到端集成)
```

### 测试覆盖范围
- CommandInspector：提取和解析命令元数据
- CommandIndex：索引查询和树构建
- ExecutionTracker：审计记录准确性
- PerformanceMonitor：统计计算正确性
- RegistryDashboard：表格格式化输出
- 端到端：从命令注册到仪表板显示的完整流程

---

## 实现优先级

1. **Phase 1 (核心)**: discovery + models + memory_store
2. **Phase 2 (追踪)**: tracking + wrapper + dashboard
3. **Phase 3 (测试)**: 完整的单元和集成测试
4. **Phase 4 (文档)**: 使用文档、API 参考、示例

---

## 成功标准

- [x] 设计已验证
- [ ] 所有代码已实现
- [ ] 单元测试覆盖率 >= 90%
- [ ] 可正常执行审计和性能监控
- [ ] 仪表板能正确展示数据
- [ ] 向后兼容性已验证
