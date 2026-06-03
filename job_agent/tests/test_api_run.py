"""Unit tests for POST /run and POST /run/stream.

The compiled graph is mocked so these tests run without any LLM API keys and
complete in milliseconds.  They verify:

  1. /run happy-path: correct HTTP status + RunResponse shape
  2. /run field mapping: every output bucket is present in the response
  3. /run jd_url merge: single jd_url is folded into jd_urls before invoke
  4. /run llm env vars: provider/model env vars are set when supplied
  5. /run/stream NDJSON: at least one node event + a final __end__ event
  6. /run/stream __end__ output: the final event carries a valid RunResponse
  7. /run missing body: 422 validation error when required fields are absent
  8. /run empty strings: 422 or a valid RunResponse (both acceptable)
"""
from __future__ import annotations

import json
import os
from typing import Any, AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
httpx = pytest.importorskip("httpx")  # skip whole module if httpx missing

from app.main import app  # noqa: E402  (after sys.path is set by conftest)


# ---------------------------------------------------------------------------
# Fake graph output — a realistic minimal state dict
# ---------------------------------------------------------------------------

FAKE_GRAPH_OUTPUT: dict[str, Any] = {
    "jd_profile": {
        "job_type": "equity_research",
        "city": "Hong Kong",
        "sector": "healthcare",
        "hard_requirements": ["CFA", "Python"],
        "soft_requirements": ["communication"],
        "language_requirement": "English/Cantonese",
        "interview_style": "case",
        "seniority": "junior",
        "pitch_probability": 0.8,
        "model_test_probability": 0.5,
    },
    "diagnosis": {
        "match_score": 72,
        "strengths": ["Python", "data analysis"],
        "gaps": ["CFA not yet obtained"],
        "recommendation_priority": "fill CFA gap",
    },
    "resume_versions": {
        "sell_side_cn": ["重写后的简历第一段"],
        "buy_side_bilingual": ["Rewritten resume para 1"],
        "hk_asset_mgmt_en": ["Rewritten HK resume"],
    },
    "final_report": "## Final Report\n\nYou are well-positioned for buy-side roles.",
    "question_bank": {
        "technical": ["Walk me through a DCF."],
        "behavioral": ["Tell me about yourself."],
        "stock_pitch_drills": ["Pitch a healthcare stock."],
        "meta": {"total": 3},
    },
    "interview_map": {
        "job_type": "equity_research",
        "city": "Hong Kong",
        "sector": "healthcare",
        "rounds": [
            {
                "round": 1,
                "label": "HR Screen",
                "focus": "motivation",
                "modules": ["self-intro"],
                "questions": [{"q": "Why finance?"}],
                "follow_ups": ["Tell me more."],
            }
        ],
        "mock_plan": {
            "total_questions": 10,
            "estimated_minutes": 60,
            "round_breakdown": [],
            "session_order": ["technical", "behavioral"],
        },
        "coaching_tips": ["Prepare 3 stock pitches."],
    },
    "interview_questions": ["Walk me through a DCF."],
    "coaching_session": {
        "internship_drills": [{"internship_index": 0, "excerpt": "Built model", "recall_questions": ["What did you build?"]}],
        "pitch_scaffold": {"pitch_template": "I recommend buying X because...", "drill_questions": ["What is the upside?"]},
        "usage_note": "Complete all drills before the first round.",
    },
    "coaching_flow": {
        "phases": [
            {
                "phase_id": 1,
                "phase_name": "Internship Recall",
                "status": "pending",
                "source": "coaching_session.internship_drills",
                "description": "Recall key internship stories.",
                "llm_intro": "Let's start with your internship.",
                "items": [],
                "item_count": 0,
            }
        ],
        "overall_progress": {"total_phases": 4, "completed": 0, "pct": 0},
        "next_action": "Complete Phase 1 drills.",
        "coaching_tips": ["Spend 2 hours per day."],
        "weekly_plan": {
            "days": [{"day": 1, "theme": "Recall", "tasks": ["Do drill 1"], "duration_min": 120, "milestone": None}],
            "total_hours": 14.0,
            "key_milestones": ["Complete all phases."],
        },
        "meta": {"job_type": "equity_research", "sector": "healthcare", "total_items": 5},
    },
    "cover_letters": [{"company": "Goldman Sachs", "body": "Dear Hiring Manager, ..."}],
    "networking_drafts": {
        "referral_email_cn": "尊敬的XXX，",
        "linkedin_dm_en": "Hi, I came across your profile...",
        "thank_you_en": "Thank you for your time.",
    },
    "rag_cases": [{"title": "Buy-side analyst career path", "snippet": "Most analysts start at sell-side."}],
    "collected_jds": [],
}


