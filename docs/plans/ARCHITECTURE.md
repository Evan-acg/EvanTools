# 配置系统架构设计

## 架构整体视图

```
┌─────────────────────────────────────────────────────────────────┐
│                         Public API Layer                         │
│  load_config() | get_config() | sync_config() | ConfigManager   │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ConfigManager                                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • 统一的公共接口                                         │    │
│  │ • 协调所有组件                                          │    │
│  │ • 热加载逻辑                                            │    │
│  │ • 并发控制                                              │    │
│  └─────────────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────────────┘
         │             │             │              │              │
         ▼             ▼             ▼              ▼              ▼
   ┌─────────┐   ┌─────────┐   ┌────────┐   ┌──────────┐    ┌────────┐
   │ConfigSrc│   │  Cache  │   │Reload  │   │  Merger  │    │ RWLock │
   │         │   │         │   │Control │   │          │    │        │
   ├─────────┤   ├─────────┤   ├────────┤   ├──────────┤    ├────────┤
   │• read   │   │• get    │   │• should│   │• merge   │    │• acquire│
   │• write  │   │• set    │   │  check │   │          │    │• release│
   │• supports   │• clear  │   │• mark  │   │          │    │        │
   │         │   │• outdated   │  reloaded   │          │    │        │
   └────┬────┘   └─────────┘   └────────┘   └──────────┘    └────────┘
        │
        ▼
   ┌─────────────────┐
   │ ConfigSources   │
   ├─────────────────┤
   │ • YAML          │
   │ • JSON (未来)   │
   │ • TOML (未来)   │
   └─────────────────┘
```

## 组件职责矩阵

| 组件 | 职责 | 依赖 | 测试 |
|------|------|------|------|
| **ConfigManager** | 统一接口、协调组件 | 所有 | 集成测试 |
| **ConfigSource** | 格式读写抽象 | 无 | 单元测试 |
| **ConfigCache** | 缓存和 mtime 检查 | 无 | 单元测试 |
| **ReloadController** | 热加载时间控制 | 无 | 单元测试 |
| **ConfigMerger** | 多文件合并 | pydash | 单元测试 |
| **RWLock** | 读写并发控制 | threading | 单元测试 |

## 数据流

### 初始化流程
```
load_config(path)
    ↓
ConfigManager.load()
    ├→ 获取写锁
    ├→ 扫描配置文件
    ├→ 遍历文件
    │   ├→ ConfigSource.read(file)
    │   ├→ ConfigCache.set()
    │   └→ 收集键路径
    ├→ ConfigMerger.merge()
    ├→ 设置 _cfg
    └→ 释放写锁
```

### 查询流程
```
get_config(path)
    ↓
ReloadController.should_check_reload()
    ├─ YES → ConfigCache.is_outdated() 检查
    │          ├─ 文件变化 → 重加载
    │          └─ 无变化 → 使用缓存
    └─ NO → 使用缓存
    ↓
获取读锁
    ↓
pydash.get() 查询值
    ↓
释放读锁
```

### 写回流程
```
sync_config()
    ↓
遍历配置路径
    ├→ 构建要写入的内容
    ├→ ConfigSource.write(file, content)
    ├→ ConfigCache.set() 更新缓存
    └→ 更新 mtime
    ↓
ReloadController.mark_reloaded()
```

## 类图

```
┌────────────────────────────┐
│   ConfigSource (ABC)       │
├────────────────────────────┤
│ + read(path) -> dict       │
│ + write(path, content)     │
│ + supports(path) -> bool   │
└────────────────────────────┘
            △
            │ implements
            │
    ┌───────┴───────┐
    │               │
┌───────────────┐  ┌───────────────┐
│ YamlCfgSource │  │ JsonCfgSource │
└───────────────┘  └───────────────┘
                   (Future expansion)

┌─────────────────────────────────┐
│    ConfigCache                  │
├─────────────────────────────────┤
│ - _cache: dict[Path, dict]      │
├─────────────────────────────────┤
│ + get(path) -> dict | None      │
│ + set(path, content, mtime)     │
│ + is_outdated(path) -> bool     │
│ + clear()                       │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│    ReloadController             │
├─────────────────────────────────┤
│ - _last_reload_time: float      │
│ - _interval: float              │
├─────────────────────────────────┤
│ + should_check_reload() -> bool │
│ + mark_reloaded()               │
│ + set_interval(float)           │
└─────────────────────────────────┘

┌──────────────────────────────────┐
│    ConfigMerger                  │
├──────────────────────────────────┤
│ + merge(configs: list) -> dict   │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│    RWLock                        │
├──────────────────────────────────┤
│ - _read_ready: Condition         │
│ - _readers: int                  │
├──────────────────────────────────┤
│ + acquire_read()                 │
│ + release_read()                 │
│ + acquire_write()                │
│ + release_write()                │
└──────────────────────────────────┘

┌──────────────────────────────────────────┐
│    ConfigManager                         │
├──────────────────────────────────────────┤
│ - _source: ConfigSource                  │
│ - _cache: ConfigCache                    │
│ - _reload_controller: ReloadController   │
│ - _merger: ConfigMerger                  │
│ - _lock: RWLock                          │
│ - _cfg: dict                             │
├──────────────────────────────────────────┤
│ + load()                                 │
│ + get(path, default) -> Any              │
│ + sync()                                 │
│ - _reload_if_needed()                    │
│ - _scan_config_files()                   │
└──────────────────────────────────────────┘
```

