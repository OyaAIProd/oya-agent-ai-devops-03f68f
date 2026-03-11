import os
import json
import ssl
import httpx


def k8s_client(api_url, token, timeout=15):
    """Create httpx client with K8s auth. Skips TLS verify for in-cluster certs."""
    return httpx.Client(
        base_url=api_url.rstrip("/"),
        headers={"Authorization": f"Bearer {token}"},
        verify=False,
        timeout=timeout,
    )


def do_get_namespaces(api_url, token):
    with k8s_client(api_url, token) as c:
        r = c.get("/api/v1/namespaces")
        r.raise_for_status()
        data = r.json()
    items = data.get("items", [])
    return {
        "namespaces": [
            {"name": ns["metadata"]["name"], "status": ns["status"]["phase"]}
            for ns in items
        ],
        "count": len(items),
    }


def do_get_pods(api_url, token, namespace, label_selector):
    params = {}
    if label_selector:
        params["labelSelector"] = label_selector
    with k8s_client(api_url, token) as c:
        r = c.get(f"/api/v1/namespaces/{namespace}/pods", params=params)
        r.raise_for_status()
        data = r.json()
    items = data.get("items", [])
    pods = []
    for p in items:
        meta = p["metadata"]
        status = p["status"]
        container_statuses = status.get("containerStatuses", [])
        pods.append({
            "name": meta["name"],
            "phase": status.get("phase", ""),
            "ready": all(cs.get("ready", False) for cs in container_statuses) if container_statuses else False,
            "restarts": sum(cs.get("restartCount", 0) for cs in container_statuses),
            "node": p["spec"].get("nodeName", ""),
            "age": meta.get("creationTimestamp", ""),
            "containers": [
                {
                    "name": cs["name"],
                    "ready": cs.get("ready", False),
                    "restarts": cs.get("restartCount", 0),
                    "state": list(cs.get("state", {}).keys())[0] if cs.get("state") else "unknown",
                    "reason": _extract_reason(cs),
                }
                for cs in container_statuses
            ],
        })
    return {"pods": pods, "count": len(pods)}


def _extract_reason(cs):
    state = cs.get("state", {})
    for _, detail in state.items():
        if isinstance(detail, dict) and detail.get("reason"):
            return detail["reason"]
    last = cs.get("lastState", {})
    for _, detail in last.items():
        if isinstance(detail, dict) and detail.get("reason"):
            return f"last: {detail['reason']}"
    return ""


def do_get_pod_logs(api_url, token, namespace, pod_name, container, tail_lines):
    params = {"tailLines": min(tail_lines, 500)}
    if container:
        params["container"] = container
    with k8s_client(api_url, token) as c:
        r = c.get(f"/api/v1/namespaces/{namespace}/pods/{pod_name}/log", params=params)
        r.raise_for_status()
    return {"pod": pod_name, "logs": r.text[-10000:]}  # Cap output size


def do_get_events(api_url, token, namespace, field_selector):
    params = {}
    if field_selector:
        params["fieldSelector"] = field_selector
    path = f"/api/v1/namespaces/{namespace}/events" if namespace else "/api/v1/events"
    with k8s_client(api_url, token) as c:
        r = c.get(path, params=params)
        r.raise_for_status()
        data = r.json()
    items = data.get("items", [])
    # Sort by last timestamp descending, take most recent
    items.sort(key=lambda e: e.get("lastTimestamp") or e.get("metadata", {}).get("creationTimestamp", ""), reverse=True)
    return {
        "events": [
            {
                "type": e.get("type", ""),
                "reason": e.get("reason", ""),
                "message": e.get("message", ""),
                "object": f"{e.get('involvedObject', {}).get('kind', '')}/{e.get('involvedObject', {}).get('name', '')}",
                "namespace": e.get("involvedObject", {}).get("namespace", ""),
                "count": e.get("count", 1),
                "last_seen": e.get("lastTimestamp", ""),
            }
            for e in items[:25]
        ],
        "count": len(items),
    }


def do_describe_pod(api_url, token, namespace, pod_name):
    with k8s_client(api_url, token) as c:
        r = c.get(f"/api/v1/namespaces/{namespace}/pods/{pod_name}")
        r.raise_for_status()
        p = r.json()
    meta = p["metadata"]
    spec = p["spec"]
    status = p["status"]
    return {
        "name": meta["name"],
        "namespace": meta["namespace"],
        "labels": meta.get("labels", {}),
        "phase": status.get("phase", ""),
        "node": spec.get("nodeName", ""),
        "ip": status.get("podIP", ""),
        "conditions": [
            {"type": c["type"], "status": c["status"], "reason": c.get("reason", "")}
            for c in status.get("conditions", [])
        ],
        "containers": [
            {
                "name": ct["name"],
                "image": ct["image"],
                "ports": [{"port": p.get("containerPort"), "protocol": p.get("protocol")} for p in ct.get("ports", [])],
                "resources": ct.get("resources", {}),
            }
            for ct in spec.get("containers", [])
        ],
        "container_statuses": [
            {
                "name": cs["name"],
                "ready": cs.get("ready", False),
                "restarts": cs.get("restartCount", 0),
                "state": cs.get("state", {}),
            }
            for cs in status.get("containerStatuses", [])
        ],
    }


