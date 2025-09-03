import os
from kubernetes import client, config
from kubernetes.client.rest import ApiException

def get_kubeconfig_path():
    return os.getenv('KUBECONFIG', 'k3s.yaml')

def list_kubernetes_nodes() -> str:
    """Liste tous les nœuds du cluster Kubernetes et leur statut."""
    try:
        kubeconfig_file = get_kubeconfig_path()
        if not os.path.exists(kubeconfig_file):
            return f"Erreur: Fichier de configuration '{kubeconfig_file}' introuvable."

        config.load_kube_config(config_file=kubeconfig_file)
        v1 = client.CoreV1Api()
        node_list = v1.list_node(timeout_seconds=10)

        output = "Statut des Nœuds:\n"
        for node in node_list.items:
            status = "Inconnu"
            for condition in node.status.conditions:
                if condition.type == "Ready":
                    status = "Prêt" if condition.status == "True" else "Non Prêt"
            output += f"- {node.metadata.name}: {status}\n"
        return output

    except ApiException as e:
        return f"Erreur API Kubernetes ({e.status}): {e.reason}"
    except Exception as e:
        return f"Une erreur inattendue est survenue lors de l'accès à Kubernetes: {e}"

def list_kubernetes_pods(namespace: str = None) -> str:
    """
    Liste les pods dans un namespace Kubernetes.
    Si aucun namespace n'est spécifié, liste les pods de tous les namespaces.
    """
    try:
        kubeconfig_file = get_kubeconfig_path()
        if not os.path.exists(kubeconfig_file):
            return f"Erreur: Fichier de configuration '{kubeconfig_file}' introuvable."

        config.load_kube_config(config_file=kubeconfig_file)
        v1 = client.CoreV1Api()

        output = "Pods:\n"
        if namespace:
            pod_list = v1.list_namespaced_pod(namespace, timeout_seconds=10)
        else:
            pod_list = v1.list_pod_for_all_namespaces(timeout_seconds=10)

        for pod in pod_list.items:
            output += f"- Namespace: {pod.metadata.namespace}, Nom: {pod.metadata.name}, Statut: {pod.status.phase}\n"

        if not pod_list.items:
            return f"Aucun pod trouvé dans le namespace '{namespace}'." if namespace else "Aucun pod trouvé."

        return output

    except ApiException as e:
        if e.status == 404:
            return f"Erreur: Le namespace '{namespace}' n'existe pas."
        return f"Erreur API Kubernetes ({e.status}): {e.reason}"
    except Exception as e:
        return f"Une erreur inattendue est survenue: {e}"

def describe_kubernetes_pod(name: str, namespace: str) -> str:
    """
    Donne des informations détaillées sur un pod spécifique dans un namespace donné,
    y compris son statut, son IP, et le nœud sur lequel il s'exécute.
    """
    try:
        kubeconfig_file = get_kubeconfig_path()
        if not os.path.exists(kubeconfig_file):
            return f"Erreur: Fichier de configuration '{kubeconfig_file}' introuvable."

        config.load_kube_config(config_file=kubeconfig_file)
        v1 = client.CoreV1Api()
        pod = v1.read_namespaced_pod(name=name, namespace=namespace, _request_timeout=10)

        output = f"Détails du Pod '{name}' dans le namespace '{namespace}':\n"
        output += f"  - Nœud: {pod.spec.node_name}\n"
        output += f"  - IP du Pod: {pod.status.pod_ip}\n"
        output += f"  - Statut: {pod.status.phase}\n"
        output += "  - Conteneurs:\n"
        for container in pod.spec.containers:
            output += f"    - {container.name} (Image: {container.image})\n"

        return output

    except ApiException as e:
        if e.status == 404:
            return f"Erreur: Le pod '{name}' n'a pas été trouvé dans le namespace '{namespace}'."
        return f"Erreur API Kubernetes ({e.status}): {e.reason}"
    except Exception as e:
        return f"Une erreur inattendue est survenue: {e}"
