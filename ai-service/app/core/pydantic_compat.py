from __future__ import annotations

from typing import Any


def model_to_dict(value: Any) -> dict[str, Any]:
    """Return a plain dict for Pydantic v1/v2 model-like values."""
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "dict"):
        return value.dict()
    if isinstance(value, dict):
        return value
    return dict(value)


def models_to_dicts(values: list[Any]) -> list[dict[str, Any]]:
    return [model_to_dict(value) for value in values]


def model_copy_update(value: Any, update: dict[str, Any]) -> Any:
    """Copy a Pydantic v1/v2 model with field updates."""
    if hasattr(value, "model_copy"):
        return value.model_copy(update=update)
    if hasattr(value, "copy"):
        return value.copy(update=update)
    copied = dict(value)
    copied.update(update)
    return copied
