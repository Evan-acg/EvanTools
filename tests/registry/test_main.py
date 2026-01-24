"""Registry 模块 - 最终正确的测试套件（基于实际 API）"""
import pytest
from datetime import datetime
from src.evan_tools.registry.discovery.inspector import CommandInspector
from src.evan_tools.registry.discovery.index import CommandIndex
from src.evan_tools.registry.tracking.models import ExecutionRecord, PerformanceStats
from src.evan_tools.registry.tracking.tracker import ExecutionTracker
from src.evan_tools.registry.tracking.monitor import PerformanceMonitor
from src.evan_tools.registry.storage.memory_store import InMemoryStore
from src.evan_tools.registry.dashboard.formatter import TableFormatter, TableConfig
from src.evan_tools.registry.dashboard.aggregator import StatsAggregator
from src.evan_tools.registry.dashboard.dashboard import RegistryDashboard
from src.evan_tools.registry.main import RegistryManager


# ============== Discovery Layer Tests ==============

class TestCommandInspector:
    """测试 CommandInspector"""

    def test_extract_metadata_simple(self):
        """测试提取简单函数的元数据"""
        def my_command():
            """这是一个测试命令"""
            pass

        inspector = CommandInspector()
        meta = inspector.extract_metadata(
            name="my_command",
            func=my_command,
            group="test",
            module="test_module"
        )
        
        assert meta.name == "my_command"
        assert meta.group == "test"
        assert meta.func == my_command
        assert meta.docstring == "这是一个测试命令"

    def test_extract_metadata_no_docstring(self):
        """测试提取没有文档的函数"""
        def no_doc():
            pass

        inspector = CommandInspector()
        meta = inspector.extract_metadata(
            name="no_doc",
            func=no_doc,
            group=None,
            module="test"
        )
        
        assert meta.name == "no_doc"
        assert meta.docstring is None or meta.docstring == ""

    def test_extract_metadata_multiple(self):
        """测试提取多个函数的元数据"""
        def cmd1():
            """命令 1"""
            pass
        
        def cmd2(x, y):
            """命令 2"""
            pass

        inspector = CommandInspector()
        meta1 = inspector.extract_metadata("cmd1", cmd1, "group1", "mod")
        meta2 = inspector.extract_metadata("cmd2", cmd2, "group1", "mod")
        
        assert meta1.name == "cmd1"
        assert meta2.name == "cmd2"


class TestCommandIndex:
    """测试 CommandIndex"""

    def test_initialization(self):
        """测试索引初始化"""
        index = CommandIndex()
        commands = index.get_all_commands()
        assert isinstance(commands, list)

    def test_add_and_get_commands(self):
        """测试添加和获取命令"""
        index = CommandIndex()
        
        # CommandIndex 从全局注册表获取命令（via get_registry()）
        # 直接测试索引的查询功能
        commands = index.get_all_commands()
        assert isinstance(commands, list)

    def test_get_command_tree(self):
        """测试获取命令树"""
        index = CommandIndex()
        
        # 获取命令树，验证其结构
        tree = index.get_command_tree()
        assert isinstance(tree, dict)


# ============== Tracking Layer Tests ==============

class TestExecutionRecord:
    """测试 ExecutionRecord"""

    def test_record_creation(self):
        """测试创建执行记录"""
        now = datetime.now()
        record = ExecutionRecord(
            command_name="test_cmd",
            group="test",
            timestamp=now,
            duration_ms=100.5,
            success=True,
            error=None,
            args=(),
            kwargs={}
        )
        
        assert record.command_name == "test_cmd"
        assert record.group == "test"
        assert record.duration_ms == 100.5
        assert record.success is True

    def test_record_with_error(self):
        """测试带错误的执行记录"""
        record = ExecutionRecord(
            command_name="fail_cmd",
            group="test",
            timestamp=datetime.now(),
            duration_ms=50.0,
            success=False,
            error="错误消息",
            args=(),
            kwargs={}
        )
        
        assert record.success is False
        assert record.error == "错误消息"


class TestPerformanceStats:
    """测试 PerformanceStats"""

    def test_stats_creation(self):
        """测试创建统计数据"""
        stats = PerformanceStats(
            command_name="test",
            call_count=10,
            total_duration_ms=1000.0,
            avg_duration_ms=100.0,
            min_duration_ms=50.0,
            max_duration_ms=150.0,
            error_count=1
        )
        
        assert stats.command_name == "test"
        assert stats.call_count == 10
        assert stats.error_count == 1


