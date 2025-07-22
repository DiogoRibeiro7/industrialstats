# my_python_package

A minimal but production-ready Python package scaffold configured for publishing to [PyPI](https://pypi.org).

---

## 📁 File Tree

```text
my_python_package/
├── pyproject.toml            # Project metadata (PEP 621), dependencies
├── README.md                 # Project overview and usage
├── LICENSE                   # Recommended (MIT by default)
├── .gitignore                # Git ignore rules
├── .pypirc                   # (Optional) Config for PyPI uploads
├── src/
│   └── my_python_package/
│       ├── __init__.py       # Package init
│       └── core.py           # Main logic
├── tests/
│   └── test_core.py          # Unit tests
├── examples/
│   └── usage.py              # Optional usage example
```

---

## 📦 pyproject.toml (using Poetry)

```toml
[tool.poetry]
name = "my_python_package"
version = "0.1.0"
description = "A short description of the package."
authors = ["Diogo Ribeiro <dfr@esmad.ipp.pt>"]
license = "MIT"
readme = "README.md"
packages = [{ include = "my_python_package", from = "src" }]
repository = "https://github.com/DiogoRibeiro7/my_python_package"

[tool.poetry.dependencies]
python = ">=3.10"

[tool.poetry.dev-dependencies]
pytest = "^8.0.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

---

## 🧪 Example `src/my_python_package/core.py`

```python
def hello(name: str) -> str:
    """Return a greeting message."""
    return f"Hello, {name}!"
```

---

## 🧪 Example `tests/test_core.py`

```python
from my_python_package.core import hello

def test_hello():
    assert hello("Diogo") == "Hello, Diogo!"
```

---

## 🚀 Commands (Using Poetry)

```bash
# Install dependencies
poetry install

# Run tests
poetry run pytest

# Build wheel and source distribution
poetry build

# Publish to PyPI (use TestPyPI first!)
poetry publish --username __token__ --password <pypi-token>
```

To test publishing:

```bash
poetry config repositories.testpypi https://test.pypi.org/legacy/
poetry publish -r testpypi --username __token__ --password <your-test-token>
```

---

## 🛡️ .gitignore

```text
__pycache__/
*.pyc
*.pyo
*.egg-info/
dist/
build/
.env
.venv
```

---

## 📄 LICENSE (MIT Example)

```
MIT License

Copyright (c) 2025 Diogo Ribeiro

Permission is hereby granted, free of charge...
```

---

## ✅ Summary

This scaffold supports:

* Modern packaging via `pyproject.toml`
* Isolated source in `src/`
* Unit testing via `pytest`
* Easy publishing to PyPI (or TestPyPI)

Just update the metadata and you're ready to go!
