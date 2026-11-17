---
name: timesheet-entry
description: |
  [WHAT] Guides the agent through the complete SAP S/4HANA timesheet entry workflow for both creating new entries and updating existing unapproved entries.
  [WHEN] Use when the user wants to log, record, create, update, correct, or change a time entry, mentions WBS, hours, project time, or timesheet.
  [NOT] Do not use for reading, reporting, or querying existing timesheet data — use a reporting skill instead. Do not use to delete entries (not supported). Do not use to modify approved entries (not allowed).
  Key terms: WBS, time type, hours, timesheet, S/4HANA, time entry, project time, update, correct, change.
allowed-tools:
  - Read
metadata:
  version: 1.1.0
  tags:
    - timesheet
    - s4hana
    - time-entry
    - update
  user-context-dependent: true
  requires-rbac-scope: false
---

# Timesheet Entry Skill

## Purpose

This skill guides the agent through two workflows:

1. **Create** — a new timesheet entry in SAP S/4HANA
2. **Update** — an existing unapproved timesheet entry in SAP S/4HANA

Both workflows enforce the same safety rules: no approved time is ever touched, no deletions are ever performed, the authenticated user's own personnel number is always used, and the user must explicitly confirm before any write.

## When to use

- User says they want to log, record, add, or create a time entry
- User says they want to update, correct, change, or fix an existing time entry
- User mentions a WBS element, project code, or time type along with hours or a date
- User says something like "I made a mistake on my timesheet for Monday" or "I need to correct last week's hours"

## When NOT to use

- User wants to view, report on, or query existing timesheet entries (no write intent)
- User wants to delete a time entry (not supported — refuse politely)
- User wants to modify an approved entry (not allowed — refuse and explain)
- User asks about approval workflows or period closings (out of scope)

---

## Instructions

### Determine Operation Type

Before collecting inputs, identify whether the user wants to **create** a new entry or **update** an existing one.

| Signal | Operation |
|--------|-----------|
| "Log time", "record hours", "I worked...", "add an entry" | CREATE |
| "Update", "correct", "change", "fix", "I made a mistake on..." | UPDATE |
| Ambiguous | Ask: "Do you want to log a new time entry, or update an existing one?" |

Proceed to the matching workflow below.

---

## Workflow A — Create New Entry

### Step A1 — Collect all required inputs

Collect the following four fields conversationally. Accept them in any order. Ask one targeted follow-up question per missing field.

| Field | Expected format | Guidance |
|-------|----------------|----------|
| WBS Element | Alphanumeric code (e.g. `P-1001`) | Accept as-is; validate in Step A2 |
| Date | ISO date YYYY-MM-DD | Accept "today", "yesterday", "last Monday" etc. and resolve to ISO format |
| Time Type | S/4HANA time type code | Accept natural language ("regular", "overtime") and map to valid codes |
| Hours | Decimal number | Must be > 0 and ≤ 24 |

Do not proceed until all four fields are non-empty.

### Step A2 — Validate inputs

| Check | Failure message |
|-------|----------------|
| WBS exists | "The WBS element [X] was not found in S/4HANA. Please check the code and try again." |
| Date is valid and in an open period | "The date [X] is in a closed period. Please use a date in an open period." |
| Time type is recognised | "The time type [X] is not recognised. Valid types are: [list]." |
| Hours in range (0.01–24) | "Hours must be between 0.01 and 24. Please enter a valid value." |

**Emit:** `M2.achieved: all inputs validated successfully — WBS, date, time type, hours`
**On failure:** `M2.missed: input validation failed — [field]: [reason]`

### Step A3 — Check approval status

Call the list MCP tool to retrieve timesheet entries for the authenticated user on the provided date. Check the approval/status field.

- **If APPROVED:** respond with "This time period has already been approved and cannot be modified." Stop. Emit: `M3.missed: target entry/period is approved — write operation blocked`
- **If OPEN:** proceed. Emit: `M3.achieved: target entry/period is open and not approved`

### Step A4 — Present confirmation summary

```
Please confirm the new time entry:

  WBS Element : [value]
  Date        : [value]
  Time Type   : [value]
  Hours       : [value]

Type "confirm" to submit, or tell me what you'd like to change.
```

**If confirmed:** emit `M4.achieved: user confirmed time entry submission` and proceed to A5.
**If changes requested:** update the field(s), re-validate, re-present.
**If declined:** emit `M4.missed: user declined or abandoned confirmation step` and end.

### Step A5 — Create the entry

