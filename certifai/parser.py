"""Source code parser for certifai provenance metadata."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterable, Iterator, Sequence

from .models import CodeArtifact, CommentBlock, ScrutinyLevel, TagMetadata


def iter_python_files(paths: Iterable[Path | str]) -> Iterator[Path]:
    """Yield Python files from the provided path collection."""

    for path in paths:
        candidate = Path(path).resolve()
        if candidate.is_dir():
            yield from candidate.rglob("*.py")
        elif candidate.suffix == ".py":
            yield candidate


def _comment_block(lines: list[str], start_line: int) -> CommentBlock | None:
    block: list[str] = []
    idx = start_line - 2
    start_idx = None
    while idx >= 0:
        line = lines[idx]
        stripped = line.lstrip()
        if stripped.startswith("#"):
            block.insert(0, stripped)
            start_idx = idx
            idx -= 1
            continue
        if not stripped:
            idx -= 1
            continue
        break
    if not block or start_idx is None:
        return None
    return CommentBlock(start_line=start_idx + 1, end_line=start_line - 1, lines=block)


class _ArtifactVisitor(ast.NodeVisitor):
    """Collect function and class definitions along with metadata."""

    def __init__(self, path: Path, lines: list[str]) -> None:
        self._path = path
        self._lines = lines
        self._qualname_parts: list[str] = []
        self.artifacts: list[CodeArtifact] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802 - AST API
        self._visit_named_node(node, "class")
        self._qualname_parts.append(node.name)
        self.generic_visit(node)
        self._qualname_parts.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        self._visit_named_node(node, "function")
        self._qualname_parts.append(node.name)
        self.generic_visit(node)
        self._qualname_parts.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        self._visit_named_node(node, "async_function")
        self._qualname_parts.append(node.name)
        self.generic_visit(node)
        self._qualname_parts.pop()

    def _visit_named_node(self, node: ast.AST, artifact_type: str) -> None:
        name = getattr(node, "name", "<anonymous>")
        qualname = ".".join([*self._qualname_parts, name])
        start_line = self._artifact_start_line(node)
        comment_block = _comment_block(self._lines, start_line)
        metadata = TagMetadata.from_comment_block(comment_block.lines) if comment_block else TagMetadata()
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
            comment_block=comment_block,
        )
        self.artifacts.append(artifact)

    @staticmethod
    def _artifact_start_line(node: ast.AST) -> int:
        decorators = getattr(node, "decorator_list", [])
        if decorators:
            return min(decorator.lineno for decorator in decorators)
        return getattr(node, "lineno", 1)


def _indent_for_line(lines: list[str], line_number: int) -> str:
    if 1 <= line_number <= len(lines):
        line = lines[line_number - 1]
        return line[: len(line) - len(line.lstrip(" \t"))]
    return ""


def parse_file(path: Path) -> Sequence[CodeArtifact]:
    """Parse a Python file and extract provenance metadata."""

    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()
    tree = ast.parse(source, filename=str(path))
    visitor = _ArtifactVisitor(path=path, lines=lines)
    visitor.visit(tree)
    return sorted(visitor.artifacts, key=lambda artifact: artifact.start_line)
