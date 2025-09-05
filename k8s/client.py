from typing import Optional
from kubernetes.client.rest import ApiException


from .config import k8s_clients
from . import router

def kubernetes_tool(
    verb: str,
    resource: str,
    name: Optional[str] = None,
    namespace: Optional[str] = None,
    replicas: Optional[int] = None,
    application_name: Optional[str] = None,
    image: Optional[str] = None
) -> str:
    """
    Tool to interact with the Kubernetes API.

    Args:
        verb (str): The action to perform.
        resource (str): The type of resource to act upon.
        name (Optional[str]): The name of the specific resource.
        namespace (Optional[str]): The namespace of the resource.
        replicas (Optional[int]): The number of replicas for a 'scale' or 'deploy' operation.
        application_name (Optional[str]): The name for a new application to deploy.
        image (Optional[str]): The container image for a new application to deploy.

    Verb-Resource Mapping:
    - 'get': ['nodes', 'namespaces', 'pods', 'deployments']
    - 'describe': ['pods', 'deployments']
    - 'history': ['deployments']
    - 'undo': ['deployments']
    - 'restart': ['deployments']
    - 'scale': ['deployments']
    - 'logs': ['pods']
    - 'check': ['health']
    - 'deploy': ['application']
    """
    if k8s_clients.error:
        return f"Erreur de configuration Kubernetes: {k8s_clients.error}"

    try:
        # We need to pass all potential arguments to dispatch
        return router.dispatch(
            verb, resource,
            v1=k8s_clients.v1, apps_v1=k8s_clients.apps_v1,
            name=name, namespace=namespace, replicas=replicas,
            application_name=application_name, image=image
        )
    except ApiException as e:
        return f"Erreur API Kubernetes ({e.status}): {e.reason}"
    except Exception as e:
        return f"Une erreur inattendue est survenue dans l'outil Kubernetes: {e}"
