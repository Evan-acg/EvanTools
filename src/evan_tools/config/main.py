import os
import threading
import typing as t
from copy import deepcopy
from pathlib import Path

import pydash
import yaml


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

    mtime = path.stat().st_mtime
    cached = _file_cache.get(path)

    if cached and cached["mtime"] == mtime:
        return cached["content"]

    with path.open("r", encoding="utf-8") as f:
        content = yaml.safe_load(f) or {}

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
    config_paths = _scan_yaml_files(base)

    merged: dict[str, t.Any] = {}
    _config_path_keys.clear()

    for p in config_paths:
        item = _read_yaml_cached(p)
        key_paths = _collect_key_paths(item)
        _config_path_keys[p] = key_paths
        pydash.merge(merged, item)

    _cfg = merged


def _reload_if_needed() -> bool:
    """检查文件是否变化，如需重新加载则执行加载（返回是否重载）。"""
    global _cfg

    _rw_lock.acquire_read()
    try:
        if _cfg is None:
            need_reload = True
        else:
            need_reload = False
            for path in _config_path_keys:
                if not path.exists():
                    need_reload = True
                    break
                mtime = path.stat().st_mtime
                cached = _file_cache.get(path)
                if not cached or cached["mtime"] != mtime:
                    need_reload = True
                    break
    finally:
        _rw_lock.release_read()

    if not need_reload:
        return False

    _rw_lock.acquire_write()
    try:
        _load_config_unlocked()
    finally:
        _rw_lock.release_write()

    return True


# ============================================================
# Public APIs
# ============================================================
def load_config(path: Path | None = None) -> None:
    """从磁盘加载 YAML 配置（外部调用会获取写锁）。"""
    _rw_lock.acquire_write()
    try:
        _load_config_unlocked(path)
    finally:
        _rw_lock.release_write()


PathT = t.Union[t.Hashable, t.List[t.Hashable]]


def get_config(path: PathT | None = None, _default: t.Any = None) -> dict[str, t.Any]:
    """拿到完整配置（读锁）+ 自动检查文件变化"""
    _reload_if_needed()

    _rw_lock.acquire_read()
    try:
        assert _cfg is not None
        _o = deepcopy(_cfg)
        if path is None:
            return _o
        return pydash.get(_o, path, _default)
    finally:
        _rw_lock.release_read()


def sync_config() -> None:
    """把 _cfg 写回各 YAML 文件（写锁）"""
    global _cfg, _file_cache

    _reload_if_needed()

    _rw_lock.acquire_write()
    try:
        if _cfg is None:
            return

        for path, keys in _config_path_keys.items():
            new_content: dict[str, t.Any] = {}

            for key in keys:
                v = pydash.get(_cfg, key)
                if v is not None:
                    pydash.set_(new_content, key, v)

            with path.open("w", encoding="utf-8") as f:
                yaml.safe_dump(new_content, f, allow_unicode=True, sort_keys=False)

            _file_cache[path] = {
                "mtime": path.stat().st_mtime,
                "content": new_content,
            }
    finally:
        _rw_lock.release_write()
