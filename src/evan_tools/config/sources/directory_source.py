"""基于目录的配置源，支持多文件扫描。"""

import logging
from pathlib import Path
from typing import Any, Optional

from .yaml_source import YamlConfigSource

logger = logging.getLogger(__name__)


class DirectoryConfigSource(YamlConfigSource):
    """扫描并合并来自目录的多个 YAML 文件的配置源。

    扩展 YamlConfigSource 以支持从目录加载所有 YAML 文件，
    按排序顺序（确定的优先级）合并它们。
    """

    def read(self, path: Path, base_path: Optional[Path] = None) -> dict[str, Any]:
        """读取并合并目录中的所有 YAML 文件。

        如果路径是目录，扫描所有 .yaml/.yml 文件并合并它们。
        如果路径是文件，委托给父类 YamlConfigSource.read()。

        参数:
            path: 目录或 YAML 文件的路径。
            base_path: 用于解析相对路径的可选基目录。

        返回:
            合并的配置字典。

        抛出:
            FileNotFoundError: 如果路径不存在。
            yaml.YAMLError: 如果任何文件不是有效的 YAML。
        """
        resolved_path = self._resolve_path(path, base_path)

        if not resolved_path.exists():
            raise FileNotFoundError(f"Configuration path not found: {resolved_path}")

        if resolved_path.is_file():
            return super().read(path, base_path)

        return self._read_directory(resolved_path)

    def _read_directory(self, directory: Path) -> dict[str, Any]:
        """读取并合并目录中的所有 YAML 文件。

        参数:
            directory: 目录路径。

        返回:
            来自所有 YAML 文件的合并配置。
        """
        yaml_files = sorted(
            list(directory.glob("*.yaml")) + list(directory.glob("*.yml"))
        )

        if not yaml_files:
            logger.warning(f"No YAML files found in {directory}")
            return {}

        merged_config: dict[str, Any] = {}

        for yaml_file in yaml_files:
            try:
                file_config = super().read(yaml_file)
                from ..core.merger import ConfigMerger
                merged_config = ConfigMerger.merge(merged_config, file_config)
                logger.debug(f"Loaded and merged {yaml_file.name}")
            except Exception as e:
                logger.error(f"Failed to load {yaml_file}: {e}")
                continue

        logger.info(f"Loaded and merged {len(yaml_files)} YAML files from {directory}")
        return merged_config

    def supports(self, path: Path) -> bool:
        """检查此源是否支持给定路径。

        支持目录和 YAML 文件。

        参数:
            path: 要检查的路径。

        返回:
            如果路径是目录或具有 .yaml/.yml 扩展名，返回 True。
        """
        return path.is_dir() or path.suffix.lower() in {'.yaml', '.yml'}

    def write(self, path: Path, config: dict[str, Any],
              base_path: Optional[Path] = None) -> None:
        """将配置写入 YAML 文件。

        对于目录，不支持此操作。改用文件路径。
        对于文件，委托给父类 YamlConfigSource.write()。

        参数:
            path: 目录或 YAML 文件的路径。
            config: 要写入的配置字典。
            base_path: 用于解析相对路径的可选基目录。

        抛出:
            ValueError: 如果路径是目录。
        """
        resolved_path = self._resolve_path(path, base_path)

        if resolved_path.is_dir():
            raise ValueError(
                f"Cannot write to directory {resolved_path}. "
                "Use a specific YAML file path instead."
            )

        super().write(path, config, base_path)