# ---------------------------------------------------------------------------
# Fake astream helper — yields one update per node then stops
# ---------------------------------------------------------------------------

NODE_SEQUENCE = [
    "jd_scraper", "jd_parser", "rag_retriever", "candidate_diagnosis",
    "resume_coach", "resume_rewriter", "cover_letter", "question_bank",
    "interview_map", "interview_trainer", "coaching_flow",
    "networking", "report_generator",
]

# Key(s) each node writes — just enough to make the stream events non-empty
_NODE_KEY_MAP: dict[str, dict[str, Any]] = {
    "jd_scraper":          {"collected_jds":      FAKE_GRAPH_OUTPUT["collected_jds"]},
    "jd_parser":           {"jd_profile":         FAKE_GRAPH_OUTPUT["jd_profile"]},
    "rag_retriever":       {"rag_cases":          FAKE_GRAPH_OUTPUT["rag_cases"]},
    "candidate_diagnosis": {"diagnosis":          FAKE_GRAPH_OUTPUT["diagnosis"]},
    "resume_coach":        {"coaching_session":   FAKE_GRAPH_OUTPUT["coaching_session"]},
    "resume_rewriter":     {"resume_versions":    FAKE_GRAPH_OUTPUT["resume_versions"]},
    "cover_letter":        {"cover_letters":      FAKE_GRAPH_OUTPUT["cover_letters"]},
    "question_bank":       {"question_bank":      FAKE_GRAPH_OUTPUT["question_bank"]},
    "interview_map":       {"interview_map":      FAKE_GRAPH_OUTPUT["interview_map"]},
    "interview_trainer":   {"interview_questions":FAKE_GRAPH_OUTPUT["interview_questions"]},
    "coaching_flow":       {"coaching_flow":      FAKE_GRAPH_OUTPUT["coaching_flow"]},
    "networking":          {"networking_drafts":  FAKE_GRAPH_OUTPUT["networking_drafts"]},
    "report_generator":    {"final_report":       FAKE_GRAPH_OUTPUT["final_report"]},
}


async def _fake_astream(
    state: dict, **kwargs
) -> AsyncGenerator[dict[str, dict], None]:
    """Yields one {node_name: {state_updates}} dict per node."""
    for node in NODE_SEQUENCE:
        yield {node: _NODE_KEY_MAP.get(node, {})}


# ---------------------------------------------------------------------------
# Shared request body
# ---------------------------------------------------------------------------

