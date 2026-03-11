import os
import json
import httpx


def api(key, host, method, path, body=None, params=None, timeout=15):
    url = f"{host.rstrip('/')}/{path.lstrip('/')}"
    with httpx.Client(timeout=timeout) as c:
        r = c.request(
            method, url,
            headers={"Authorization": f"Bearer {key}"},
            json=body, params=params,
        )
        r.raise_for_status()
        return r.json() if r.content else {}


def do_query_events(key, host, project_id, event_name, properties_filter, date_from, date_to, limit):
    params = {"limit": min(limit, 100)}
    if event_name:
        params["event"] = event_name
    if date_from:
        params["after"] = date_from
    if date_to:
        params["before"] = date_to
    if properties_filter:
        params["properties"] = properties_filter

    data = api(key, host, "GET", f"api/projects/{project_id}/events/", params=params)
    results = data.get("results", [])
    return {
        "events": [
            {
                "id": e.get("id", ""),
                "event": e.get("event", ""),
                "distinct_id": e.get("distinct_id", ""),
                "timestamp": e.get("timestamp", ""),
                "properties": {
                    k: v for k, v in (e.get("properties") or {}).items()
                    if k in ("$browser", "$os", "$current_url", "$pathname", "$referrer", "$device_type")
                },
            }
            for e in results[:limit]
        ],
        "count": len(results),
    }


def do_get_insights(key, host, project_id, search, limit):
    params = {"limit": min(limit, 50)}
    if search:
        params["search"] = search
    data = api(key, host, "GET", f"api/projects/{project_id}/insights/", params=params)
    results = data.get("results", [])
    return {
        "insights": [
            {
                "id": i.get("id"),
                "name": i.get("name", ""),
                "description": i.get("description", ""),
                "filters": i.get("filters", {}),
                "last_refresh": i.get("last_refresh", ""),
            }
            for i in results
        ],
        "count": len(results),
    }


def do_get_insight(key, host, project_id, insight_id):
    data = api(key, host, "GET", f"api/projects/{project_id}/insights/{insight_id}/")
    return {
        "id": data.get("id"),
        "name": data.get("name", ""),
        "description": data.get("description", ""),
        "filters": data.get("filters", {}),
        "result": data.get("result", []),
        "last_refresh": data.get("last_refresh", ""),
    }


def do_get_feature_flags(key, host, project_id):
    data = api(key, host, "GET", f"api/projects/{project_id}/feature_flags/", params={"limit": 100})
    results = data.get("results", [])
    return {
        "flags": [
            {
                "id": f.get("id"),
                "key": f.get("key", ""),
                "name": f.get("name", ""),
                "active": f.get("active", False),
                "rollout_percentage": f.get("rollout_percentage"),
                "created_at": f.get("created_at", ""),
            }
            for f in results
        ],
        "count": len(results),
    }


def do_get_persons(key, host, project_id, search, limit):
    params = {"limit": min(limit, 50)}
    if search:
        params["search"] = search
    data = api(key, host, "GET", f"api/projects/{project_id}/persons/", params=params)
    results = data.get("results", [])
    return {
        "persons": [
            {
                "id": p.get("id"),
                "distinct_ids": p.get("distinct_ids", [])[:3],
                "properties": {
                    k: v for k, v in (p.get("properties") or {}).items()
                    if k in ("email", "$name", "$browser", "$os", "$initial_referrer", "name")
                },
                "created_at": p.get("created_at", ""),
            }
            for p in results
        ],
        "count": len(results),
    }


def do_get_trends(key, host, project_id, events_json, date_from, date_to):
    events = json.loads(events_json) if isinstance(events_json, str) else events_json
    body = {
        "insight": "TRENDS",
        "events": events,
        "date_from": date_from or "-7d",
    }
    if date_to:
        body["date_to"] = date_to
    data = api(key, host, "POST", f"api/projects/{project_id}/insights/trend/", body=body)
    return {
        "result": data.get("result", []),
    }


try:
    key = os.environ["POSTHOG_API_KEY"]
    project_id = os.environ["POSTHOG_PROJECT_ID"]
    host = os.environ.get("POSTHOG_HOST", "https://us.posthog.com")
    inp = json.loads(os.environ.get("INPUT_JSON", "{}"))
    action = inp.get("action", "")

    if action == "query_events":
        result = do_query_events(
            key, host, project_id,
            inp.get("event_name", ""),
            inp.get("properties_filter", ""),
            inp.get("date_from", "-7d"),
            inp.get("date_to", ""),
            inp.get("limit", 10),
        )
    elif action == "get_insights":
        result = do_get_insights(key, host, project_id, inp.get("search", ""), inp.get("limit", 10))
    elif action == "get_insight":
        result = do_get_insight(key, host, project_id, inp.get("insight_id", 0))
    elif action == "get_feature_flags":
        result = do_get_feature_flags(key, host, project_id)
    elif action == "get_persons":
        result = do_get_persons(key, host, project_id, inp.get("search", ""), inp.get("limit", 10))
    elif action == "get_trends":
        result = do_get_trends(
            key, host, project_id,
            inp.get("events_json", "[]"),
            inp.get("date_from", "-7d"),
            inp.get("date_to", ""),
        )
    else:
        result = {"error": f"Unknown action: {action}"}

    print(json.dumps(result))

except Exception as e:
    print(json.dumps({"error": str(e)}))
