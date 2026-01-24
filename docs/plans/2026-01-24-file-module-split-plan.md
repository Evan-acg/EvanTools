# File Module Split Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Restructure the PathGatherer code into cohesive modules (types/config, filters, traversal, public API) while keeping the public API stable and test suite green.

**Architecture:** Split responsibilities into focused modules: enums/config and dataclasses in one place, filtering in another, traversal/collection isolated, and the builder/API facade separated. Keep `evan_tools.file` exports and backward compatibility via `main.py` and `__init__.py`.

**Tech Stack:** Python (standard library), pytest, uv for execution (per pyproject).

---

### Task 1: Add type and config modules

**Files:**
- Create: `src/evan_tools/file/config.py`
- Create: `src/evan_tools/file/sorting.py`

**Step 1: Write skeleton modules**
- Add `SortBy` enum and `_make_sort_key` in `sorting.py` (moved from `main.py`).
- Add `GatherConfig`, `FilterRules`, `TraversalOptions` in `config.py` (moved from `main.py`).

**Step 2: No code changes elsewhere yet**
- Keep original file intact until later tasks.

**Step 3: (Optional) quick import check**
- Run: `uv run python -c "import evan_tools.file.sorting, evan_tools.file.config"`
- Expected: no output/errors.

**Step 4: Commit (after later tasks)**
- Deferred; commit after full refactor.

### Task 2: Extract filter logic

**Files:**
- Create: `src/evan_tools/file/filters.py`
- Modify later: `src/evan_tools/file/main.py` to remove `PathFilter`

**Step 1: Move `PathFilter` class to `filters.py` using new imports from `config.py`.

**Step 2: Ensure `__all__` (if any) not needed now; keep class importable via module path.

**Step 3: No tests yet; will run after full wiring.

### Task 3: Extract traversal/collector logic

**Files:**
- Create: `src/evan_tools/file/collector.py`
- Modify later: `src/evan_tools/file/main.py`

**Step 1: Move `PathCollector` to `collector.py`, importing `TraversalOptions` from `config.py` and `PathFilter` from `filters.py`.

**Step 2: Keep implementation identical; only adjust imports.

### Task 4: Build gatherer facade module

**Files:**
- Create: `src/evan_tools/file/gatherer.py`
- Modify later: `src/evan_tools/file/main.py`

**Step 1: Move `_process_depth`, `PathGatherer`, and `gather_paths` into `gatherer.py`, importing from new modules (`config.py`, `filters.py`, `collector.py`, `sorting.py`).

**Step 2: Keep behavior unchanged (sorting, error tracking, chaining semantics).

### Task 5: Thin shim in `main.py` and exports

**Files:**
- Modify: `src/evan_tools/file/main.py`
- Modify: `src/evan_tools/file/__init__.py`

**Step 1: Replace old content in `main.py` with a thin re-export wrapper importing from the new modules to preserve backward compatibility for any direct imports.

**Step 2: Update `__init__.py` exports to pull from `gatherer.py` (and `config.py`/`sorting.py` if desired) while keeping the existing public API surface (`gather_paths`, `PathGatherer`, `SortBy`, `GatherConfig`).

### Task 6: Run tests and verify

**Files:**
- Tests: `tests/file/test_main.py`, `tests/file/test_path_gatherer.py`, `tests/file/test_performance.py`

**Step 1: Run focused test suite**
- Command: `uv run pytest tests/file -q`
- Expected: all tests pass.

**Step 2: (Optional) run full suite if desired**
- Command: `uv run pytest -q`

**Step 3: Prepare for commit**
- Command: `git status` to review changes.

**Step 4: Commit**
- Command: `git add src/evan_tools/file docs/plans/2026-01-24-file-module-split-plan.md`
- Command: `git commit -m "refactor(file): split path gatherer modules"`
