# Specification: timesheet-update-agent

> **Guidelines**: Read all applicable guidelines before executing ANY tasks below:
> - [guidelines.md](../guidelines.md) — Universal execution rules
> - [guidelines-agent.md](../guidelines-agent.md) — Universal agent patterns
> - [guidelines-agent-python.md](../guidelines-agent-python.md) — Python implementation details
> - [guidelines-agent-skills.md](../guidelines-agent-skills.md) — Runtime skills patterns
> - [guidelines-agent-mcp.md](../guidelines-agent-mcp.md) — MCP integration patterns

---

## Basic Setup

- [x] Read `product-requirements-document.md` and `intent.md` at the solution root for full context
- [x] Bootstrap agent code in `assets/timesheet-update-agent/` using instructions from the `sap-agent-bootstrap` section (invoke from inside `assets/timesheet-update-agent/`, use copy commands — do NOT create files manually)
- [x] Install dependencies, validate the agent starts and responds at `/.well-known/agent.json`

---

## Runtime Skills

- [x] Create a runtime skill `assets/timesheet-update-agent/app/skills/timesheet-entry/SKILL.md` with the following:
  - **Purpose**: Guide the agent through the exact 5-step timesheet entry workflow
  - **Step 1 — Collect inputs**: Accept WBS element, date, time type and hours from the user in any order. Ask targeted follow-up questions for any missing field. Accept natural language for time type (e.g. "regular", "overtime") and resolve to the valid S/4HANA code.
  - **Step 2 — Validate inputs**: Call the MCP tool to verify the WBS element exists. Check that the date is a valid calendar date and in an open (non-past-closed) period. Confirm hours are a positive number ≤ 24. If any check fails, explain what is wrong and ask the user to correct it before proceeding.
  - **Step 3 — Check approval status**: Call the MCP tool to read timesheet entries for the authenticated user on the provided date. If the period is approved, refuse to proceed and explain the restriction clearly. Only continue if the period is open.
  - **Step 4 — Present confirmation summary**: Display a structured summary:
    - WBS Element: `<value>`
    - Date: `<value>`
    - Time Type: `<value>`
    - Hours: `<value>`
    Ask the user to confirm or correct any field. Do not proceed until the user explicitly confirms.
  - **Step 5 — Create time entry**: Call the MCP tool to create the time entry in S/4HANA with the confirmed values. Report success (including the created entry ID if returned) or surface the exact API error message if the call fails.
  - **Guardrails (enforce in every step)**:
    - NEVER call any update or delete operation
    - NEVER use any personnel number other than the authenticated user's own
    - NEVER proceed past Step 3 if the period is approved
    - NEVER submit without explicit user confirmation from Step 4

---

## Project-Specific Tasks

### Conversational Time Entry Collection (R1)

- [x] Implement system prompt in `app/agent.py` that instructs the agent to:
  - Greet the user and explain it can help log time entries in S/4HANA
  - Collect WBS element, date, time type and hours conversationally (any order)
  - Ask one targeted follow-up question per missing field — never ask for all fields at once
  - Accept natural language for dates (e.g. "yesterday", "last Monday") and resolve to ISO format (YYYY-MM-DD)
  - Accept natural language time type descriptions and resolve to valid S/4HANA time type codes
  - NEVER fabricate, guess, or invent data — always use MCP tools to retrieve live data
  - Set page size parameter to a maximum of 100 on every tool call that accepts it
  - Relay tool errors verbatim without embellishment

### Input Validation (R2)

- [x] Instruct the agent to validate all four fields before proceeding to Step 3:
  - WBS element: call `read_timesheet`-type MCP tool (or equivalent) to confirm WBS exists in S/4HANA
  - Date: validate format and that the date is not in a locked/closed period
  - Time type: confirm the value is a recognised S/4HANA time type code (or map from natural language)
  - Hours: confirm value is a positive number between 0.01 and 24.00
- [x] Add error-handling instructions: if any validation fails, surface a plain-language explanation and prompt the user to correct the specific field before continuing

### Approved Time Guard (R3)

- [x] Implement a check in the agent workflow: before presenting the confirmation summary, call the MCP read tool to retrieve timesheet status for the user's date
- [x] Instruct the agent: if the API indicates the period is approved, respond with a clear refusal message (e.g. "This time period has already been approved and cannot be modified. Please contact your manager if a correction is needed.") and stop the workflow
- [x] Log milestone M3 based on the outcome (achieved / missed)

### Confirmation Gate (R4)

- [x] Implement the confirmation summary display as described in the runtime skill Step 4
- [x] Instruct the agent to wait for explicit user confirmation before calling the create MCP tool
- [x] If the user requests changes, allow editing of any field and re-present the full summary
- [x] Log milestone M4 based on the outcome (achieved / missed)

