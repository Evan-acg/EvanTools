"""Setup 模块高级使用示例

本示例展示了 evan_tools.setup 的高级用法，包括：
- 依赖注入（使用自定义构建器、部署器）
- 自定义构建链
- 高级错误处理和恢复
"""

from pathlib import Path
from typing import Optional

from evan_tools.setup import (
    BuildError,
    BuildResult,
    BuilderProtocol,
    CleanResult,
    CleanerProtocol,
    DeployError,
    DeployResult,
    DeployerProtocol,
    FileSystemCleaner,
    Orchestrator,
    ProjectConfig,
    PyInstallerBuilder,
)


class CustomLoggingBuilder:
    """自定义构建器 - 添加详细日志
    
    这个示例演示了如何创建一个自定义构建器，在 PyInstaller 基础上
    添加更详细的日志输出。
    """

    def __init__(self, base_builder: BuilderProtocol):
        """初始化自定义构建器
        
        Args:
            base_builder: 基础构建器（通常是 PyInstallerBuilder）
        """
        self.base_builder = base_builder

    def build(self, config: ProjectConfig) -> BuildResult:
        """执行构建（带详细日志）
        
        Args:
            config: 项目配置
            
        Returns:
            构建结果
        """
        print(f"[CustomLoggingBuilder] 开始构建: {config.name}")
        print(f"  - Entry point: {config.entry_point}")
        print(f"  - Output dir: {config.output_dir}")
        print(f"  - Python version: {config.python_version}")

        # 委托给基础构建器
        result = self.base_builder.build(config)

        print(f"[CustomLoggingBuilder] 构建完成")
        print(f"  - 成功: {result.success}")
        print(f"  - 耗时: {result.duration:.2f} 秒")

        if result.warnings:
            print(f"  - 警告数: {len(result.warnings)}")

        return result


class ZipDeployer:
    """自定义部署器 - 创建 ZIP 压缩包
    
    这个示例演示了如何创建一个自定义部署器，将构建输出压缩成 ZIP 文件。
    """

    def __init__(self, zip_path: Optional[Path] = None):
        """初始化 ZIP 部署器
        
        Args:
            zip_path: ZIP 文件输出路径（如果 None，使用项目名称）
        """
        self.zip_path = zip_path

    def deploy(self, config: ProjectConfig) -> DeployResult:
        """执行部署（创建 ZIP 压缩包）
        
        Args:
            config: 项目配置
            
        Returns:
            部署结果
        """
        try:
            import shutil
            import time

            start_time = time.time()

            # 确定 ZIP 文件路径
            zip_path = self.zip_path or Path(f"{config.name}.zip")

            # 创建 ZIP 文件
            output_path = Path(config.output_dir)
            if output_path.exists():
                shutil.make_archive(
                    str(zip_path.with_suffix("")),  # 不含 .zip 后缀
                    "zip",
                    output_path,
                )

                duration = time.time() - start_time

                print(f"[ZipDeployer] ZIP 文件创建成功: {zip_path}")

                return DeployResult(
                    success=True,
                    output_path=zip_path,
                    duration=duration,
                )
            else:
                raise DeployError(f"输出目录不存在: {output_path}")

        except Exception as e:
            return DeployResult(
                success=False,
                output_path=None,
                duration=0.0,
                error=str(e),
            )


class SmartCleaner:
    """自定义清理器 - 智能清理
    
    这个示例演示了如何创建一个智能清理器，可以选择清理的内容。
    """

    def __init__(self, keep_patterns: Optional[list[str]] = None):
        """初始化智能清理器
        
        Args:
            keep_patterns: 保留的文件模式列表
        """
        self.keep_patterns = keep_patterns or []

    def clean(self, config: ProjectConfig) -> CleanResult:
        """执行清理（带选择性保留）
        
        Args:
            config: 项目配置
            
        Returns:
            清理结果
        """
        try:
            import shutil

            working_dir = Path(config.working_dir)
            files_deleted = 0

            if working_dir.exists():
                for item in working_dir.rglob("*"):
                    # 检查是否应该保留
                    should_keep = any(
                        pattern in str(item) for pattern in self.keep_patterns
                    )

                    if not should_keep and item.is_file():
                        item.unlink()
                        files_deleted += 1
                    elif not should_keep and item.is_dir():
                        shutil.rmtree(item)
                        files_deleted += 1

            return CleanResult(
                success=True,
                files_deleted=files_deleted,
                duration=0.1,
            )

        except Exception as e:
            return CleanResult(
                success=False,
                files_deleted=0,
                duration=0.0,
                error=str(e),
            )


