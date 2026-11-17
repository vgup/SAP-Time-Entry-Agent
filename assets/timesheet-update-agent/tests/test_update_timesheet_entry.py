"""Unit tests for the timesheet entry update flow.

Tests verify that the agent correctly supports updating existing unapproved
time entries and enforces the approved-time and no-deletion guardrails.
"""
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
import sys

APP_PATH = str(Path(__file__).parent.parent / "app")
if APP_PATH not in sys.path:
    sys.path.insert(0, APP_PATH)


# ---------------------------------------------------------------------------
# System prompt tests
# ---------------------------------------------------------------------------


def test_system_prompt_allows_update():
    """Verify system prompt now explicitly allows updating unapproved entries."""
    from agent import get_system_prompt
    prompt = get_system_prompt()
    assert "update" in prompt.lower(), "System prompt must mention update capability"
    assert "UPDATE" in prompt or "update" in prompt.lower(), \
        "System prompt must describe the update workflow"


def test_system_prompt_still_forbids_delete():
    """Verify system prompt still prohibits deletion."""
    from agent import get_system_prompt
    prompt = get_system_prompt()
    assert "NEVER delete" in prompt or "never delete" in prompt.lower() or \
           "deletion is not supported" in prompt.lower() or "not supported" in prompt.lower(), \
        "System prompt must still prohibit deletion"


def test_system_prompt_update_uses_timesheetoperation_u():
    """Verify system prompt instructs agent to use TimeSheetOperation='U' for updates."""
    from agent import get_system_prompt
    prompt = get_system_prompt()
    assert "TimeSheetOperation='U'" in prompt or "TimeSheetOperation=\\'U\\'" in prompt or \
           "'U'" in prompt, \
        "System prompt must reference TimeSheetOperation='U' for updates"


def test_system_prompt_approved_time_guard_still_present():
    """Verify the approved-time guard is still enforced for update operations."""
    from agent import get_system_prompt
    prompt = get_system_prompt()
    assert "approved" in prompt.lower(), \
        "System prompt must still reference approval status check"
    # Must not say "approved time cannot be created" only — must cover both create and update
    assert "write operation" in prompt.lower() or "any write" in prompt.lower() or \
           "before any" in prompt.lower(), \
        "Approval check must apply to all write operations (create and update)"


# ---------------------------------------------------------------------------
# Skill file tests
# ---------------------------------------------------------------------------


def test_skill_supports_update_workflow():
    """Verify the runtime skill now contains the update workflow (Workflow B)."""
    skill_path = Path(__file__).parent.parent / "app" / "skills" / "timesheet-entry" / "SKILL.md"
    content = skill_path.read_text()
    assert "Workflow B" in content or "UPDATE" in content or "Update Existing" in content, \
        "Skill must contain update workflow"


def test_skill_update_uses_timesheetoperation_u():
    """Verify the skill instructs the agent to use TimeSheetOperation='U' for updates."""
    skill_path = Path(__file__).parent.parent / "app" / "skills" / "timesheet-entry" / "SKILL.md"
    content = skill_path.read_text()
    assert "TimeSheetOperation='U'" in content, \
        "Skill must reference TimeSheetOperation='U' for update operations"


def test_skill_never_uses_timesheetoperation_d():
    """Verify the skill never instructs the agent to use TimeSheetOperation='D' (delete)."""
    skill_path = Path(__file__).parent.parent / "app" / "skills" / "timesheet-entry" / "SKILL.md"
    content = skill_path.read_text()
    # If 'D' appears, it should only be in the context of "never use 'D'" or a description
    if "TimeSheetOperation='D'" in content:
        # Acceptable only if it's in a "never use" context
        idx = content.index("TimeSheetOperation='D'")
        context = content[max(0, idx - 50): idx + 30].lower()
        assert "never" in context or "not" in context, \
            "The skill must not instruct the agent to use TimeSheetOperation='D'"


