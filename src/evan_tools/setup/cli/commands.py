"""Setup 模块 CLI 命令

实现命令行界面，提供构建、部署和发布命令。
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import typer

from evan_tools.setup.builders.pyinstaller import PyInstallerBuilder
from evan_tools.setup.cleaners.filesystem import FileSystemCleaner
from evan_tools.setup.core.config import ProjectConfig
from evan_tools.setup.core.exceptions import SetupError
from evan_tools.setup.core.orchestrator import Orchestrator
from evan_tools.setup.deployers.local import LocalDeployer

# 创建 Typer 应用
app = typer.Typer(
    name="setup",
    help="项目构建和部署工具",
)


def create_orchestrator(config: ProjectConfig) -> Orchestrator:
    """创建编排器实例的工厂函数

    根据提供的配置创建具有所有必要依赖的编排器实例。

    Args:
        config: 项目配置对象

    Returns:
        Orchestrator: 配置好的编排器实例

    Examples:
        >>> config = ProjectConfig(name="myapp", entry_point="main.py")
        >>> orch = create_orchestrator(config)
        >>> result = orch.build()
    """
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("setup")

    # 创建依赖实例
    builder = PyInstallerBuilder()
    deployer = LocalDeployer()
    cleaner = FileSystemCleaner(Path.cwd())

    # 创建并返回编排器
    return Orchestrator(config, builder, deployer, cleaner, logger)


@app.command()
def build(
    config_path: Optional[str] = typer.Option(
        None,
        "--config",
        "-c",
        help="项目配置文件路径",
    ),
) -> None:
    """构建项目

    执行项目构建，生成可执行文件。

    Args:
        config_path: 项目配置文件路径（可选）

    Examples:
        >>> from typer.testing import CliRunner
        >>> runner = CliRunner()
        >>> result = runner.invoke(app, ["build"])
        >>> assert result.exit_code == 0
    """
    try:
        # 加载配置
        if config_path:
            # TODO: 从配置文件加载
            config = ProjectConfig(name="testapp", entry_point="main.py")
        else:
            config = ProjectConfig(name="testapp", entry_point="main.py")

        config.validate()

        # 创建编排器
        orch = create_orchestrator(config)

        # 执行构建
        typer.secho("开始构建项目...", fg=typer.colors.BLUE, bold=True)
        result = orch.build()

        if result.success:
            typer.secho(
                f"✓ 构建成功！",
                fg=typer.colors.GREEN,
                bold=True,
            )
            typer.echo(f"  输出路径: {result.output_path}")
            typer.echo(f"  耗时: {result.duration_seconds:.2f}s")
            typer.secho("", bold=False)
        else:
            typer.secho(
                f"✗ 构建失败！",
                fg=typer.colors.RED,
                bold=True,
            )
            if result.stderr:
                typer.secho("错误信息:", fg=typer.colors.RED)
                typer.echo(result.stderr)
            sys.exit(1)

    except SetupError as e:
        typer.secho(f"✗ 错误: {e}", fg=typer.colors.RED, bold=True)
        sys.exit(1)
    except Exception as e:
        typer.secho(
            f"✗ 未预期的错误: {e}",
            fg=typer.colors.RED,
            bold=True,
        )
        sys.exit(1)


@app.command()
def deploy(
    target: str = typer.Argument(
        ...,
        help="目标部署目录路径",
    ),
    config_path: Optional[str] = typer.Option(
        None,
        "--config",
        "-c",
        help="项目配置文件路径",
    ),
    clean_dist: bool = typer.Option(
        True,
        "--clean/--no-clean",
        help="是否清理旧的部署文件",
    ),
) -> None:
    """部署项目

    将构建输出部署到指定目录。

    Args:
        target: 目标部署目录
        config_path: 项目配置文件路径（可选）
        clean_dist: 是否清理旧文件

    Examples:
        >>> from typer.testing import CliRunner
        >>> runner = CliRunner()
        >>> result = runner.invoke(app, ["deploy", "C:/Tools/myapp"])
        >>> assert result.exit_code == 0
    """
    try:
        target_path = Path(target)

        # 加载配置
        if config_path:
            # TODO: 从配置文件加载
            config = ProjectConfig(name="testapp", entry_point="main.py")
        else:
            config = ProjectConfig(name="testapp", entry_point="main.py")

        config.validate()

        # 创建编排器
        orch = create_orchestrator(config)

        # 执行部署
        typer.secho(
            f"开始部署项目到: {target_path}",
            fg=typer.colors.BLUE,
            bold=True,
        )
        result = orch.deploy(target_path, clean_dist=clean_dist)

        if result.success:
            typer.secho(
                f"✓ 部署成功！",
                fg=typer.colors.GREEN,
                bold=True,
            )
            typer.echo(f"  源: {result.source}")
            typer.echo(f"  目标: {result.target}")
            typer.echo(
                f"  文件数: {result.files_copied} "
                f"({result.bytes_copied / 1024:.1f} KB)"
            )
            typer.echo(f"  耗时: {result.duration_seconds:.2f}s")
            typer.secho("", bold=False)
        else:
            typer.secho(
                f"✗ 部署失败！",
                fg=typer.colors.RED,
                bold=True,
            )
            sys.exit(1)

    except SetupError as e:
        typer.secho(f"✗ 错误: {e}", fg=typer.colors.RED, bold=True)
        sys.exit(1)
    except Exception as e:
        typer.secho(
            f"✗ 未预期的错误: {e}",
            fg=typer.colors.RED,
            bold=True,
        )
        sys.exit(1)


@app.command()
def release(
    target: str = typer.Argument(
        ...,
        help="目标部署目录路径",
    ),
    config_path: Optional[str] = typer.Option(
        None,
        "--config",
        "-c",
        help="项目配置文件路径",
    ),
    clean_dist: bool = typer.Option(
        True,
        "--clean/--no-clean",
        help="是否清理旧的部署文件",
    ),
) -> None:
    """执行完整的发布流程

    按顺序执行构建和部署操作。

    Args:
        target: 目标部署目录
        config_path: 项目配置文件路径（可选）
        clean_dist: 是否清理旧文件

    Examples:
        >>> from typer.testing import CliRunner
        >>> runner = CliRunner()
        >>> result = runner.invoke(app, ["release", "C:/Tools/myapp"])
        >>> assert result.exit_code == 0
    """
    try:
        target_path = Path(target)

        # 加载配置
        if config_path:
            # TODO: 从配置文件加载
            config = ProjectConfig(name="testapp", entry_point="main.py")
        else:
            config = ProjectConfig(name="testapp", entry_point="main.py")

        config.validate()

        # 创建编排器
        orch = create_orchestrator(config)

        # 执行发布
        typer.secho(
            "开始执行发布流程...",
            fg=typer.colors.BLUE,
            bold=True,
        )

        build_result, deploy_result = orch.release(target_path, clean_dist=clean_dist)

        # 输出构建结果
        if build_result.success:
            typer.secho("✓ 构建成功", fg=typer.colors.GREEN)
        else:
            typer.secho("✗ 构建失败", fg=typer.colors.RED)

        # 输出部署结果
        if deploy_result.success:
            typer.secho("✓ 部署成功", fg=typer.colors.GREEN)
        else:
            typer.secho("✗ 部署失败", fg=typer.colors.RED)

        # 总结
        typer.secho("")
        if build_result.success and deploy_result.success:
            typer.secho(
                "✓ 发布成功！",
                fg=typer.colors.GREEN,
                bold=True,
            )
            typer.echo(f"  项目已部署到: {deploy_result.target}")
            typer.echo(
                f"  总耗时: {build_result.duration_seconds + deploy_result.duration_seconds:.2f}s"
            )
        else:
            typer.secho(
                "✗ 发布失败！",
                fg=typer.colors.RED,
                bold=True,
            )
            sys.exit(1)

    except SetupError as e:
        typer.secho(f"✗ 错误: {e}", fg=typer.colors.RED, bold=True)
        sys.exit(1)
    except Exception as e:
        typer.secho(
            f"✗ 未预期的错误: {e}",
            fg=typer.colors.RED,
            bold=True,
        )
        sys.exit(1)
