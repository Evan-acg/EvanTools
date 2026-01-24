# 配置系统 SOLID 重构实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 重构配置系统，应用 SOLID 原则，实现模块化、可扩展的架构

**Architecture:** 将单一文件的全局变量设计拆分为多个模块，每个模块职责单一。使用依赖注入和接口抽象，支持多种配置格式扩展。保留向后兼容的公共 API。

**Tech Stack:** Python 3.11+, typing, abc (Abstract Base Classes), pydash, yaml

---

## Task 1: 创建模块结构和并发控制模块

**Files:**

- Create: `src/evan_tools/config/core/__init__.py`
- Create: `src/evan_tools/config/core/source.py` (ConfigSource 接口)
- Create: `src/evan_tools/config/concurrency/__init__.py`
- Create: `src/evan_tools/config/concurrency/rw_lock.py` (RWLock 类)
- Create: `src/evan_tools/config/sources/__init__.py`

**Step 1: 创建核心目录结构**

创建空的 `__init__.py` 文件：

```bash
mkdir -p src/evan_tools/config/core
mkdir -p src/evan_tools/config/sources
mkdir -p src/evan_tools/config/concurrency
touch src/evan_tools/config/core/__init__.py
touch src/evan_tools/config/sources/__init__.py
touch src/evan_tools/config/concurrency/__init__.py
```

**Step 2: 创建 RWLock 并发控制模块**

File: `src/evan_tools/config/concurrency/rw_lock.py`

```python
import threading


class RWLock:
    """读写锁：允许多个读，一个写（非可重入）"""
    
    def __init__(self):
        self._read_ready = threading.Condition(threading.Lock())
        self._readers = 0

    def acquire_read(self):
        """获取读锁"""
        with self._read_ready:
            self._readers += 1

    def release_read(self):
        """释放读锁"""
        with self._read_ready:
            self._readers -= 1
            if self._readers == 0:
                self._read_ready.notify_all()

    def acquire_write(self):
        """获取写锁"""
        self._read_ready.acquire()
        while self._readers > 0:
            self._read_ready.wait()

    def release_write(self):
        """释放写锁"""
        self._read_ready.release()
```

File: `src/evan_tools/config/concurrency/__init__.py`

```python
from .rw_lock import RWLock

__all__ = ["RWLock"]
```

**Step 3: 创建 ConfigSource 抽象接口**

File: `src/evan_tools/config/core/source.py`

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class ConfigSource(ABC):
    """配置源抽象接口"""
    
    @abstractmethod
    def read(self, path: Path) -> dict[str, Any]:
        """
        读取配置文件
        
        Args:
            path: 配置文件路径
            
        Returns:
            配置字典
            
        Raises:
            OSError: 文件访问失败
            ValueError: 格式解析失败
        """
        pass
    
    @abstractmethod
    def write(self, path: Path, content: dict[str, Any]) -> None:
        """
        写入配置文件
        
        Args:
            path: 配置文件路径
            content: 配置字典
            
        Raises:
            OSError: 文件写入失败
            ValueError: 格式序列化失败
        """
        pass
    
    @abstractmethod
    def supports(self, path: Path) -> bool:
        """
        检查是否支持该文件格式
        
        Args:
            path: 配置文件路径
            
        Returns:
            是否支持
        """
        pass
```

File: `src/evan_tools/config/core/__init__.py`

```python
from .source import ConfigSource