### Self-Service Boundary (R5)

- [x] Add a system prompt guardrail: the agent must always use the authenticated user's own personnel number when calling any MCP tool — never accept a personnel number from user input
- [x] Add a system prompt instruction: if the user attempts to log time for another person, respond that only self-service is supported and refuse the operation

### Create-Only Constraint (R6)

- [x] Add a system prompt guardrail: the agent is permitted to call ONLY read (list/get) and create MCP tools from the Workforce Timesheet MCP server — NEVER update or delete tools
- [x] If the user asks to update or delete an existing entry, the agent must refuse and explain the constraint
- [x] Log milestone M5 on success or miss

---

## Business Instrumentation

- [x] Implement structured logging and OpenTelemetry spans for all five PRD milestones:

  | ID | Name | Achieved log | Missed log |
  |----|------|--------------|------------|
  | M1 | Time entry initiated | `M1.achieved: all required time entry fields collected from user` | `M1.missed: user session ended before all required fields were provided` |
  | M2 | Inputs validated | `M2.achieved: all inputs validated successfully — WBS, date, time type, hours` | `M2.missed: input validation failed — [field]: [reason]` |
  | M3 | Approval status checked | `M3.achieved: target date period is open and not approved` | `M3.missed: target date period is approved — entry creation blocked` |
  | M4 | Confirmation presented | `M4.achieved: user confirmed time entry submission` | `M4.missed: user declined or abandoned confirmation step` |
  | M5 | Entry created in S/4HANA | `M5.achieved: time entry created in S/4HANA — WBS: [wbs], date: [date], hours: [hours]` | `M5.missed: time entry creation failed — API error: [error_message]` |

- [x] Extract all business logic from `stream()` into a plain async helper (e.g. `_run_agent()`) to avoid `GeneratorExit` span context errors — instrument `_run_agent()` with `with tracer.start_as_current_span(...)` blocks
- [x] Verify `bootstrap(app)` is called after `app = server.build()` in `main.py`

---

## MCP Tool Integration

> Read [guidelines-agent-mcp.md](../guidelines-agent-mcp.md) for complete MCP integration patterns.

- [x] Invoke `mcp-translation-file` skill using the downloaded API spec at `specification/timesheet-update-agent/api-specs/API_MANAGE_WORKFORCE_TIMESHEET.edmx`
  - API ORD ID: `sap.s4:apiResource:API_MANAGE_WORKFORCE_TIMESHEET:v1`
  - API type: `edmx`
  - MCP tool scope: `read-write`
  - Resources in scope: `TimeSheetEntry` (read to check approval status; create for new entries)
- [x] After `mcp-translation-file` completes, invoke `setup-solution` skill to register the MCP server asset
- [x] Read the generated `asset.yaml` for the MCP server and copy the exact `ordId` value
- [x] Wire MCP tool loading in `agent.py` using `get_mcp_tools()` from the `mcp_tools` module — NEVER import directly from `sap_cloud_sdk.agentgateway`
- [x] Add the generated MCP server to `asset.yaml` under `requires`:
  ```yaml
  requires:
    - name: workforce-timesheet-mcp-server
      kind: mcp-server
      ordId: <exact ordId from generated asset.yaml>
  ```
- [x] Generate `mcp-mock.json` using the `mcp-mock-config` skill after MCP translation completes

```
MCP API: sap.s4:apiResource:API_MANAGE_WORKFORCE_TIMESHEET:v1
MCP tool scope: read-write
Resources in scope: TimeSheetEntry
```

---

## Testing

> See [guidelines-agent-python.md](../guidelines-agent-python.md) for Python testing setup and patterns.

- [x] `conftest.py` sets only `IBD_TESTING=true` — this causes the agent to run with mock MCP tool results during tests
- [x] Write unit tests in `assets/timesheet-update-agent/tests/` — one test per MCP tool used:
  - `test_read_timesheet_entry.py` — test the read/query tool (approval status check scenarios: open period, approved period)
  - `test_create_timesheet_entry.py` — test the create tool (success, API error, validation failure)
- [x] Write one integration test `test_agent_end_to_end.py` exercising the full 5-step flow with mocked LLM responses and mocked MCP tools (must run fully offline)
- [x] Run `pytest` from `assets/timesheet-update-agent/` (no args) — if coverage < 70%, add tests until threshold is met
- [x] Run `pytest` again from `assets/timesheet-update-agent/` (no args) to generate final `test_report.json`
- [x] Verify `test_report.json` exists in `assets/timesheet-update-agent/`