## 文件系统结构

```
src/evan_tools/config/
│
├── __init__.py
│   └─ 公共 API 导出
│
├── main.py (改造)
│   └─ 向后兼容适配层
│       • load_config()
│       • get_config()
│       • sync_config()
│
├── manager.py (新建)
│   └─ ConfigManager 统一接口
│
├── core/ (新建)
│   ├── __init__.py
│   ├── source.py
│   │   └─ ConfigSource 抽象接口
│   ├── cache.py
│   │   └─ ConfigCache 缓存管理
│   ├── reload.py
│   │   └─ ReloadController 热加载
│   └── merger.py
│       └─ ConfigMerger 配置合并
│
├── sources/ (新建)
│   ├── __init__.py
│   └── yaml_source.py
│       └─ YamlConfigSource 实现
│
└── concurrency/ (新建)
    ├── __init__.py
    └── rw_lock.py
        └─ RWLock 并发控制
```

## 测试覆盖

```
tests/config/
│
├── test_main.py (现有)
│   └─ 向后兼容性验证
│
├── test_cache.py (新建)
│   ├─ 缓存设置/获取
│   ├─ 缓存过期检查
│   └─ 缓存清空
│
├── test_reload.py (新建)
│   ├─ 初始检查
│   ├─ 时间窗口缓存
│   └─ 间隔设置
│
├── test_sources.py (新建)
│   ├─ YAML 格式支持
│   ├─ YAML 文件读写
│   ├─ 格式错误处理
│   └─ 合并器验证
│
└── test_manager.py (新建)
    ├─ 简单配置加载
    ├─ 路径查询
    ├─ 多文件合并
    ├─ 热加载
    └─ 文件写回
```

## SOLID 原则映射

### S - Single Responsibility
每个类只有一个职责：
- `ConfigCache`: 仅管理缓存
- `ReloadController`: 仅控制重加载时机
- `ConfigMerger`: 仅合并配置
- `ConfigManager`: 仅协调组件

### O - Open/Closed Principle
对扩展开放，对修改关闭：
- 实现新格式：继承 `ConfigSource`
- 无需修改现有代码

### L - Liskov Substitution
子类可替换父类：
```python
source = YamlConfigSource()  # 或 JsonConfigSource()
manager = ConfigManager(source)  # 无差别使用
```

### I - Interface Segregation
接口最小化，职责明确：
```python
class ConfigSource(ABC):  # 3 个方法，职责清晰
    @abstractmethod
    def read(self, path): ...
    @abstractmethod
    def write(self, path, content): ...
    @abstractmethod
    def supports(self, path): ...
```

### D - Dependency Inversion
依赖于抽象，不依赖于具体：
```python
# 依赖抽象接口
manager = ConfigManager(source: ConfigSource)

# 不依赖具体实现
# manager = ConfigManager(source=YamlConfigSource())  ✓
# manager = ConfigManager(source=JsonConfigSource())  ✓
```

## 扩展示例

### 添加 JSON 支持
```python
# src/evan_tools/config/sources/json_source.py

class JsonConfigSource(ConfigSource):
    def read(self, path: Path) -> dict:
        with open(path) as f:
            return json.load(f)
    
    def write(self, path: Path, content: dict) -> None:
        with open(path, 'w') as f:
            json.dump(content, f)
    
    def supports(self, path: Path) -> bool:
        return path.suffix == '.json'

# 使用
from evan_tools.config.manager import ConfigManager
from evan_tools.config.sources.json_source import JsonConfigSource

manager = ConfigManager(JsonConfigSource(), "./config")
manager.load()
```

## 性能特性

### 缓存优化
- **mtime 检查**: 避免频繁文件读取
- **内存缓存**: 热数据在内存中

### 并发控制
- **读写锁**: 支持多线程并发读取
- **单一写入**: 保证写操作原子性

### 热加载
- **时间窗口**: 5 秒内不重复检查
- **选择性重加载**: 仅在文件变化时重加载

