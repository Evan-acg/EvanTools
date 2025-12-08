# from .config import get_config, load_config, sync_config
# from .file import gather_paths
# from .md5 import MD5Result, calc_full_md5, calc_sparse_md5
# from .registry import get_registry, load_commands, register_command, register_with_typer
# from .setup import AutoDeployer, ProjectConfig, run_deployer
# from .time import duration
# from .tui import Tui

# __all__ = [
#     "gather_paths",
#     "ProjectConfig",
#     "AutoDeployer",
#     "run_deployer",
#     "calc_sparse_md5",
#     "MD5Result",
#     "calc_full_md5",
#     "load_config",
#     "get_config",
#     "sync_config",
#     "Tui",
#     "duration",
#     "register_command",
#     "get_registry",
#     "register_with_typer",
#     "load_commands",
# ]

# flake8: noqa: F403, F401
import sys
import typing as t

from .config import *
from .file import *
from .md5 import *
from .registry import *
from .setup import *
from .time import *
from .tui import *

_pkg = __name__


_all: list[str] = []
for mod_name, mod in list(sys.modules.items()):
    if mod_name.startswith(_pkg + ".") and hasattr(mod, "__all__"):
        _all.extend(mod.__all__)

__all__: list[str] = list(dict.fromkeys(_all))  # pyright: ignore[reportUnsupportedDunderAll]
