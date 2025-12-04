from operator import add
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import typer


@dataclass
class ProjectConfig:
    # 项目名称
    name: str
    # 入口点脚本
    entry_point: str = "starter.py"
    # 隐藏导入的模块
    hidden_imports: list[str] = field(default_factory=list)
    # 额外包含的数据文件
    add_data: list[str] = field(default_factory=list)
    # 排除的模块
    exclude_modules: list[str] = field(default_factory=list)
    # 应用图标路径
    icon_path: Path | None = None
    # 默认部署路径
    default_deploy_path: Path = Path(r"C:\Tools")
    # True: 使用单文件部署，False: 使用单目录部署
    use_one_dir: bool = True


class AutoDeployer:
    def __init__(self, config: ProjectConfig):
        self.config = config
        self.dist_path = Path("dist")
        self.build_path = Path("build")
        self.spec_file = Path(f"{self.config.name}.spec")

    def clean(self):
        """清理构建生成的文件和目录。"""
        print("清理构建文件...")
        shutil.rmtree(self.dist_path, ignore_errors=True)
        shutil.rmtree(self.build_path, ignore_errors=True)
        if self.spec_file.exists():
            self.spec_file.unlink()

    def prepare_command(self) -> list[str]:
        cmd = [
            sys.executable,
            "-m",
            "PyInstaller",
            "--clean",
            "--noconfirm",
            "--name",
            self.config.name,
        ]

        if self.config.use_one_dir:
            cmd.append("--onedir")
            cmd.extend(["--contents-directory", f"{self.config.name}_Internal"])
        else:
            cmd.append("--onefile")

        for data in self.config.add_data:
            cmd.extend(["--add-data", data])

        for imp in self.config.hidden_imports:
            cmd.extend(["--hidden-import", imp])

        for exc in self.config.exclude_modules:
            cmd.extend(["--exclude-module", exc])

        if self.config.icon_path and Path(self.config.icon_path).exists():
            cmd.extend(["--icon", self.config.icon_path.resolve().as_posix()])

        cmd.append(self.config.entry_point)

        return cmd

    def build(self):
        """构建项目为可执行文件。"""
        self.clean()
        typer.secho("构建项目...", fg=typer.colors.BLUE)

        cmd = self.prepare_command()

        typer.echo(f"执行命令: {' '.join(cmd)}")

        try:
            subprocess.run(cmd, check=True)
            typer.secho("构建成功！", fg=typer.colors.GREEN, bold=True)
            typer.echo(f"可执行文件位于: {self.dist_path / self.config.name}")
            typer.echo(f"输出位置： {self.dist_path / self.config.name}")
        except subprocess.CalledProcessError as e:
            typer.secho(f"构建失败！ {e}", fg=typer.colors.RED, bold=True)
            sys.exit(1)

    def deploy(self, target_folder: Path) -> None:
        """部署"""
        typer.secho(f"部署到 {target_folder}...", fg=typer.colors.BLUE)

        if not self.dist_path.exists():
            typer.secho(
                "部署失败：找不到构建输出目录。请先构建项目。",
                fg=typer.colors.RED,
                bold=True,
            )
            raise typer.Exit(code=1)

        if self.config.use_one_dir:
            source = self.dist_path / self.config.name
        else:
            source = self.dist_path / f"{self.config.name}.exe"

        if not source.exists():
            typer.secho(
                "部署失败：找不到可执行文件。请先构建项目。",
                fg=typer.colors.RED,
                bold=True,
            )
            raise typer.Exit(code=1)

        destination = (
            target_folder / self.config.name
            if self.config.use_one_dir
            else target_folder / f"{self.config.name}.exe"
        )

        try:
            target_folder.mkdir(parents=True, exist_ok=True)

            if self.config.use_one_dir:
                shutil.copytree(source, destination, dirs_exist_ok=True)
            else:
                shutil.copy2(source, destination)

            typer.secho("部署成功！", fg=typer.colors.GREEN, bold=True)
        except Exception as e:
            typer.secho(f"部署失败：{e}", fg=typer.colors.RED, bold=True)
            raise typer.Exit(code=1)


def run_deployer(config: ProjectConfig) -> None:
    app = typer.Typer(help="自动化构建和部署工具", add_completion=False)
    deployer = AutoDeployer(config)

    @app.command()
    def build():
        deployer.build()

    @app.command()
    def deploy(
        folder: Path = typer.Option(
            config.default_deploy_path,
            "-f",
            "--folder",
            help="部署目标文件夹路径",
        ),
    ) -> None:
        deployer.deploy(folder)

    @app.command()
    def release(
        folder: Path = typer.Option(
            config.default_deploy_path, "-f", "--folder", help="部署目标文件夹路径"
        ),
    ) -> None:
        deployer.build()
        deployer.deploy(folder)

    if __name__ == "__main__":
        pass

    app()
