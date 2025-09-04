import os
from typing import Optional
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from . import handlers

def get_kubeconfig_path():
    return os.getenv('KUBECONFIG', 'k3s.yaml')

DISPATCHER = {
    ('get', 'nodes'): handlers.get_nodes,
    ('get', 'pods'): handlers.get_pods,
    ('get', 'deployments'): handlers.get_deployments,
    ('get', 'services'): handlers.get_services,
    ('describe', 'pods'): handlers.describe_pod,
    ('describe', 'deployments'): handlers.describe_deployment,
    ('restart', 'deployments'): handlers.restart_deployment,
    ('logs', 'pods'): handlers.get_pod_logs,
    ('scale', 'deployments'): handlers.scale_deployment,
}

def kubernetes_tool(verb: str, resource: str, name: Optional[str] = None, namespace: Optional[str] = None, replicas: Optional[int] = None) -> str:
    """
    Outil universel pour interagir avec l'API Kubernetes.
    Verbes supportés: 'get', 'describe', 'restart', 'logs', 'scale'.
    Ressources supportées: 'nodes', 'pods', 'deployments', 'services'.
    'restart' et 'scale' sont pour 'deployments'. 'logs' et 'describe' sont pour 'pods' et 'deployments'.
    Pour 'scale', l'argument 'replicas' est obligatoire.
    """
    try:
        kubeconfig_file = get_kubeconfig_path()
        if not os.path.exists(kubeconfig_file):
            return f"Erreur: Fichier de configuration '{kubeconfig_file}' introuvable."

        config.load_kube_config(config_file=kubeconfig_file)
        v1 = client.CoreV1Api()
        apps_v1 = client.AppsV1Api()

        handler = DISPATCHER.get((verb, resource))

        if handler:
            if verb in ['describe', 'restart', 'logs'] and (not name or not namespace):
                return f"Erreur: Pour l'action '{verb}', le nom et le namespace sont obligatoires."
            if verb == 'scale' and (not name or not namespace or replicas is None):
                return f"Erreur: Pour l'action 'scale', le nom, le namespace et le nombre de réplicas sont obligatoires."

            return handler(v1=v1, apps_v1=apps_v1, name=name, namespace=namespace, replicas=replicas)
        else:
            return f"Erreur: La combinaison de l'action '{verb}' et de la ressource '{resource}' n'est pas supportée."

    except ApiException as e:
        if e.status == 404:
            return f"Erreur: La ressource '{name}' n'a pas été trouvée dans le namespace '{namespace}'."
        return f"Erreur API Kubernetes ({e.status}): {e.reason}"
    except Exception as e:
        return f"Une erreur inattendue est survenue: {e}"
