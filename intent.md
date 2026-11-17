# SAP Timesheet Update Agent

Conversational AI agent that allows employees to create time entries in SAP S/4HANA by providing WBS, date, time type, and hours — through a browser-based chat interface, without ever modifying approved time.

## Business challenge

Employees spend an average of 2 hours per week manually entering timesheet data in SAP S/4HANA. The process is tedious and error-prone. A conversational AI agent should allow users to record time entries naturally through chat, automatically creating entries in S/4HANA while enforcing the rule that approved time is never modified.

## Business Goals & Success Criteria

| Metric | Baseline | Target | Timeline | Process / Capability | Source |
|--------|----------|--------|----------|----------------------|--------|
| Average weekly timesheet entry time per employee | 2 hours | 30 minutes | Within 3 months of go-live | Time Sheet Management (S/4HANA) | user |

## Key Milestones

1. **Time entry initiated** — User opens the agent and provides WBS, date, time type and hours conversationally
2. **Inputs validated** — Agent validates all required fields (WBS exists, date is valid, time type is recognised, hours are within reasonable range)
3. **Approval status checked** — Agent confirms the target time period has no approved entries that would be affected
4. **Confirmation presented** — Agent presents a structured summary of the entry for user review
5. **Entry created in S/4HANA** — Upon user confirmation, agent creates the time entry via the Workforce Timesheet API

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
| Check approval status of time entries before update | Workforce Timesheet OData API | `sap.s4:apiResource:API_MANAGE_WORKFORCE_TIMESHEET:v1` | — | — | — | — | No | Read operation on same API |
| Conversational chat interface for time entry | — | — | — | — | — | — | Yes | Custom Python AI agent required |
| Self-service — only logged-in user's own time | Principal propagation via S/4HANA API | `sap.s4:apiResource:API_MANAGE_WORKFORCE_TIMESHEET:v1` | — | — | — | — | No | Agent uses authenticated user context |

### Key findings

- The **Workforce Timesheet OData API** (`API_MANAGE_WORKFORCE_TIMESHEET:v1`) is available in the customer's landscape and covers both read (approval status check) and write (time entry creation) operations.
- No pre-built MCP server exists for this API — one will be generated as part of the solution build.
- Several related APIs (CATS Upload, Time Entry OData, Time Report OData) are marked **unavailable** in this landscape and will not be used.
- SAP Fieldglass and SuccessFactors capabilities are out of scope — this is an internal workforce, S/4HANA-only scenario.
- The conversational interface is the primary gap, covered by a custom Python AI agent (A2A protocol).
- The agent will strictly enforce a guard: approved time entries must never be modified or deleted.

## Recommendations

### Conversational Timesheet Agent on SAP S/4HANA

#### Executive Summary

Python AI agent with S/4HANA Workforce Timesheet API via generated MCP server.

#### Recommended Solution

A pro-code Python AI agent (A2A protocol) deployed as a browser-based chat interface. The agent collects WBS, date, time type, and hours from the user conversationally, validates inputs, checks approval status, presents a confirmation summary, and — upon user approval — creates the time entry in SAP S/4HANA using the Workforce Timesheet OData API. An MCP server will be generated from the API specification to expose the relevant operations as tools to the agent.

#### Problem Statement

Employees spend an average of 2 hours per week navigating SAP S/4HANA screens to enter timesheet data. The manual process is repetitive, error-prone, and disengaging. There is no conversational or guided interface to simplify the task.

#### Affected User Roles

- Employees (all staff who record time against WBS elements in S/4HANA)

#### Important factors

##### Simplicity through conversation
The agent removes the need to navigate complex SAP screens. Users simply state what they want to log and the agent handles the rest.

##### Safety by design
The agent is explicitly constrained to creating new time entries only. It will never update or delete existing entries, and it will refuse any operation on approved time periods.

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
