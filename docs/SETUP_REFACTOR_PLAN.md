# Setup 模块重构任务清单

**项目**: evan_tools.setup 深度重构  
**分支**: refactor/setup-brainstorm-2026-01-25  
**工作区**: .worktrees/setup-refactor  
**计划日期**: 2026-01-25

---

## 执行原则

1. ✅ **每完成一项任务，标记为 `[x]`**
2. ✅ **每项任务完成后运行相关测试**
3. ✅ **遵循 TDD：先写测试，再写实现**
4. ✅ **每个大阶段完成后执行 `git commit`**

---

## 阶段 0: 准备工作（Pre-flight）

- [x] 创建 git worktree
- [x] 运行基准测试（确认环境）
- [x] 生成头脑风暴报告
- [x] 提交初始状态: `git commit -m "chore(setup): 启动重构 - 创建工作区和分析报告"`

---

## 阶段 1: 基础设施搭建（Foundation） ✅ 已完成

### 1.1 创建核心目录结构

- [x] 创建 `src/evan_tools/setup/core/` 目录
- [x] 创建 `src/evan_tools/setup/builders/` 目录
- [x] 创建 `src/evan_tools/setup/deployers/` 目录
- [x] 创建 `src/evan_tools/setup/cleaners/` 目录
- [x] 创建 `src/evan_tools/setup/cli/` 目录
- [x] 创建 `src/evan_tools/setup/utils/` 目录
- [x] 创建 `tests/setup/` 目录（测试根目录）

### 1.2 定义核心抽象

- [x] 创建 `core/exceptions.py` - 定义异常层次
  - `SetupError`
  - `BuildError`
  - `DeployError`
  - `CleanError`
  - `ConfigValidationError`

- [x] 创建 `core/protocols.py` - 定义接口协议
  - `BuilderProtocol`
  - `DeployerProtocol`
  - `CleanerProtocol`

- [x] 创建 `core/models.py` - 定义数据模型
  - `BuildResult`
  - `DeployResult`
  - `CleanResult`

- [x] 创建 `core/config.py` - 重构配置类
- [x] 编写 `tests/setup/core/test_exceptions.py`
- [x] 编写 `tests/setup/core/test_models.py`
- [x] 编写 `tests/setup/core/test_config.py`

### 1.3 提交

- [x] 运行测试: `uv run pytest tests/setup/core/ -v` (37 passed)
- [x] 提交: `git commit -m "feat(setup): 创建核心抽象层（异常、协议、模型）"`

---

## 阶段 2: 配置管理重构（Configuration）

### 2.1 重构 ProjectConfig

- [ ] 将 `ProjectConfig` 移动到 `core/config.py`
- [ ] 添加验证方法: `validate()`
- [ ] 添加类型检查增强
- [ ] 添加默认值工厂函数
- [ ] 添加 `from_dict()` / `to_dict()` 方法

### 2.2 创建配置验证器

- [ ] 创建 `utils/validators.py`
  - `validate_path_exists()`
  - `validate_file_extension()`
  - `validate_project_name()`

### 2.3 测试

- [ ] 编写 `tests/setup/core/test_config.py`
  - 测试配置创建
  - 测试验证逻辑
  - 测试边界条件

### 2.4 提交

- [ ] 运行测试: `uv run pytest tests/setup/core/test_config.py -v`
- [ ] 提交: `git commit -m "refactor(setup): 重构配置管理，添加验证逻辑"`

---

## 阶段 3: 清理器组件（Cleaner）

### 3.1 实现清理器

- [ ] 创建 `cleaners/base.py` - 抽象基类
- [ ] 创建 `cleaners/filesystem.py` - 文件系统清理实现
  - `clean_dist()`
  - `clean_build()`
  - `clean_spec()`
  - `clean_all()`

### 3.2 测试

- [ ] 编写 `tests/setup/cleaners/test_filesystem.py`
  - 测试单个目录清理
  - 测试批量清理
  - 测试清理不存在的目录

### 3.3 提交

- [ ] 运行测试: `uv run pytest tests/setup/cleaners/ -v`
- [ ] 提交: `git commit -m "feat(setup): 实现独立清理器组件"`

---

## 阶段 4: 构建器组件（Builder）

### 4.1 实现构建器基类

- [ ] 创建 `builders/base.py`
  - 定义抽象方法 `build()`
  - 定义抽象方法 `prepare_command()`

