"""Setup 模块基本使用示例

本示例展示了如何使用 evan_tools.setup 进行基本的项目构建和部署。

示例场景：
- 构建一个 Python 项目为独立的可执行文件
- 部署到本地文件系统
"""

from pathlib import Path

from evan_tools.setup import (
    FileSystemCleaner,
    LocalDeployer,
    ProjectConfig,
    PyInstallerBuilder,
    create_orchestrator,
)


def example_1_basic_build_and_deploy():
    """示例 1: 基本构建和部署流程
    
    这是最简单的使用场景：
    1. 配置项目
    2. 创建编排器
    3. 执行构建
    4. 执行部署
    """
    print("=" * 60)
    print("示例 1: 基本构建和部署")
    print("=" * 60)

    # 步骤 1: 配置项目
    config = ProjectConfig(
        name="my_application",
        entry_point="main.py",
        output_dir="dist",
        working_dir=Path("./build"),
    )

    # 步骤 2: 创建编排器
    # create_orchestrator 会自动注入默认的构建器、部署器和清理器
    orchestrator = create_orchestrator(config)

    # 步骤 3: 执行构建
    print("\n[1/3] 开始构建...")
    build_result = orchestrator.build()
    if build_result.success:
        print(f"✓ 构建成功！输出: {build_result.output_path}")
    else:
        print(f"✗ 构建失败: {build_result.error}")
        return

    # 步骤 4: 执行部署
    print("\n[2/3] 开始部署...")
    deploy_result = orchestrator.deploy()
    if deploy_result.success:
        print(f"✓ 部署成功！部署到: {deploy_result.output_path}")
    else:
        print(f"✗ 部署失败: {deploy_result.error}")
        return

    # 步骤 5: 清理构建文件（可选）
    print("\n[3/3] 清理构建文件...")
    clean_result = orchestrator.clean()
    if clean_result.success:
        print(f"✓ 清理成功！已删除: {clean_result.files_deleted} 个文件")
    else:
        print(f"✗ 清理失败: {clean_result.error}")

    print("\n✓ 完整流程执行完毕！\n")


def example_2_build_only():
    """示例 2: 仅执行构建（不部署）
    
    场景：你只想构建项目，不立即部署
    """
    print("=" * 60)
    print("示例 2: 仅构建")
    print("=" * 60)

    config = ProjectConfig(
        name="build_only_app",
        entry_point="src/main.py",
        output_dir="dist",
    )

    orchestrator = create_orchestrator(config)

    # 只执行构建
    result = orchestrator.build()

    if result.success:
        print(f"\n✓ 构建完成！")
        print(f"  输出路径: {result.output_path}")
        print(f"  耗时: {result.duration:.2f} 秒")
    else:
        print(f"\n✗ 构建失败: {result.error}")

    print()


def example_3_custom_output_directory():
    """示例 3: 使用自定义输出目录
    
    场景：你想把不同项目的构建输出放在不同的目录
    """
    print("=" * 60)
    print("示例 3: 自定义输出目录")
    print("=" * 60)

    # 为项目设置特定的输出目录
    projects = [
        ("frontend_app", "frontend/main.py", "dist/frontend"),
        ("backend_api", "backend/main.py", "dist/backend"),
        ("worker_service", "workers/main.py", "dist/workers"),
    ]

    for name, entry_point, output_dir in projects:
        print(f"\n正在构建 {name}...")

        config = ProjectConfig(
            name=name,
            entry_point=entry_point,
            output_dir=output_dir,
        )

        orchestrator = create_orchestrator(config)
        result = orchestrator.build()

        if result.success:
            print(f"  ✓ {name} 构建成功 -> {result.output_path}")
        else:
            print(f"  ✗ {name} 构建失败: {result.error}")

    print()


def example_4_error_handling():
    """示例 4: 错误处理
    
    展示如何处理构建和部署中的各种错误
    """
    print("=" * 60)
    print("示例 4: 错误处理")
    print("=" * 60)

    from evan_tools.setup import BuildError, ConfigValidationError, DeployError

    config = ProjectConfig(
        name="error_handling_app",
        entry_point="main.py",
        output_dir="dist",
    )

    orchestrator = create_orchestrator(config)

    try:
        # 尝试构建
        build_result = orchestrator.build()

        if not build_result.success:
            # 处理构建失败
            raise BuildError(f"构建失败: {build_result.error}")

        # 尝试部署
        deploy_result = orchestrator.deploy()

        if not deploy_result.success:
            # 处理部署失败
            raise DeployError(f"部署失败: {deploy_result.error}")

        print("\n✓ 构建和部署成功！")

    except ConfigValidationError as e:
        print(f"\n✗ 配置错误: {e}")
        print("  请检查项目配置是否正确")

    except BuildError as e:
        print(f"\n✗ 构建错误: {e}")
        print("  可能原因: entry_point 不存在或包含语法错误")

    except DeployError as e:
        print(f"\n✗ 部署错误: {e}")
        print("  可能原因: 输出目录无法写入或部署目录不可达")

    print()


def example_5_check_build_result():
    """示例 5: 检查构建结果详情
    
    展示如何获取构建结果的详细信息
    """
    print("=" * 60)
    print("示例 5: 构建结果详情")
    print("=" * 60)

    config = ProjectConfig(
        name="detail_check_app",
        entry_point="main.py",
        output_dir="dist",
    )

    orchestrator = create_orchestrator(config)
    result = orchestrator.build()

    print(f"\n构建结果:")
    print(f"  成功: {result.success}")
    print(f"  输出路径: {result.output_path}")
    print(f"  耗时: {result.duration:.2f} 秒")

    if result.error:
        print(f"  错误: {result.error}")

    if result.warnings:
        print(f"  警告数: {len(result.warnings)}")
        for warning in result.warnings:
            print(f"    - {warning}")

    print()


if __name__ == "__main__":
    print("\n")
    print("█" * 60)
    print("Setup 模块基本使用示例")
    print("█" * 60)
    print()

    # 运行示例
    # 注意：实际运行时需要确保环境中已安装依赖
    # 建议按需运行单个示例

    example_1_basic_build_and_deploy()
    example_2_build_only()
    example_3_custom_output_directory()
    example_4_error_handling()
    example_5_check_build_result()

    print("█" * 60)
    print("所有示例执行完毕")
    print("█" * 60)
    print()
