---
name: kubernetes
display_name: "Kubernetes"
description: "Monitor and manage Kubernetes clusters — pods, deployments, logs, events, and nodes"
category: infrastructure
icon: server
skill_type: sandbox
catalog_type: platform
requirements: "httpx>=0.25"
resource_requirements:
  - env_var: K8S_API_URL
    name: "Kubernetes API URL"
    description: "Cluster API server URL (e.g. https://kubernetes.default.svc)"
  - env_var: K8S_TOKEN
    name: "Kubernetes Bearer Token"
    description: "Service account bearer token with read access"
  - env_var: K8S_NAMESPACE
    name: "Default Namespace"
    description: "Default namespace to query (e.g. default, production)"
tool_schema:
  name: kubernetes
  description: "Monitor and manage Kubernetes clusters — pods, deployments, logs, events, and nodes"
  parameters:
    type: object
    properties:
      action:
        type: "string"
        description: "Which operation to perform"
        enum: ['get_pods', 'get_pod_logs', 'get_events', 'describe_pod', 'get_deployments', 'describe_deployment', 'get_nodes', 'get_namespaces', 'rollout_restart']
      namespace:
        type: "string"
        description: "Kubernetes namespace (overrides default)"
        default: ""
      pod_name:
        type: "string"
        description: "Pod name — for get_pod_logs, describe_pod"
        default: ""
      deployment_name:
        type: "string"
        description: "Deployment name — for describe_deployment, rollout_restart"
        default: ""
      container:
        type: "string"
        description: "Container name — for get_pod_logs (optional, defaults to first container)"
        default: ""
      tail_lines:
        type: "integer"
        description: "Number of log lines to return — for get_pod_logs (default 100)"
        default: 100
      label_selector:
        type: "string"
        description: "Label selector to filter resources (e.g. 'app=myapp')"
        default: ""
      field_selector:
        type: "string"
        description: "Field selector — for get_events (e.g. 'type=Warning')"
        default: ""
    required: [action]
---
# Kubernetes

Monitor and manage Kubernetes clusters. View pods, deployments, logs, events, and nodes.

## Navigation
- **get_namespaces** — List all namespaces.
- **get_pods** — List pods in a namespace. Optionally filter by `label_selector`.
- **get_deployments** — List deployments in a namespace. Optionally filter by `label_selector`.
- **get_nodes** — List cluster nodes with status and capacity.
- **get_events** — List cluster events. Filter by `namespace`, `field_selector` (e.g. `type=Warning`).

## Inspection
- **describe_pod** — Get detailed pod info including containers, status, conditions. Provide `pod_name`.
- **describe_deployment** — Get deployment details including replicas, strategy, conditions. Provide `deployment_name`.
- **get_pod_logs** — Get logs from a pod. Provide `pod_name`, optional `container`, `tail_lines`.

## Actions
- **rollout_restart** — Trigger a rolling restart of a deployment. Provide `deployment_name`.

## Tips
- Start with `get_events` with `field_selector: "type=Warning"` to find problems.
- Use `get_pods` to check pod statuses — look for CrashLoopBackOff, OOMKilled, Pending.
- Use `get_pod_logs` to investigate failing pods.
- Check `get_nodes` for resource pressure (MemoryPressure, DiskPressure).
