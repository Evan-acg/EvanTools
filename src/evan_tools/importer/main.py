import ast
import sys
import warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path


def _process_file(
    file_path: Path, stdlib_modules: frozenset, dir_name: str
) -> set[str]:
    """处理单个文件，返回第三方导入"""
    imports = set()

    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except Exception:
        return imports

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top_level = alias.name.split(".")[0]
                if top_level not in stdlib_modules and top_level != dir_name:
                    imports.add(alias.name)

        elif isinstance(node, ast.ImportFrom):
            if node.level > 0 or node.module is None:
                continue

            top_level = node.module.split(".")[0]
            if top_level not in stdlib_modules and top_level != dir_name:
                imports.add(node.module)

    return imports


def collect_third_party_imports(
    directory: str, *, max_workers: int = 4, file_threshold: int = 100
) -> set[str]:
    """收集指定目录所有Python文件中非标准库和第三方库的导入语句中的模块名。"""
    stdlib_modules = sys.stdlib_module_names
    dir_name = Path(directory).name
    py_files = list(Path(directory).rglob("*.py"))
    third_party_imports = set()

    if len(py_files) > file_threshold:
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(_process_file, f, stdlib_modules, dir_name)
                for f in py_files
            ]

            for future in futures:
                try:
                    third_party_imports.update(future.result())
                except Exception as e:
                    warnings.warn(f"Processing failed: {e}")
    else:
        for py_file in py_files:
            third_party_imports.update(_process_file(py_file, stdlib_modules, dir_name))

    return third_party_imports
