# Registry 模块 Pylance 检查与修复计划

生成时间: 2026-01-25  
工具: mypy (Pylance 替代品)  
工作区: .worktrees/pylance-check (branch: fix/registry-pylance)

## 检查结果

### Registry 相关错误 (3 项)

#### 1. ❌ memory_store.py:63 - 字典推导式类型不兼容
**文件**: `src/evan_tools/registry/storage/memory_store.py:63`  
**错误代码**: `[misc]`  
**问题描述**:
```
Value expression in dictionary comprehension has incompatible type 
"PerformanceStats | None"; expected type "PerformanceStats"
```

**原因**: `get_all_stats()` 方法返回的值可能为 `None`，但字典推导式要求为 `PerformanceStats`。

**行号**: 第 63 行 (get_all_stats() 方法)

**修复方案**: 
```python
# 当前
stats_dict = {cmd: self._stats[cmd] for cmd in sorted(self._stats.keys())}

# 修复后
stats_dict = {
    cmd: stat 
    for cmd, stat in self._stats.items() 
    if stat is not None
}
```

---

#### 2. ❌ aggregator.py:58 - sorted() 参数类型错误
**文件**: `src/evan_tools/registry/dashboard/aggregator.py:58`  
**错误代码**: `[type-var]`  
**问题描述**:
```
Value of type variable "SupportsRichComparisonT" of "sorted" 
cannot be "str | None"
```

**原因**: `sorted()` 中的 key 可能为 `None`（分组名），但 sorted 期望非 None 可比较类型。

**行号**: 第 58 行 (get_performance_stats_formatted() 方法中的 sorted)

**修复方案**:
```python
# 当前
for cmd_name in sorted(all_stats.keys()):

# 修复后  
for cmd_name in sorted(all_stats.keys(), key=str):
```

---

#### 3. ❌ aggregator.py:68 - 返回类型不兼容
**文件**: `src/evan_tools/registry/dashboard/aggregator.py:68`  
**错误代码**: `[return-value]`  
**问题描述**:
```
Incompatible return value type (got "list[list[str | None]]", 
expected "list[list[str]]")
```

**原因**: `get_command_tree_formatted()` 返回的列表中包含 `None` 值，但函数签名要求 `list[list[str]]`。

**行号**: 第 68 行 (返回语句)

**修复方案**:
```python
# 当前
return rows  # rows 中某些元素可能为 None

# 修复后
rows.append([group_name or "", cmd])  # 确保不返回 None
```

---

#### 4. ❌ index.py:57 - sorted() 参数类型错误 (同 aggregator.py:58)
**文件**: `src/evan_tools/registry/discovery/index.py:57`  
**错误代码**: `[type-var]`  
**问题描述**:
```
Value of type variable "SupportsRichComparisonT" of "sorted" 
cannot be "str | None"
```

**原因**: `sorted()` 的 key 可能为 `None`。

**行号**: 第 57 行 (get_command_tree() 方法)

**修复方案**:
```python
# 当前
for group in sorted(tree.keys()):

# 修复后
for group in sorted(tree.keys(), key=lambda x: x or ""):
```

---

## 修复执行顺序

| 优先级 | 文件 | 行号 | 问题 | 修复复杂度 |
|-------|------|------|------|----------|
| 1️⃣ | memory_store.py | 63 | 字典推导式类型 | 低 |
| 2️⃣ | aggregator.py | 58 | sorted() 类型 | 低 |
| 3️⃣ | aggregator.py | 68 | 返回值类型 | 低 |
| 4️⃣ | index.py | 57 | sorted() 类型 | 低 |

## 预计影响

- ✅ 所有修复均为类型注解相关，不影响运行时行为
- ✅ 现有 49 项测试预期全部通过
- ✅ 修复后支持严格类型检查 (mypy --strict)

## 验证步骤

1. 应用所有修复
2. 运行 `python -m mypy src/evan_tools/registry --show-error-codes` 验证
3. 运行 `pytest tests/registry -v` 确认功能完整
4. 合并回 master

## 状态追踪

- [ ] 修复 memory_store.py
- [ ] 修复 aggregator.py (2 处)
- [ ] 修复 index.py
- [ ] 验证 mypy 检查无报错
- [ ] 运行完整测试
- [ ] 合并 PR
