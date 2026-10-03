"""Load the integrity scripts as modules: scripts/ is not a package."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

SCRIPTS = Path(__file__).resolve().parents[1]


def load_script(name: str) -> ModuleType:
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


import pytest  # noqa: E402


@pytest.fixture(scope="session")
def integrity() -> ModuleType:
    return load_script("check_corpus_integrity")


@pytest.fixture(scope="session")
def separation() -> ModuleType:
    return load_script("check_dataset_separation")
