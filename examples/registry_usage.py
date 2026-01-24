"""
Registry 模块使用示例

演示如何使用 Registry 模块进行命令注册、追踪和监控。
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.evan_tools.registry import RegistryManager


def example_basic_tracking():
    """示例 1: 基础追踪"""
    print("=" * 60)
    print("示例 1: 基础追踪")
    print("=" * 60)
    
    manager = RegistryManager()
    tracker = manager.get_tracker()
    
    # 启用追踪
    manager.enable_tracking()
    print("✓ 已启用追踪")
    
    # 记录几个命令执行
    commands = [
        ("download", "file", 150.0, True, None),
        ("upload", "file", 200.0, True, None),
        ("compress", "file", 500.0, False, "CompressionError: invalid format"),
    ]
    
    for cmd_name, group, duration, success, error in commands:
        tracker.record_execution(
            command_name=cmd_name,
            group=group,
            duration_ms=duration,
            success=success,
            error=error,
            args=(),
            kwargs={},
        )
        status = "✓" if success else "✗"
        print(f"  {status} {cmd_name}: {duration}ms")
    
    # 显示执行历史
    dashboard = manager.get_dashboard()
    print("\n执行历史:")
    print(dashboard.show_execution_history(limit=10))
    
    manager.disable_tracking()
    print("\n✓ 已禁用追踪")


def example_performance_monitoring():
    """示例 2: 性能监控"""
    print("\n" + "=" * 60)
    print("示例 2: 性能监控")
    print("=" * 60)
    
    manager = RegistryManager()
    tracker = manager.get_tracker()
    monitor = manager.get_monitor()
    
    manager.enable_tracking()
    
    # 模拟多次执行同一个命令
    print("模拟 process_data 命令多次执行...")
    for i in range(5):
        duration = 100 + (i % 3) * 20  # 100, 120, 140, 100, 120
        success = i < 4  # 最后一次失败
        error = None if success else "ProcessError: timeout"
        
        tracker.record_execution(
            command_name="process_data",
            group="data",
            duration_ms=float(duration),
            success=success,
            error=error,
            args=(),
            kwargs={},
        )
    
    # 查询统计数据
    stats = monitor.get_stats("process_data")
    if stats:
        print(f"\nprocess_data 统计:")
        print(f"  调用次数: {stats.call_count}")
        print(f"  总耗时: {stats.total_duration_ms:.2f}ms")
        print(f"  平均耗时: {stats.avg_duration_ms:.2f}ms")
        print(f"  最小耗时: {stats.min_duration_ms:.2f}ms")
        print(f"  最大耗时: {stats.max_duration_ms:.2f}ms")
        print(f"  错误次数: {stats.error_count}")
    
    # 显示性能统计表
    dashboard = manager.get_dashboard()
    print("\n性能统计:")
    print(dashboard.show_performance_stats())
    
    manager.disable_tracking()


def example_command_discovery():
    """示例 3: 命令发现"""
    print("\n" + "=" * 60)
    print("示例 3: 命令发现与命令树")
    print("=" * 60)
    
    manager = RegistryManager()
    cmd_index = manager.get_command_index()
    dashboard = manager.get_dashboard()
    
    # 获取所有注册的命令
    all_commands = cmd_index.get_all_commands()
    print(f"已注册命令总数: {len(all_commands)}")
    
    # 显示命令树
    tree = cmd_index.get_command_tree()
    if tree:
        print("\n命令树:")
        print(dashboard.show_command_tree())
    else:
        print("（暂未注册命令）")


def example_full_workflow():
    """示例 4: 完整工作流"""
    print("\n" + "=" * 60)
    print("示例 4: 完整工作流")
    print("=" * 60)
    
    manager = RegistryManager()
    tracker = manager.get_tracker()
    monitor = manager.get_monitor()
    dashboard = manager.get_dashboard()
    
    print("第 1 步: 启用追踪")
    manager.enable_tracking()
    
    print("第 2 步: 模拟各种命令执行")
    operations = [
        ("backup", "system", 300.0, True, None),
        ("backup", "system", 280.0, True, None),
        ("restore", "system", 200.0, False, "RestoreError: corrupted file"),
        ("cleanup", "system", 50.0, True, None),
        ("sync", "data", 150.0, True, None),
    ]
    
    for cmd_name, group, duration, success, error in operations:
        tracker.record_execution(
            command_name=cmd_name,
            group=group,
            duration_ms=duration,
            success=success,
            error=error,
            args=(),
            kwargs={},
        )
    
    print("第 3 步: 查询追踪结果")
    all_stats = monitor.get_all_stats()
    print(f"\n已追踪 {len(all_stats)} 个不同的命令:")
    for cmd_name in sorted(all_stats.keys()):
        stats = all_stats[cmd_name]
        print(f"  - {cmd_name}: 执行 {stats.call_count} 次 "
              f"(平均 {stats.avg_duration_ms:.1f}ms, 错误 {stats.error_count} 次)")
    
    print("\n第 4 步: 生成报告")
    print("\n>>> 执行历史:")
    print(dashboard.show_execution_history(limit=10))
    
    print("\n>>> 性能统计:")
    print(dashboard.show_performance_stats())
    
    print("\n第 5 步: 禁用追踪")
    manager.disable_tracking()
    print("✓ 完成")


if __name__ == "__main__":
    # 运行所有示例
    example_basic_tracking()
    example_performance_monitoring()
    example_command_discovery()
    example_full_workflow()
    
    print("\n" + "=" * 60)
    print("所有示例执行完毕！")
    print("=" * 60)
