# 配置系统 SOLID 原则重构设计

## 目标
将现有的全局变量和混杂职责的配置系统重构为基于 SOLID 原则的模块化架构，支持多格式扩展、易于测试和维护。

## 架构概览

### 当前问题
- **SRP 违反**: `main.py` 混合 YAML 加载、缓存、并发控制、合并、查询逻辑
- **OCP 违反**: 难以扩展支持 JSON、TOML 等格式
- **DIP 违反**: 依赖具体实现而非抽象
- **全局变量**: 状态分散，难以测试

### 重构后的结构

```
src/evan_tools/config/
├── __init__.py                 # 公共 API 入口
├── core/
│   ├── __init__.py
│   ├── source.py               # ConfigSource 抽象接口
│   ├── cache.py                # ConfigCache 缓存管理
│   ├── reload.py               # ReloadController 热加载控制
│   └── merger.py               # ConfigMerger 配置合并
├── sources/
│   ├── __init__.py
│   ├── yaml_source.py          # YAML 配置源实现
│   └── json_source.py          # JSON 配置源实现（可扩展）
├── concurrency/
│   ├── __init__.py
│   └── rw_lock.py              # RWLock 并发控制
└── manager.py                  # ConfigManager 统一接口

tests/config/
├── test_main.py                # （现有测试保留）
├── test_sources.py             # 配置源测试
├── test_cache.py               # 缓存管理测试
└── test_manager.py             # 管理器集成测试
```

## 设计原则

### 1. **依赖倒置原则 (DIP)**
- 定义 `ConfigSource` 抽象接口
- `ConfigManager` 依赖接口，不依赖具体格式实现

### 2. **开闭原则 (OCP)**
- 新增格式只需实现 `ConfigSource` 接口
- 无需修改现有代码

### 3. **单一职责原则 (SRP)**
- `ConfigSource`: 读取配置文件
- `ConfigCache`: 缓存管理和 mtime 检查
- `ReloadController`: 热加载逻辑和时间窗口
- `ConfigMerger`: 配置合并
- `ConfigManager`: 统一公共 API

### 4. **接口隔离原则 (ISP)**
- 每个接口职责明确，不冗余

---

## 核心组件设计

### ConfigSource (抽象接口)
```python
from abc import ABC, abstractmethod
from pathlib import Path

class ConfigSource(ABC):
    """配置源抽象接口"""
    
    @abstractmethod
    def read(self, path: Path) -> dict[str, Any]:
        """读取配置文件"""
        pass
    
    @abstractmethod
    def write(self, path: Path, content: dict[str, Any]) -> None:
        """写入配置文件"""
        pass
    
    @abstractmethod
    def supports(self, path: Path) -> bool:
        """检查是否支持该文件格式"""
        pass
```

### RWLock (并发控制)
- 移至专属模块
- 保留现有实现，无需修改

### ConfigCache (缓存管理)
```python
class ConfigCache:
    """管理文件缓存和 mtime 检查"""
    
    def __init__(self):
        self._cache: dict[Path, dict] = {}
    
    def get(self, path: Path) -> dict | None:
        """获取缓存"""
        pass
    
    def set(self, path: Path, content: dict, mtime: float) -> None:
        """设置缓存"""
        pass
    
    def is_outdated(self, path: Path) -> bool:
        """检查文件是否已更改"""
        pass
```

### ReloadController (热加载控制)
```python
class ReloadController:
    """管理热加载逻辑和时间窗口"""
    
    def __init__(self, interval: float = 5.0):
        self._last_reload_time = 0.0
        self._interval = interval
    
    def should_reload(self) -> bool:
        """检查是否在时间窗口内"""
        pass
    
    def mark_reloaded(self) -> None:
        """标记已重加载"""
        pass
```

### ConfigMerger (配置合并)
```python
class ConfigMerger:
    """合并多个配置文件"""
    
    def merge(self, configs: list[dict]) -> dict:
        """按优先级合并配置"""
        pass
```

### ConfigManager (统一管理)
```python
class ConfigManager:
    """配置管理的公共接口"""
    
    def __init__(self, source: ConfigSource, base_path: Path):
        self._source = source
        self._cache = ConfigCache()
        self._reload_controller = ReloadController()
    
    def load(self) -> None:
        """加载配置"""
        pass
    
    def get(self, path: str | list = None, default = None):
        """查询配置"""
        pass
    
    def sync(self) -> None:
        """写回配置"""
        pass
```

---

## 向后兼容性

保留现有的公共 API：
- `load_config(path)` → 创建 `ConfigManager` 实例
- `get_config(path, default)` → 委托给 `ConfigManager`
- `sync_config()` → 委托给 `ConfigManager`

现有测试保持不变，新增模块化测试。

---

## 关键改进

✅ **易于扩展**: 支持 JSON、TOML 等格式  
✅ **易于测试**: 依赖注入，可模拟所有组件  
✅ **职责清晰**: 每个类单一职责  
✅ **并发安全**: RWLock 保留并独立使用  
✅ **向后兼容**: 现有 API 不变  