__all__ = ["ConfigSource"]
```

**Step 4: 运行验证（创建文件后）**

Run: `python -c "from src.evan_tools.config.concurrency import RWLock; print('RWLock imported successfully')"`

Expected: `RWLock imported successfully`

**Step 5: Commit**

```bash
git add src/evan_tools/config/core/ src/evan_tools/config/concurrency/ src/evan_tools/config/sources/
git commit -m "refactor: create module structure and abstraction interfaces"
```

---

## Task 2: 创建缓存和重加载控制模块

**Files:**

- Create: `src/evan_tools/config/core/cache.py`
- Create: `src/evan_tools/config/core/reload.py`
- Create: `tests/config/test_cache.py`
- Create: `tests/config/test_reload.py`

**Step 1: 创建缓存管理模块**

File: `src/evan_tools/config/core/cache.py`

```python
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ConfigCache:
    """配置文件缓存管理器"""
    
    def __init__(self):
        self._cache: dict[Path, dict[str, Any]] = {}
    
    def get(self, path: Path) -> dict[str, Any] | None:
        """
        获取缓存内容
        
        Args:
            path: 配置文件路径
            
        Returns:
            缓存内容（包含 mtime）或 None
        """
        return self._cache.get(path)
    
    def set(self, path: Path, content: dict[str, Any], mtime: float) -> None:
        """
        设置缓存
        
        Args:
            path: 配置文件路径
            content: 配置内容
            mtime: 文件修改时间
        """
        self._cache[path] = {
            "mtime": mtime,
            "content": content,
        }
        logger.debug(f"缓存已更新: {path}")
    
    def is_outdated(self, path: Path) -> bool:
        """
        检查缓存是否过期（文件已修改）
        
        Args:
            path: 配置文件路径
            
        Returns:
            是否需要重新加载
        """
        try:
            current_mtime = path.stat().st_mtime
        except OSError as e:
            logger.warning(f"无法获取文件 mtime: {path}, {e}")
            return True
        
        cached = self._cache.get(path)
        if cached is None:
            return True
        
        return cached["mtime"] != current_mtime
    
    def clear(self) -> None:
        """清空所有缓存"""
        self._cache.clear()
        logger.debug("缓存已清空")
```

**Step 2: 创建热加载控制模块**

File: `src/evan_tools/config/core/reload.py`

```python
import logging
import time

logger = logging.getLogger(__name__)


class ReloadController:
    """热加载控制器，管理时间窗口和重加载策略"""
    
    def __init__(self, interval: float = 5.0):
        """
        初始化重加载控制器
        
        Args:
            interval: 检查间隔（秒），默认 5 秒
        """
        self._last_reload_time = 0.0
        self._interval = interval
    
    def should_check_reload(self) -> bool:
        """
        检查是否应该进行重加载检查
        
        基于时间窗口，避免频繁的文件系统检查
        
        Returns:
            是否应该检查
        """
        current_time = time.time()
        if current_time - self._last_reload_time < self._interval:
            return False
        return True
    
    def mark_reloaded(self) -> None:
        """标记已进行重加载，更新时间戳"""
        self._last_reload_time = time.time()
        logger.debug("重加载时间戳已更新")
    
    def set_interval(self, interval: float) -> None:
        """
        设置检查间隔
        
        Args:
            interval: 新的检查间隔（秒）
        """
        self._interval = interval
        logger.debug(f"重加载间隔已设置为 {interval} 秒")
```

**Step 3: 创建缓存模块测试**

File: `tests/config/test_cache.py`

```python
import time
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest

from src.evan_tools.config.core.cache import ConfigCache


@pytest.fixture
def cache():
    return ConfigCache()


def test_cache_set_and_get(cache):
    """测试缓存的设置和获取"""
    config_path = Path("/test/config.yaml")
    content = {"app": {"name": "test"}}
    
    cache.set(config_path, content, 12345.0)
    cached = cache.get(config_path)
    
    assert cached is not None
    assert cached["content"] == content
    assert cached["mtime"] == 12345.0


def test_cache_get_nonexistent(cache):
    """测试获取不存在的缓存"""
    config_path = Path("/test/nonexistent.yaml")
    
    assert cache.get(config_path) is None


def test_cache_clear(cache):
    """测试清空缓存"""
    config_path = Path("/test/config.yaml")
    cache.set(config_path, {"app": {}}, 12345.0)
    
    cache.clear()
    
    assert cache.get(config_path) is None


def test_cache_is_outdated_with_real_file():
    """测试检查真实文件是否过期"""
    cache = ConfigCache()
    
    with NamedTemporaryFile(delete=False, suffix=".yaml") as f:
        path = Path(f.name)
        f.write(b"test")
    
    try:
        # 初始缓存
        mtime = path.stat().st_mtime
        cache.set(path, {"test": "content"}, mtime)
        
        # 缓存应该是最新的
        assert not cache.is_outdated(path)
        
        # 修改文件
        time.sleep(0.1)
        path.write_text("modified")
        
        # 缓存应该过期
        assert cache.is_outdated(path)
    finally:
        path.unlink()
```

**Step 4: 创建重加载控制模块测试**

File: `tests/config/test_reload.py`

```python
import time

import pytest

from src.evan_tools.config.core.reload import ReloadController


def test_reload_controller_should_check_initially():
    """测试初始时应该进行检查"""
    controller = ReloadController(interval=5.0)
    
    assert controller.should_check_reload() is True


