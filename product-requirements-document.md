# Product Requirements Document (PRD)

**Title:** SAP Timesheet Update Agent
**Date:** 2026-11-15
**Owner:** Project Team
**Solution Category:** AI Agent

---

## Product Purpose & Value Proposition

**Elevator Pitch:**
Employees waste up to 2 hours every week navigating complex SAP screens to log their time. A conversational AI agent lets them record timesheet entries by simply describing what they worked on — the agent handles validation, safety checks, and submission to S/4HANA automatically.

**Business Need:**
There is no guided or conversational interface for timesheet entry in SAP S/4HANA. Employees must navigate multiple screens, look up WBS element codes, and manually select time types — a repetitive, error-prone process that consumes significant productive time each week.

**Expected Value:**
Reduce average weekly timesheet entry time per employee from 2 hours to 30 minutes within 3 months of go-live — a 75% reduction in time spent on administrative data entry.

**Product Objectives (Prioritized):**
1. Enable employees to create S/4HANA timesheet entries conversationally in under 5 minutes
2. Eliminate incorrect submissions by validating all inputs before writing to S/4HANA
3. Guarantee data integrity by enforcing a strict no-modify / no-touch-approved-time policy
4. Provide a self-service experience that requires no SAP screen navigation

---

## Business Metrics

| Metric | Baseline | Target | Timeline | Process / Capability | Source |
|--------|----------|--------|----------|----------------------|--------|
| Average weekly timesheet entry time per employee | 2 hours | 30 minutes | Within 3 months of go-live | Time Sheet Management (S/4HANA) | user |

---

## User Profiles & Personas

### Primary Persona: Alex — Project Employee

Alex is a 34-year-old project team member who works across multiple WBS elements each week. Every Friday afternoon, Alex spends up to 2 hours logging time in SAP S/4HANA, switching between a spreadsheet of WBS codes and the SAP timesheet screens. Alex knows the work done but struggles to remember the exact WBS codes and time type labels required by SAP. Alex is comfortable with chat-based tools (Teams, Slack) and would much rather say "I worked 6 hours on project X-100 today as regular time" than navigate SAP screens. Alex's main frustration is the mismatch between how naturally time is tracked mentally and how rigidly it must be entered into the system.

**Goals:**
- Log weekly timesheet entries quickly without opening SAP screens
- Avoid submission errors that require corrections later

**Key Tasks:**
- Provide WBS element, date, time type and hours to the agent conversationally
- Review and confirm the entry summary before it is submitted
- Receive clear feedback when an input is invalid so it can be corrected immediately

### Other User Types

- **IT / SAP Administrator**: Responsible for deploying and maintaining the agent; not an end-user of the timesheet function.

---

## Product Principles

1. **Conversation first**: All interactions happen in natural language. The agent collects missing inputs through follow-up questions rather than requiring the user to know the exact format upfront.
2. **Validate before you write**: No data is sent to S/4HANA until all inputs are confirmed valid and the user has explicitly approved the submission.
3. **Safety by constraint**: The agent is hard-coded to create entries only. It will never update, delete, or touch approved time — regardless of what the user asks.
4. **Self-service boundaries**: The agent operates strictly within the authenticated user's own timesheet. It cannot access or modify another person's data.
5. **Fail clearly**: When a validation fails or an API error occurs, the agent explains what went wrong in plain language and guides the user to correct it.

---

## Goals and Non-Goals

### Goals (In Scope)

- Allow employees to create new timesheet entries in SAP S/4HANA through a conversational chat interface
- Validate WBS element, date, time type and hours before submission
- Check that the target time period contains no approved entries before writing
- Present a structured confirmation summary and require explicit user approval before submitting
- Restrict all operations to the currently authenticated user's own timesheet

### Non-Goals (Out of Scope)

- Updating or deleting existing timesheet entries of any kind
- Submitting or approving timesheet periods
- Manager proxy entry (entering time on behalf of another employee)
- Reading back or reporting on existing timesheet history
- Integration with SAP SuccessFactors, CATS, or any non-S/4HANA time system
- Timesheet dashboards, analytics, or exports

