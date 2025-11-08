"""Decorator helpers for certifai provenance metadata."""

from __future__ import annotations

import ast
import json
from typing import Any, Callable, Iterable, Sequence, TypeVar

from .models import ScrutinyLevel, TagMetadata

F = TypeVar("F", bound=Callable[..., Any])

PROVENANCE_DECORATOR_NAME = "certifai"
PROVENANCE_DECORATOR_ALIASES = {
    PROVENANCE_DECORATOR_NAME,
    f"decorators.{PROVENANCE_DECORATOR_NAME}",
    f"certifai.decorators.{PROVENANCE_DECORATOR_NAME}",
}


def certifai(
    *,
    ai_composed: str | None = None,
    human_certified: str | None = None,
    scrutiny: str | ScrutinyLevel | None = None,
    date: str | None = None,
    notes: str | None = None,
    history: Sequence[str] | None = None,
    extras: Sequence[str] | None = None,
) -> Callable[[F], F]:
    """Runtime no-op decorator used to attach provenance metadata."""

    def _decorator(target: F) -> F:
        return target

    return _decorator


def decorator_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Call):
        return decorator_name(node.func)
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parts: list[str] = []
        current: ast.AST | None = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value  # type: ignore[assignment]
        if isinstance(current, ast.Name):
            parts.append(current.id)
            return ".".join(reversed(parts))
    return None


def is_metadata_decorator(node: ast.AST) -> bool:
    name = decorator_name(node)
    if name is None:
        return False
    short_name = name.split(".")[-1]
    return short_name == PROVENANCE_DECORATOR_NAME or name in PROVENANCE_DECORATOR_ALIASES


def metadata_from_decorator(node: ast.AST) -> TagMetadata:
    if not isinstance(node, ast.Call):
        return TagMetadata()

    kwargs: dict[str, Any] = {}
    for keyword in node.keywords:
        if keyword.arg is None:
            continue
        kwargs[keyword.arg] = _literal_value(keyword.value)

    history = _normalize_sequence(kwargs.get("history"))
    extras = _normalize_sequence(kwargs.get("extras"))
    scrutiny = kwargs.get("scrutiny")
    if isinstance(scrutiny, ScrutinyLevel):
        scrutiny_value: ScrutinyLevel | str | None = scrutiny
    elif isinstance(scrutiny, str):
        scrutiny_value = scrutiny
    else:
        scrutiny_value = None

    return TagMetadata.from_decorator_kwargs(
        ai_composed=_as_optional_str(kwargs.get("ai_composed")),
        human_certified=_as_optional_str(kwargs.get("human_certified")),
        scrutiny=scrutiny_value,
        date=_as_optional_str(kwargs.get("date")),
        notes=_as_optional_str(kwargs.get("notes")),
        history=history,
        extras=extras,
    )


def format_metadata_decorator(metadata: TagMetadata, indent: str = "") -> list[str]:
    payload = metadata.to_decorator_payload()
    lines: list[str] = []
    prefix = f"{indent}@{PROVENANCE_DECORATOR_NAME}"
    if not payload:
        return [f"{prefix}()"]

    lines.append(f"{prefix}(")
    for key in ("ai_composed", "human_certified", "scrutiny", "date", "notes"):
        if key in payload:
            value = payload.pop(key)
            lines.append(f"{indent}    {key}={_format_value(value)},")

    for sequence_key in ("history", "extras"):
        if sequence_key in payload:
            values = payload.pop(sequence_key)
            lines.extend(_format_sequence(sequence_key, values, indent))

    for key, value in payload.items():
        lines.append(f"{indent}    {key}={_format_value(value)},")

    lines.append(f"{indent})")
    return lines


def _format_sequence(name: str, values: Iterable[Any], indent: str) -> list[str]:
    nested: list[str] = [f"{indent}    {name}=["]
    for item in values:
        nested.append(f"{indent}        {_format_value(item)},")
    nested.append(f"{indent}    ],")
    return nested


def _format_value(value: Any) -> str:
    if isinstance(value, ScrutinyLevel):
        return _format_value(value.value)
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, (list, tuple)):
        inner = ", ".join(_format_value(item) for item in value)
        return f"[{inner}]"
    if value is None:
        return "None"
    if isinstance(value, bool):
        return "True" if value else "False"
    return repr(value)


def _literal_value(node: ast.AST) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, (ast.List, ast.Tuple)):
        return [_literal_value(element) for element in node.elts]
    return None


def _normalize_sequence(value: Any) -> list[str] | None:
    if value is None:
        return None
    if isinstance(value, str):
        return [value]
    if isinstance(value, Sequence):
        result: list[str] = []
        for item in value:
            if item is None:
                continue
            result.append(str(item))
        return result
    return None


def _as_optional_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return str(value)


__all__ = [
    "PROVENANCE_DECORATOR_NAME",
    "PROVENANCE_DECORATOR_ALIASES",
    "certifai",
    "decorator_name",
    "format_metadata_decorator",
    "is_metadata_decorator",
    "metadata_from_decorator",
]
