---
name: sentry
display_name: "Sentry"
description: "Monitor and manage application errors in Sentry — list issues, view stack traces, resolve, and assign"
category: monitoring
icon: bug
skill_type: sandbox
catalog_type: platform
requirements: "httpx>=0.25"
resource_requirements:
  - env_var: SENTRY_AUTH_TOKEN
    name: "Sentry Auth Token"
    description: "Organization auth token from Sentry (Settings > Auth Tokens)"
  - env_var: SENTRY_ORG
    name: "Sentry Organization"
    description: "Sentry organization slug"
  - env_var: SENTRY_PROJECT
    name: "Sentry Project"
    description: "Sentry project slug"
tool_schema:
  name: sentry
  description: "Monitor and manage application errors in Sentry — list issues, view stack traces, resolve, and assign"
  parameters:
    type: object
    properties:
      action:
        type: "string"
        description: "Which operation to perform"
        enum: ['list_issues', 'get_issue', 'get_latest_event', 'resolve_issue', 'unresolve_issue', 'assign_issue', 'list_projects']
      issue_id:
        type: "string"
        description: "Sentry issue ID — for get_issue, get_latest_event, resolve_issue, unresolve_issue, assign_issue"
        default: ""
      query:
        type: "string"
        description: "Search query — for list_issues (e.g. 'is:unresolved level:error')"
        default: "is:unresolved"
      sort:
        type: "string"
        description: "Sort order — for list_issues"
        enum: ['date', 'new', 'freq']
        default: "date"
      limit:
        type: "integer"
        description: "Max results — for list_issues (default 10, max 25)"
        default: 10
      assignee:
        type: "string"
        description: "User email or 'me' — for assign_issue"
        default: ""
    required: [action]
---
# Sentry

Monitor and manage application errors in Sentry. View issues, stack traces, and error trends.

## Navigation
- **list_projects** — List all accessible projects in the organization.
- **list_issues** — List issues with optional search. Provide `query` (default: `is:unresolved`), `sort`, and `limit`.
- **get_issue** — Get full details of an issue including tags and stats. Provide `issue_id`.
- **get_latest_event** — Get the most recent event/stack trace for an issue. Provide `issue_id`.

## Issue Management
- **resolve_issue** — Mark an issue as resolved. Provide `issue_id`.
- **unresolve_issue** — Re-open a resolved issue. Provide `issue_id`.
- **assign_issue** — Assign an issue to a user. Provide `issue_id` and `assignee` (email or 'me').

## Example queries for list_issues
- `is:unresolved` — All unresolved issues
- `is:unresolved level:error` — Unresolved errors only
- `is:unresolved assigned:me` — My unresolved issues
- `is:unresolved first-seen:-24h` — New issues in last 24 hours
- `is:unresolved times-seen:>100` — Frequent issues
- `is:unresolved !has:assignee` — Unassigned issues