---

## Requirements

### Must-Have Requirements

**R1: Conversational Time Entry Collection**

- **Problem to Solve**: Employees must navigate complex SAP screens and know exact field values to enter timesheet data, which is slow and error-prone.
- **User Story**: As an employee, I want to tell the agent what time I worked (WBS, date, time type, hours) in natural language so that I do not need to navigate SAP screens.
- **Acceptance Criteria**:
  - Given I start a conversation with the agent, when I provide all four fields (WBS, date, time type, hours), then the agent acknowledges each and proceeds to validation.
  - Given I provide incomplete information, when the agent detects missing fields, then it asks me a targeted follow-up question for each missing item.
- **Maps to Objective**: Objective 1
- **Priority Rank**: 1

**R2: Input Validation**

- **Problem to Solve**: Invalid WBS codes, dates, time types or unreasonable hours cause submission failures that employees only discover after the fact.
- **User Story**: As an employee, I want the agent to validate my inputs before submitting so that I can correct mistakes immediately.
- **Acceptance Criteria**:
  - Given I provide a WBS element, when the agent calls S/4HANA to verify it, then invalid or non-existent WBS elements are rejected with a clear explanation.
  - Given I provide a date, when the agent evaluates it, then dates in closed periods or far-future dates are flagged before submission.
  - Given I provide a time type, when the agent checks the valid values, then unrecognised time types are rejected and the agent offers valid alternatives.
  - Given I provide hours, when the agent evaluates the value, then values outside an acceptable daily range (e.g., 0–24) are rejected.
- **Maps to Objective**: Objective 2
- **Priority Rank**: 2

**R3: Approved Time Guard**

- **Problem to Solve**: Submitting a time entry against an already-approved period causes SAP errors and may violate payroll controls.
- **User Story**: As an employee, I want the agent to check whether my target date has already been approved so that I never accidentally attempt to modify approved time.
- **Acceptance Criteria**:
  - Given the user provides a date, when the agent reads the timesheet status for that date via the API, then if the period is approved the agent informs the user and refuses to proceed.
  - Given the period is not approved, when the check passes, then the agent continues to the confirmation step.
- **Maps to Objective**: Objective 3
- **Priority Rank**: 3

**R4: Confirmation Gate**

- **Problem to Solve**: Accidental or incorrect submissions are difficult to reverse once written to S/4HANA.
- **User Story**: As an employee, I want to review a structured summary of my entry and explicitly confirm it before it is submitted so that I can catch and correct any errors.
- **Acceptance Criteria**:
  - Given all inputs are valid and the period is not approved, when the agent is ready to submit, then it presents a summary showing WBS, date, time type and hours and asks for confirmation.
  - Given the user confirms, when the agent receives confirmation, then it proceeds to create the entry in S/4HANA.
  - Given the user does not confirm or requests a change, when the agent receives that response, then it allows the user to correct any field and re-presents the summary.
- **Maps to Objective**: Objectives 1 & 2
- **Priority Rank**: 4

**R5: Self-Service Boundary**

- **Problem to Solve**: An agent that can access other users' timesheets poses a data privacy and compliance risk.
- **User Story**: As an employee, I want the agent to only ever act on my own timesheet so that my colleagues' data is never accessible or affected.
- **Acceptance Criteria**:
  - Given the agent is authenticated, when it calls the Workforce Timesheet API, then it always uses the authenticated user's own personnel number — never an externally supplied one.
  - Given any attempt to supply another user's ID, when the agent processes the request, then it rejects the operation and explains the self-service constraint.
- **Maps to Objective**: Objective 3
- **Priority Rank**: 5

**R6: Create-Only Constraint**

