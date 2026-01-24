"""PyInstaller 构建器实现

提供了使用 PyInstaller 构建 Python 项目为可执行文件的实现。
"""

import subprocess
import sys
from pathlib import Path

from ..core.config import ProjectConfig
from ..core.exceptions import BuildError, ConfigValidationError
from ..core.models import BuildResult
from .base import BuilderBase


class PyInstallerBuilder(BuilderBase):
    """PyInstaller 构建器

    使用 PyInstaller 将 Python 项目构建为可执行文件的构建器实现。

    Attributes:
        work_dir: 工作目录
        output_dir: 输出目录
        clean_before_build: 构建前是否清理旧文件

    Examples:
        >>> builder = PyInstallerBuilder()
        >>> config = ProjectConfig(name="myapp", entry_point="main.py")
        >>> result = builder.build(config)
        >>> print(f"构建耗时: {result.duration_seconds:.2f}s")
    """

    def __init__(
        self,
        work_dir: Path | None = None,
        output_dir: Path | None = None,
        clean_before_build: bool = True,
    ) -> None:
        """初始化 PyInstaller 构建器

        Args:
            work_dir: 工作目录，默认为当前目录
            output_dir: 输出目录，默认为 'dist'
            clean_before_build: 构建前是否清理旧文件，默认为 True
        """
        super().__init__(work_dir, output_dir)
        self.clean_before_build = clean_before_build
        self._build_dir = self.work_dir / "build"
        self._spec_file_pattern = "{name}.spec"

    def prepare_command(self, config: ProjectConfig) -> list[str]:
        """准备 PyInstaller 构建命令

        根据配置生成完整的 PyInstaller 命令行。

        Args:
            config: 项目配置对象

        Returns:
            PyInstaller 命令的字符串列表

        Raises:
            ConfigValidationError: 配置无效时抛出

        Examples:
            >>> builder = PyInstallerBuilder()
            >>> config = ProjectConfig(name="myapp", entry_point="main.py")
            >>> cmd = builder.prepare_command(config)
            >>> print(cmd[:3])
            ['python', '-m', 'PyInstaller']
        """
        # 首先验证配置
        try:
            config.validate()
        except Exception as e:
            raise ConfigValidationError(f"配置验证失败: {str(e)}")

        # 基础命令
        cmd = [
            sys.executable,
            "-m",
            "PyInstaller",
            "--clean",
            "--noconfirm",
            "--name",
            config.name,
        ]

        # 添加输出目录选项
        cmd.extend(["--distpath", str(self.output_dir)])
        cmd.extend(["--buildpath", str(self._build_dir)])

        # 添加 spec 文件选项
        spec_file = self._get_spec_file_path(config.name)
        cmd.extend(["--specpath", str(self.work_dir)])

        # 处理打包模式（onedir 或 onefile）
        if config.use_one_dir:
            cmd.append("--onedir")
            cmd.extend(["--contents-directory", f"{config.name}_Internal"])
        else:
            cmd.append("--onefile")

        # 添加数据文件
        for data in config.add_data:
            cmd.extend(["--add-data", data])

        # 添加隐藏导入
        for hidden_import in config.hidden_imports:
            cmd.extend(["--hidden-import", hidden_import])

        # 添加排除模块
        for exclude_module in config.exclude_modules:
            cmd.extend(["--exclude-module", exclude_module])

        # 添加图标（如果存在）
        if config.icon_path is not None:
            icon_path = Path(config.icon_path)
            if icon_path.exists():
                cmd.extend(["--icon", str(icon_path.resolve())])
            else:
                self.logger.warning(f"图标文件不存在，将被忽略: {icon_path}")

        # 添加入口点
        cmd.append(config.entry_point)

        return cmd

    def build(self, config: ProjectConfig) -> BuildResult:
        """执行 PyInstaller 构建

        运行 PyInstaller 命令构建项目，并捕获输出和执行结果。

        Args:
            config: 项目配置对象

        Returns:
            BuildResult: 包含构建结果的对象

        Raises:
            BuildError: 构建失败时抛出

        Examples:
            >>> builder = PyInstallerBuilder()
            >>> config = ProjectConfig(name="myapp", entry_point="main.py")
            >>> result = builder.build(config)
            >>> if result.success:
            ...     print(f"可执行文件位于: {result.output_path}")
        """
        # 清理旧的构建文件（如果需要）
        if self.clean_before_build:
            self._clean_build_artifacts(config.name)

        # 准备命令
        try:
            command = self.prepare_command(config)
        except ConfigValidationError as e:
            self.logger.error(f"配置验证失败: {e}")
            raise

        # 记录命令
        self._log_command(command)

        # 执行构建并测量时间
        try:
            result, duration = self._measure_time(
                self._run_pyinstaller, command
            )
            stdout, stderr = result

            # 确定输出路径
            if config.use_one_dir:
                output_path = self.output_dir / config.name
            else:
                output_path = self.output_dir / f"{config.name}.exe"

            # 创建构建结果
            build_result = BuildResult(
                success=True,
                output_path=output_path,
                duration_seconds=duration,
                command=command,
                stdout=stdout,
                stderr=stderr,
                metadata={
                    "mode": "onedir" if config.use_one_dir else "onefile",
                    "config_name": config.name,
                },
            )

            self.logger.info(f"构建成功: {output_path} (耗时 {duration:.2f}s)")
            return build_result

        except BuildError as e:
            self.logger.error(f"构建失败: {e}")
            raise

    def _run_pyinstaller(self, command: list[str]) -> tuple[str, str]:
        """运行 PyInstaller 命令

        执行 PyInstaller 命令并捕获标准输出和错误输出。

        Args:
            command: PyInstaller 命令列表

        Returns:
            元组 (stdout, stderr)

        Raises:
            BuildError: 当 PyInstaller 执行失败时抛出
        """
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                cwd=self.work_dir,
            )
            return result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            error_msg = f"PyInstaller 执行失败 (exit code: {e.returncode})"
            raise BuildError(
                error_msg,
                {
                    "exit_code": e.returncode,
                    "stdout": e.stdout or "",
                    "stderr": e.stderr or "",
                },
            ) from e
        except FileNotFoundError as e:
            error_msg = f"PyInstaller 未找到或 Python 不可用: {e}"
            raise BuildError(error_msg, {"original_error": str(e)}) from e

    def _clean_build_artifacts(self, project_name: str) -> None:
        """清理旧的构建文件

        删除旧的 dist、build 和 spec 文件。

        Args:
            project_name: 项目名称
        """
        import shutil

        # 清理 dist 目录
        if self.output_dir.exists():
            self.logger.debug(f"删除目录: {self.output_dir}")
            shutil.rmtree(self.output_dir, ignore_errors=True)

        # 清理 build 目录
        if self._build_dir.exists():
            self.logger.debug(f"删除目录: {self._build_dir}")
            shutil.rmtree(self._build_dir, ignore_errors=True)

        # 清理 spec 文件
        spec_file = self._get_spec_file_path(project_name)
        if spec_file.exists():
            self.logger.debug(f"删除文件: {spec_file}")
            spec_file.unlink()

    def _get_spec_file_path(self, project_name: str) -> Path:
        """获取 spec 文件的完整路径

        Args:
            project_name: 项目名称

        Returns:
            spec 文件的完整路径
        """
        spec_filename = self._spec_file_pattern.format(name=project_name)
        return self.work_dir / spec_filename
