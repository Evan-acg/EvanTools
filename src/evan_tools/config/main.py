import logging
import os
import threading
import time
import typing as t
from copy import deepcopy
from pathlib import Path

import pydash
import yaml

logger = logging.getLogger(__name__)


# ============================================================
# RWLock：允许多个读，一个写（非可重入）
# ============================================================
class RWLock:
    def __init__(self):
        self._read_ready = threading.Condition(threading.Lock())
        self._readers = 0

    def acquire_read(self):
        with self._read_ready:
            self._readers += 1

    def release_read(self):
        with self._read_ready:
            self._readers -= 1
            if self._readers == 0:
                self._read_ready.notify_all()

    def acquire_write(self):
        self._read_ready.acquire()
        while self._readers > 0:
            self._read_ready.wait()

    def release_write(self):
        self._read_ready.release()


# ============================================================
# Globals
# ============================================================
_cfg: dict[str, t.Any] | None = None
_config_path_keys: dict[Path, list[str]] = {}
_file_cache: dict[Path, dict[str, t.Any]] = {}
_rw_lock = RWLock()
_last_reload_time: float = 0  # 上次检查文件的时间戳
_reload_check_interval: float = 5.0  # 检查间隔（秒）


# ============================================================
# Internal helpers
# ============================================================
def _scan_yaml_files(base: Path) -> list[Path]:
    if base.is_file():
        return [base]
    return [
        Path(root) / f
        for root, _, files in os.walk(base)
        for f in files
        if f.endswith((".yml", ".yaml"))
    ]


def _read_yaml_cached(path: Path) -> dict[str, t.Any]:
    """读 YAML（带缓存 + mtime 检查）。"""
    global _file_cache

    try:
        mtime = path.stat().st_mtime
    except OSError as e:
        logger.warning(f"无法访问配置文件 {path}: {e}")
        return {}

    cached = _file_cache.get(path)

    if cached and cached["mtime"] == mtime:
        return cached["content"]

    try:
        with path.open("r", encoding="utf-8") as f:
            content = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        logger.error(f"YAML 解析失败 {path}: {e}")
        return {}
    except OSError as e:
        logger.warning(f"文件读取失败 {path}: {e}")
        return {}

    _file_cache[path] = {
        "mtime": mtime,
        "content": content,
    }
    return content


def _collect_key_paths(obj: t.Any, prefix: str = "") -> list[str]:
    paths = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_prefix = f"{prefix}.{k}" if prefix else k
            paths.extend(_collect_key_paths(v, new_prefix))
    else:
        paths.append(prefix)
    return paths


def _load_config_unlocked(path: Path | None = None) -> None:
    """
    真正的加载逻辑（假设调用方已持有写锁）。
    这个函数不会获取任何锁 — 调用者必须保证写锁被持有。
    """
    global _cfg, _config_path_keys, _file_cache

    base = Path.cwd() / "config" if path is None else Path(path)
    
    try:
        config_paths = _scan_yaml_files(base)
    except OSError as e:
        logger.error(f"无法扫描配置目录 {base}: {e}")
        raise

    if not config_paths:
        logger.warning(f"未找到任何配置文件在 {base}")

    merged: dict[str, t.Any] = {}
    _config_path_keys.clear()

    contents: list[dict[str, t.Any]] = []
    loaded_count = 0

    for p in config_paths:
        item = _read_yaml_cached(p)
        if item:  # 只统计成功加载的
            loaded_count += 1
            key_paths = _collect_key_paths(item)
            _config_path_keys[p] = key_paths
            contents.append(item)
        else:
            logger.debug(f"跳过配置文件 {p}（为空或加载失败）")

    # 如果一个配置文件都没加载成功，抛出异常
    if config_paths and loaded_count == 0:
        raise RuntimeError(f"所有配置文件加载失败，共尝试 {len(config_paths)} 个")

    logger.info(f"成功加载 {loaded_count} 个配置文件")

    sorted_contents = sorted(contents, key=lambda o: o.get("priority", -1))

    for item in sorted_contents:
        pydash.merge(merged, item)

    _cfg = merged


