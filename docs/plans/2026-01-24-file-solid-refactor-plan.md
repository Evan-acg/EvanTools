# File Module SOLID Refactor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor the file collection utilities to follow SOLID principles, remove duplicated traversal code, and provide clear, test-covered behavior for path gathering, filtering, sorting, progress, and error handling.

**Architecture:** Introduce a small traversal engine that separates concerns: immutable config objects, a reusable path filter, a traversal executor that owns error/progress reporting, and a thin PathGatherer facade plus gather_paths wrapper that delegate to the engine.

**Tech Stack:** Python (stdlib, pathlib, os, fnmatch, dataclasses), pytest via uv, existing repo layout.

---

### Task 1: Baseline behavior tests

**Files:**
- Create: `tests/file/test_main.py`
- Modify: none
- Test: `tests/file/test_main.py`

**Step 1: Write the failing tests**

```python
import os
from pathlib import Path
import pytest
from evan_tools.file.main import gather_paths, PathGatherer, SortBy


@pytest.fixture()
def tmp_tree(tmp_path: Path):
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.log").write_text("bb")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "c.txt").write_text("ccc")
    return tmp_path


def test_gather_paths_shallow_files_only(tmp_tree: Path):
    result = list(gather_paths([tmp_tree], deep=False, dir_only=False))
    names = sorted(p.name for p in result)
    assert names == ["a.txt", "b.log"]


def test_gather_paths_dir_only_depth(tmp_tree: Path):
    result = list(gather_paths([tmp_tree], deep=True, dir_only=True))
    assert {p.name for p in result} == {"sub"}


def test_path_gatherer_filters_and_sort(tmp_tree: Path):
    gatherer = (
        PathGatherer([tmp_tree], deep=True)
        .pattern("*.txt")
        .exclude("c.txt")
        .filter_by(size_min=1)
        .sort_by(SortBy.NAME)
    )
    result = list(gatherer.gather())
    assert [p.name for p in result] == ["a.txt"]


def test_path_gatherer_records_errors(tmp_path: Path):
    missing = tmp_path / "missing"
    gatherer = PathGatherer([missing])
    result = list(gatherer.gather())
    assert result == []
    assert gatherer.errors  # should capture the missing directory error
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/file/test_main.py -vv`

Expected: Failing assertions or import errors because refactor is not implemented yet.

**Step 3: Keep tests committed as a behavioral contract**

No code changes yet; use these tests to guide the refactor.

---

### Task 2: Extract traversal and filtering engine

**Files:**
- Modify: `src/evan_tools/file/main.py`
- Test: `tests/file/test_main.py`

**Step 1: Introduce immutable config objects**
- Add focused dataclasses (e.g., `TraversalOptions`, `FilterRules`) to hold deep/dir_only, patterns/excludes, size/mtime thresholds, sort preferences, callbacks, and error handler.
- Add lightweight validation helpers (e.g., normalize depth via `_process_depth`).

**Step 2: Implement a reusable `PathFilter`**
- Encapsulate `_should_include` logic: pattern include, exclude, attribute checks, custom filter. Keep dir vs file distinction explicit.
- Ensure it accepts a `Path` and returns bool without side effects.

**Step 3: Implement a `PathCollector`**
- Move traversal into a dedicated class that receives options + filter + callbacks.
- Provide methods for flat and recursive traversal using `os.scandir`/`os.walk`, with depth control, progress notification, and centralized error recording.
- Preserve generator semantics; avoid list materialization unless sorting is requested upstream.

**Step 4: Wire sorting strategy**
- Provide a pure function or small helper that computes sort keys (name/extension/size/mtime/ctime) using safe stat calls and handles errors deterministically.

**Step 5: Run focused tests**

Run: `uv run pytest tests/file/test_main.py::test_gather_paths_shallow_files_only tests/file/test_main.py::test_gather_paths_dir_only_depth -vv`

Expected: Still failing tests until PathGatherer is reconnected, but traversal/filter helpers should be in place with no new regressions.

---

### Task 3: Adapt PathGatherer to the engine

**Files:**
- Modify: `src/evan_tools/file/main.py`
- Test: `tests/file/test_main.py`

**Step 1: Replace internal methods**
- Update `PathGatherer` to compose `PathCollector` + `PathFilter` rather than owning traversal methods.
- Ensure chainable mutators build a `GatherConfig` that converts into the engine configs just-in-time.

**Step 2: Preserve public API and behaviors**
- Maintain `pattern`, `exclude`, `sort_by`, `filter_by`, `on_progress`, `errors` access.
- Keep generator-based results when unsorted; materialize only when sorting is requested.
- Ensure dir_only semantics apply both to roots and traversed entries.

**Step 3: Verify sorting and error recording**

Run: `uv run pytest tests/file/test_main.py::test_path_gatherer_filters_and_sort tests/file/test_main.py::test_path_gatherer_records_errors -vv`

Expected: Tests should now pass; adjust implementations until they do.

---

### Task 4: Unify `gather_paths` with the refactor

**Files:**
- Modify: `src/evan_tools/file/main.py`
- Test: `tests/file/test_main.py`

**Step 1: Re-implement `gather_paths` as a thin facade**
- Delegate to the new engine (e.g., instantiate `PathGatherer` or `PathCollector`) instead of duplicating traversal logic.
- Preserve existing signature and behaviors for dir_only and depth.

**Step 2: Clean up duplication**
- Remove or inline obsolete helpers (`_gather_flat`, `_gather_recursive`, etc.) now handled by the engine.
- Keep error handling consistent (silent failures vs recorded errors per tests).

**Step 3: Run the full file tests**

Run: `uv run pytest tests/file/test_main.py -vv`

Expected: All file-related tests should pass.

---

### Task 5: Regression sweep

**Files:**
- Modify: none (code complete)
- Test: project suite

**Step 1: Run full test suite**

Run: `uv run pytest -vv`

Expected: All tests green. Investigate and fix any regressions uncovered by other modules.

**Step 2: Finalize changes**
- Review for SOLID separation, type annotations, and docstrings.
- Prepare commit following `feat(scope): message` style.
