# k8s/client.py

from typing import Optional
from kubernetes.client.rest import ApiException

# Import handlers FIRST to run their decorators and populate the registry.
from .handlers import cluster_handler, deployment_handler, pod_handler

from .config import k8s_clients
from . import router  # Now, import the router with its registry populated.

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
        return router.dispatch(
            verb,
            resource,
            v1=k8s_clients.v1,
            apps_v1=k8s_clients.apps_v1,
            name=name,
            namespace=namespace,
            replicas=replicas
        )
    except ApiException as e:
        return f"Erreur API Kubernetes ({e.status}): {e.reason}"
    except Exception as e:
        return f"Une erreur inattendue est survenue dans l'outil Kubernetes: {e}"
