import os
import json
import httpx

BASE = "https://sentry.io/api/0"


def api(token, method, path, body=None, params=None, timeout=15):
    with httpx.Client(timeout=timeout) as c:
        r = c.request(
            method,
            f"{BASE}/{path}",
            headers={"Authorization": f"Bearer {token}"},
            json=body,
            params=params,
        )
        if r.status_code >= 400:
            detail = ""
            try:
                detail = r.json().get("detail", r.text[:300])
            except Exception:
                detail = r.text[:300]
            raise Exception(f"Sentry API {r.status_code}: {detail}")
        return r.json() if r.content else {}


def do_list_projects(token, org):
    data = api(token, "GET", f"organizations/{org}/projects/")
    return {
        "projects": [
            {"slug": p["slug"], "name": p["name"], "platform": p.get("platform")}
            for p in data
        ],
        "count": len(data),
    }


def do_list_issues(token, org, project, query, sort, limit):
    params = {"query": query, "sort": sort, "limit": min(limit, 25)}
    data = api(token, "GET", f"projects/{org}/{project}/issues/", params=params)
    return {
        "issues": [
            {
                "id": i["id"],
                "title": i["title"],
                "culprit": i.get("culprit", ""),
                "level": i.get("level", ""),
                "status": i.get("status", ""),
                "count": i.get("count", "0"),
                "first_seen": i.get("firstSeen", ""),
                "last_seen": i.get("lastSeen", ""),
                "assignee": (i.get("assignedTo") or {}).get("email", ""),
                "link": i.get("permalink", ""),
            }
            for i in data
        ],
        "count": len(data),
    }


def do_get_issue(token, issue_id):
    data = api(token, "GET", f"issues/{issue_id}/")
    return {
        "id": data["id"],
        "title": data["title"],
        "culprit": data.get("culprit", ""),
        "level": data.get("level", ""),
        "status": data.get("status", ""),
        "count": data.get("count", "0"),
        "first_seen": data.get("firstSeen", ""),
        "last_seen": data.get("lastSeen", ""),
        "assignee": (data.get("assignedTo") or {}).get("email", ""),
        "link": data.get("permalink", ""),
        "tags": [
            {"key": t["key"], "top_values": [v["value"] for v in t.get("topValues", [])[:3]]}
            for t in data.get("tags", [])[:10]
        ],
        "stats": data.get("stats", {}),
    }


def do_get_latest_event(token, issue_id):
    data = api(token, "GET", f"issues/{issue_id}/events/latest/")
    entries = data.get("entries", [])
    exception_entry = next((e for e in entries if e.get("type") == "exception"), None)
    frames = []
    if exception_entry:
        for exc_val in exception_entry.get("data", {}).get("values", []):
            exc_type = exc_val.get("type", "")
            exc_value = exc_val.get("value", "")
            for frame in (exc_val.get("stacktrace") or {}).get("frames", [])[-5:]:
                frames.append({
                    "file": frame.get("filename", ""),
                    "line": frame.get("lineNo"),
                    "function": frame.get("function", ""),
                    "context": frame.get("context", []),
                })
    return {
        "event_id": data.get("eventID", ""),
        "timestamp": data.get("dateCreated", ""),
        "message": data.get("message", ""),
        "exception_type": exc_type if exception_entry else "",
        "exception_value": exc_value if exception_entry else "",
        "frames": frames,
        "tags": {t["key"]: t["value"] for t in data.get("tags", [])[:10]},
    }


def do_resolve_issue(token, issue_id):
    data = api(token, "PUT", f"issues/{issue_id}/", body={"status": "resolved"})
    return {"ok": True, "id": issue_id, "status": "resolved"}


def do_unresolve_issue(token, issue_id):
    data = api(token, "PUT", f"issues/{issue_id}/", body={"status": "unresolved"})
    return {"ok": True, "id": issue_id, "status": "unresolved"}


def do_assign_issue(token, issue_id, assignee):
    data = api(token, "PUT", f"issues/{issue_id}/", body={"assignedTo": assignee})
    return {"ok": True, "id": issue_id, "assigned_to": assignee}


try:
    token = os.environ["SENTRY_AUTH_TOKEN"]
    org = os.environ["SENTRY_ORG"]
    project = os.environ.get("SENTRY_PROJECT", "")
    inp = json.loads(os.environ.get("INPUT_JSON", "{}"))
    action = inp.get("action", "")

    if action == "list_projects":
        result = do_list_projects(token, org)
    elif action == "list_issues":
        result = do_list_issues(
            token, org, project,
            inp.get("query", "is:unresolved"),
            inp.get("sort", "date"),
            inp.get("limit", 10),
        )
    elif action == "get_issue":
        result = do_get_issue(token, inp.get("issue_id", ""))
    elif action == "get_latest_event":
        result = do_get_latest_event(token, inp.get("issue_id", ""))
    elif action == "resolve_issue":
        result = do_resolve_issue(token, inp.get("issue_id", ""))
    elif action == "unresolve_issue":
        result = do_unresolve_issue(token, inp.get("issue_id", ""))
    elif action == "assign_issue":
        result = do_assign_issue(token, inp.get("issue_id", ""), inp.get("assignee", ""))
    else:
        result = {"error": f"Unknown action: {action}"}

    print(json.dumps(result))

except Exception as e:
    print(json.dumps({"error": str(e)}))