def do_get_deployments(api_url, token, namespace, label_selector):
    params = {}
    if label_selector:
        params["labelSelector"] = label_selector
    with k8s_client(api_url, token) as c:
        r = c.get(f"/apis/apps/v1/namespaces/{namespace}/deployments", params=params)
        r.raise_for_status()
        data = r.json()
    items = data.get("items", [])
    return {
        "deployments": [
            {
                "name": d["metadata"]["name"],
                "replicas": d["spec"].get("replicas", 0),
                "ready": d["status"].get("readyReplicas", 0),
                "updated": d["status"].get("updatedReplicas", 0),
                "available": d["status"].get("availableReplicas", 0),
                "strategy": d["spec"].get("strategy", {}).get("type", ""),
                "age": d["metadata"].get("creationTimestamp", ""),
            }
            for d in items
        ],
        "count": len(items),
    }


def do_describe_deployment(api_url, token, namespace, deployment_name):
    with k8s_client(api_url, token) as c:
        r = c.get(f"/apis/apps/v1/namespaces/{namespace}/deployments/{deployment_name}")
        r.raise_for_status()
        d = r.json()
    return {
        "name": d["metadata"]["name"],
        "namespace": d["metadata"]["namespace"],
        "labels": d["metadata"].get("labels", {}),
        "replicas": d["spec"].get("replicas", 0),
        "ready": d["status"].get("readyReplicas", 0),
        "updated": d["status"].get("updatedReplicas", 0),
        "available": d["status"].get("availableReplicas", 0),
        "strategy": d["spec"].get("strategy", {}),
        "conditions": [
            {"type": c["type"], "status": c["status"], "reason": c.get("reason", ""), "message": c.get("message", "")}
            for c in d["status"].get("conditions", [])
        ],
        "containers": [
            {"name": ct["name"], "image": ct["image"]}
            for ct in d["spec"].get("template", {}).get("spec", {}).get("containers", [])
        ],
    }


def do_get_nodes(api_url, token):
    with k8s_client(api_url, token) as c:
        r = c.get("/api/v1/nodes")
        r.raise_for_status()
        data = r.json()
    items = data.get("items", [])
    return {
        "nodes": [
            {
                "name": n["metadata"]["name"],
                "conditions": [
                    {"type": c["type"], "status": c["status"]}
                    for c in n["status"].get("conditions", [])
                ],
                "capacity": {
                    "cpu": n["status"].get("capacity", {}).get("cpu", ""),
                    "memory": n["status"].get("capacity", {}).get("memory", ""),
                    "pods": n["status"].get("capacity", {}).get("pods", ""),
                },
                "allocatable": {
                    "cpu": n["status"].get("allocatable", {}).get("cpu", ""),
                    "memory": n["status"].get("allocatable", {}).get("memory", ""),
                },
                "os": n["status"].get("nodeInfo", {}).get("osImage", ""),
                "kubelet": n["status"].get("nodeInfo", {}).get("kubeletVersion", ""),
            }
            for n in items
        ],
        "count": len(items),
    }


def do_rollout_restart(api_url, token, namespace, deployment_name):
    import datetime
    patch = {
        "spec": {
            "template": {
                "metadata": {
                    "annotations": {
                        "kubectl.kubernetes.io/restartedAt": datetime.datetime.utcnow().isoformat() + "Z"
                    }
                }
            }
        }
    }
    with k8s_client(api_url, token) as c:
        r = c.patch(
            f"/apis/apps/v1/namespaces/{namespace}/deployments/{deployment_name}",
            json=patch,
            headers={"Content-Type": "application/strategic-merge-patch+json"},
        )
        r.raise_for_status()
    return {"ok": True, "deployment": deployment_name, "action": "rollout_restart"}


try:
    api_url = os.environ["K8S_API_URL"]
    token = os.environ["K8S_TOKEN"]
    default_ns = os.environ.get("K8S_NAMESPACE", "default")
    inp = json.loads(os.environ.get("INPUT_JSON", "{}"))
    action = inp.get("action", "")
    ns = inp.get("namespace", "") or default_ns

    if action == "get_namespaces":
        result = do_get_namespaces(api_url, token)
    elif action == "get_pods":
        result = do_get_pods(api_url, token, ns, inp.get("label_selector", ""))
    elif action == "get_pod_logs":
        result = do_get_pod_logs(api_url, token, ns, inp.get("pod_name", ""), inp.get("container", ""), inp.get("tail_lines", 100))
    elif action == "get_events":
        result = do_get_events(api_url, token, ns, inp.get("field_selector", ""))
    elif action == "describe_pod":
        result = do_describe_pod(api_url, token, ns, inp.get("pod_name", ""))
    elif action == "get_deployments":
        result = do_get_deployments(api_url, token, ns, inp.get("label_selector", ""))
    elif action == "describe_deployment":
        result = do_describe_deployment(api_url, token, ns, inp.get("deployment_name", ""))
    elif action == "get_nodes":
        result = do_get_nodes(api_url, token)
    elif action == "rollout_restart":
        result = do_rollout_restart(api_url, token, ns, inp.get("deployment_name", ""))
    else:
        result = {"error": f"Unknown action: {action}"}

    print(json.dumps(result))

except Exception as e:
    print(json.dumps({"error": str(e)}))
