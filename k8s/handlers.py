import datetime
import pytz
from kubernetes import client

# --- Handlers pour le verbe 'GET' ---

def get_nodes(v1, **kwargs):
    items = v1.list_node().items
    output = "Nœuds:\n"
    for item in items:
        status = next((c.status for c in item.status.conditions if c.type == 'Ready'), 'Inconnu')
        output += f"- {item.metadata.name} (Statut: {'Prêt' if status == 'True' else 'Non Prêt'})\n"
    return output

def get_pods(v1, namespace=None, **kwargs):
    items = v1.list_pod_for_all_namespaces().items if not namespace else v1.list_namespaced_pod(namespace).items
    output = "Pods:\n"
    for item in items:
        output += f"- NS: {item.metadata.namespace}, Nom: {item.metadata.name}, Statut: {item.status.phase}\n"
    return output if items else "Aucun pod trouvé."

def get_deployments(apps_v1, namespace=None, **kwargs):
    items = apps_v1.list_deployment_for_all_namespaces().items if not namespace else apps_v1.list_namespaced_deployment(namespace).items
    output = "Déploiements:\n"
    for item in items:
        output += f"- NS: {item.metadata.namespace}, Nom: {item.metadata.name}, Replicas: {item.status.replicas}\n"
    return output if items else "Aucun déploiement trouvé."

def get_services(v1, namespace=None, **kwargs):
    items = v1.list_service_for_all_namespaces().items if not namespace else v1.list_namespaced_service(namespace).items
    output = "Services:\n"
    for item in items:
        output += f"- NS: {item.metadata.namespace}, Nom: {item.metadata.name}, Type: {item.spec.type}, IP: {item.spec.cluster_ip}\n"
    return output if items else "Aucun service trouvé."

# --- Handlers pour le verbe 'DESCRIBE' ---

def describe_pod(v1, name, namespace, **kwargs):
    pod = v1.read_namespaced_pod(name=name, namespace=namespace)
    output = f"Détails du Pod '{name}' (NS: {namespace}):\n"
    output += f"  - Nœud: {pod.spec.node_name}\n"
    output += f"  - IP: {pod.status.pod_ip}\n"
    output += f"  - Statut: {pod.status.phase}\n"
    output += "  - Conteneurs:\n"
    for container in pod.spec.containers:
        output += f"    - {container.name} (Image: {container.image})\n"
    return output

def describe_deployment(apps_v1, name, namespace, **kwargs):
    """Récupère les détails d'un déploiement spécifique."""
    deployment = apps_v1.read_namespaced_deployment(name=name, namespace=namespace)
    spec = deployment.spec
    status = deployment.status

    output = f"Détails du Déploiement '{name}' (NS: {namespace}):\n"
    output += f"  - Replicas: {status.replicas or 0} désirés | {status.updated_replicas or 0} à jour | {status.ready_replicas or 0} prêts | {status.available_replicas or 0} disponibles\n"
    output += f"  - Stratégie: {spec.strategy.type}\n"

    # On cherche l'annotation de redémarrage
    annotations = spec.template.metadata.annotations
    restarted_at = annotations.get('kubectl.kubernetes.io/restartedAt') if annotations else None
    if restarted_at:
        output += f"  - Redémarré le: {restarted_at}\n"

    output += "  - Conteneurs:\n"
    for container in spec.template.spec.containers:
        output += f"    - {container.name} (Image: {container.image})\n"

    return output


def restart_deployment(apps_v1, name, namespace, **kwargs):
    """Redémarre un déploiement en mettant à jour ses annotations."""
    patch = {
        "spec": {
            "template": {
                "metadata": {
                    "annotations": {
                        "kubectl.kubernetes.io/restartedAt": datetime.datetime.utcnow().replace(tzinfo=pytz.UTC).isoformat()
                    }
                }
            }
        }
    }
    apps_v1.patch_namespaced_deployment(name=name, namespace=namespace, body=patch)
    return f"Le redémarrage du déploiement '{name}' dans le namespace '{namespace}' a été initié."
