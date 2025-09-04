import os
from typing import Optional
from kubernetes import client, config
from kubernetes.client.rest import ApiException

def get_kubeconfig_path():
    return os.getenv('KUBECONFIG', 'k3s.yaml')

def _get_nodes(v1, **kwargs):
    items = v1.list_node().items
    output = "Nœuds:\n"
    for item in items:
        status = next((c.status for c in item.status.conditions if c.type == 'Ready'), 'Inconnu')
        output += f"- {item.metadata.name} (Statut: {'Prêt' if status == 'True' else 'Non Prêt'})\n"
    return output

def _get_pods(v1, namespace=None, **kwargs):
    items = v1.list_pod_for_all_namespaces().items if not namespace else v1.list_namespaced_pod(namespace).items
    output = "Pods:\n"
    for item in items:
        output += f"- NS: {item.metadata.namespace}, Nom: {item.metadata.name}, Statut: {item.status.phase}\n"
    return output if items else "Aucun pod trouvé."

def _get_deployments(apps_v1, namespace=None, **kwargs):
    items = apps_v1.list_deployment_for_all_namespaces().items if not namespace else apps_v1.list_namespaced_deployment(namespace).items
    output = "Déploiements:\n"
    for item in items:
        output += f"- NS: {item.metadata.namespace}, Nom: {item.metadata.name}, Replicas: {item.status.replicas}\n"
    return output if items else "Aucun déploiement trouvé."

def _get_services(v1, namespace=None, **kwargs):
    items = v1.list_service_for_all_namespaces().items if not namespace else v1.list_namespaced_service(namespace).items
    output = "Services:\n"
    for item in items:
        output += f"- NS: {item.metadata.namespace}, Nom: {item.metadata.name}, Type: {item.spec.type}, IP: {item.spec.cluster_ip}\n"
    return output if items else "Aucun service trouvé."

DISPATCHER = {
    ('get', 'nodes'): _get_nodes,
    ('get', 'pods'): _get_pods,
    ('get', 'deployments'): _get_deployments,
    ('get', 'services'): _get_services,
}

def kubernetes_tool(verb: str, resource: str, name: Optional[str] = None, namespace: Optional[str] = None) -> str:
    """
    Outil universel pour interagir avec l'API Kubernetes via la librairie Python.
    Traduit des commandes simples en appels API natifs.
    Verbes supportés: 'get'.
    Ressources supportées: 'nodes', 'pods', 'deployments', 'services'.
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
            return handler(v1=v1, apps_v1=apps_v1, name=name, namespace=namespace)
        else:
            return f"Erreur: La combinaison de l'action '{verb}' et de la ressource '{resource}' n'est pas supportée."

    except ApiException as e:
        if e.status == 404:
            return f"Erreur: La ressource '{name}' n'a pas été trouvée dans le namespace '{namespace}'."
        return f"Erreur API Kubernetes ({e.status}): {e.reason}"
    except Exception as e:
        return f"Une erreur inattendue est survenue: {e}"