def _reload_if_needed() -> bool:
    """检查文件是否变化，如需重新加载则执行加载（返回是否重载）。"""
    global _cfg, _last_reload_time

    current_time = time.time()
    
    # 检查是否在时间窗口内，如果是则跳过检查
    if current_time - _last_reload_time < _reload_check_interval:
        return False

    _rw_lock.acquire_read()
    try:
        if _cfg is None:
            need_reload = True
        else:
            need_reload = False
            for path in _config_path_keys:
                try:
                    if not path.exists():
                        need_reload = True
                        logger.debug(f"配置文件已删除: {path}")
                        break
                    mtime = path.stat().st_mtime
                    cached = _file_cache.get(path)
                    if not cached or cached["mtime"] != mtime:
                        need_reload = True
                        logger.debug(f"配置文件已修改: {path}")
                        break
                except OSError as e:
                    logger.warning(f"检查文件变化失败 {path}: {e}")
                    need_reload = True
                    break
    finally:
        _rw_lock.release_read()

    if not need_reload:
        return False

    _rw_lock.acquire_write()
    try:
        _load_config_unlocked()
        _last_reload_time = time.time()  # 更新最后检查时间
        logger.info("配置已重新加载")
    finally:
        _rw_lock.release_write()

    return True


# ============================================================
# Public APIs
# ============================================================
def load_config(path: Path | None = None) -> None:
    """从磁盘加载 YAML 配置（外部调用会获取写锁）。"""
    logger.info(f"开始加载配置，路径: {path or 'config'}")
    _rw_lock.acquire_write()
    try:
        _load_config_unlocked(path)
        logger.info("配置加载完成")
    except Exception as e:
        logger.error(f"配置加载失败: {e}")
        raise
    finally:
        _rw_lock.release_write()


PathT = t.Union[t.Hashable, t.List[t.Hashable]]


@t.overload
def get_config[T](path: PathT, default: T) -> T: ...


@t.overload
def get_config[T](path: PathT, default: None = None) -> T | None: ...


@t.overload
def get_config(path: None = None, default: t.Any = None) -> t.Any: ...


def get_config(path: PathT | None = None, default: t.Any = None) -> t.Any:
    """拿到完整配置（读锁）+ 自动检查文件变化"""
    reloaded = _reload_if_needed()
    if reloaded:
        logger.info(f"配置热加载完成")

    _rw_lock.acquire_read()
    try:
        assert _cfg is not None
        _o = deepcopy(_cfg)
        if path is None:
            return _o
        result = pydash.get(_o, path, default)
        logger.debug(f"读取配置: {path}")
        return result
    finally:
        _rw_lock.release_read()


def sync_config() -> None:
    """把 _cfg 写回各 YAML 文件（写锁）"""
    global _cfg, _file_cache, _last_reload_time

    _reload_if_needed()

    _rw_lock.acquire_write()
    try:
        if _cfg is None:
            logger.warning("配置为空，无法写入")
            return

        for path, keys in _config_path_keys.items():
            new_content: dict[str, t.Any] = {}

            for key in keys:
                v = pydash.get(_cfg, key)
                if v is not None:
                    pydash.set_(new_content, key, v)

            try:
                with path.open("w", encoding="utf-8") as f:
                    yaml.safe_dump(new_content, f, allow_unicode=True, sort_keys=False)
                
                # 更新缓存 mtime，避免下次立即重加载
                mtime = path.stat().st_mtime
                _file_cache[path] = {
                    "mtime": mtime,
                    "content": new_content,
                }
                logger.info(f"配置已写入 {path}")
            except OSError as e:
                logger.error(f"写入配置文件失败 {path}: {e}")
                raise

        # 更新最后重加载时间，防止刚写完马上又重加载
        _last_reload_time = time.time()
    finally:
        _rw_lock.release_write()
