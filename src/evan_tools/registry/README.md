# Registry 模块 - 命令注册与追踪系统

## 概述

Registry 模块提供了一套完整的命令注册、追踪、统计和仪表板功能，帮助开发者监控和可视化应用程序的命令执行情况。

## 核心功能

### 1. 命令注册 (`Discovery Layer`)
- **CommandMetadata**: 存储命令元数据（名称、分组、文档、签名等）
- **CommandInspector**: 从函数对象提取元数据
- **CommandIndex**: 构建命令索引、搜索和文档生成

### 2. 执行追踪 (`Tracking Layer`)
- **ExecutionTracker**: 记录命令执行历史
- **ExecutionRecord**: 单条执行记录（时间、耗时、成功/失败、错误信息）
- **PerformanceMonitor**: 查询性能统计数据
- **PerformanceStats**: 聚合统计（调用次数、平均/最小/最大耗时、错误数）

### 3. 数据存储 (`Storage Layer`)
- **InMemoryStore**: 内存存储（适合开发、测试、临时追踪）
- 支持统计数据计算和清空

### 4. 可视化 (`Visualization Layer`)
- **TableFormatter**: ASCII 表格格式化（可配置边界和分隔符）
- **StatsAggregator**: 将追踪数据转换为表格行
- **RegistryDashboard**: 统一仪表板，展示命令树、执行历史、性能统计

### 5. 管理器 (`Manager`)
- **RegistryManager**: 集中管理所有组件，提供统一入口

## 使用指南

### 基础使用

```python
from src.evan_tools.registry import RegistryManager

# 1. 创建管理器
manager = RegistryManager()

# 2. 启用追踪
manager.enable_tracking()

# 3. 记录命令执行
tracker = manager.get_tracker()
tracker.record_execution(
    command_name="process_file",
    group="file",
    duration_ms=125.5,
    success=True,
    error=None,
    args=(),
    kwargs={},
)

# 4. 查看仪表板
dashboard = manager.get_dashboard()
print(dashboard.show_execution_history(limit=20))
print(dashboard.show_performance_stats())

# 5. 关闭追踪
manager.disable_tracking()
```

### 性能监视

```python
# 获取特定命令的统计
monitor = manager.get_monitor()
stats = monitor.get_stats("process_file")
if stats:
    print(f"执行次数: {stats.call_count}")
    print(f"平均耗时: {stats.avg_duration_ms:.2f}ms")
    print(f"错误次数: {stats.error_count}")
```

### 命令发现

```python
# 获取所有注册命令
cmd_index = manager.get_command_index()
all_commands = cmd_index.get_all_commands()

# 按分组查询
file_commands = cmd_index.get_commands_by_group("file")

# 搜索命令
results = cmd_index.search_commands("sync")

# 显示命令树
tree = cmd_index.get_command_tree()
print(dashboard.show_command_tree())
```

## 架构设计

### 分层结构

```
┌─────────────────────────────────────────┐
│   Visualization Layer                   │
│  ┌─────────────────────────────────────┐│
│  │ TableFormatter                      ││ 表格格式化
│  │ StatsAggregator                     ││ 数据聚合
│  │ RegistryDashboard                   ││ 仪表板
│  └─────────────────────────────────────┘│
├─────────────────────────────────────────┤
│   Tracking Layer                        │
│  ┌─────────────────────────────────────┐│
│  │ ExecutionTracker                    ││ 执行追踪
│  │ PerformanceMonitor                  ││ 性能监视
│  │ ExecutionRecord / PerformanceStats  ││ 数据模型
│  └─────────────────────────────────────┘│
├─────────────────────────────────────────┤
│   Storage Layer                         │
│  ┌─────────────────────────────────────┐│
│  │ InMemoryStore                       ││ 内存存储
│  │ (支持统计计算)                      ││
│  └─────────────────────────────────────┘│
├─────────────────────────────────────────┤
│   Discovery Layer                       │
│  ┌─────────────────────────────────────┐│
│  │ CommandIndex                        ││ 命令索引
│  │ CommandInspector                    ││ 元数据提取
│  │ CommandMetadata                     ││ 数据模型
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

### 核心类关系

```
RegistryManager
├── ExecutionTracker
│   └── InMemoryStore
├── PerformanceMonitor (使用 ExecutionTracker 获取数据)
├── CommandIndex
└── RegistryDashboard
    ├── ExecutionTracker
    ├── CommandIndex
    ├── TableFormatter
    └── StatsAggregator
