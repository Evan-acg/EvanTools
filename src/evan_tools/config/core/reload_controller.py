"""配置重载控制器，追踪文件修改时间以实现热重载。"""

import os
from pathlib import Path
from typing import Optional


class ReloadController:
    """根据文件更改控制何时应重载配置。

    追踪配置文件的修改时间，并通过比较当前 mtime
    与缓存的 mtime 来确定是否需要重载。

    属性:
        _config_path: 正在跟踪的配置文件路径。
        _last_mtime: 配置文件的最后已知修改时间。
    """

    def __init__(self):
        """初始化重载控制器。"""
        self._config_path: Optional[Path] = None
        self._last_mtime: Optional[float] = None

    def set_config_path(self, config_path: Path) -> None:
        """设置要跟踪的配置文件路径。

        参数:
            config_path: 配置文件的路径。
        """
        self._config_path = config_path
        self._update_mtime()

    def _update_mtime(self) -> None:
        """从文件系统更新缓存的修改时间。"""
        if self._config_path and self._config_path.exists():
            self._last_mtime = os.path.getmtime(self._config_path)
        else:
            self._last_mtime = None

    def has_file_changed(self) -> bool:
        """检查配置文件是否自上次检查以来被修改。

        返回:
            如果文件已更改或不存在，返回 True。
            如果未更改，返回 False。
        """
        if not self._config_path:
            return True

        if not self._config_path.exists():
            if self._last_mtime is not None:
                self._last_mtime = None
                return True
            return False

        current_mtime = os.path.getmtime(self._config_path)
        if self._last_mtime is None:
            self._last_mtime = current_mtime
            return True

        if current_mtime != self._last_mtime:
            self._last_mtime = current_mtime
            return True

        return False

    def reset(self) -> None:
        """重置控制器状态。"""
        self._config_path = None
        self._last_mtime = None
