"""Spec-007 AUD-030 — ``app.middleware`` must be a real package, not a namespace.

T003 named ``apps/api/app/middleware/__init__.py`` as a deliverable. A namespace
package can import by accident today and break later under packaging changes or
path shadowing, so the guard asserts the concrete artifact and both supported
import styles.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

pytestmark = pytest.mark.spec007_isolation

PACKAGE_INIT = Path("apps/api/app/middleware/__init__.py")


def test_middleware_package_initializer_exists() -> None:
    assert PACKAGE_INIT.is_file(), f"missing required package initializer: {PACKAGE_INIT.as_posix()}"


def test_middleware_imports_as_a_regular_package() -> None:
    package = importlib.import_module("app.middleware")

    assert package.__file__ is not None, "app.middleware resolved as a namespace package"
    assert Path(package.__file__).name == "__init__.py"
    assert len(list(package.__path__)) == 1, f"app.middleware is shadowed across paths: {list(package.__path__)}"


def test_both_supported_import_styles_resolve_the_same_module() -> None:
    module = importlib.import_module("app.middleware.tenant_middleware")
    from app.middleware.tenant_middleware import TenantMiddleware, add_tenant_middleware

    assert module.TenantMiddleware is TenantMiddleware
    assert module.add_tenant_middleware is add_tenant_middleware
    assert Path(module.__file__ or "").parent == Path(importlib.import_module("app.middleware").__path__[0])