### 4.2 实现 PyInstaller 构建器

- [ ] 创建 `builders/pyinstaller.py`
  - 迁移 `prepare_command()` 逻辑
  - 实现 `build()` 方法
  - 分离命令参数构建逻辑
  - 添加进度回调支持

### 4.3 添加日志系统

- [ ] 创建 `utils/logging.py`
  - 配置标准 logging
  - 定义日志格式
  - 支持日志级别配置

### 4.4 测试

- [ ] 编写 `tests/setup/builders/test_pyinstaller.py`
  - 测试命令生成（Mock subprocess）
  - 测试构建成功场景
  - 测试构建失败场景
  - 测试配置注入

### 4.5 提交

- [ ] 运行测试: `uv run pytest tests/setup/builders/ -v`
- [ ] 提交: `git commit -m "feat(setup): 实现 PyInstaller 构建器组件"`

---

## 阶段 5: 部署器组件（Deployer）

### 5.1 实现部署器基类

- [ ] 创建 `deployers/base.py`
  - 定义抽象方法 `deploy()`
  - 定义抽象方法 `validate()`

### 5.2 实现本地部署器

- [ ] 创建 `deployers/local.py`
  - 迁移 `_clean_old_deployments()` 逻辑
  - 实现 `deploy()` 方法
  - 实现 `validate()` 方法
  - 添加回滚机制

### 5.3 测试

- [ ] 编写 `tests/setup/deployers/test_local.py`
  - 测试部署到临时目录
  - 测试旧文件清理
  - 测试部署验证
  - 测试回滚机制

### 5.4 提交

- [ ] 运行测试: `uv run pytest tests/setup/deployers/ -v`
- [ ] 提交: `git commit -m "feat(setup): 实现本地文件系统部署器"`

---

## 阶段 6: 编排器（Orchestrator）

### 6.1 创建新的 AutoDeployer

- [ ] 创建 `core/orchestrator.py`
  - 接收依赖注入（builder, deployer, cleaner）
  - 实现 `build()` 方法
  - 实现 `deploy()` 方法
  - 实现 `release()` 方法（build + deploy）

### 6.2 测试

- [ ] 编写 `tests/setup/core/test_orchestrator.py`
  - Mock 所有依赖
  - 测试完整工作流
  - 测试错误处理

### 6.3 提交

- [ ] 运行测试: `uv run pytest tests/setup/core/test_orchestrator.py -v`
- [ ] 提交: `git commit -m "feat(setup): 实现编排器（依赖注入模式）"`

---

## 阶段 7: CLI 层重构（CLI）

### 7.1 分离 CLI 关注点

- [ ] 创建 `cli/commands.py`
  - 迁移 Typer CLI 定义
  - 创建工厂函数构建 orchestrator
  - 移除核心逻辑中的 `typer` 依赖

### 7.2 创建 CLI 适配器

- [ ] 实现 `cli/output.py`
  - 定义输出接口
  - 实现控制台输出适配器

### 7.3 测试

- [ ] 编写 `tests/setup/cli/test_commands.py`
  - 使用 Typer 测试工具
  - 测试命令行参数解析

### 7.4 提交

- [ ] 运行测试: `uv run pytest tests/setup/cli/ -v`
- [ ] 提交: `git commit -m "refactor(setup): 分离 CLI 层，解除核心逻辑耦合"`

---

## 阶段 8: 更新公共 API（Public API）

### 8.1 更新 **init**.py

- [ ] 导出新的核心组件
- [ ] 保留向后兼容的 API（标记为 deprecated）
- [ ] 更新 `__all__`

### 8.2 创建迁移指南

- [ ] 创建 `docs/SETUP_MIGRATION_GUIDE.md`
  - 列出破坏性变更
  - 提供迁移示例
  - 解释新架构优势

### 8.3 提交

- [ ] 提交: `git commit -m "refactor(setup): 更新公共 API，添加迁移指南"`

---

## 阶段 9: 删除旧代码（Cleanup）

### 9.1 移除旧实现

- [ ] 备份 `main.py` 为 `main.py.old`
- [ ] 删除 `main.py` 中的旧代码
- [ ] 在 `main.py` 中添加 deprecated 导入（向后兼容）

### 9.2 提交

- [ ] 提交: `git commit -m "chore(setup): 移除旧实现，保留向后兼容导入"`

---