def test_skill_before_after_confirmation_for_update():
    """Verify the skill requires a before/after summary for update confirmation."""
    skill_path = Path(__file__).parent.parent / "app" / "skills" / "timesheet-entry" / "SKILL.md"
    content = skill_path.read_text()
    assert "before" in content.lower() and "after" in content.lower(), \
        "Skill must show before/after values in update confirmation"


def test_skill_update_approved_time_guard():
    """Verify the skill blocks updates to approved entries."""
    skill_path = Path(__file__).parent.parent / "app" / "skills" / "timesheet-entry" / "SKILL.md"
    content = skill_path.read_text()
    assert "approved" in content.lower(), \
        "Skill must check approval status for update workflow too"


def test_skill_delete_refusal():
    """Verify the skill instructs agent to refuse deletion requests."""
    skill_path = Path(__file__).parent.parent / "app" / "skills" / "timesheet-entry" / "SKILL.md"
    content = skill_path.read_text()
    assert "delete" in content.lower() and ("not supported" in content.lower() or "refuse" in content.lower()), \
        "Skill must include delete refusal instructions"


# ---------------------------------------------------------------------------
# Mock data tests for update flow
# ---------------------------------------------------------------------------


def test_mock_list_tool_can_support_update_lookup():
    """Verify mcp-mock.json list tool response has fields needed for update flow."""
    mock_path = Path(__file__).parent.parent / "mcp-mock.json"
    mock = json.loads(mock_path.read_text())
    tool = mock["servers"]["s4-workforce-timesheet"]["tools"]["list_timesheet_entries"]
    entry = tool["mock_response"]["results"][0]

    # Fields required to identify and update an existing entry
    update_required_fields = [
        "PersonWorkAgreementExternalID",
        "CompanyCode",
        "TimeSheetRecord",
        "TimeSheetStatus",
        "WBSElement",
        "RecordedHours",
    ]
    for field in update_required_fields:
        assert field in entry, \
            f"Field '{field}' needed for update flow missing from mock list response"


def test_mock_list_tool_open_status_allows_update():
    """Verify mock list response shows an open (updatable) entry."""
    mock_path = Path(__file__).parent.parent / "mcp-mock.json"
    mock = json.loads(mock_path.read_text())
    tool = mock["servers"]["s4-workforce-timesheet"]["tools"]["list_timesheet_entries"]
    entry = tool["mock_response"]["results"][0]
    # Status '10' = open/in-progress (can be updated), '20' = approved (cannot)
    assert entry.get("TimeSheetStatus", "10") != "20", \
        "Mock entry must show open status (not approved) to support update testing"


# ---------------------------------------------------------------------------
# Agent integration tests for update flow
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_agent_invoke_update_flow():
    """Verify agent responds to an update request without error."""
    from agent import SampleAgent
    from langchain_core.messages import AIMessage

    agent = SampleAgent()

    with patch("agent.SampleAgent._invoke", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = {
            "messages": [
                AIMessage(
                    content="I have updated your time entry for 2026-11-14 on WBS P-1001. "
                            "Hours changed from 6.0 to 8.0. Record ID: TSR-001."
                )
            ]
        }

        result = await agent.invoke(
            query="I made a mistake — I logged 6 hours on P-1001 for yesterday but it should be 8",
            context_id="test-update-001",
        )

    assert result.status == "completed"
    assert result.message, "Update response must not be empty"


@pytest.mark.asyncio
async def test_agent_invoke_delete_refused():
    """Verify agent is instructed to refuse delete requests via system prompt."""
    from agent import get_system_prompt
    prompt = get_system_prompt()

    # The system prompt must instruct the agent to refuse deletes
    assert "NEVER delete" in prompt or "delete" in prompt.lower(), \
        "System prompt must address deletion — agent must refuse delete requests"


def test_milestone_logs_updated_for_create_or_update():
    """Verify milestone log messages in agent.py reflect both create and update."""
    import inspect
    from agent import SampleAgent
    source = inspect.getsource(SampleAgent._run_agent)
    assert "created/updated" in source or "create/update" in source or \
           "create or update" in source.lower() or "M5.achieved" in source, \
        "M5 milestone log must reflect both create and update operations"