- **Problem to Solve**: Allowing updates or deletions risks corrupting historical timesheet data and payroll integrity.
- **User Story**: As an employee, I want the agent to be limited to creating new entries only so that existing or approved records are never accidentally changed.
- **Acceptance Criteria**:
  - Given any user request to update or delete a time entry, when the agent interprets the intent, then it refuses and explains that only new entries can be created.
  - Given a confirmed new entry, when the agent submits to S/4HANA, then it uses only the Create operation of the Workforce Timesheet API.
- **Maps to Objective**: Objective 3
- **Priority Rank**: 6

---

## Solution Architecture

**Architecture Overview:**
A Python AI agent (A2A protocol) is deployed as a browser-based chat service. It connects to SAP S/4HANA through a generated MCP server that exposes the Workforce Timesheet OData API operations as structured tools. The agent uses these tools to read timesheet status and create new entries, while all business logic (validation, approval check, confirmation gate, guardrails) is handled within the agent itself.

**Key Components:**

- **Python AI Agent (A2A)**: Conversational engine that collects inputs, enforces business rules, and orchestrates tool calls. Deployed as a browser-accessible chat interface.
- **MCP Server (generated)**: Translates the Workforce Timesheet OData API (`API_MANAGE_WORKFORCE_TIMESHEET:v1`) into structured MCP tools consumable by the agent. Exposes read (status/approval check) and create (time entry) operations only.
- **SAP S/4HANA — Workforce Timesheet OData API**: The system of record. All time entry data is read from and written to this API.

**Integration Points:**

- S/4HANA Workforce Timesheet API (`sap.s4:apiResource:API_MANAGE_WORKFORCE_TIMESHEET:v1`): bidirectional — read for approval status check, write for entry creation. Real-time, per-user request.

**Deployment Environments:**

- Dev: Isolated environment with test S/4HANA tenant; no production data.
- Production: Live S/4HANA system; authenticated user context enforced at all times.

### Agent Extensibility & Instrumentation

**Agent Extensibility:**
The agent is designed with extension points to support future capabilities without requiring a rewrite:
- A skill/tool registration mechanism allows new MCP tools to be added (e.g., read existing entries, submit timesheet periods) without modifying core agent logic.
- The system prompt is parameterised so guardrails and behaviour can be adjusted per deployment configuration.
- The confirmation gate is implemented as a reusable step that can be applied to future write operations.

**Business Step Instrumentation:**
All five key business milestones must emit structured log statements to enable production observability and debugging. Log pattern: `[MILESTONE_ID].[achieved|missed]: [description]`. See the Milestones section for full definitions.

### Automation & Agent Behaviour

**Automation Level:** Autonomous agent with mandatory human confirmation gate before write operations.

**Actions the system performs without human approval:**
- Collecting and parsing user-provided inputs
- Validating WBS element against S/4HANA
- Checking approval status of the target date
- Formatting and presenting the confirmation summary

**Actions that require human review or approval:**
- Creating a time entry in S/4HANA (always requires explicit user confirmation)

**Model or engine used:** Large language model via SAP Generative AI Hub

**Knowledge & data sources accessed:**
- SAP S/4HANA Workforce Timesheet API: timesheet entry status (read), time entry creation (write)

**Tools or connectors invoked:**
- `read_timesheet_entries` (MCP tool, read-only): reads existing timesheet records to check approval status for a given date and personnel number
- `create_timesheet_entry` (MCP tool, write): creates a new timesheet entry in S/4HANA with the provided WBS, date, time type and hours

**Guardrails & fail-safes:**
- The agent must never call any update or delete operation on the Workforce Timesheet API under any circumstances.
- If the target date's timesheet period is approved, the agent must refuse and inform the user — no exception.
- All API calls must use the authenticated user's own personnel number; externally supplied personnel numbers must be rejected.
- If the Workforce Timesheet API returns an error, the agent must surface a plain-language explanation and allow the user to correct inputs.
- If confidence in parsing the user's intent is low, the agent must ask a clarifying question rather than guessing.

---

## Milestones

### M1: Time Entry Initiated

