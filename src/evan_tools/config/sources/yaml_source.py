"""YAML 配置源实现。"""

import logging
from pathlib import Path
from typing import Any, Optional

import yaml

from ..core.source import ConfigSource

logger = logging.getLogger(__name__)


class YamlConfigSource(ConfigSource):
    """YAML 文件的配置源。

    使用 PyYAML 读写配置文件。
    支持安全加载，并尽可能保留格式。
    """

    def read(self, path: Path, base_path: Optional[Path] = None) -> dict[str, Any]:
        """从 YAML 文件读取配置。

        参数:
            path: YAML 文件的路径。
            base_path: 用于解析相对路径的可选基目录。

        返回:
            配置字典。

        抛出:
            FileNotFoundError: 如果文件不存在。
            yaml.YAMLError: 如果文件不是有效的 YAML。
        """
        resolved_path = self._resolve_path(path, base_path)

        if not resolved_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {resolved_path}")

        try:
            with open(resolved_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if data is None:
                data = {}

            logger.info(f"Loaded configuration from {resolved_path}")
            return data

        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML file {resolved_path}: {e}")
            raise

    def write(self, path: Path, config: dict[str, Any],
              base_path: Optional[Path] = None) -> None:
        """将配置写入 YAML 文件。

        参数:
            path: 要写入的 YAML 文件路径。
            config: 要写入的配置字典。
            base_path: 用于解析相对路径的可选基目录。

        抛出:
            IOError: 如果写入失败。
        """
        resolved_path = self._resolve_path(path, base_path)
        resolved_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(resolved_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(config, f, default_flow_style=False,
                              allow_unicode=True, sort_keys=False)

            logger.info(f"Wrote configuration to {resolved_path}")

        except IOError as e:
            logger.error(f"Failed to write YAML file {resolved_path}: {e}")
            raise

    def supports(self, path: Path) -> bool:
        """检查此源是否支持给定文件路径。

        参数:
            path: 要检查的路径。

        返回:
            如果文件具有 .yaml 或 .yml 扩展名，返回 True。
        """
        return path.suffix.lower() in {'.yaml', '.yml'}

    def _resolve_path(self, path: Path, base_path: Optional[Path]) -> Path:
        """针对基路径解析可能的相对路径。

        参数:
            path: 要解析的路径。
            base_path: 可选的基目录。

        返回:
            绝对路径。
        """
        if path.is_absolute():
            return path

        if base_path is None:
            return path.resolve()

        return (base_path / path).resolve()
