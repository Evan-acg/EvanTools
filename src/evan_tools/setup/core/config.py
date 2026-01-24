"""Setup 模块配置管理

定义了项目配置的数据类和验证逻辑。
"""

from dataclasses import dataclass, field
from pathlib import Path

from .exceptions import ConfigValidationError


@dataclass
class ProjectConfig:
    """项目配置数据类

    封装了项目构建和部署所需的所有配置信息。

    Attributes:
        name: 项目名称
        entry_point: 入口点脚本路径
        hidden_imports: 隐藏导入的模块列表
        add_data: 额外包含的数据文件列表
        exclude_modules: 排除的模块列表
        icon_path: 应用图标路径
        default_deploy_path: 默认部署路径
        use_one_dir: True 使用单目录部署，False 使用单文件部署

    Examples:
        >>> config = ProjectConfig(
        ...     name="myapp",
        ...     entry_point="main.py",
        ...     hidden_imports=["pkg_resources"],
        ...     icon_path=Path("assets/icon.ico")
        ... )
        >>> config.validate()  # 验证配置
    """

    name: str
    entry_point: str = "starter.py"
    hidden_imports: list[str] = field(default_factory=list)
    add_data: list[str] = field(default_factory=list)
    exclude_modules: list[str] = field(default_factory=list)
    icon_path: Path | None = None
    default_deploy_path: Path = field(default_factory=lambda: Path(r"C:\Tools"))
    use_one_dir: bool = True

    def validate(self) -> None:
        """验证配置的有效性

        检查配置项是否满足要求，如入口文件是否存在等。

        Raises:
            ConfigValidationError: 当配置无效时抛出

        Examples:
            >>> config = ProjectConfig(name="", entry_point="main.py")
            >>> config.validate()  # 抛出 ConfigValidationError
        """
        # 验证项目名称
        if not self.name or not self.name.strip():
            raise ConfigValidationError("项目名称不能为空", {"name": self.name})

        if " " in self.name:
            raise ConfigValidationError(
                "项目名称不能包含空格", {"name": self.name}
            )

        # 验证入口文件
        if not self.entry_point or not self.entry_point.strip():
            raise ConfigValidationError(
                "入口文件不能为空", {"entry_point": self.entry_point}
            )

        entry_path = Path(self.entry_point)
        if not entry_path.exists():
            raise ConfigValidationError(
                f"入口文件不存在: {self.entry_point}",
                {"entry_point": self.entry_point, "path": entry_path},
            )

        if entry_path.suffix != ".py":
            raise ConfigValidationError(
                f"入口文件必须是 .py 文件: {self.entry_point}",
                {"entry_point": self.entry_point, "suffix": entry_path.suffix},
            )

        # 验证图标路径（如果提供）
        if self.icon_path is not None:
            if not self.icon_path.exists():
                raise ConfigValidationError(
                    f"图标文件不存在: {self.icon_path}",
                    {"icon_path": self.icon_path},
                )

            if self.icon_path.suffix not in [".ico", ".png", ".icns"]:
                raise ConfigValidationError(
                    f"图标文件格式不支持: {self.icon_path.suffix}",
                    {"icon_path": self.icon_path, "suffix": self.icon_path.suffix},
                )

    def to_dict(self) -> dict[str, object]:
        """将配置转换为字典

        Returns:
            配置的字典表示

        Examples:
            >>> config = ProjectConfig(name="myapp")
            >>> data = config.to_dict()
            >>> data["name"]
            'myapp'
        """
        return {
            "name": self.name,
            "entry_point": self.entry_point,
            "hidden_imports": self.hidden_imports.copy(),
            "add_data": self.add_data.copy(),
            "exclude_modules": self.exclude_modules.copy(),
            "icon_path": str(self.icon_path) if self.icon_path else None,
            "default_deploy_path": str(self.default_deploy_path),
            "use_one_dir": self.use_one_dir,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "ProjectConfig":
        """从字典创建配置对象

        Args:
            data: 配置字典

        Returns:
            ProjectConfig 实例

        Examples:
            >>> data = {"name": "myapp", "entry_point": "main.py"}
            >>> config = ProjectConfig.from_dict(data)
            >>> config.name
            'myapp'
        """
        # 处理 Path 类型的字段
        if "icon_path" in data and data["icon_path"] is not None:
            data["icon_path"] = Path(str(data["icon_path"]))

        if "default_deploy_path" in data:
            data["default_deploy_path"] = Path(str(data["default_deploy_path"]))

        return cls(**data)  # type: ignore[arg-type]
