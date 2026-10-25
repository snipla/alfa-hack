"""Проверки обнаружения новых доменов и безопасной автогенерации."""

import importlib
import sys

import app.domains
from app.core import model_loader
from app.database.models.base import Base


def test_load_models_discovers_new_files_and_nested_packages(tmp_path, monkeypatch):
    sources = {
        "loader_probe/__init__.py": "",
        "loader_probe/models.py": "MARKER = 'file'",
        "loader_package/__init__.py": "",
        "loader_package/models/__init__.py": "MARKER = 'package'",
        "loader_package/models/nested/__init__.py": "",
        "loader_package/models/nested/extra.py": "MARKER = 'nested'",
        "loader_probe/services.py": "raise RuntimeError('must not import services')",
        "loader_probe/__pycache__/models.py": "raise RuntimeError('cache')",
        ".hidden/models.py": "raise RuntimeError('hidden')",
    }
    for name, source in sources.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
    monkeypatch.setattr(model_loader, "DOMAINS_PATH", tmp_path)
    monkeypatch.setattr(app.domains, "__path__", [str(tmp_path)])
    importlib.invalidate_caches()
    try:
        modules = model_loader.load_models()
        assert modules == (
            "app.domains.loader_package.models",
            "app.domains.loader_package.models.nested",
            "app.domains.loader_package.models.nested.extra",
            "app.domains.loader_probe.models",
        )
        assert sys.modules[modules[0]].MARKER == "package"
        assert sys.modules[modules[2]].MARKER == "nested"
        assert sys.modules[modules[3]].MARKER == "file"
        assert model_loader.load_models() == modules
    finally:
        for name in tuple(sys.modules):
            if name.startswith(
                ("app.domains.loader_probe", "app.domains.loader_package")
            ):
                del sys.modules[name]


def test_unmapped_tables_are_excluded_from_autogeneration():
    model_loader.load_models()
    for name in ("users", "roles", "sessions", "requests", "unrelated_table"):
        assert not model_loader.include_model_object(None, name, "table", True, None)
    for name in Base.metadata.tables:
        # assert model_loader.include_model_object(None, name, "table", False, None)
        assert model_loader.include_model_object(None, name, "table", False, None) is (
            name != "companies"
        )


def test_domain_router_keeps_existing_ping_contract():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.domains.system.router import router

    app = FastAPI()
    app.include_router(router, prefix="/api")
    with TestClient(app) as client:
        response = client.get("/api/system/ping")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
