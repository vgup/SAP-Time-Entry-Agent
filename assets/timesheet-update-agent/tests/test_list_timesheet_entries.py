"""Unit tests for the list_timesheet_entries MCP tool mock.

Tests verify the mock response structure for the tool that reads timesheet entries
to check approval status before creating new entries.
"""
import json
from pathlib import Path


def test_list_timesheet_entries_mock_exists():
    """Verify mcp-mock.json contains the list_timesheet_entries tool."""
    mock_path = Path(__file__).parent.parent / "mcp-mock.json"
    assert mock_path.exists(), "mcp-mock.json must exist"
    mock = json.loads(mock_path.read_text())
    server = mock["servers"]["s4-workforce-timesheet"]
    assert "list_timesheet_entries" in server["tools"], "list_timesheet_entries tool must be defined"


def test_list_timesheet_entries_has_mock_response():
    """Verify mock response for list_timesheet_entries has correct structure."""
    mock_path = Path(__file__).parent.parent / "mcp-mock.json"
    mock = json.loads(mock_path.read_text())
    tool = mock["servers"]["s4-workforce-timesheet"]["tools"]["list_timesheet_entries"]

    assert "mock_response" in tool
    response = tool["mock_response"]
    assert "results" in response, "List response must have 'results' array"
    assert len(response["results"]) >= 1, "Must have at least one result"


def test_list_timesheet_entries_result_has_required_fields():
    """Verify timesheet entry result has key fields needed for approval status check."""
    mock_path = Path(__file__).parent.parent / "mcp-mock.json"
    mock = json.loads(mock_path.read_text())
    tool = mock["servers"]["s4-workforce-timesheet"]["tools"]["list_timesheet_entries"]
    entry = tool["mock_response"]["results"][0]

    required_fields = [
        "PersonWorkAgreementExternalID",
        "CompanyCode",
        "TimeSheetRecord",
        "TimeSheetDate",
        "TimeSheetStatus",
        "WBSElement",
        "RecordedHours",
    ]
    for field in required_fields:
        assert field in entry, f"Required field '{field}' missing from mock entry"


def test_list_timesheet_entries_input_schema():
    """Verify input schema for list_timesheet_entries has expected filter parameters."""
    mock_path = Path(__file__).parent.parent / "mcp-mock.json"
    mock = json.loads(mock_path.read_text())
    tool = mock["servers"]["s4-workforce-timesheet"]["tools"]["list_timesheet_entries"]

    assert "input_schema" in tool
    schema = tool["input_schema"]
    assert schema["type"] == "object"
    assert "properties" in schema
    # Must have filter parameter for approval status check
    assert "filter" in schema["properties"], "filter parameter needed for approval status check"


def test_list_timesheet_entries_open_period_status():
    """Verify mock entry shows an open (not approved) time period status."""
    mock_path = Path(__file__).parent.parent / "mcp-mock.json"
    mock = json.loads(mock_path.read_text())
    tool = mock["servers"]["s4-workforce-timesheet"]["tools"]["list_timesheet_entries"]
    entry = tool["mock_response"]["results"][0]

    # Status '10' = In-Progress / Open (not approved)
    # Status '20' = Approved
    assert entry["TimeSheetStatus"] in ["10", ""], "Mock should show an open period status"
