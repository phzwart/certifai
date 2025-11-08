from __future__ import annotations

from pathlib import Path

from certifai.models import ScrutinyLevel
from certifai.parser import parse_file


# @ai_composed: gpt-5
# @human_certified: PHZ
# scrutiny: high
# date: 2025-11-08T01:38:57.455828+00:00
# notes: manual review
# history: 2025-11-08T01:38:57.455828+00:00 digest=485f26e46ca6174af30e3707cdacc236ce9239f8 certified by PHZ (high) last_commit=f07d0d9 by phzwart

def test_parse_file_extracts_metadata(tmp_path: Path) -> None:
    source = """
# helper comment
def external():
    return 1

# @ai_composed: gpt-4
# @human_certified: Mentor
# scrutiny: high
# date: 2025-11-07
class Reviewed:
    pass
""".strip()
    module = tmp_path / "example.py"
    module.write_text(source + "\n", encoding="utf-8")

    artifacts = parse_file(module)
    names = [artifact.name for artifact in artifacts]

    assert names == ["external", "Reviewed"], "Expected function and class artifacts"

    external = artifacts[0]
    assert not external.tags.has_metadata
    assert external.comment_block is not None
    assert external.comment_block.lines == ["# helper comment"]

    reviewed = artifacts[1]
    assert reviewed.tags.ai_composed == "gpt-4"
    assert reviewed.tags.human_certified == "Mentor"
    assert reviewed.tags.scrutiny == ScrutinyLevel.HIGH
    assert reviewed.comment_block is not None
    assert reviewed.comment_block.start_line == 5
    assert reviewed.indent == ""