def test_reload_controller_time_window():
    """测试时间窗口缓存"""
    controller = ReloadController(interval=0.2)
    
    # 第一次检查
    assert controller.should_check_reload() is True
    controller.mark_reloaded()
    
    # 时间窗口内不检查
    assert controller.should_check_reload() is False
    
    # 等待超过窗口
    time.sleep(0.25)
    assert controller.should_check_reload() is True


def test_reload_controller_set_interval():
    """测试设置重加载间隔"""
    controller = ReloadController(interval=1.0)
    
    controller.set_interval(0.5)
    assert controller.should_check_reload() is True
    controller.mark_reloaded()
    
    # 0.1 秒后，应该不检查（小于 0.5 秒）
    time.sleep(0.1)
    assert controller.should_check_reload() is False
```

**Step 5: 运行测试**

Run: `pytest tests/config/test_cache.py tests/config/test_reload.py -v`

Expected: All tests PASS

**Step 6: Commit**

```bash
git add src/evan_tools/config/core/cache.py src/evan_tools/config/core/reload.py
git add tests/config/test_cache.py tests/config/test_reload.py
git commit -m "feat: add cache and reload controller modules"
```

---

## Task 3: 创建配置合并和 YAML 配置源

**Files:**

- Create: `src/evan_tools/config/core/merger.py`
- Create: `src/evan_tools/config/sources/yaml_source.py`
- Create: `tests/config/test_sources.py`

**Step 1: 创建配置合并模块**

File: `src/evan_tools/config/core/merger.py`

```python
import logging
from typing import Any

import pydash

logger = logging.getLogger(__name__)


class ConfigMerger:
    """配置合并器，按优先级合并多个配置"""
    
    def merge(self, configs: list[dict[str, Any]]) -> dict[str, Any]:
        """
        按优先级合并配置
        
        优先级由配置中的 'priority' 字段决定，数值越大优先级越高
        
        Args:
            configs: 配置字典列表
            
        Returns:
            合并后的配置
        """
        if not configs:
            logger.warning("没有配置要合并")
            return {}
        
        # 按优先级排序
        sorted_configs = sorted(
            configs,
            key=lambda c: c.get("priority", -1)
        )
        
        merged: dict[str, Any] = {}
        for config in sorted_configs:
            pydash.merge(merged, config)
        
        logger.info(f"已合并 {len(configs)} 个配置文件")
        return merged
```

**Step 2: 创建 YAML 配置源**

File: `src/evan_tools/config/sources/yaml_source.py`

```python
import logging
from pathlib import Path
from typing import Any

import yaml

from src.evan_tools.config.core.source import ConfigSource

logger = logging.getLogger(__name__)


class YamlConfigSource(ConfigSource):
    """YAML 格式配置源实现"""
    
    SUPPORTED_EXTENSIONS = {".yaml", ".yml"}
    
    def read(self, path: Path) -> dict[str, Any]:
        """
        读取 YAML 配置文件
        
        Args:
            path: 配置文件路径
            
        Returns:
            配置字典
            
        Raises:
            OSError: 文件访问失败
            yaml.YAMLError: YAML 格式错误
        """
        try:
            with path.open("r", encoding="utf-8") as f:
                content = yaml.safe_load(f) or {}
            logger.debug(f"YAML 文件读取成功: {path}")
            return content
        except yaml.YAMLError as e:
            logger.error(f"YAML 解析失败 {path}: {e}")
            raise ValueError(f"Invalid YAML in {path}") from e
        except OSError as e:
            logger.warning(f"文件读取失败 {path}: {e}")
            raise
    
    def write(self, path: Path, content: dict[str, Any]) -> None:
        """
        写入 YAML 配置文件
        
        Args:
            path: 配置文件路径
            content: 配置字典
            
        Raises:
            OSError: 文件写入失败
        """
        try:
            with path.open("w", encoding="utf-8") as f:
                yaml.safe_dump(content, f, allow_unicode=True, sort_keys=False)
            logger.debug(f"YAML 文件写入成功: {path}")
        except OSError as e:
            logger.error(f"写入配置文件失败 {path}: {e}")
            raise
    
    def supports(self, path: Path) -> bool:
        """
        检查是否支持该文件格式
        
        Args:
            path: 配置文件路径
            
        Returns:
            是否为 YAML/YML 格式
        """
        return path.suffix.lower() in self.SUPPORTED_EXTENSIONS
