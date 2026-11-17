# SAP Timesheet Update Agent

Conversational AI agent that allows employees to create new time entries and update existing unapproved time entries in SAP S/4HANA by providing WBS, date, time type, and hours — through a browser-based chat interface, without ever modifying approved time.

## Business challenge

Employees spend an average of 2 hours per week manually entering and correcting timesheet data in SAP S/4HANA. The process is tedious and error-prone. A conversational AI agent should allow users to record new time entries and update existing unapproved entries naturally through chat, automatically writing to S/4HANA while enforcing the rule that approved time is never modified.

## Business Goals & Success Criteria

| Metric | Baseline | Target | Timeline | Process / Capability | Source |
|--------|----------|--------|----------|----------------------|--------|
| Average weekly timesheet entry time per employee | 2 hours | 30 minutes | Within 3 months of go-live | Time Sheet Management (S/4HANA) | user |

## Key Milestones

1. **Operation identified** — User expresses intent to create a new entry or update an existing unapproved entry; agent determines the operation type
2. **Inputs collected & validated** — Agent collects WBS, date, time type and hours (for create) or retrieves the existing entry and collects the fields to change (for update); validates all fields
3. **Approval status checked** — Agent confirms the target time entry/period is not approved before proceeding with any write operation
4. **Confirmation presented** — Agent presents a structured summary of the planned create or update for user review
5. **Entry written to S/4HANA** — Upon user confirmation, agent creates or updates the time entry via the Workforce Timesheet API

## Business Architecture (RBA)

### End-to-End Process

Recruit to Retire

### Process Hierarchy

```
Recruit to Retire
└── Manage Workforce (generic)
    └── Manage time and attendance (BPS-393)
        └── Record activities (BA-2722)
```

### Summary

Updating an employee timesheet with WBS, date, time type, and hours maps to the "Record activities" business activity within the "Manage time and attendance" sub-process of the Recruit to Retire end-to-end process.

## Fit Gap Analysis

| Requirement (business) | Standard asset(s) found | API ORD ID | MCP Server ORD ID | MCP Server Version | Webhook API ORD ID | Data Product ORD ID | Gap? | Notes / assumptions |
|------------------------|------------------------|------------|-------------------|--------------------|--------------------|---------------------|------|---------------------|
| Create time entries (WBS, date, time type, hours) in S/4HANA | Workforce Timesheet OData API | `sap.s4:apiResource:API_MANAGE_WORKFORCE_TIMESHEET:v1` | — | — | — | — | No | MCP server must be generated from API spec |
| Update existing unapproved time entries in S/4HANA | Workforce Timesheet OData API | `sap.s4:apiResource:API_MANAGE_WORKFORCE_TIMESHEET:v1` | — | — | — | — | No | Update operation on same API; TimeSheetOperation='U' |
| Check approval status of time entries before any write | Workforce Timesheet OData API | `sap.s4:apiResource:API_MANAGE_WORKFORCE_TIMESHEET:v1` | — | — | — | — | No | Read operation on same API |
| Conversational chat interface for time entry | — | — | — | — | — | — | Yes | Custom Python AI agent required |
| Self-service — only logged-in user's own time | Principal propagation via S/4HANA API | `sap.s4:apiResource:API_MANAGE_WORKFORCE_TIMESHEET:v1` | — | — | — | — | No | Agent uses authenticated user context |

### Key findings

- The **Workforce Timesheet OData API** (`API_MANAGE_WORKFORCE_TIMESHEET:v1`) is available in the customer's landscape and covers read, create (`TimeSheetOperation='C'`), and update (`TimeSheetOperation='U'`) operations via the same POST endpoint.
- The existing MCP server asset (`sap-s4-manage-workforce-timesheet-mcp-server`) already exposes the required tools; the update operation uses `create_timesheet_entry` with `TimeSheetOperation='U'`.
- Several related APIs (CATS Upload, Time Entry OData, Time Report OData) are marked **unavailable** in this landscape and will not be used.
- SAP Fieldglass and SuccessFactors capabilities are out of scope — this is an internal workforce, S/4HANA-only scenario.
- The conversational interface gap is covered by the existing custom Python AI agent (A2A protocol).
- The agent enforces the guard: approved time entries must never be modified or deleted.

## Recommendations

### Conversational Timesheet Agent on SAP S/4HANA

#### Executive Summary

Python AI agent supporting create and update of unapproved time entries via S/4HANA Workforce Timesheet API.

#### Recommended Solution

A pro-code Python AI agent (A2A protocol) deployed as a browser-based chat interface. The agent supports two operations: (1) creating new time entries by collecting WBS, date, time type, and hours conversationally; and (2) updating existing unapproved time entries by first retrieving the entry, then collecting the fields the user wants to change. In both cases the agent validates inputs, checks that the target period is not approved, presents a confirmation summary, and — upon user approval — writes to SAP S/4HANA using the Workforce Timesheet OData API. The existing MCP server is extended to include an update tool. Approved time is never modified under any circumstances.

#### Problem Statement

Employees spend an average of 2 hours per week navigating SAP S/4HANA screens to enter timesheet data. The manual process is repetitive, error-prone, and disengaging. There is no conversational or guided interface to simplify the task.

#### Affected User Roles

- Employees (all staff who record time against WBS elements in S/4HANA)

#### Important factors

##### Simplicity through conversation
The agent removes the need to navigate complex SAP screens. Users simply state what they want to log and the agent handles the rest.

##### Safety by design
The agent is constrained to creating new entries and updating existing unapproved entries only. It will never delete entries, and it will refuse any write operation on approved time periods.

##### Confirmation gate
The agent always presents a structured summary before writing to S/4HANA, giving users a clear opportunity to review and correct inputs.

#### Potential risks

##### WBS validation accuracy
If the user provides an incomplete or incorrect WBS element, the agent must handle API errors gracefully and guide the user to correct the input.

##### Time type vocabulary
Users may use informal names for time types. The agent must map natural language descriptions to valid S/4HANA time type codes.

#### Recommended solution category

AI Agent

#### Intent fit
95%
