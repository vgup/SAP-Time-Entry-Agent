"""Unit tests for the create_timesheet_entry MCP tool mock.

Tests verify the mock response structure and input schema for the tool that
creates new time entries in SAP S/4HANA.
"""
import json
from pathlib import Path


def test_create_timesheet_entry_mock_exists():
    """Verify mcp-mock.json contains the create_timesheet_entry tool."""
    mock_path = Path(__file__).parent.parent / "mcp-mock.json"
    assert mock_path.exists(), "mcp-mock.json must exist"
    mock = json.loads(mock_path.read_text())
    server = mock["servers"]["s4-workforce-timesheet"]
    assert "create_timesheet_entry" in server["tools"], "create_timesheet_entry tool must be defined"


def test_create_timesheet_entry_has_mock_response():
    """Verify mock response for create_timesheet_entry has correct structure."""
    mock_path = Path(__file__).parent.parent / "mcp-mock.json"
    mock = json.loads(mock_path.read_text())
    tool = mock["servers"]["s4-workforce-timesheet"]["tools"]["create_timesheet_entry"]

    assert "mock_response" in tool
    response = tool["mock_response"]
    # Create response returns a single entity (not an array)
    assert isinstance(response, dict), "Create response must be a single object"
    assert "TimeSheetRecord" in response, "Must return created record ID"


def test_create_timesheet_entry_mock_has_required_output_fields():
    """Verify created entry mock response has fields confirming successful creation."""
    mock_path = Path(__file__).parent.parent / "mcp-mock.json"
    mock = json.loads(mock_path.read_text())
    tool = mock["servers"]["s4-workforce-timesheet"]["tools"]["create_timesheet_entry"]
    response = tool["mock_response"]

    required_fields = [
        "PersonWorkAgreementExternalID",
        "CompanyCode",
        "TimeSheetRecord",
        "TimeSheetDate",
        "TimeSheetOperation",
        "RecordedHours",
    ]
    for field in required_fields:
        assert field in response, f"Required output field '{field}' missing from mock response"


def test_create_timesheet_entry_operation_is_create():
    """Verify mock response shows 'C' (Create) operation type."""
    mock_path = Path(__file__).parent.parent / "mcp-mock.json"
    mock = json.loads(mock_path.read_text())
    tool = mock["servers"]["s4-workforce-timesheet"]["tools"]["create_timesheet_entry"]
    response = tool["mock_response"]
    assert response["TimeSheetOperation"] == "C", "Mock create entry must have operation 'C'"


def test_create_timesheet_entry_input_schema():
    """Verify input schema requires body parameter."""
    mock_path = Path(__file__).parent.parent / "mcp-mock.json"
    mock = json.loads(mock_path.read_text())
    tool = mock["servers"]["s4-workforce-timesheet"]["tools"]["create_timesheet_entry"]

    assert "input_schema" in tool
    schema = tool["input_schema"]
    assert schema["type"] == "object"
    assert "body" in schema.get("required", []), "body must be required for create"


def test_create_timesheet_entry_no_approved_time_flag():
    """Verify mock response shows entry is NOT in approved status (create-only guard)."""
    mock_path = Path(__file__).parent.parent / "mcp-mock.json"
    mock = json.loads(mock_path.read_text())
    tool = mock["servers"]["s4-workforce-timesheet"]["tools"]["create_timesheet_entry"]
    response = tool["mock_response"]
    # Newly created entries should be in initial status (10 = In-Progress), not approved (20)
    assert response.get("TimeSheetStatus", "10") != "20", \
        "Newly created entry must not have approved status"
