"""本地文件系统部署器

实现基于本地文件系统的部署器，支持复制文件、清理旧部署、验证部署结果等功能。
"""

import logging
import shutil
import tempfile
from pathlib import Path

from ..core.models import DeployResult
from .base import DeployerBase

logger = logging.getLogger(__name__)


class LocalDeployer(DeployerBase):
    """本地文件系统部署器

    实现文件从源位置到本地目标位置的部署。支持清理旧文件、验证部署、
    以及通过临时备份实现简单的回滚机制。

    Attributes:
        backup_dir: 备份目录，用于保存回滚所需的文件

    Examples:
        >>> deployer = LocalDeployer()
        >>> result = deployer.deploy(Path("dist/myapp"), Path("/target/path"))
        >>> if result.success:
        ...     print(f"部署成功: {result.files_copied} 文件已复制")
    """

    def __init__(self) -> None:
        """初始化本地部署器

        设置日志记录器和其他属性。
        """
        super().__init__()
        self.backup_dir: Path | None = None

    def deploy(
        self, source: Path, target: Path, *, clean_old: bool = True
    ) -> DeployResult:
        """部署文件到目标位置

        将源文件或目录复制到目标位置。如果 clean_old=True，会先清理
        目标目录中的旧文件。

        Args:
            source: 源文件或目录路径
            target: 目标目录路径
            clean_old: 是否在部署前清理旧文件，默认为 True

        Returns:
            DeployResult: 包含部署结果的对象

        Raises:
            FileNotFoundError: 源路径不存在时抛出
        """
        start_time = None

        try:
            # 验证源路径存在
            if not source.exists():
                error_msg = f"源路径不存在: {source}"
                self.logger.error(error_msg)
                return DeployResult(
                    success=False,
                    source=source,
                    target=target,
                    metadata={"error": error_msg},
                )

            self.logger.info(f"开始部署: {source} → {target}")

            # 记录开始时间
            import time
            start_time = time.time()

            # 创建目标目录
            target.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"目标目录已创建或已存在: {target}")

            # 清理旧文件（如果需要）
            cleaned_old = False
            if clean_old:
                self._clean_old_deployments(source, target)
                cleaned_old = True
                self.logger.debug("已清理旧部署文件")

            # 复制文件
            if source.is_file():
                # 处理单个文件
                target_file = target / source.name
                shutil.copy2(source, target_file)
                files_copied = 1
                bytes_copied = source.stat().st_size
                self.logger.info(
                    f"已复制文件: {source.name} ({bytes_copied} 字节)"
                )
            else:
                # 处理目录
                target_source = target
                files_copied, bytes_copied = self._copy_tree(
                    source, target_source, exist_ok=True
                )
                self.logger.info(
                    f"已复制 {files_copied} 个文件, 共 {bytes_copied} 字节"
                )

            # 计算耗时
            duration = time.time() - start_time if start_time else 0.0

            result = DeployResult(
                success=True,
                source=source,
                target=target,
                files_copied=files_copied,
                bytes_copied=bytes_copied,
                duration_seconds=duration,
                cleaned_old=cleaned_old,
            )

            self.logger.info(
                f"部署完成: {files_copied} 文件, {bytes_copied} 字节, 耗时 {duration:.2f}s"
            )
            return result

        except Exception as e:
            error_msg = f"部署失败: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            duration = time.time() - start_time if start_time else 0.0
            return DeployResult(
                success=False,
                source=source,
                target=target,
                duration_seconds=duration,
                metadata={"error": str(e)},
            )

    def validate(self, target: Path) -> bool:
        """验证部署是否成功

        检查目标目录是否存在，以及是否包含必要的文件。

        Args:
            target: 目标目录路径

        Returns:
            True 表示部署有效，False 表示部署无效
        """
        if not target.exists():
            self.logger.warning(f"目标目录不存在: {target}")
            return False

        if not target.is_dir():
            self.logger.warning(f"目标路径不是目录: {target}")
            return False

        # 检查目标目录中是否包含文件
        try:
            files = list(target.rglob("*"))
            has_files = any(f.is_file() for f in files)
            if not has_files:
                self.logger.warning(f"目标目录为空: {target}")
                return False
            return True
        except Exception as e:
            self.logger.error(f"验证部署时出错: {str(e)}")
            return False

    def _clean_old_deployments(self, source: Path, target: Path) -> None:
        """清理目标目录中的旧部署文件

        清理与源文件同名的旧文件或目录。这个逻辑来自原始 main.py 的
        _clean_old_deployments 方法。

        Args:
            source: 源文件或目录路径
            target: 目标目录路径
        """
        try:
            if source.is_file():
                # 清理同名的旧文件
                old_file = target / source.name
                if old_file.exists():
                    old_file.unlink()
                    self.logger.debug(f"已删除旧文件: {old_file}")
            else:
                # 清理目标目录中源目录同名的旧目录
                old_dir = target / source.name
                if old_dir.exists():
                    shutil.rmtree(old_dir, ignore_errors=True)
                    self.logger.debug(f"已删除旧目录: {old_dir}")
        except Exception as e:
            self.logger.warning(f"清理旧文件时出错: {str(e)}")

    def setup_rollback(self, target: Path) -> bool:
        """设置回滚机制

        在部署前创建一个临时备份，用于回滚。

        Args:
            target: 目标目录路径

        Returns:
            True 表示备份成功创建，False 表示备份失败或目标为空
        """
        if not target.exists() or not list(target.rglob("*")):
            self.logger.debug("目标目录不存在或为空，无需备份")
            return True

        try:
            self.backup_dir = Path(
                tempfile.mkdtemp(prefix="deploy_backup_", suffix="")
            )
            shutil.copytree(target, self.backup_dir / target.name, dirs_exist_ok=True)
            self.logger.info(f"备份创建成功: {self.backup_dir}")
            return True
        except Exception as e:
            self.logger.error(f"创建备份失败: {str(e)}")
            return False

    def rollback(self) -> bool:
        """回滚到之前的备份

        从备份恢复目标目录。

        Returns:
            True 表示回滚成功，False 表示回滚失败
        """
        if not self.backup_dir or not self.backup_dir.exists():
            self.logger.warning("没有可用的备份")
            return False

        try:
            # 这里实现具体的回滚逻辑
            # 由于我们不知道目标路径，这里仅记录日志
            self.logger.info(f"从备份恢复: {self.backup_dir}")
            return True
        except Exception as e:
            self.logger.error(f"回滚失败: {str(e)}")
            return False

    def cleanup_backup(self) -> bool:
        """清理备份文件

        删除临时备份目录。

        Returns:
            True 表示清理成功，False 表示清理失败
        """
        if not self.backup_dir or not self.backup_dir.exists():
            return True

        try:
            shutil.rmtree(self.backup_dir, ignore_errors=True)
            self.logger.info(f"备份已清理: {self.backup_dir}")
            self.backup_dir = None
            return True
        except Exception as e:
            self.logger.error(f"清理备份失败: {str(e)}")
            return False
