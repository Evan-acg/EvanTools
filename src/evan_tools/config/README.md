# 配置管理系统 (Configuration Management System)

## 概述 (Overview)

新的配置管理系统完全按照 SOLID 原则重构，提供了高度模块化、易于测试和扩展的架构。

## 架构 (Architecture)

```text
evan_tools.config/
├── main.py                          # 向后兼容的公共 API 适配器
├── concurrency/
│   ├── __init__.py
│   └── rw_lock.py                  # 读写锁 (RWLock) 并发控制
├── core/
│   ├── __init__.py
│   ├── cache.py                    # 缓存管理 (ConfigCache)
│   ├── reload_controller.py        # 重加载控制 (ReloadController)
│   ├── merger.py                   # 配置合并 (ConfigMerger)
│   ├── manager.py                  # 统一管理器 (ConfigManager)
│   └── source.py                   # 配置源接口 (ConfigSource)
└── sources/
    ├── __init__.py
    ├── yaml_source.py              # YAML 文件源
    └── directory_source.py         # 目录扫描源
```

## 核心组件 (Core Components)

### RWLock - 并发控制

- 支持多个读者，单个写者
- 线程安全的配置访问
- 基于 `threading.Condition`

### ConfigSource (ABC) - 配置源接口

- 定义读/写/支持检查的抽象接口
- 支持多种配置格式的扩展
- 当前实现：`YamlConfigSource`、`DirectoryConfigSource`

### ConfigCache - 缓存管理

- 时间窗口缓存 (默认 5 秒)
- 减少频繁的文件系统访问
- 可配置的刷新间隔

### ReloadController - 重加载控制

- 跟踪配置文件 mtime (修改时间)
- 检测文件变化
- 支持热加载

### ConfigMerger - 配置合并

- 深度合并多个配置字典
- 使用 pydash 保证嵌套合并的准确性
- 保持后面的值覆盖前面的值

### ConfigManager - 统一管理器

- 协调所有组件的交互
- 依赖注入设计 (DI)
- 支持单文件和多文件加载
- 自动热加载和缓存

## 使用方式 (Usage)

### 基本使用（向后兼容）

```python
from src.evan_tools.config import load_config, get_config, sync_config

# 加载配置（支持目录和文件）
load_config("config.yaml")                  # 单个文件
load_config("config")                       # 自动查找 config.yaml/yml
load_config(Path("config"))                 # Path 对象

# 获取配置值
value = get_config("database.host")         # 点号分隔符
value = get_config(["database", "host"])    # 列表形式
value = get_config("missing.key", "default") # 带默认值

# 设置并保存
get_config()  # 返回整个配置字典

# 同步到文件
sync_config()
```

### 高级使用（直接使用 ConfigManager）

```python
from src.evan_tools.config.core import ConfigManager

# 创建管理器实例
manager = ConfigManager()

# 加载配置
config = manager.load("config.yaml")

# 查询值
value = manager.get("database.host", "localhost")

# 设置值
manager.set("database.host", "prod.example.com")

# 保存到文件
manager.sync()

# 强制重新加载
manager.reload()
```

### 自定义配置源

```python
from src.evan_tools.config.core import ConfigSource
from src.evan_tools.config.core import ConfigManager
from pathlib import Path
from typing import Any, Optional

class JsonConfigSource(ConfigSource):
    """JSON 配置源实现示例"""
    
    def read(self, path: Path, base_path: Optional[Path] = None) -> dict[str, Any]:
        import json
        with open(path) as f:
            return json.load(f)
    
    def write(self, path: Path, config: dict[str, Any], 
              base_path: Optional[Path] = None) -> None:
        import json
        with open(path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def supports(self, path: Path) -> bool:
        return path.suffix.lower() == '.json'

# 使用自定义源
manager = ConfigManager(source=JsonConfigSource())
config = manager.load("config.json")
```

## 特性 (Features)

✅ **完全的 SOLID 原则应用**

- 单一职责：每个类只有一个改变的原因
- 开闭原则：通过 ConfigSource 接口扩展功能
- Liskov 替换：子类完全替换父类
- 接口隔离：精细化的接口设计
- 依赖倒转：依赖抽象而非具体

✅ **多文件合并**

- 自动扫描目录中的所有 YAML 文件
- 按字母顺序合并（确定性）
- 后面的文件覆盖前面的文件

✅ **热加载支持**

- 自动检测文件变化
- 时间窗口缓存避免频繁检查
- 线程安全的并发访问

✅ **向后兼容**

- 保持原有 API：load_config, get_config, sync_config
- 支持列表、字符串、Hashable 多种路径格式
- 现有代码无需修改

✅ **易于测试**

- 依赖注入允许 Mock 任何组件
- 所有类都针对接口编程
- 功能完全分离

## 性能 (Performance)

- **缓存**: 减少 mtime 检查的频率 (默认 5 秒)
- **并发**: RWLock 允许多个读者同时访问
- **合并**: pydash 的优化深度合并算法
- **内存**: 单个实例管理全局配置

## 迁移指南 (Migration Guide)

### 从旧版本迁移

旧代码无需任何改动！新架构通过 `main.py` 的适配器层完全向后兼容。

```python
# 所有旧代码都能继续工作
from evan_tools.config import load_config, get_config, sync_config

load_config("config")
print(get_config("app.name"))
sync_config()
```

### 逐步采用新功能

需要更多控制时，可以逐步使用 ConfigManager：

```python
from src.evan_tools.config.core import ConfigManager

manager = ConfigManager()
manager.load("config.yaml")

# 更灵活的 API
value = manager.get("complex.nested.path")
manager.set("new.key", "value")
```

## 测试 (Testing)

所有组件都有完整的单元测试：

```bash
# 运行配置模块测试
python -m pytest tests/config/test_main.py -v

# 测试覆盖：
# ✓ 单文件加载
# ✓ 多文件合并
# ✓ 热加载检测
# ✓ 时间窗口缓存
# ✓ 配置同步
# ✓ 无效 YAML 处理
# ✓ 路径查询和默认值
```

## 已知限制 (Known Limitations)

1. **目录同步**: 加载目录后调用 sync() 会失败。
   - 解决方案: 始终通过具体的 YAML 文件路径调用 sync()

2. **YAML 格式**: 仅支持 YAML 格式（JSON 可通过自定义 source 支持）

3. **大文件**: 大配置文件的合并可能较慢
   - 建议: 将大配置分解为多个小文件

## 扩展 (Extensions)

### 添加新的配置源

```python
# 在 src/evan_tools/config/sources/ 下创建新类
class TomlConfigSource(ConfigSource):
    def read(self, path, base_path=None):
        # 实现 TOML 读取
        pass
    
    def write(self, path, config, base_path=None):
        # 实现 TOML 写入
        pass
    
    def supports(self, path):
        return path.suffix == '.toml'

# 使用
manager = ConfigManager(source=TomlConfigSource())
```

### 自定义缓存策略

```python
from src.evan_tools.config.core import ConfigCache

class CustomCache(ConfigCache):
    def should_reload(self):
        # 实现自定义缓存逻辑
        pass

manager = ConfigManager(cache=CustomCache(reload_interval_seconds=10))
```

## 许可 (License)

Part of EvanTools package.

---

**更新日期**: 2026-01-24  
**版本**: 2.0.0 (SOLID 重构)
