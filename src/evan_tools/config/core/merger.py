"""配置合并器，使用深合并策略。"""

from typing import Any

import pydash


class ConfigMerger:
    """使用深合并策略合并多个配置字典。

    使用 pydash 的 merge_with 进行深合并，确保嵌套
    字典被正确组合而不是被替换。
    """

    @staticmethod
    def merge(*configs: dict[str, Any]) -> dict[str, Any]:
        """深合并多个配置字典。

        后面的配置覆盖前面的配置。嵌套字典被
        递归合并而不是完全替换。

        参数:
            *configs: 可变数量的配置字典用于合并。

        返回:
            包含合并的新配置字典。

        示例:
            >>> base = {"db": {"host": "localhost", "port": 5432}}
            >>> override = {"db": {"host": "prod.example.com"}}
            >>> ConfigMerger.merge(base, override)
            {'db': {'host': 'prod.example.com', 'port': 5432}}
        """
        if not configs:
            return {}

        result: dict[str, Any] = {}
        for config in configs:
            result = pydash.merge_with(result, config)

        return result