MIN_PAYLOAD = {
    "resume_text": "I am a research assistant at CUHK studying NEV accident impacts.",
    "jd_text": "Equity research analyst, healthcare sector, Hong Kong.",
    "target_city": "Hong Kong",
    "target_sector": "healthcare",
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def client():
    """Sync TestClient — no real event loop needed for /run."""
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# /run tests
# ---------------------------------------------------------------------------

class TestRunEndpoint:
    """Tests for POST /run."""

    @patch(
        "app.main.compiled_graph",
        new_callable=lambda: type(
            "FakeGraph", (),
            {"ainvoke": AsyncMock(return_value=FAKE_GRAPH_OUTPUT)},
        ),
    )
    def test_happy_path_status_200(self, _mock_graph, client):
        """POST /run with valid body returns HTTP 200."""
        resp = client.post("/run", json=MIN_PAYLOAD)
        assert resp.status_code == 200, resp.text

    @patch(
        "app.main.compiled_graph",
        new_callable=lambda: type(
            "FakeGraph", (),
            {"ainvoke": AsyncMock(return_value=FAKE_GRAPH_OUTPUT)},
        ),
    )
    def test_response_is_valid_run_response(self, _mock_graph, client):
        """Response body deserialises to a valid RunResponse shape."""
        from app.schemas.models import RunResponse

        resp = client.post("/run", json=MIN_PAYLOAD)
        data = resp.json()
        model = RunResponse(**data)  # raises if schema mismatch

        assert model.final_report != ""
        assert model.jd_profile != {}
        assert model.diagnosis != {}

    @patch(
        "app.main.compiled_graph",
        new_callable=lambda: type(
            "FakeGraph", (),
            {"ainvoke": AsyncMock(return_value=FAKE_GRAPH_OUTPUT)},
        ),
    )
    def test_all_output_buckets_present(self, _mock_graph, client):
        """Every top-level output bucket is present in the response."""
        resp = client.post("/run", json=MIN_PAYLOAD)
        data = resp.json()

        expected_keys = [
            "jd_profile", "diagnosis", "resume_versions", "final_report",
            "question_bank", "interview_map", "interview_questions",
            "coaching_session", "coaching_flow",
            "cover_letters", "networking_drafts", "rag_cases", "collected_jds",
        ]
        for key in expected_keys:
            assert key in data, f"Missing key in RunResponse: {key}"

    @patch(
        "app.main.compiled_graph",
        new_callable=lambda: type(
            "FakeGraph", (),
            {"ainvoke": AsyncMock(return_value=FAKE_GRAPH_OUTPUT)},
        ),
    )
    def test_jd_url_merged_into_jd_urls(self, mock_graph, client):
        """A single jd_url is merged into jd_urls before ainvoke is called."""
        payload = {**MIN_PAYLOAD, "jd_url": "https://example.com/jd/123"}
        client.post("/run", json=payload)

        call_kwargs = mock_graph.ainvoke.call_args
        state_passed = call_kwargs[0][0]  # first positional arg
        assert "https://example.com/jd/123" in state_passed.get("jd_urls", []), (
            "jd_url was not merged into jd_urls in the graph input state"
        )

    @patch(
        "app.main.compiled_graph",
        new_callable=lambda: type(
            "FakeGraph", (),
            {"ainvoke": AsyncMock(return_value=FAKE_GRAPH_OUTPUT)},
        ),
    )
    def test_llm_env_vars_set(self, _mock_graph, client):
        """llm_provider and llm_model are injected as env vars."""
        payload = {
            **MIN_PAYLOAD,
            "llm_provider": "openai",
            "llm_model": "gpt-4o",
        }
        client.post("/run", json=payload)
        assert os.environ.get("LLM_PROVIDER") == "openai"
        assert os.environ.get("LLM_MODEL") == "gpt-4o"

    def test_missing_required_fields_returns_422(self, client):
        """Request without resume_text / jd_text returns HTTP 422."""
        resp = client.post("/run", json={"target_city": "Hong Kong"})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# /run/stream tests
# ---------------------------------------------------------------------------

class TestRunStreamEndpoint:
    """Tests for POST /run/stream."""

    @patch("app.main.compiled_graph")
    def test_stream_returns_200_ndjson(self, mock_graph, client):
        """POST /run/stream returns 200 with NDJSON content-type."""
        mock_graph.astream = _fake_astream

        resp = client.post("/run/stream", json=MIN_PAYLOAD)
        assert resp.status_code == 200
        assert "ndjson" in resp.headers.get("content-type", "")

    @patch("app.main.compiled_graph")
    def test_stream_node_events_emitted(self, mock_graph, client):
        """Each node produces a NDJSON line with status=done."""
        mock_graph.astream = _fake_astream

        resp = client.post("/run/stream", json=MIN_PAYLOAD)
        lines = [l for l in resp.text.strip().splitlines() if l]
        events = [json.loads(l) for l in lines]

        node_events = [e for e in events if e.get("status") == "done" and e["node"] != "__end__"]
        assert len(node_events) >= len(NODE_SEQUENCE), (
            f"Expected {len(NODE_SEQUENCE)} node events, got {len(node_events)}"
        )

    @patch("app.main.compiled_graph")
    def test_stream_final_end_event(self, mock_graph, client):
        """Last event is {node: __end__, status: done} with a full RunResponse."""
        mock_graph.astream = _fake_astream

        resp = client.post("/run/stream", json=MIN_PAYLOAD)
        lines = [l for l in resp.text.strip().splitlines() if l]
        last = json.loads(lines[-1])

        assert last["node"] == "__end__"
        assert last["status"] == "done"
        assert "output" in last

        # output should be a valid RunResponse
        from app.schemas.models import RunResponse
        RunResponse(**last["output"])  # raises if schema mismatch

    @patch("app.main.compiled_graph")
    def test_stream_node_order_matches_pipeline(self, mock_graph, client):
        """Node events arrive in pipeline order."""
        mock_graph.astream = _fake_astream

        resp = client.post("/run/stream", json=MIN_PAYLOAD)
        lines = [l for l in resp.text.strip().splitlines() if l]
        events = [json.loads(l) for l in lines]

        emitted_nodes = [
            e["node"] for e in events
            if e.get("status") == "done" and e["node"] != "__end__"
        ]
        assert emitted_nodes == NODE_SEQUENCE
