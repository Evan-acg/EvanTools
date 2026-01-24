"""发现层包初始化。

聚合命令元数据定义、提取与索引能力。
"""

from .metadata import CommandMetadata
from .inspector import CommandInspector
from .index import CommandIndex

__all__ = ["CommandMetadata", "CommandInspector", "CommandIndex"]
