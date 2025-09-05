from typing import Optional
from kubernetes.client.rest import ApiException
from kubernetes import client
from .config import k8s_clients
from .handlers import cluster_handler, deployment_handler, pod_handler

DISPATCHER = {
    ('get', 'nodes'): cluster_handler.get_nodes,
    ('get', 'namespaces'): cluster_handler.get_namespaces,
    ('check', 'health'): cluster_handler.check_cluster_health,
    ('history', 'deployments'): deployment_handler.get_deployment_history,
    ('get', 'pods'): pod_handler.get_pods,
    ('describe', 'pods'): pod_handler.describe_pod,
    ('logs', 'pods'): pod_handler.get_pod_logs,
    ('get', 'deployments'): deployment_handler.get_deployments,
    ('describe', 'deployments'): deployment_handler.describe_deployment,
    ('restart', 'deployments'): deployment_handler.restart_deployment,
    ('scale', 'deployments'): deployment_handler.scale_deployment,
    ('undo', 'deployments'): deployment_handler.undo_deployment_rollout,
}

def kubernetes_tool(verb: str, resource: str, name: Optional[str] = None, namespace: Optional[str] = None, replicas: Optional[int] = None) -> str:
    """
    Tool to interact with the Kubernetes API.

    Args:
        verb (str): The action to perform.
        resource (str): The type of resource to act upon.
        name (Optional[str]): The name of the specific resource.
        namespace (Optional[str]): The namespace of the resource.
        replicas (Optional[int]): The number of replicas for a 'scale' operation.

    Verb-Resource Mapping:
    - 'get': ['nodes', 'namespaces', 'pods', 'deployments']
    - 'describe': ['pods', 'deployments']
    - 'history': ['deployments']
    - 'undo': ['deployments']
    - 'restart': ['deployments']
    - 'scale': ['deployments']
    - 'logs': ['pods']
    - 'check': ['health']
    """
    if k8s_clients.error:
        return f"Erreur de configuration Kubernetes: {k8s_clients.error}"

    try:
        handler = DISPATCHER.get((verb, resource))
        if handler:
            return handler(v1=k8s_clients.v1, apps_v1=k8s_clients.apps_v1, name=name, namespace=namespace, replicas=replicas)
        else:
            return f"Erreur: Combinaison non supportée: {verb} {resource}."
    except ApiException as e:
        return f"Erreur API Kubernetes ({e.status}): {e.reason}"
    except Exception as e:
        return f"Une erreur inattendue est survenue dans l'outil Kubernetes: {e}"
