"""Загрузка моделей доменов для Alembic без ручного списка импортов."""

import importlib
from pathlib import Path

from app.database.models.base import Base

DOMAINS_PATH = Path(__file__).resolve().parents[1] / "domains"


def _model_module_names(root: Path, package: str) -> tuple[str, ...]:
    modules: set[str] = set()
    for file in root.rglob("*.py"):
        relative = file.relative_to(root)
        if any(part.startswith((".", "__pycache__")) for part in relative.parts):
            continue
        if file.name != "models.py" and "models" not in relative.parts[:-1]:
            continue
        parts = relative.with_suffix("").parts
        if parts[-1] == "__init__":
            parts = parts[:-1]
        modules.add(".".join((package, *parts)))
    return tuple(sorted(modules))


def load_models() -> tuple[str, ...]:
    modules = _model_module_names(DOMAINS_PATH, "app.domains")
    for module in modules:
        importlib.import_module(module)
    return modules


def include_model_object(obj, name, type_, reflected, compare_to) -> bool:
    if type_ == "table":
        table = Base.metadata.tables.get(name)
        return table is not None and table.info.get("managed_by") != "laravel"
    table = getattr(obj, "table", None)
    if table is not None:
        mapped = Base.metadata.tables.get(table.key)
        if mapped is not None and mapped.info.get("managed_by") == "laravel":
            return False
    return True