def example_1_dependency_injection():
    """示例 1: 依赖注入
    
    使用自定义的构建器和部署器创建编排器。
    """
    print("=" * 60)
    print("示例 1: 依赖注入")
    print("=" * 60)

    config = ProjectConfig(
        name="injection_app",
        entry_point="main.py",
        output_dir="dist",
    )

    # 创建自定义构建器
    base_builder = PyInstallerBuilder()
    custom_builder = CustomLoggingBuilder(base_builder)

    # 创建自定义部署器
    custom_deployer = ZipDeployer(Path("output/app.zip"))

    # 创建自定义清理器
    custom_cleaner = SmartCleaner(keep_patterns=["important"])

    # 使用自定义组件创建编排器
    orchestrator = Orchestrator(
        config=config,
        builder=custom_builder,
        deployer=custom_deployer,
        cleaner=custom_cleaner,
    )

    print("\n开始构建...")
    build_result = orchestrator.build()

    if build_result.success:
        print(f"✓ 构建成功: {build_result.output_path}\n")

        print("开始部署...")
        deploy_result = orchestrator.deploy()

        if deploy_result.success:
            print(f"✓ 部署成功: {deploy_result.output_path}\n")

    print()


def example_2_multiple_builders():
    """示例 2: 多个构建器链（构建管道）
    
    演示如何按顺序使用多个构建器。
    """
    print("=" * 60)
    print("示例 2: 构建管道")
    print("=" * 60)

    config = ProjectConfig(
        name="pipeline_app",
        entry_point="main.py",
        output_dir="dist",
    )

    print("\n构建管道:")
    print("  1. 标准构建 (PyInstaller)")
    print("  2. 添加日志 (CustomLoggingBuilder)")
    print("  3. 部署为 ZIP (ZipDeployer)")

    # 构建链：PyInstaller -> CustomLoggingBuilder -> ZipDeployer
    base_builder = PyInstallerBuilder()
    logging_builder = CustomLoggingBuilder(base_builder)

    orchestrator = Orchestrator(
        config=config,
        builder=logging_builder,
        deployer=ZipDeployer(),
    )

    print("\n执行构建管道...")
    result = orchestrator.build()

    if result.success:
        print(f"\n✓ 管道执行成功!")
    else:
        print(f"\n✗ 管道执行失败: {result.error}")

    print()


def example_3_advanced_error_handling():
    """示例 3: 高级错误处理和恢复策略
    
    演示如何处理和恢复各种错误情况。
    """
    print("=" * 60)
    print("示例 3: 高级错误处理")
    print("=" * 60)

    config = ProjectConfig(
        name="error_recovery_app",
        entry_point="main.py",
        output_dir="dist",
    )

    orchestrator = create_orchestrator(config)

    # 策略 1: 构建失败时重试
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            print(f"\n尝试 {attempt}/{max_retries}...")
            result = orchestrator.build()

            if result.success:
                print(f"✓ 第 {attempt} 次尝试成功!")
                break
            else:
                print(f"✗ 构建失败: {result.error}")
                if attempt < max_retries:
                    print("  准备重试...")

        except Exception as e:
            print(f"✗ 异常: {e}")
            if attempt == max_retries:
                print("✗ 已达最大重试次数，放弃")

    print()


def example_4_workflow_with_validation():
    """示例 4: 带验证的完整工作流
    
    演示如何在完整工作流中进行验证。
    """
    print("=" * 60)
    print("示例 4: 完整工作流（带验证）")
    print("=" * 60)

    configs = [
        ProjectConfig(
            name="app_v1",
            entry_point="src/v1/main.py",
            output_dir="dist/v1",
        ),
        ProjectConfig(
            name="app_v2",
            entry_point="src/v2/main.py",
            output_dir="dist/v2",
        ),
    ]

    results = {
        "success": 0,
        "failed": 0,
        "details": [],
    }

    for config in configs:
        print(f"\n处理: {config.name}")
        print("-" * 40)

        try:
            # 验证配置
            entry_point = Path(config.entry_point)
            if not entry_point.exists():
                print(f"⚠ 警告: Entry point 不存在: {entry_point}")
                print("  继续执行（可能在实际构建时失败）")

            orchestrator = create_orchestrator(config)

            # 执行构建
            build_result = orchestrator.build()

            if build_result.success:
                # 执行部署
                deploy_result = orchestrator.deploy()

                if deploy_result.success:
                    # 执行清理
                    clean_result = orchestrator.clean()

                    status = "✓ 完成" if clean_result.success else "⚠ 部分完成"
                    results["success"] += 1
                else:
                    status = "✗ 部署失败"
                    results["failed"] += 1
            else:
                status = "✗ 构建失败"
                results["failed"] += 1

            results["details"].append((config.name, status))

        except Exception as e:
            results["failed"] += 1
            results["details"].append((config.name, f"✗ 异常: {e}"))

    # 打印总结
    print("\n" + "=" * 60)
    print("工作流总结")
    print("=" * 60)
    print(f"成功: {results['success']}")
    print(f"失败: {results['failed']}")
    for name, status in results["details"]:
        print(f"  {name}: {status}")

    print()


# 辅助函数
def create_orchestrator(config: ProjectConfig) -> Orchestrator:
    """创建编排器（从基础示例中复用）"""
    from evan_tools.setup import create_orchestrator as create_default

    return create_default(config)


if __name__ == "__main__":
    print("\n")
    print("█" * 60)
    print("Setup 模块高级使用示例")
    print("█" * 60)
    print()

    # 运行示例
    example_1_dependency_injection()
    example_2_multiple_builders()
    example_3_advanced_error_handling()
    example_4_workflow_with_validation()

    print("█" * 60)
    print("所有高级示例执行完毕")
    print("█" * 60)
    print()
