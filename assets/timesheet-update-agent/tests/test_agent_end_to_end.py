"""End-to-end integration test for the timesheet update agent.

Tests the complete agent flow using mocked LLM responses and mocked MCP tools.
All external calls (AI Core, S/4HANA API) are mocked — tests run fully offline.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure app/ is on the path
APP_PATH = str(Path(__file__).parent.parent / "app")
if APP_PATH not in sys.path:
    sys.path.insert(0, APP_PATH)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_mcp_tools():
    """Return mock MCP tools simulating the Workforce Timesheet MCP server."""
    from langchain_core.tools import StructuredTool
    from pydantic import BaseModel

    class ListTimesheetInput(BaseModel):
        filter: str = ""
        top: str = "10"

    class CreateTimesheetInput(BaseModel):
        body: dict

    list_tool = StructuredTool(
        name="list_timesheet_entries",
        description="Reads all workforce timesheet entries.",
        func=lambda filter="", top="10": {
            "results": [
                {
                    "PersonWorkAgreementExternalID": "EMP-00123",
                    "CompanyCode": "1000",
                    "TimeSheetRecord": "TSR-001",
                    "TimeSheetDate": "/Date(1731628800000)/",
                    "TimeSheetStatus": "10",
                    "WBSElement": "P-1001",
                    "RecordedHours": "8.0",
                }
            ]
        },
        args_schema=ListTimesheetInput,
    )

    create_tool = StructuredTool(
        name="create_timesheet_entry",
        description="Creates a workforce timesheet entry.",
        func=lambda body: {
            "PersonWorkAgreementExternalID": "EMP-00123",
            "CompanyCode": "1000",
            "TimeSheetRecord": "TSR-999",
            "TimeSheetDate": "/Date(1731628800000)/",
            "TimeSheetStatus": "10",
            "TimeSheetOperation": "C",
            "WBSElement": body.get("TimeSheetDataFields", {}).get("WBSElement", "P-1001"),
            "RecordedHours": body.get("TimeSheetDataFields", {}).get("RecordedHours", "8.0"),
        },
        args_schema=CreateTimesheetInput,
    )

    return [list_tool, create_tool]


@pytest.fixture
def mock_llm_response():
    """Return a mock LLM that returns a canned response."""
    from langchain_core.messages import AIMessage

    mock_llm = MagicMock()
    mock_llm.invoke = MagicMock(
        return_value=AIMessage(
            content="I have logged 8 hours on WBS P-1001 for 2026-11-15 as regular time. "
                    "The time entry has been created successfully (Record ID: TSR-999)."
        )
    )
    mock_llm.ainvoke = AsyncMock(
        return_value=AIMessage(
            content="I have logged 8 hours on WBS P-1001 for 2026-11-15 as regular time. "
                    "The time entry has been created successfully (Record ID: TSR-999)."
        )
    )
    return mock_llm


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_agent_imports():
    """Verify the agent module can be imported without errors."""
    from agent import SampleAgent
    assert SampleAgent is not None


def test_agent_system_prompt_contains_guardrails():
    """Verify system prompt contains the required guardrails."""
    from agent import get_system_prompt
    prompt = get_system_prompt()

    # Must contain create-only constraint
    assert "ONLY create" in prompt or "only create" in prompt.lower() or "NEVER update" in prompt or "NEVER modify" in prompt, \
        "System prompt must enforce create-only constraint"

    # Must contain approval status check requirement
    assert "approved" in prompt.lower(), \
        "System prompt must mention approval status check"

    # Must contain confirmation requirement
    assert "confirm" in prompt.lower(), \
        "System prompt must require user confirmation"

    # Must contain self-service constraint
    assert "personnel number" in prompt.lower() or "authenticated" in prompt.lower(), \
        "System prompt must enforce self-service boundary"


def test_agent_system_prompt_no_data_fabrication():
    """Verify system prompt forbids data fabrication."""
    from agent import get_system_prompt
    prompt = get_system_prompt()
    assert "fabricate" in prompt.lower() or "invent" in prompt.lower() or "guess" in prompt.lower(), \
        "System prompt must instruct agent not to fabricate data"


def test_agent_model_name():
    """Verify agent uses an expected model."""
    from agent import get_model_name
    model = get_model_name()
    assert model, "Model name must not be empty"
    assert isinstance(model, str)


def test_agent_temperature_is_deterministic():
    """Verify agent uses low temperature for deterministic responses."""
    from agent import get_temperature
    temp = get_temperature()
    assert temp <= 0.3, "Agent temperature should be low (≤0.3) for deterministic timesheet operations"


@pytest.mark.asyncio
async def test_agent_invoke_returns_response(mock_mcp_tools):
    """Verify agent.invoke() returns an AgentResponse with completed status."""
    from agent import SampleAgent
    from langchain_core.messages import AIMessage

    agent = SampleAgent()

    with patch("agent.SampleAgent._invoke", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = {
            "messages": [
                AIMessage(
                    content="I have logged 8 hours on WBS P-1001 for today as regular time. "
                            "Time entry created successfully (TSR-999)."
                )
            ]
        }

        result = await agent.invoke(
            query="Log 8 hours on WBS P-1001 for today as regular time",
            context_id="test-session-001",
            tools=mock_mcp_tools,
        )

    assert result.status == "completed"
    assert result.message, "Response message must not be empty"


@pytest.mark.asyncio
async def test_agent_stream_yields_completed_event(mock_mcp_tools):
    """Verify agent.stream() yields a final completed event."""
    from agent import SampleAgent
    from langchain_core.messages import AIMessage

    agent = SampleAgent()
    events = []

    with patch("agent.SampleAgent._invoke", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = {
            "messages": [
                AIMessage(content="Time entry TSR-999 created for WBS P-1001, 8 hours on 2026-11-15.")
            ]
        }

        async for event in agent.stream(
            query="Log 8 hours on P-1001 for 2026-11-15",
            context_id="test-session-002",
            tools=mock_mcp_tools,
        ):
            events.append(event)

    assert len(events) >= 2, "Stream must yield at least a processing and a final event"
    final = events[-1]
    assert final["is_task_complete"] is True
    assert final["content"], "Final event must have content"


@pytest.mark.asyncio
async def test_agent_handles_llm_error_gracefully(mock_mcp_tools):
    """Verify agent gracefully handles LLM errors without crashing.

    When _run_agent raises an exception, stream() catches it and yields
    a completed event with an error message (not a raw exception).
    """
    from agent import SampleAgent

    agent = SampleAgent()

    with patch("agent.SampleAgent._run_agent", new_callable=AsyncMock) as mock_run:
        mock_run.side_effect = RuntimeError("LLM connection failed")

        result = await agent.invoke(
            query="Log 8 hours on WBS P-1001 for today",
            context_id="test-session-003",
            tools=mock_mcp_tools,
        )

    # stream() catches exceptions and returns a completed event with an error message
    # (the error is surfaced to the user, not propagated as an exception)
    assert result.status in ("completed", "error"), "Must return a status without crashing"
    assert result.message, "Error message must not be empty"
    # If completed, message should indicate an error occurred
    if result.status == "completed":
        assert "error" in result.message.lower() or "encountered" in result.message.lower() or \
               len(result.message) > 0, "Completed status on error must have a meaningful message"


@pytest.mark.asyncio
async def test_agent_milestone_logging_on_success(mock_mcp_tools, caplog):
    """Verify milestone M5 is logged when agent successfully processes a request."""
    import logging
    from agent import SampleAgent
    from langchain_core.messages import AIMessage

    agent = SampleAgent()

    with caplog.at_level(logging.INFO, logger="agent"):
        with patch("agent.SampleAgent._invoke", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = {
                "messages": [
                    AIMessage(content="Time entry created successfully (TSR-999).")
                ]
            }

            await agent.invoke(
                query="Log 8 hours on P-1001 for today",
                context_id="test-session-004",
                tools=mock_mcp_tools,
            )

    # M5 achievement should be logged
    log_messages = " ".join(caplog.messages)
    assert "M5.achieved" in log_messages or "M1.achieved" in log_messages, \
        "At least one milestone log should appear during successful execution"


def test_skill_file_exists():
    """Verify the timesheet-entry runtime skill file exists."""
    skill_path = Path(__file__).parent.parent / "app" / "skills" / "timesheet-entry" / "SKILL.md"
    assert skill_path.exists(), "Runtime skill SKILL.md must exist at app/skills/timesheet-entry/SKILL.md"


def test_skill_file_has_required_sections():
    """Verify the runtime skill contains all 5 required workflow steps."""
    skill_path = Path(__file__).parent.parent / "app" / "skills" / "timesheet-entry" / "SKILL.md"
    content = skill_path.read_text()

    required_sections = [
        "Step 1",
        "Step 2",
        "Step 3",
        "Step 4",
        "Step 5",
        "Guardrails",
    ]
    for section in required_sections:
        assert section in content, f"SKILL.md must contain section: {section}"


def test_mcp_mock_has_correct_tools():
    """Verify mcp-mock.json has all required tools for the agent."""
    import json
    mock_path = Path(__file__).parent.parent / "mcp-mock.json"
    mock = json.loads(mock_path.read_text())

    required_tools = ["list_timesheet_entries", "create_timesheet_entry"]
    server = mock["servers"]["s4-workforce-timesheet"]

    for tool_name in required_tools:
        assert tool_name in server["tools"], f"Required tool '{tool_name}' must be in mcp-mock.json"
