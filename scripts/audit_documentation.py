"""Script to audit documentation completeness and accuracy."""

from __future__ import annotations

import ast
import doctest
import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Tuple

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "src" / "industrialstats"


def _iter_modules() -> List[str]:
    """Return dotted module paths for all modules in the package."""
    modules: List[str] = []
    for path in PACKAGE_ROOT.rglob("*.py"):
        if path.name == "__init__.py":
            continue
        rel = path.relative_to(PACKAGE_ROOT.parent)
        modules.append(".".join(rel.with_suffix("").parts))
    return modules


def check_docstring_examples() -> Dict[str, doctest.TestResults]:
    """Run doctest on all modules and collect results."""
    results: Dict[str, doctest.TestResults] = {}
    for mod_path in _iter_modules():
        module = importlib.import_module(mod_path)
        results[mod_path] = doctest.testmod(module, verbose=False)
    return results


def check_parameter_documentation() -> Dict[str, List[str]]:
    """Verify all parameters in functions appear in docstrings."""
    missing: Dict[str, List[str]] = {}
    for mod_path in _iter_modules():
        module = importlib.import_module(mod_path)
        for name, func in inspect.getmembers(module, inspect.isfunction):
            doc = inspect.getdoc(func) or ""
            params = [p.name for p in inspect.signature(func).parameters.values()]
            undocumented = [p for p in params if p not in doc]
            if undocumented:
                missing[f"{mod_path}.{name}"] = undocumented
    return missing


def generate_documentation_report() -> (
    Tuple[Dict[str, doctest.TestResults], Dict[str, List[str]]]
):
    """Generate a tuple containing doctest and parameter coverage results."""
    example_results = check_docstring_examples()
    param_results = check_parameter_documentation()
    return example_results, param_results


if __name__ == "__main__":
    examples, params = generate_documentation_report()
    for mod, result in examples.items():
        print(
            f"{mod}: {result.failed} failed, {result.attempted} attempted doctest examples"
        )
    if params:
        print("\nMissing parameter documentation:")
        for func, missing_params in params.items():
            print(f"- {func}: {', '.join(missing_params)}")