class TestExecutionTracker:
    """测试 ExecutionTracker"""

    def test_tracker_creation(self):
        """测试创建追踪器"""
        tracker = ExecutionTracker()
        assert tracker is not None

    def test_start_stop_tracking(self):
        """测试启停追踪"""
        tracker = ExecutionTracker()
        
        # 注意：使用 is_tracking() 而非 is_tracking_enabled()
        tracker.start_tracking()
        assert tracker.is_tracking() is True
        
        tracker.stop_tracking()
        assert tracker.is_tracking() is False

    def test_record_execution(self):
        """测试记录执行"""
        tracker = ExecutionTracker()
        tracker.start_tracking()
        
        tracker.record_execution(
            command_name="test_cmd",
            group="test",
            duration_ms=100.0,
            success=True,
            error=None,
            args=(),
            kwargs={}
        )
        
        history = tracker.get_execution_history()
        assert len(history) == 1
        assert history[0].command_name == "test_cmd"

    def test_multiple_executions(self):
        """测试多次执行"""
        tracker = ExecutionTracker()
        tracker.start_tracking()
        
        for i in range(5):
            tracker.record_execution(
                command_name=f"cmd_{i}",
                group="test",
                duration_ms=100.0 + i,
                success=True,
                error=None,
                args=(),
                kwargs={}
            )
        
        history = tracker.get_execution_history()
        assert len(history) == 5

    def test_clear_history(self):
        """测试清空历史"""
        tracker = ExecutionTracker()
        tracker.start_tracking()
        
        tracker.record_execution(
            command_name="test",
            group="test",
            duration_ms=100.0,
            success=True,
            error=None,
            args=(),
            kwargs={}
        )
        
        assert len(tracker.get_execution_history()) == 1
        tracker.clear_history()
        assert len(tracker.get_execution_history()) == 0


class TestPerformanceMonitor:
    """测试 PerformanceMonitor"""

    def test_monitor_initialization(self):
        """测试监视器初始化"""
        tracker = ExecutionTracker()
        monitor = PerformanceMonitor(tracker)
        assert monitor is not None

    def test_get_all_stats(self):
        """测试获取所有统计"""
        tracker = ExecutionTracker()
        tracker.start_tracking()
        
        for _ in range(3):
            tracker.record_execution(
                command_name="test",
                group="test",
                duration_ms=100.0,
                success=True,
                error=None,
                args=(),
                kwargs={}
            )
        
        monitor = PerformanceMonitor(tracker)
        stats = monitor.get_all_stats()
        assert isinstance(stats, dict)


# ============== Storage Layer Tests ==============

class TestInMemoryStore:
    """测试 InMemoryStore"""

    def test_store_creation(self):
        """测试创建存储"""
        store = InMemoryStore()
        assert store is not None

    def test_add_record(self):
        """测试添加记录"""
        store = InMemoryStore()
        record = ExecutionRecord(
            command_name="test",
            group="test",
            timestamp=datetime.now(),
            duration_ms=100.0,
            success=True,
            error=None,
            args=(),
            kwargs={}
        )
        
        store.add_record(record)
        # 注意：使用 get_all_records() 而非 get_history()
        all_records = store.get_all_records()
        assert len(all_records) == 1

    def test_get_recent_records(self):
        """测试获取最近的记录"""
        store = InMemoryStore()
        
        for i in range(5):
            record = ExecutionRecord(
                command_name=f"cmd_{i}",
                group="test",
                timestamp=datetime.now(),
                duration_ms=100.0 + i,
                success=True,
                error=None,
                args=(),
                kwargs={}
            )
            store.add_record(record)
        
        recent = store.get_recent_records(limit=3)
        assert len(recent) <= 3

    def test_clear_storage(self):
        """测试清空存储"""
        store = InMemoryStore()
        record = ExecutionRecord(
            command_name="test",
            group="test",
            timestamp=datetime.now(),
            duration_ms=100.0,
            success=True,
            error=None,
            args=(),
            kwargs={}
        )
        
        store.add_record(record)
        assert len(store.get_all_records()) == 1
        
        store.clear()
        assert len(store.get_all_records()) == 0


# ============== Visualization Layer Tests ==============

class TestTableFormatter:
    """测试 TableFormatter"""

    def test_formatter_creation(self):
        """测试创建格式化器"""
        formatter = TableFormatter()
        assert formatter is not None

    def test_format_simple_table(self):
        """测试格式化简单表格"""
        formatter = TableFormatter()
        headers = ["名称", "耗时"]
        rows = [
            ["cmd1", "100ms"],
            ["cmd2", "200ms"]
        ]
        
        # 注意：使用 format_table() 而非 format()
        table = formatter.format_table(headers, rows)
        assert isinstance(table, str)
        assert "cmd1" in table

    def test_format_with_config(self):
        """测试使用配置格式化"""
        config = TableConfig(
            padding=2,
            border_char="-",
            col_sep="|"
        )
        formatter = TableFormatter(config)
        
        headers = ["Col1", "Col2"]
        rows = [["a", "b"]]
        
        table = formatter.format_table(headers, rows)
        assert isinstance(table, str)