```

File: `src/evan_tools/config/sources/__init__.py`

```python
from .yaml_source import YamlConfigSource

__all__ = ["YamlConfigSource"]
```

**Step 3: 创建源和合并器测试**

File: `tests/config/test_sources.py`

```python
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest
import yaml

from src.evan_tools.config.sources.yaml_source import YamlConfigSource
from src.evan_tools.config.core.merger import ConfigMerger


class TestYamlConfigSource:
    def test_supports_yaml_files(self):
        """测试支持 YAML 格式识别"""
        source = YamlConfigSource()
        
        assert source.supports(Path("config.yaml"))
        assert source.supports(Path("config.yml"))
        assert not source.supports(Path("config.json"))
    
    def test_read_yaml_file(self):
        """测试读取 YAML 文件"""
        source = YamlConfigSource()
        
        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"app": {"name": "test"}}, f)
            path = Path(f.name)
        
        try:
            content = source.read(path)
            assert content["app"]["name"] == "test"
        finally:
            path.unlink()
    
    def test_write_yaml_file(self):
        """测试写入 YAML 文件"""
        source = YamlConfigSource()
        
        with NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            path = Path(f.name)
        
        try:
            source.write(path, {"app": {"name": "test"}})
            
            with open(path) as f:
                content = yaml.safe_load(f)
            assert content["app"]["name"] == "test"
        finally:
            path.unlink()
    
    def test_read_invalid_yaml(self):
        """测试读取无效 YAML 文件"""
        source = YamlConfigSource()
        
        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: [")
            path = Path(f.name)
        
        try:
            with pytest.raises(ValueError):
                source.read(path)
        finally:
            path.unlink()


class TestConfigMerger:
    def test_merge_empty_list(self):
        """测试合并空列表"""
        merger = ConfigMerger()
        
        result = merger.merge([])
        assert result == {}
    
    def test_merge_single_config(self):
        """测试合并单个配置"""
        merger = ConfigMerger()
        
        result = merger.merge([{"app": {"name": "test"}}])
        assert result == {"app": {"name": "test"}}
    
    def test_merge_multiple_configs_by_priority(self):
        """测试按优先级合并多个配置"""
        merger = ConfigMerger()
        
        configs = [
            {"priority": 10, "app": {"name": "base", "version": "1.0"}},
            {"priority": 20, "app": {"name": "override"}},
        ]
        
        result = merger.merge(configs)
        
        # 优先级高的覆盖低的
        assert result["app"]["name"] == "override"
        # 未覆盖的保留
        assert result["app"]["version"] == "1.0"
```

**Step 4: 运行测试**

Run: `pytest tests/config/test_sources.py -v`

Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/evan_tools/config/core/merger.py src/evan_tools/config/sources/yaml_source.py
git add tests/config/test_sources.py
git commit -m "feat: add merger and yaml config source"
```

---

## Task 4: 创建 ConfigManager 和集成测试

**Files:**

- Create: `src/evan_tools/config/manager.py`
- Create: `tests/config/test_manager.py`

**Step 1: 创建 ConfigManager 统一接口**

File: `src/evan_tools/config/manager.py`

```python
import logging
import os
from pathlib import Path
from typing import Any

import pydash

from src.evan_tools.config.concurrency.rw_lock import RWLock
from src.evan_tools.config.core.cache import ConfigCache
from src.evan_tools.config.core.merger import ConfigMerger
from src.evan_tools.config.core.reload import ReloadController
from src.evan_tools.config.core.source import ConfigSource

logger = logging.getLogger(__name__)

PathT = str | list[str]


class ConfigManager:
    """配置管理器，统一的公共接口"""
    
    def __init__(
        self,
        source: ConfigSource,
        base_path: Path | str | None = None,
        reload_interval: float = 5.0,
    ):
        """
        初始化配置管理器
        
        Args:
            source: 配置源实现
            base_path: 配置文件基础路径，默认为 cwd/config
            reload_interval: 热加载检查间隔（秒）
        """
        self._source = source
        self._base_path = Path(base_path) if base_path else Path.cwd() / "config"
        self._cache = ConfigCache()
        self._reload_controller = ReloadController(interval=reload_interval)
        self._merger = ConfigMerger()
        self._lock = RWLock()
        self._cfg: dict[str, Any] | None = None
        self._config_keys: dict[Path, list[str]] = {}
    
    def load(self) -> None:
        """
        加载配置文件
        
        Raises:
            RuntimeError: 所有配置文件加载失败
        """
        logger.info(f"开始加载配置，路径: {self._base_path}")
        self._lock.acquire_write()
        try:
            self._load_unlocked()
            logger.info("配置加载完成")
        except Exception as e:
            logger.error(f"配置加载失败: {e}")
            raise
        finally:
            self._lock.release_write()
    
    def get(
        self,
        path: PathT | None = None,
        default: Any = None,
    ) -> Any:
        """
        获取配置值
        
        Args:
            path: 配置路径，如 'app.name' 或 ['app', 'name']
            default: 默认值
            
        Returns:
            配置值或默认值
        """
        self._reload_if_needed()
        
        self._lock.acquire_read()
        try:
            if self._cfg is None:
                return default
            
            if path is None:
                from copy import deepcopy
                return deepcopy(self._cfg)
            
            result = pydash.get(self._cfg, path, default)
            logger.debug(f"读取配置: {path}")
            return result
        finally:
            self._lock.release_read()
    
    def sync(self) -> None:
        """
        将内存配置写回文件
        """
        self._reload_if_needed()
        
        self._lock.acquire_write()
        try:
            if self._cfg is None:
                logger.warning("配置为空，无法写入")
                return
            
            for path, keys in self._config_keys.items():
                new_content: dict[str, Any] = {}
                
                for key in keys:
                    v = pydash.get(self._cfg, key)
                    if v is not None:
                        pydash.set_(new_content, key, v)
                
                self._source.write(path, new_content)
                
                # 更新缓存
                mtime = path.stat().st_mtime
                self._cache.set(path, new_content, mtime)
                logger.info(f"配置已写入 {path}")
            
            # 更新重加载时间
            self._reload_controller.mark_reloaded()
        finally:
            self._lock.release_write()
    
    # 私有方法
    
    def _load_unlocked(self) -> None:
        """加载配置（假设已持有写锁）"""
        config_paths = self._scan_config_files()
        
        if not config_paths:
            logger.warning(f"未找到配置文件在 {self._base_path}")
        
        configs = []
        loaded_count = 0
        
        for p in config_paths:
            try:
                content = self._source.read(p)
                if content:
                    loaded_count += 1
                    keys = self._collect_key_paths(content)
                    self._config_keys[p] = keys
                    configs.append(content)
                    
                    mtime = p.stat().st_mtime
                    self._cache.set(p, content, mtime)
            except Exception as e:
                logger.error(f"加载配置文件失败 {p}: {e}")
        
        if config_paths and loaded_count == 0:
            raise RuntimeError(
                f"所有配置文件加载失败，共尝试 {len(config_paths)} 个"
            )
        
        logger.info(f"成功加载 {loaded_count} 个配置文件")
        self._cfg = self._merger.merge(configs)
    
    def _reload_if_needed(self) -> None:
        """检查并进行热加载"""
        if not self._reload_controller.should_check_reload():
            return
        
        # 检查是否有文件改变
        need_reload = self._cfg is None
        
        if not need_reload:
            for path in self._config_keys:
                if self._cache.is_outdated(path):
                    need_reload = True
                    logger.debug(f"配置文件已修改: {path}")
                    break
        
        if need_reload:
            self._lock.acquire_write()
            try:
                self._load_unlocked()
                self._reload_controller.mark_reloaded()
                logger.info("配置已重新加载")
            finally:
                self._lock.release_write()
    
    def _scan_config_files(self) -> list[Path]:
        """扫描配置文件"""
        if self._base_path.is_file():
            return [self._base_path]
        
        result = []
        for root, _, files in os.walk(self._base_path):
            for f in files:
                path = Path(root) / f
                if self._source.supports(path):
                    result.append(path)
        
        return sorted(result)
    
    @staticmethod
    def _collect_key_paths(obj: Any, prefix: str = "") -> list[str]:
        """收集对象中的所有键路径"""
        paths = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                new_prefix = f"{prefix}.{k}" if prefix else k
                paths.extend(ConfigManager._collect_key_paths(v, new_prefix))
        else:
            paths.append(prefix)
        return paths
```

**Step 2: 创建 ConfigManager 集成测试**

File: `tests/config/test_manager.py`

```python
import tempfile
import time
from pathlib import Path

import pytest
import yaml

from src.evan_tools.config.manager import ConfigManager
from src.evan_tools.config.sources.yaml_source import YamlConfigSource


@pytest.fixture
def temp_config_dir():
    """创建临时配置目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def manager(temp_config_dir):
    """创建配置管理器"""
    source = YamlConfigSource()
    return ConfigManager(source, temp_config_dir)


def test_manager_load_simple_config(manager, temp_config_dir):
    """测试加载简单配置"""
    config_file = temp_config_dir / "config.yaml"
    config_file.write_text("app:\n  name: test\n  version: 1.0")
    
    manager.load()
    
    result = manager.get()
    assert result["app"]["name"] == "test"
    assert result["app"]["version"] == 1.0


def test_manager_get_with_path(manager, temp_config_dir):
    """测试使用路径查询配置"""
    config_file = temp_config_dir / "config.yaml"
    config_file.write_text("app:\n  name: test\n  port: 8080")
    
    manager.load()
    
    assert manager.get("app.name") == "test"
    assert manager.get("app.port") == 8080
    assert manager.get("app.missing", "default") == "default"


def test_manager_load_multiple_configs(manager, temp_config_dir):
    """测试加载多个配置文件"""
    (temp_config_dir / "base.yaml").write_text(
        "priority: 10\napp:\n  name: base\n  version: 1.0"
    )
    (temp_config_dir / "override.yaml").write_text(
        "priority: 20\napp:\n  name: override"
    )
    
    manager.load()
    
    result = manager.get()
    assert result["app"]["name"] == "override"
    assert result["app"]["version"] == 1.0


def test_manager_hot_reload(manager, temp_config_dir):
    """测试热加载"""
    config_file = temp_config_dir / "config.yaml"
    config_file.write_text("app:\n  name: v1")
    
    manager.load()
    assert manager.get("app.name") == "v1"
    
    # 修改文件
    time.sleep(0.1)
    config_file.write_text("app:\n  name: v2")
    
    # 强制检查（重置时间戳）
    manager._reload_controller._last_reload_time = 0
    
    # 获取时应该自动重加载
    assert manager.get("app.name") == "v2"


def test_manager_sync_writes_back(manager, temp_config_dir):
    """测试 sync 写回文件"""
    config_file = temp_config_dir / "config.yaml"
    config_file.write_text("app:\n  name: original")
    
    manager.load()
    
    # 修改内存配置
    cfg = manager.get()
    cfg["app"]["name"] = "modified"
    manager._cfg = cfg
    
    # 写回
    manager.sync()
    
    # 验证文件内容
    with open(config_file) as f:
        content = yaml.safe_load(f)
    assert content["app"]["name"] == "modified"
```

**Step 3: 运行集成测试**

Run: `pytest tests/config/test_manager.py -v`

Expected: All tests PASS

**Step 4: Commit**

```bash
git add src/evan_tools/config/manager.py
git add tests/config/test_manager.py
git commit -m "feat: add config manager with unified interface"
```

---

## Task 5: 更新主模块并保持向后兼容性

**Files:**

- Modify: `src/evan_tools/config/__init__.py`
- Modify: `src/evan_tools/config/main.py`

**Step 1: 保留原有的公共 API**

File: `src/evan_tools/config/main.py` （改造为适配层）

```python
"""
配置系统适配层

保持向后兼容的公共 API，委托给 ConfigManager 实现
"""

import logging
from pathlib import Path
from typing import Any

from .manager import ConfigManager
from .sources.yaml_source import YamlConfigSource

logger = logging.getLogger(__name__)

# 全局管理器实例
_manager: ConfigManager | None = None


def load_config(path: Path | str | None = None) -> None:
    """
    从磁盘加载 YAML 配置
    
    Args:
        path: 配置文件或目录路径，默认为 cwd/config
    """
    global _manager
    source = YamlConfigSource()
    _manager = ConfigManager(source, path)
    _manager.load()


def get_config(path: str | list[str] | None = None, default: Any = None) -> Any:
    """
    获取配置值
    
    Args:
        path: 配置路径，如 'app.name'
        default: 默认值
        
    Returns:
        配置值或默认值
    """
    if _manager is None:
        # 如果未加载，尝试默认加载
        load_config()
    
    return _manager.get(path, default)


def sync_config() -> None:
    """
    将内存配置写回文件
    """
    if _manager is None:
        logger.warning("配置未加载，无法同步")
        return
    
    _manager.sync()
```

**Step 2: 更新公共 API 入口**

File: `src/evan_tools/config/__init__.py`

```python
"""
配置管理系统

提供统一的配置加载、查询和持久化接口
"""

from .main import get_config, load_config, sync_config
from .manager import ConfigManager
from .sources.yaml_source import YamlConfigSource
from .core.source import ConfigSource

__all__ = [
    "load_config",
    "get_config",
    "sync_config",
    "ConfigManager",
    "ConfigSource",
    "YamlConfigSource",
]
```

**Step 3: 运行现有测试验证兼容性**

Run: `pytest tests/config/test_main.py -v`

Expected: All tests PASS (uses old API, should still work)

**Step 4: Commit**

```bash
git add src/evan_tools/config/main.py src/evan_tools/config/__init__.py
git commit -m "refactor: convert main.py to adapter layer for backward compatibility"
```

---

## Task 6: 文档和清理

**Files:**

- Create: `src/evan_tools/config/README.md`

**Step 1: 创建模块文档**

File: `src/evan_tools/config/README.md`

```markdown
# 配置管理系统

模块化、可扩展的配置管理系统，基于 SOLID 原则设计。

## 架构

```

ConfigManager
├── ConfigSource (抽象)
│   └── YamlConfigSource (实现)
├── ConfigCache (缓存管理)
├── ReloadController (热加载)
├── ConfigMerger (合并)
└── RWLock (并发控制)

```

## 使用

### 基础 API（向后兼容）

```python
from evan_tools.config import load_config, get_config, sync_config

# 加载配置
load_config()  # 从 cwd/config 加载

# 查询配置
value = get_config("app.name")
value = get_config("app.name", default="unknown")

# 修改并同步
config = get_config()
config["app"]["name"] = "new_name"
sync_config()  # 写回文件
```

### 高级用法（新 API）

```python
from evan_tools.config import ConfigManager
from evan_tools.config.sources.yaml_source import YamlConfigSource

# 创建自定义管理器
source = YamlConfigSource()
manager = ConfigManager(source, base_path="./config", reload_interval=5.0)

manager.load()
value = manager.get("app.name")
manager.sync()
```

### 扩展（实现新格式）

```python
from evan_tools.config.core.source import ConfigSource
from pathlib import Path
from typing import Any
import json

class JsonConfigSource(ConfigSource):
    def read(self, path: Path) -> dict[str, Any]:
        with open(path) as f:
            return json.load(f)
    
    def write(self, path: Path, content: dict[str, Any]) -> None:
        with open(path, "w") as f:
            json.dump(content, f)
    
    def supports(self, path: Path) -> bool:
        return path.suffix == ".json"

# 使用
source = JsonConfigSource()
manager = ConfigManager(source, "./config")
manager.load()
```

## 特性

- ✅ **多格式支持**: 通过实现 `ConfigSource` 接口支持 YAML、JSON、TOML 等
- ✅ **热加载**: 文件修改时自动重加载（可配置时间窗口）
- ✅ **并发安全**: 使用 RWLock 支持多线程读取
- ✅ **缓存优化**: mtime 检查避免频繁文件系统操作
- ✅ **易于测试**: 依赖注入设计，易于模拟
- ✅ **向后兼容**: 现有 API 无需修改

## 模块说明

| 模块 | 职责 |
|------|------|
| `ConfigSource` | 配置源接口 |
| `ConfigCache` | 缓存和 mtime 检查 |
| `ReloadController` | 热加载时间窗口控制 |
| `ConfigMerger` | 多文件合并 |
| `ConfigManager` | 统一管理接口 |
| `YamlConfigSource` | YAML 格式实现 |
| `RWLock` | 读写锁并发控制 |

```

**Step 2: 运行全部测试**

Run: `pytest tests/config/ -v --tb=short`

Expected: All tests PASS

**Step 3: Commit**

```bash
git add src/evan_tools/config/README.md
git commit -m "docs: add comprehensive config system documentation"
```

---

## 最后步骤

**Step 1: 验证完整性**

Run:

```bash
python -c "from evan_tools.config import load_config, get_config, sync_config, ConfigManager; print('All imports successful')"
pytest tests/config/ -v
```

**Step 2: Final commit**

```bash
git log --oneline | head -10
```

Expected: 查看最后 10 个提交，应该都是重构相关的