```

## 测试覆盖

- **单元测试**: 46 项（每个模块独立测试）
- **集成测试**: 3 项（完整工作流验证）
- **总计**: 49 项测试，100% 通过率

### 测试场景

| 模块 | 测试项数 | 覆盖范围 |
|------|---------|---------|
| Discovery | 12 | 元数据提取、索引构建、搜索、文档生成 |
| Tracking | 13 | 追踪启停、历史记录、统计计算 |
| Storage | 4 | 记录添加、统计、清空 |
| Visualization | 14 | 表格格式化、数据聚合、仪表板展示 |
| Manager | 3 | 初始化、启停、组件访问 |
| Integration | 3 | 注册流程、完整工作流、仪表板显示 |

## 最佳实践

### 1. 追踪生命周期管理

```python
manager = RegistryManager()

try:
    manager.enable_tracking()
    # 执行业务逻辑
finally:
    manager.disable_tracking()
    # 查看报告
```

### 2. 错误记录

```python
try:
    # 执行命令
    result = execute_something()
except Exception as e:
    tracker.record_execution(
        command_name="risky_operation",
        group="ops",
        duration_ms=elapsed_ms,
        success=False,
        error=f"{type(e).__name__}: {str(e)}",
        args=(),
        kwargs={},
    )
```

### 3. 性能分析

```python
# 执行一批操作后查看热点
stats = monitor.get_all_stats()
for cmd_name, stat in sorted(stats.items(), 
                             key=lambda x: x[1].total_duration_ms, 
                             reverse=True):
    print(f"{cmd_name}: {stat.total_duration_ms:.2f}ms")
```

## 文件结构

```
src/evan_tools/registry/
├── __init__.py                 # 公共导出
├── main.py                     # 命令注册和管理器
├── discovery/
│   ├── __init__.py
│   ├── metadata.py            # CommandMetadata 数据类
│   ├── inspector.py           # CommandInspector 检查器
│   └── index.py               # CommandIndex 索引
├── tracking/
│   ├── __init__.py
│   ├── models.py              # ExecutionRecord 等数据类
│   ├── tracker.py             # ExecutionTracker 追踪器
│   └── monitor.py             # PerformanceMonitor 监视器
├── storage/
│   ├── __init__.py
│   └── memory_store.py        # InMemoryStore 存储
├── dashboard/
│   ├── __init__.py
│   ├── formatter.py           # TableFormatter 格式化
│   ├── aggregator.py          # StatsAggregator 聚合
│   └── dashboard.py           # RegistryDashboard 仪表板
└── README.md                   # 本文件
```

## 扩展点

### 1. 自定义存储后端
继承 `InMemoryStore` 接口，实现数据库、文件等持久化存储。

### 2. 自定义表格格式
自定义 `TableConfig` 参数或扩展 `TableFormatter` 以支持不同的输出格式（HTML、Markdown 等）。

### 3. 远程上报
在 `ExecutionTracker.record_execution()` 后添加钩子，将数据上报到远程服务。

## 性能特性

- **零开销追踪**: 关闭时无额外开销
- **内存高效**: 使用数据类和简单数据结构
- **快速查询**: O(1) 命令查询，O(n) 统计计算
- **可扩展**: 支持水平扩展到数千条记录

## 许可证

MIT
