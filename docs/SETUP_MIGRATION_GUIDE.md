# Setup 模块迁移指南

**版本**: 1.x → 2.0  
**日期**: 2026-01-25

---

## 概述

Setup 模块在 2.0 版本中进行了全面重构，采用了更加模块化和可扩展的架构。本文档指导您从旧 API 迁移到新 API。

---

## 主要变更

### 1. API 重命名

| 旧 API (1.x) | 新 API (2.0) | 状态 |
|-------------|-------------|------|
| `AutoDeployer` | `Orchestrator` | ⚠️ 旧 API 已弃用 |
| `run_deployer()` | `run_cli()` | ⚠️ 旧 API 已弃用 |
| `ProjectConfig` | `ProjectConfig` | ✅ 保持兼容 |

### 2. 架构变更

**旧架构 (1.x)**:
```
AutoDeployer (单一类)
├── build()
├── deploy()
└── clean()
```

**新架构 (2.0)**:
```
Orchestrator (编排器)
├── builder: BuilderProtocol
├── deployer: DeployerProtocol
└── cleaner: CleanerProtocol
```

---

## 迁移步骤

### 步骤 1: 更新导入

**旧代码**:
```python
from evan_tools.setup import AutoDeployer, ProjectConfig, run_deployer
```

**新代码**:
```python
from evan_tools.setup import (
    ProjectConfig,
    create_orchestrator,  # 替代 AutoDeployer
    run_cli,              # 替代 run_deployer
)
```

### 步骤 2: 替换 AutoDeployer

**旧代码**:
```python
config = ProjectConfig(name="myapp", entry_point="main.py")
deployer = AutoDeployer(config)

# 构建
deployer.build()

# 部署
deployer.deploy(Path("C:/Tools"), clean_dist=True)
```

**新代码**:
```python
from pathlib import Path
from evan_tools.setup import ProjectConfig, create_orchestrator

config = ProjectConfig(name="myapp", entry_point="main.py")
orchestrator = create_orchestrator(config)

# 构建
result = orchestrator.build()
print(f"构建成功: {result.success}")

# 部署
result = orchestrator.deploy(Path("C:/Tools"), clean_dist=True)
print(f"部署成功: {result.success}")

# 或者一步完成
result = orchestrator.release(Path("C:/Tools"), clean_dist=True)
```

### 步骤 3: 替换 run_deployer

**旧代码**:
```python
from evan_tools.setup import ProjectConfig, run_deployer

config = ProjectConfig(name="myapp", entry_point="main.py")
run_deployer(config)
```

**新代码**:
```python
from evan_tools.setup import ProjectConfig
from evan_tools.setup.cli import run_cli

config = ProjectConfig(name="myapp", entry_point="main.py")
run_cli(config)
```

---

## 新功能亮点

### 1. 依赖注入

新架构支持完全的依赖注入，您可以自定义构建器、部署器和清理器：

```python
from evan_tools.setup import (
    ProjectConfig,
    Orchestrator,
    PyInstallerBuilder,
    LocalDeployer,
    FileSystemCleaner,
)
from evan_tools.setup.utils import get_logger

config = ProjectConfig(name="myapp", entry_point="main.py")

# 自定义组件
builder = PyInstallerBuilder()
deployer = LocalDeployer()
cleaner = FileSystemCleaner()
logger = get_logger("myapp")

# 手动创建编排器
orchestrator = Orchestrator(
    config=config,
    builder=builder,
    deployer=deployer,
    cleaner=cleaner,
    logger=logger,
)
```

### 2. 结果对象

所有操作现在返回结果对象，包含详细的元数据：

```python
# 构建结果
result = orchestrator.build()
print(f"成功: {result.success}")
print(f"输出路径: {result.output_path}")
print(f"耗时: {result.duration_seconds}s")
print(f"命令: {' '.join(result.command)}")

# 部署结果
result = orchestrator.deploy(Path("C:/Tools"))
print(f"复制文件数: {result.files_copied}")
print(f"复制字节数: {result.bytes_copied}")

# 清理结果
result = orchestrator.cleaner.clean_all()
print(f"删除文件数: {result.files_removed}")
print(f"释放空间: {result.bytes_freed / 1024 / 1024:.2f} MB")
```

### 3. 完整的日志系统

```python
from evan_tools.setup.utils import get_logger
import logging

# 配置日志级别
logger = get_logger("myapp", level=logging.DEBUG)

orchestrator = create_orchestrator(config, logger=logger)
orchestrator.build()  # 会输出详细的日志
```

### 4. 异常层次

```python
from evan_tools.setup import (
    SetupError,
    BuildError,
    DeployError,
    CleanError,
    ConfigValidationError,
)

try:
    result = orchestrator.build()
except BuildError as e:
    print(f"构建失败: {e.message}")
    print(f"详细信息: {e.details}")
except SetupError as e:
    print(f"其他错误: {e}")
```

---

## 向后兼容性

### 兼容期限

- **2.0.x**: 旧 API 可用，但会发出 `DeprecationWarning`
- **3.0.0**: 旧 API 将被完全移除

### 如何处理警告

如果您暂时无法迁移，可以临时禁用警告：

```python
import warnings

# 禁用弃用警告（不推荐）
warnings.filterwarnings("ignore", category=DeprecationWarning)

from evan_tools.setup import AutoDeployer  # 不会显示警告
```

但我们**强烈建议**尽快迁移到新 API。

---

## 常见问题 (FAQ)

### Q1: 为什么要重构？

**A**: 旧架构存在以下问题：
- 违反单一职责原则（`AutoDeployer` 做太多事情）
- 核心逻辑与 CLI 框架耦合
- 难以扩展（如添加新的构建工具）
- 难以测试（缺少依赖注入）

### Q2: 新 API 有什么好处？

**A**:
- ✅ 遵循 SOLID 原则
- ✅ 支持依赖注入和 Mock 测试
- ✅ 易于扩展（如支持 Nuitka 构建器）
- ✅ 完整的类型提示和文档
- ✅ 独立的日志系统
- ✅ 详细的结果对象

### Q3: 我需要修改多少代码？

**A**: 大多数情况下，只需要：
1. 修改导入语句
2. 将 `AutoDeployer` 替换为 `create_orchestrator()`
3. 将 `run_deployer()` 替换为 `run_cli()`

通常每个文件只需要修改 2-5 行代码。

### Q4: 配置文件需要修改吗？

**A**: 不需要。`ProjectConfig` 保持向后兼容，所有旧的配置代码无需修改。

### Q5: 性能有影响吗？

**A**: 几乎没有。新架构增加了少量抽象层，但对性能的影响可以忽略不计（< 1%）。

---

## 需要帮助？

如果您在迁移过程中遇到问题，请：

1. 查看示例代码: `examples/setup_basic_usage.py`
2. 阅读 API 文档: `src/evan_tools/setup/`
3. 提交 Issue 或联系维护者

---

**最后更新**: 2026-01-25  
**作者**: Setup 重构团队