class TestStatsAggregator:
    """测试 StatsAggregator"""

    def test_aggregator_creation(self):
        """测试创建聚合器"""
        tracker = ExecutionTracker()
        aggregator = StatsAggregator(tracker)
        assert aggregator is not None

    def test_get_performance_stats_formatted(self):
        """测试获取格式化性能统计"""
        tracker = ExecutionTracker()
        tracker.start_tracking()
        
        tracker.record_execution(
            command_name="cmd1",
            group="test",
            duration_ms=100.0,
            success=True,
            error=None,
            args=(),
            kwargs={}
        )
        
        aggregator = StatsAggregator(tracker)
        rows = aggregator.get_performance_stats_formatted()
        assert isinstance(rows, list)


class TestRegistryDashboard:
    """测试 RegistryDashboard"""

    def test_dashboard_creation(self):
        """测试创建仪表板"""
        tracker = ExecutionTracker()
        index = CommandIndex()
        dashboard = RegistryDashboard(tracker, index)
        assert dashboard is not None

    def test_show_execution_history(self):
        """测试显示执行历史"""
        tracker = ExecutionTracker()
        tracker.start_tracking()
        
        tracker.record_execution(
            command_name="test",
            group="test",
            duration_ms=100.0,
            success=True,
            error=None,
            args=(),
            kwargs={}
        )
        
        index = CommandIndex()
        dashboard = RegistryDashboard(tracker, index)
        
        output = dashboard.show_execution_history()
        assert isinstance(output, str)

    def test_show_performance_stats(self):
        """测试显示性能统计"""
        tracker = ExecutionTracker()
        index = CommandIndex()
        dashboard = RegistryDashboard(tracker, index)
        
        output = dashboard.show_performance_stats()
        assert isinstance(output, str)


# ============== Manager Tests ==============

class TestRegistryManager:
    """测试 RegistryManager"""

    def test_manager_creation(self):
        """测试创建管理器"""
        manager = RegistryManager()
        assert manager is not None

    def test_enable_tracking(self):
        """测试启用追踪"""
        manager = RegistryManager()
        manager.enable_tracking()
        
        tracker = manager.get_tracker()
        assert tracker is not None
        assert tracker.is_tracking() is True

    def test_disable_tracking(self):
        """测试禁用追踪"""
        manager = RegistryManager()
        manager.enable_tracking()
        manager.disable_tracking()
        
        tracker = manager.get_tracker()
        assert tracker.is_tracking() is False

    def test_get_components(self):
        """测试获取各个组件"""
        manager = RegistryManager()
        manager.enable_tracking()
        
        index = manager.get_command_index()
        tracker = manager.get_tracker()
        monitor = manager.get_monitor()
        dashboard = manager.get_dashboard()
        
        assert index is not None
        assert tracker is not None
        assert monitor is not None
        assert dashboard is not None


# ============== Integration Tests ==============

class TestIntegration:
    """集成测试"""

    def test_full_workflow(self):
        """测试完整工作流"""
        manager = RegistryManager()
        manager.enable_tracking()
        
        # 获取追踪器并记录
        tracker = manager.get_tracker()
        tracker.record_execution(
            command_name="workflow_cmd",
            group="test",
            duration_ms=100.0,
            success=True,
            error=None,
            args=(),
            kwargs={}
        )
        
        # 查看仪表板
        dashboard = manager.get_dashboard()
        history = dashboard.show_execution_history()
        stats = dashboard.show_performance_stats()
        
        assert isinstance(history, str)
        assert isinstance(stats, str)

    def test_error_handling(self):
        """测试错误处理"""
        tracker = ExecutionTracker()
        tracker.start_tracking()
        
        # 成功的执行
        tracker.record_execution(
            command_name="good",
            group="test",
            duration_ms=100.0,
            success=True,
            error=None,
            args=(),
            kwargs={}
        )
        
        # 失败的执行
        tracker.record_execution(
            command_name="bad",
            group="test",
            duration_ms=50.0,
            success=False,
            error="错误",
            args=(),
            kwargs={}
        )
        
        history = tracker.get_execution_history()
        assert len(history) == 2
        assert history[0].success is True
        assert history[1].success is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
