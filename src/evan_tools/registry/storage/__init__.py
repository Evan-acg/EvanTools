"""存储层包初始化。

提供默认的内存实现，未来可在此扩展其他后端。
"""

from .memory_store import InMemoryStore

__all__ = ["InMemoryStore"]
