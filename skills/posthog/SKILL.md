---
name: posthog
display_name: "PostHog"
description: "Query analytics events, insights, and feature flags in PostHog"
category: monitoring
icon: bar-chart
skill_type: sandbox
catalog_type: platform
requirements: "httpx>=0.25"
resource_requirements:
  - env_var: POSTHOG_API_KEY
    name: "PostHog Personal API Key"
    description: "Personal API key from PostHog (Settings > Personal API Keys)"
  - env_var: POSTHOG_PROJECT_ID
    name: "PostHog Project ID"
    description: "Project ID (found in project settings URL)"
  - env_var: POSTHOG_HOST
    name: "PostHog Host"
    description: "PostHog instance URL (e.g. https://us.posthog.com)"
tool_schema:
  name: posthog
  description: "Query analytics events, insights, and feature flags in PostHog"
  parameters:
    type: object
    properties:
      action:
        type: "string"
        description: "Which operation to perform"
        enum: ['query_events', 'get_insights', 'get_insight', 'get_feature_flags', 'get_persons', 'get_trends']
      event_name:
        type: "string"
        description: "Event name to filter by — for query_events (e.g. '$pageview', 'user_signed_up')"
        default: ""
      properties_filter:
        type: "string"
        description: "JSON array of property filters — for query_events (e.g. [{\"key\": \"$browser\", \"value\": \"Chrome\"}])"
        default: ""
      date_from:
        type: "string"
        description: "Start date — for query_events, get_trends (e.g. '-7d', '-24h', '2025-01-01')"
        default: "-7d"
      date_to:
        type: "string"
        description: "End date — for query_events, get_trends"
        default: ""
      limit:
        type: "integer"
        description: "Max results (default 10, max 100)"
        default: 10
      insight_id:
        type: "integer"
        description: "Insight ID — for get_insight"
        default: 0
      search:
        type: "string"
        description: "Search query — for get_persons, get_insights"
        default: ""
      events_json:
        type: "string"
        description: "JSON array of event definitions — for get_trends (e.g. [{\"id\": \"$pageview\", \"math\": \"total\"}])"
        default: ""
    required: [action]
---
# PostHog

Query analytics events, insights, and feature flags in PostHog.

## Queries
- **query_events** — List recent events. Optionally filter by `event_name`, `properties_filter`, `date_from`, `date_to`, `limit`.
- **get_trends** — Get event trend data. Provide `events_json` (array of event definitions), `date_from`, `date_to`.

## Insights
- **get_insights** — List saved insights. Optionally filter by `search`.
- **get_insight** — Get a specific insight with results. Provide `insight_id`.

## Feature Flags
- **get_feature_flags** — List all feature flags with their status.

## Persons
- **get_persons** — Search for persons/users. Provide `search` (email, name, or distinct_id).

## Example event filter
```json
[{"key": "$browser", "value": "Chrome", "operator": "exact"}]
```

## Example trends events
```json
[{"id": "$pageview", "math": "total"}, {"id": "user_signed_up", "math": "dau"}]
```
