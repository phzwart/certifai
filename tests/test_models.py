from __future__ import annotations

from certifai.models import ScrutinyLevel, TagMetadata


def test_tag_metadata_reviewers_roundtrip() -> None:
    metadata = TagMetadata.from_decorator_kwargs(
        ai_composed="gpt-5",
        human_certified="Alice",
        agent_certified="bot-1",
        scrutiny="high",
        done=True,
        reviewers=[
            {
                "kind": "human",
                "id": "Alice",
                "scrutiny": "high",
                "notes": "Pair review",
                "timestamp": "2025-11-08T12:00:00+00:00",
            },
            {
                "kind": "agent",
                "id": "bot-1",
                "scrutiny": "medium",
            },
        ],
    )

    assert metadata.agent_certified == "bot-1"
    assert metadata.reviewers[0].kind == "human"
    assert metadata.reviewers[1].kind == "agent"
    assert metadata.reviewers[0].scrutiny == ScrutinyLevel.HIGH
    assert metadata.agent_ids == ["bot-1"]
    payload = metadata.to_decorator_payload()
    assert payload["reviewers"][0]["id"] == "Alice"
    clone = metadata.clone()
    assert clone.reviewers[0].id == "Alice"
    assert not clone.is_pending_certification