Call the create MCP tool with `TimeSheetOperation='C'` and the confirmed values. Always use the authenticated user's own personnel number.

**On success:** confirm to the user and emit `M5.achieved: time entry created in S/4HANA — WBS: [wbs], date: [date], hours: [hours]`
**On error:** report the exact API error and emit `M5.missed: time entry creation failed — API error: [error_message]`

---

## Workflow B — Update Existing Entry

### Step B1 — Identify the entry to update

Ask the user which entry they want to change. Minimum: a date. Optionally: WBS element or record ID.

Call the list MCP tool filtered by the user's date (and WBS if provided) to retrieve matching entries for the authenticated user. Present a brief list if multiple entries are found and ask the user to identify which one.

### Step B2 — Collect the changes

Ask the user what they want to change. They may change one or more of: WBS element, time type, hours, date.

Show the current values and ask for new values only for the fields they want to change. Keep unchanged fields from the existing entry.

### Step B3 — Validate new inputs

Apply the same validation rules as Step A2, but only for the fields being changed.

**Emit:** `M2.achieved: all inputs validated successfully — WBS, date, time type, hours`
**On failure:** `M2.missed: input validation failed — [field]: [reason]`

### Step B4 — Check approval status

Check the existing entry's approval status from the data retrieved in Step B1.

- **If APPROVED:** respond with "This time entry has already been approved and cannot be changed." Stop. Emit: `M3.missed: target entry/period is approved — write operation blocked`
- **If OPEN:** proceed. Emit: `M3.achieved: target entry/period is open and not approved`

### Step B5 — Present before/after confirmation summary

```
Please confirm the update:

  Field       : Before         → After
  ─────────────────────────────────────
  WBS Element : [current]      → [new or unchanged]
  Date        : [current]      → [new or unchanged]
  Time Type   : [current]      → [new or unchanged]
  Hours       : [current]      → [new or unchanged]

Type "confirm" to submit, or tell me what you'd like to change.
```

**If confirmed:** emit `M4.achieved: user confirmed time entry submission` and proceed to B6.
**If changes requested:** update the field(s), re-validate, re-present.
**If declined:** emit `M4.missed: user declined or abandoned confirmation step` and end.

### Step B6 — Update the entry

Call the create MCP tool with `TimeSheetOperation='U'`, the existing entry's record key fields, and the updated field values. Always use the authenticated user's own personnel number.

**On success:** confirm to the user and emit `M5.achieved: time entry updated in S/4HANA — WBS: [wbs], date: [date], hours: [hours]`
**On error:** report the exact API error and emit `M5.missed: time entry update failed — API error: [error_message]`

---

## Guardrails (enforce in every step)

- **NEVER** call any delete MCP tool operation under any circumstances.
- **NEVER** use any personnel number other than the authenticated user's own.
- **NEVER** proceed past the approval check if the entry or period is approved.
- **NEVER** submit to S/4HANA without explicit user confirmation.
- **NEVER** fabricate, guess, or invent data — always use MCP tools.
- If the user asks to delete an entry, refuse and explain that deletion is not supported.

---

## Examples

### Example 1 — Create happy path

**User:** "I worked 8 hours on project P-1001 today as regular time"
**Agent:** collects all fields → validates → checks approval (open) → confirms → creates entry

### Example 2 — Update happy path

**User:** "I made a mistake — I logged 6 hours on P-1001 for yesterday but it should be 8"
**Agent:** retrieves entry for yesterday on P-1001 → shows current values → collects change (hours: 8) → validates → checks approval (open) → shows before/after → user confirms → updates with TimeSheetOperation='U'

### Example 3 — Approved entry update attempt

**User:** "Can you update my entry for last month?"
**Agent:** retrieves entry → checks approval → approved → "This time entry has already been approved and cannot be changed. Please contact your manager if a correction is needed."

### Example 4 — Delete attempt

**User:** "Delete my time entry for Monday"
**Agent:** "I'm sorry, deletion of time entries is not supported. I can update the entry instead — would you like to change it to 0 hours or correct any field?"

---

## Gotchas

- **TimeSheetOperation field**: Create uses `'C'`, Update uses `'U'`. Never use `'D'` (Delete).
- **Personnel number must come from authentication** — never from user input.
- **Date resolution** — always resolve natural language dates to YYYY-MM-DD before calling MCP tools.
- **Update requires the record key** — when calling the update operation, include `PersonWorkAgreementExternalID`, `CompanyCode`, and `TimeSheetRecord` from the existing entry retrieved in Step B1.
- **Confirmation for updates** — always show both before and after values so the user can catch unintended changes.
