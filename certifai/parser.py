"""Source code parser for certifai provenance metadata."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterable, Iterator, Sequence

from .decorators import certifai, is_metadata_decorator, metadata_from_decorator
from .models import CodeArtifact, DecoratorBlock, ScrutinyLevel, TagMetadata


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:34:45.681446+00:00",
    notes="No obvious issues found.",
    history=[
        "2025-11-08T01:22:48.035364+00:00 digest=50142e7a6ec20b2027c337092f6e5136ee531bd3 last_commit=f07d0d9 by phzwart",
    ],
)
def iter_python_files(paths: Iterable[Path | str]) -> Iterator[Path]:
    """Yield Python files from the provided path collection."""

    for path in paths:
        candidate = Path(path).resolve()
        if candidate.is_dir():
            yield from candidate.rglob("*.py")
        elif candidate.suffix == ".py":
            yield candidate


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:34:45.681446+00:00",
    notes="bulk annotation",
    history=[
        "2025-11-08T01:22:48.035364+00:00 digest=ec46bf4c3989aa26bf0fd3d9524f536586596757 last_commit=f07d0d9 by phzwart",
    ],
)
def _metadata_decorator_block(lines: list[str], node: ast.AST) -> tuple[TagMetadata, DecoratorBlock | None]:
    for decorator in getattr(node, "decorator_list", []):
        if is_metadata_decorator(decorator):
            metadata = metadata_from_decorator(decorator)
            start_line = decorator.lineno
            end_line = getattr(decorator, "end_lineno", decorator.lineno)
            block_lines = lines[start_line - 1 : end_line]
            return metadata, DecoratorBlock(
                start_line=start_line,
                end_line=end_line,
                lines=block_lines,
            )
    return TagMetadata(), None


@certifai(
    ai_composed="gpt-5",
    human_certified="pending",
    scrutiny="auto",
    date="2025-11-08T00:34:45.681446+00:00",
    notes="No obvious issues found.",
    history=[
        "2025-11-08T01:22:48.035364+00:00 digest=0f16a049beb35d443e545187bb913a462048d47d last_commit=f07d0d9 by phzwart",
    ],
)
class _ArtifactVisitor(ast.NodeVisitor):
    """Collect function and class definitions along with metadata."""

    @certifai(
        ai_composed="gpt-5",
        human_certified="PHZ",
        scrutiny="auto",
        date="2025-11-08T00:34:45.681446+00:00",
        notes="No obvious issues found.",
        history=[
            "2025-11-08T01:22:48.035364+00:00 digest=50142e7a6ec20b2027c337092f6e5136ee531bd3 last_commit=f07d0d9 by phzwart",
        ],
    )
    def __init__(self, path: Path, lines: list[str]) -> None:
        self._path = path
        self._lines = lines
        self._qualname_parts: list[str] = []
        self.artifacts: list[CodeArtifact] = []

    @certifai(
        ai_composed="gpt-5",
        human_certified="PHZ",
        scrutiny="auto",
        date="2025-11-08T00:34:45.681446+00:00",
        notes="No obvious issues found.",
        history=[
            "2025-11-08T01:22:48.035364+00:00 digest=50142e7a6ec20b2027c337092f6e5136ee531bd3 last_commit=f07d0d9 by phzwart",
        ],
    )
    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802 - AST API
        self._visit_named_node(node, "class")
        self._qualname_parts.append(node.name)
        self.generic_visit(node)
        self._qualname_parts.pop()

    @certifai(
        ai_composed="gpt-5",
        human_certified="PHZ",
        scrutiny="auto",
        date="2025-11-08T00:34:45.681446+00:00",
        notes="No obvious issues found.",
        history=[
            "2025-11-08T01:22:48.035364+00:00 digest=50142e7a6ec20b2027c337092f6e5136ee531bd3 last_commit=f07d0d9 by phzwart",
        ],
    )
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        self._visit_named_node(node, "function")
        self._qualname_parts.append(node.name)
        self.generic_visit(node)
        self._qualname_parts.pop()

    @certifai(
        ai_composed="gpt-5",
        human_certified="PHZ",
        scrutiny="auto",
        date="2025-11-08T00:34:45.681446+00:00",
        notes="No obvious issues found.",
        history=[
            "2025-11-08T01:22:48.035364+00:00 digest=50142e7a6ec20b2027c337092f6e5136ee531bd3 last_commit=f07d0d9 by phzwart",
        ],
    )
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        self._visit_named_node(node, "async_function")
        self._qualname_parts.append(node.name)
        self.generic_visit(node)
        self._qualname_parts.pop()

    @certifai(
        ai_composed="gpt-5",
        human_certified="PHZ",
        scrutiny="auto",
        date="2025-11-08T00:34:45.681446+00:00",
        notes="No obvious issues found.",
        history=[
            "2025-11-08T01:22:48.035364+00:00 digest=50142e7a6ec20b2027c337092f6e5136ee531bd3 last_commit=f07d0d9 by phzwart",
        ],
    )
    def _visit_named_node(self, node: ast.AST, artifact_type: str) -> None:
        name = getattr(node, "name", "<anonymous>")
        qualname = ".".join([*self._qualname_parts, name])
        start_line = self._artifact_start_line(node)
        metadata, decorator_block = _metadata_decorator_block(self._lines, node)
        end_lineno = getattr(node, "end_lineno", None)
        indent = _indent_for_line(self._lines, start_line)
        artifact = CodeArtifact(
            name=qualname,
            artifact_type=artifact_type,
            filepath=self._path,
            lineno=node.lineno,
            end_lineno=end_lineno,
            start_line=start_line,
            tags=metadata,
            indent=indent,
            decorator=decorator_block,
        )
        self.artifacts.append(artifact)

    @certifai(
        ai_composed="gpt-5",
        human_certified="PHZ",
        scrutiny="auto",
        date="2025-11-08T00:34:45.681446+00:00",
        notes="No obvious issues found.",
        history=[
            "2025-11-08T01:22:48.035364+00:00 digest=50142e7a6ec20b2027c337092f6e5136ee531bd3 last_commit=f07d0d9 by phzwart",
        ],
    )
    @staticmethod
    def _artifact_start_line(node: ast.AST) -> int:
        decorators = getattr(node, "decorator_list", [])
        if decorators:
            return min(decorator.lineno for decorator in decorators)
        return getattr(node, "lineno", 1)


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:34:45.681446+00:00",
    notes="No obvious issues found.",
    history=[
        "2025-11-08T01:22:48.035364+00:00 digest=50142e7a6ec20b2027c337092f6e5136ee531bd3 last_commit=f07d0d9 by phzwart",
    ],
)
def _indent_for_line(lines: list[str], line_number: int) -> str:
    if 1 <= line_number <= len(lines):
        line = lines[line_number - 1]
        return line[: len(line) - len(line.lstrip(" \t"))]
    return ""


@certifai(
    ai_composed="gpt-5",
    human_certified="PHZ",
    scrutiny="auto",
    date="2025-11-08T00:34:45.681446+00:00",
    notes="No obvious issues found.",
    history=[
        "2025-11-08T01:22:48.035364+00:00 digest=50142e7a6ec20b2027c337092f6e5136ee531bd3 last_commit=f07d0d9 by phzwart",
    ],
)
def parse_file(path: Path) -> Sequence[CodeArtifact]:
    """Parse a Python file and extract provenance metadata."""

    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()
    tree = ast.parse(source, filename=str(path))
    visitor = _ArtifactVisitor(path=path, lines=lines)
    visitor.visit(tree)
    return sorted(visitor.artifacts, key=lambda artifact: artifact.start_line)
