---
name: timesheet-entry
description: |
  [WHAT] Guides the agent through the complete 5-step SAP S/4HANA timesheet entry workflow.
  [WHEN] Use when the user wants to log, record, or create a time entry, mentions WBS, hours, project time, or timesheet.
  [NOT] Do not use for reading, reporting, or querying existing timesheet data — use a reporting skill instead. Do not use to update or delete existing entries (not supported).
  Key terms: WBS, time type, hours, timesheet, S/4HANA, time entry, project time.
allowed-tools:
  - Read
metadata:
  version: 1.0.0
  tags:
    - timesheet
    - s4hana
    - time-entry
  user-context-dependent: true
  requires-rbac-scope: false
---

# Timesheet Entry Skill

## Purpose

This skill guides the agent through a strict 5-step workflow for creating a new timesheet entry in SAP S/4HANA. It ensures all inputs are collected and validated, the time period is not already approved, the user explicitly confirms the entry, and the entry is created via MCP tools only.

This skill encodes the business rules that protect data integrity: no modifications to existing entries, no changes to approved periods, and no access to any user's data other than the authenticated user.

## When to use

- User says they want to log time, record hours, create a timesheet entry, or similar
- User mentions a WBS element, project code, or time type along with hours or a date
- User asks to "add" or "submit" time for a specific date or date range

## When NOT to use

- User wants to view, report on, or query existing timesheet entries
- User wants to update or correct an existing entry (not supported — refuse politely)
- User wants to delete a time entry (not supported — refuse politely)
- User asks about approval workflows or period closings (out of scope)

---

## Instructions

### Step 1 — Collect all required inputs

Collect the following four fields conversationally. Accept them in any order. Ask one targeted follow-up question per missing field — never ask for all fields at once.

| Field | Expected format | Natural language guidance |
|-------|----------------|---------------------------|
| WBS Element | Alphanumeric code (e.g. `P-1001`, `WBS-200-A`) | Accept as-is; validate against S/4HANA in Step 2 |
| Date | ISO date YYYY-MM-DD | Accept "today", "yesterday", "last Monday" etc. and resolve to ISO format |
| Time Type | S/4HANA time type code | Accept natural language ("regular", "overtime", "on-call") and map to valid codes; if mapping is uncertain, list valid options from the MCP tool response |
| Hours | Decimal number | Must be > 0 and ≤ 24 |

**Do not proceed to Step 2 until all four fields are non-empty.**

### Step 2 — Validate all inputs

Perform the following checks using MCP tools. If any check fails, explain the problem in plain language and return to Step 1 to collect a corrected value.

| Check | How | Failure message |
|-------|-----|----------------|
| WBS exists | Call the read MCP tool and verify the WBS element appears in the result | "The WBS element [X] was not found in S/4HANA. Please check the code and try again." |
| Date is valid | Verify it is a real calendar date and not in a locked/closed period | "The date [X] is in a closed period. Please use a date in an open period." |
| Time type is valid | Confirm the mapped time type code is recognised | "The time type [X] is not recognised. Valid types are: [list from tool]." |
| Hours in range | 0 < hours ≤ 24 | "Hours must be between 0.01 and 24. Please enter a valid value." |

**Emit:** `M2.achieved: all inputs validated successfully — WBS, date, time type, hours`
**On failure:** `M2.missed: input validation failed — [field]: [reason]`

### Step 3 — Check approval status

Call the read MCP tool to retrieve timesheet entries for the authenticated user on the provided date. Check the approval/status field.

**If the period is APPROVED:**
- Respond: "This time period has already been approved and cannot be modified. Please contact your manager if a correction is needed."
- Stop. Do not proceed to Step 4.
- Emit: `M3.missed: target date period is approved — entry creation blocked`

**If the period is OPEN:**
- Proceed to Step 4.
- Emit: `M3.achieved: target date period is open and not approved`

### Step 4 — Present confirmation summary

Display the following structured summary and ask the user to confirm:

```
Please confirm the time entry details:

  WBS Element : [value]
  Date        : [value]
  Time Type   : [value]
  Hours       : [value]

Type "confirm" to submit, or tell me what you'd like to change.
```

**If the user confirms:** emit `M4.achieved: user confirmed time entry submission` and proceed to Step 5.
**If the user requests changes:** update the relevant field(s), re-validate (Step 2), and re-present this summary.
**If the user declines or abandons:** emit `M4.missed: user declined or abandoned confirmation step` and end the workflow gracefully.

### Step 5 — Create the time entry

Call the create MCP tool with the confirmed WBS element, date, time type, and hours. Always use the authenticated user's own personnel number — never accept a personnel number from user input.

**On success:**
- Confirm to the user: "Your time entry has been created successfully. [Include entry ID if returned by the API.]"
- Emit: `M5.achieved: time entry created in S/4HANA — WBS: [wbs], date: [date], hours: [hours]`

**On API error:**
- Report the exact error message from the API without modification.
- Emit: `M5.missed: time entry creation failed — API error: [error_message]`
- Offer the user the option to retry or cancel.

---

## Guardrails (enforce in every step)

- **NEVER** call any update or delete MCP tool operation under any circumstances.
- **NEVER** use any personnel number other than the authenticated user's own.
- **NEVER** proceed past Step 3 if the time period is approved.
- **NEVER** submit to S/4HANA without explicit user confirmation from Step 4.
- **NEVER** fabricate, guess, or invent data — always use MCP tools.

---

## Examples

### Example 1 — Complete happy path

**User:** "I worked 8 hours on project P-1001 today as regular time"

**Agent collects:** WBS=P-1001, Date=2026-11-15, TimeType=0100 (regular), Hours=8.0
**Agent validates:** all pass
**Agent checks approval:** period is open
**Agent confirms:** presents summary, user types "confirm"
**Agent creates:** calls create MCP tool, responds with success message

### Example 2 — Approved period

**User:** "Log 4 hours on WBS X-200 for 2026-10-01"

**Agent:** After validation, checks approval status → period is approved
**Agent responds:** "This time period has already been approved and cannot be modified. Please contact your manager if a correction is needed."
**Workflow ends.**

### Example 3 — Invalid WBS

**User:** "Log 6 hours on INVALID-WBS for today"

**Agent:** Calls read tool, WBS not found
**Agent responds:** "The WBS element INVALID-WBS was not found in S/4HANA. Please check the code and try again."
**Returns to Step 1 for correction.**

---

## Gotchas

- **Personnel number must come from authentication context** — never from user input. If the MCP tool requires a personnel number parameter, retrieve it from the authenticated session, not from what the user typed.
- **Date resolution** — always resolve natural language dates to YYYY-MM-DD before calling MCP tools. "Today" must be resolved using the current date, not hard-coded.
- **Time type mapping** — if the user says "regular" and the valid S/4HANA code is "0100", map it silently. Only ask for clarification if the mapping is genuinely ambiguous.
- **Confirmation must be explicit** — words like "yes", "ok", "looks good", "correct", "submit", or "confirm" are acceptable confirmations. Vague responses like "maybe" or "I guess" should prompt a clearer answer.
