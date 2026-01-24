import importlib
import pkgutil
import typing as t
from functools import wraps

import typer

_Registry = tuple[str | None, str, t.Callable[..., None]]
_registered_commands: list[_Registry] = []


def register_command(
    name: str, group: str | None = None
) -> t.Callable[[t.Callable[..., None]], t.Callable[..., None]]:
    def decorator(fn: t.Callable[..., None]) -> t.Callable[..., None]:
        @wraps(fn)
        def wrapper(*args: t.Any, **kwargs: t.Any) -> t.Any:
            return fn(*args, **kwargs)

        _registered_commands.append((group, name, fn))
        return wrapper

    return decorator


def get_registry() -> list[_Registry]:
    return _registered_commands.copy()


def register_with_typer(app: typer.Typer) -> None:
    group_apps: dict[str, typer.Typer] = {}
    for group, name, func in get_registry():
        if group is None:
            app.command(name)(func)
            continue

        if group not in group_apps:
            group_apps[group] = typer.Typer()
            app.add_typer(group_apps[group], name=group)

        group_apps[group].command(name)(func)


def load_commands(module_src: str, *, verbose: bool = False) -> None:
    m = importlib.import_module(module_src)

    prefix: str = f"{module_src}."

    for _, name, is_pkg in pkgutil.iter_modules(m.__path__):
        module_name = f"{prefix}{name}"
        if verbose:
            print(f"Loading commands from module: {module_name}")
        importlib.import_module(module_name)
        if is_pkg:
            load_commands(module_name, verbose=verbose)


class RegistryManager:
    """统一的注册表管理器 - 提供对所有组件的访问"""

    def __init__(self) -> None:
        """初始化管理器"""
        from .tracking.tracker import ExecutionTracker
        from .tracking.monitor import PerformanceMonitor
        from .discovery.index import CommandIndex
        from .dashboard.dashboard import RegistryDashboard

        self._tracker = ExecutionTracker()
        self._monitor = PerformanceMonitor(self._tracker)
        self._cmd_index = CommandIndex()
        self._dashboard = RegistryDashboard(self._tracker, self._cmd_index)

    def enable_tracking(self) -> None:
        """启用执行跟踪"""
        self._tracker.start_tracking()

    def disable_tracking(self) -> None:
        """禁用执行跟踪"""
        self._tracker.stop_tracking()

    def get_tracker(self) -> t.Any:
        """获取执行跟踪器"""
        return self._tracker

    def get_monitor(self) -> t.Any:
        """获取性能监视器"""
        return self._monitor

    def get_command_index(self) -> t.Any:
        """获取命令索引"""
        return self._cmd_index

    def get_dashboard(self) -> t.Any:
        """获取仪表板"""
        return self._dashboard
