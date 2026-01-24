"""Setup 模块编排器

编排器负责协调构建器、部署器和清理器的工作，实现完整的构建和部署工作流。
"""

import logging
from pathlib import Path
from typing import Optional

from .config import ProjectConfig
from .exceptions import DeployError, SetupError
from .models import BuildResult, CleanResult, DeployResult
from .protocols import BuilderProtocol, CleanerProtocol, DeployerProtocol


class Orchestrator:
    """项目构建和部署编排器

    编排器负责协调各个组件（构建器、部署器、清理器）完成项目的构建、部署和发布工作流。

    Attributes:
        config: 项目配置对象
        builder: 项目构建器
        deployer: 文件部署器
        cleaner: 文件清理器
        logger: 日志记录器

    Examples:
        >>> from unittest.mock import Mock
        >>> config = ProjectConfig(name="myapp", entry_point="main.py")
        >>> builder = Mock()
        >>> deployer = Mock()
        >>> cleaner = Mock()
        >>> orch = Orchestrator(config, builder, deployer, cleaner)
        >>> result = orch.build()
        >>> assert result.success
    """

    def __init__(
        self,
        config: ProjectConfig,
        builder: BuilderProtocol,
        deployer: DeployerProtocol,
        cleaner: CleanerProtocol,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """初始化编排器

        Args:
            config: 项目配置对象
            builder: 项目构建器协议实现
            deployer: 文件部署器协议实现
            cleaner: 文件清理器协议实现
            logger: 可选的日志记录器。如果不提供，将创建一个默认的日志记录器

        Examples:
            >>> config = ProjectConfig(name="myapp", entry_point="main.py")
            >>> orch = Orchestrator(config, builder, deployer, cleaner)
            >>> assert orch.config.name == "myapp"
        """
        self.config = config
        self.builder = builder
        self.deployer = deployer
        self.cleaner = cleaner
        self.logger = logger or logging.getLogger(__name__)

    def build(self) -> BuildResult:
        """构建项目

        执行清理和构建操作，返回构建结果。

        首先调用清理器清理旧的构建产物，然后调用构建器进行项目构建。

        Returns:
            BuildResult: 构建结果对象，包含构建成功与否、输出路径等信息

        Raises:
            SetupError: 当构建失败时抛出该异常的子类

        Examples:
            >>> result = orch.build()
            >>> if result.success:
            ...     print(f"构建输出: {result.output_path}")
            ... else:
            ...     print(f"构建失败: {result.stderr}")
        """
        self.logger.info("开始构建项目: %s", self.config.name)

        # 清理旧的构建产物
        try:
            self.logger.debug("清理旧的构建产物")
            clean_result = self.cleaner.clean_all()
            if not clean_result.success:
                self.logger.warning(
                    "清理过程中发生错误: %s", clean_result.errors
                )
        except SetupError as e:
            self.logger.error("清理失败: %s", e)
            raise

        # 执行构建
        try:
            self.logger.debug("调用构建器执行项目构建")
            result = self.builder.build(self.config)
            if result.success:
                self.logger.info("构建成功: %s", result.output_path)
            else:
                self.logger.error("构建失败: %s", result.stderr)
            return result
        except SetupError as e:
            self.logger.error("构建异常: %s", e)
            raise

    def deploy(
        self,
        target: Path,
        *,
        clean_dist: bool = True,
    ) -> DeployResult:
        """部署项目到目标位置

        将构建输出部署到指定的目标目录。

        Args:
            target: 目标部署目录路径
            clean_dist: 是否在部署前清理目标目录中的旧文件（默认 True）

        Returns:
            DeployResult: 部署结果对象，包含部署成功与否、文件数量等信息

        Raises:
            DeployError: 当部署失败时抛出

        Examples:
            >>> target = Path("C:/Tools/myapp")
            >>> result = orch.deploy(target)
            >>> print(f"部署了 {result.files_copied} 个文件")
        """
        self.logger.info("开始部署项目到: %s", target)

        try:
            # 获取构建输出路径
            dist_path = Path("dist") / self.config.name
            if not dist_path.exists():
                self.logger.error("构建输出目录不存在: %s", dist_path)
                raise DeployError(
                    f"构建输出目录不存在: {dist_path}",
                    {"dist_path": str(dist_path)},
                )

            self.logger.debug(
                "部署文件从 %s 到 %s (clean_dist=%s)",
                dist_path,
                target,
                clean_dist,
            )
            result = self.deployer.deploy(
                dist_path,
                target,
                clean_old=clean_dist,
            )

            if result.success:
                self.logger.info(
                    "部署成功: 复制了 %d 个文件 (%d 字节)",
                    result.files_copied,
                    result.bytes_copied,
                )
            else:
                self.logger.error("部署失败")

            return result
        except SetupError as e:
            self.logger.error("部署异常: %s", e)
            raise

    def release(
        self,
        target: Path,
        *,
        clean_dist: bool = True,
    ) -> tuple[BuildResult, DeployResult]:
        """执行完整的发布流程

        按顺序执行构建和部署操作，返回两个操作的结果。

        如果构建失败，将不会执行部署。

        Args:
            target: 目标部署目录路径
            clean_dist: 是否在部署前清理目标目录中的旧文件（默认 True）

        Returns:
            包含构建结果和部署结果的元组 (BuildResult, DeployResult)

        Raises:
            SetupError: 当构建或部署失败时抛出相应异常

        Examples:
            >>> target = Path("C:/Tools/myapp")
            >>> build_result, deploy_result = orch.release(target)
            >>> if deploy_result.success:
            ...     print("发布成功！")
        """
        self.logger.info("开始执行发布流程: 构建 + 部署")

        # 首先执行构建
        build_result = self.build()
        if not build_result.success:
            self.logger.error("构建失败，中止发布流程")
            raise SetupError(
                "构建失败，无法继续执行发布流程",
                {"build_success": False},
            )

        # 构建成功后执行部署
        deploy_result = self.deploy(target, clean_dist=clean_dist)

        if deploy_result.success:
            self.logger.info("发布流程完成: 构建和部署都成功")
        else:
            self.logger.error("发布流程中部署失败")

        return build_result, deploy_result