## 阶段 10: 文档完善（Documentation）

### 10.1 添加 Docstring

- [ ] 为所有模块添加模块级文档
- [ ] 为所有类添加中文 Google Docstring
- [ ] 为所有公共方法添加文档

### 10.2 创建使用示例

- [ ] 创建 `examples/setup_basic_usage.py`
- [ ] 创建 `examples/setup_advanced_usage.py`
- [ ] 创建 `examples/setup_custom_builder.py`

### 10.3 更新 README

- [ ] 更新模块说明
- [ ] 添加架构图
- [ ] 添加快速开始指南

### 10.4 提交

- [ ] 提交: `git commit -m "docs(setup): 完善文档和使用示例"`

---

## 阶段 11: 最终验证（Final Verification）

### 11.1 运行完整测试套件

- [ ] 运行所有测试: `uv run pytest tests/setup/ -v --cov=src/evan_tools/setup`
- [ ] 检查测试覆盖率 ≥ 80%

### 11.2 静态检查

- [ ] 运行 Pylance 检查
- [ ] 运行 Ruff 检查: `uv run ruff check src/evan_tools/setup/`
- [ ] 运行类型检查: `uv run mypy src/evan_tools/setup/`

### 11.3 集成测试

- [ ] 编写 `tests/setup/test_integration.py`
  - 测试完整构建和部署流程（使用临时项目）

### 11.4 性能测试

- [ ] 对比重构前后的性能
- [ ] 记录在 `docs/SETUP_PERFORMANCE_REPORT.md`

### 11.5 提交

- [ ] 提交: `git commit -m "test(setup): 添加集成测试和性能验证"`

---

## 阶段 12: 代码审查和清理（Code Review）

### 12.1 自我审查

- [ ] 检查代码风格一致性
- [ ] 检查命名规范
- [ ] 移除调试代码和注释

### 12.2 生成审查报告

- [ ] 创建 `docs/SETUP_REFACTOR_REVIEW.md`
  - 列出所有变更
  - 记录设计决策
  - 标注潜在风险

### 12.3 提交

- [ ] 提交: `git commit -m "chore(setup): 代码审查和清理完成"`

---

## 阶段 13: 完成和合并（Completion）

### 13.1 最终检查清单

- [ ] 所有测试通过 ✅
- [ ] 测试覆盖率 ≥ 80% ✅
- [ ] 无 Pylance 错误 ✅
- [ ] 文档完整 ✅
- [ ] 迁移指南完成 ✅

### 13.2 生成完成报告

- [ ] 创建 `docs/SETUP_REFACTOR_COMPLETION.md`
  - 总结重构成果
  - 记录指标对比
  - 列出后续改进建议

### 13.3 合并分支

- [ ] 切换到主分支: `git checkout master`
- [ ] 合并分支: `git merge refactor/setup-brainstorm-2026-01-25`
- [ ] 删除工作区: `git worktree remove .worktrees/setup-refactor --force`
- [ ] 清理残留文件（**pycache**, .pytest_cache）
- [ ] 删除分支: `git branch -d refactor/setup-brainstorm-2026-01-25`

---

## 风险和注意事项

### ⚠️ 高风险区域

1. **破坏性 API 变更**: 确保向后兼容层正常工作
2. **依赖注入复杂性**: 确保 CLI 层正确构建依赖图
3. **测试隔离**: 确保测试不依赖真实文件系统（使用 tmp_path）

### ✅ 缓解措施

1. 保留旧 API 别名，标记为 deprecated
2. 提供工厂函数简化依赖创建
3. 使用 pytest fixture 提供 mock 环境

---

## 预计时间表

| 阶段 | 预计耗时 | 累计耗时 |
|-----|---------|---------|
| 0-1 基础设施 | 2 小时 | 2 小时 |
| 2-3 配置和清理 | 3 小时 | 5 小时 |
| 4-5 构建和部署 | 6 小时 | 11 小时 |
| 6-7 编排和 CLI | 4 小时 | 15 小时 |
| 8-9 API 更新 | 2 小时 | 17 小时 |
| 10-11 文档和验证 | 4 小时 | 21 小时 |
| 12-13 审查和完成 | 3 小时 | 24 小时 |

**总计**: 约 3 个工作日

---

**计划生成时间**: 2026-01-25  
**预计开始时间**: 2026-01-25  
**预计完成时间**: 2026-01-28