- **Description**: The user has provided all four required fields — WBS element, date, time type, and hours — conversationally.
- **Achieved when**: All four fields have been captured and are non-empty.
- **Log on achievement**: `M1.achieved: all required time entry fields collected from user`
- **Log on miss**: `M1.missed: user session ended before all required fields were provided`

### M2: Inputs Validated

- **Description**: All four inputs have been checked against S/4HANA — WBS exists, date is in an open period, time type is valid, and hours are within range.
- **Achieved when**: All validation checks pass with no errors returned.
- **Log on achievement**: `M2.achieved: all inputs validated successfully — WBS, date, time type, hours`
- **Log on miss**: `M2.missed: input validation failed — [field]: [reason]`

### M3: Approval Status Checked

- **Description**: The agent has queried S/4HANA to confirm the target date's timesheet period is not approved.
- **Achieved when**: The API confirms the period is open and not approved.
- **Log on achievement**: `M3.achieved: target date period is open and not approved`
- **Log on miss**: `M3.missed: target date period is approved — entry creation blocked`

### M4: Confirmation Presented

- **Description**: The agent has presented a structured summary of the planned entry and is awaiting explicit user confirmation.
- **Achieved when**: The confirmation summary has been displayed and the user has responded.
- **Log on achievement**: `M4.achieved: user confirmed time entry submission`
- **Log on miss**: `M4.missed: user declined or abandoned confirmation step`

### M5: Entry Created in S/4HANA

- **Description**: The time entry has been successfully written to S/4HANA via the Workforce Timesheet API.
- **Achieved when**: The API returns a success response for the create operation.
- **Log on achievement**: `M5.achieved: time entry created in S/4HANA — WBS: [wbs], date: [date], hours: [hours]`
- **Log on miss**: `M5.missed: time entry creation failed — API error: [error_message]`

---

## Risks, Assumptions, and Dependencies

### Risks

- **WBS validation accuracy**: If the user provides a partially correct WBS code, the API may return an ambiguous result. The agent must handle this gracefully and prompt the user to provide the full, exact code.
- **Time type vocabulary mismatch**: Users may use informal terms (e.g., "overtime", "regular") that do not map directly to S/4HANA time type codes. The agent must maintain or dynamically retrieve a mapping from natural language to valid codes.
- **API availability**: If the S/4HANA Workforce Timesheet API is unavailable, the agent must inform the user clearly and avoid retrying silently.

### Assumptions (Validate These)

- The Workforce Timesheet OData API (`API_MANAGE_WORKFORCE_TIMESHEET:v1`) supports both read (status check) and create operations with principal propagation for the authenticated user.
- The S/4HANA system exposes the API with sufficient permissions for standard employee self-service use.
- WBS elements used by employees are active and accessible via the API.
- The deployment environment supports browser-based access to the agent chat interface.

### Dependencies

- SAP S/4HANA system with the Workforce Timesheet OData API enabled and accessible
- SAP Generative AI Hub for the LLM model endpoint
- MCP server generated from the `API_MANAGE_WORKFORCE_TIMESHEET:v1` API specification

---

## Appendix

### Glossary

- **WBS Element**: Work Breakdown Structure element — a project code used in S/4HANA to categorise and track time and costs against specific project tasks.
- **Time Type**: A classification code in S/4HANA that describes the nature of the hours worked (e.g., regular time, overtime, on-call).
- **Approved Time**: A timesheet period that has been reviewed and approved in S/4HANA. Once approved, entries cannot be modified without an explicit correction workflow.
- **A2A Protocol**: Agent-to-Agent protocol — the communication standard used by the Python agent to expose its capabilities as a service.
- **MCP Server**: Model Context Protocol server — a generated adapter that translates an OData or REST API into structured tools consumable by an AI agent.

### References

- SAP Workforce Timesheet OData API: `sap.s4:apiResource:API_MANAGE_WORKFORCE_TIMESHEET:v1`
- SAP Reference Business Architecture: Recruit to Retire → Manage time and attendance (BPS-393)
