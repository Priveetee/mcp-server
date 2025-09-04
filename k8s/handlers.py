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
        ready_containers = sum(1 for s in item.status.container_statuses if s.ready) if item.status.container_statuses else 0
        total_containers = len(item.spec.containers)
        restarts = sum(s.restart_count for s in item.status.container_statuses) if item.status.container_statuses else 0
        output += (f"- NS: {item.metadata.namespace}, Nom: {item.metadata.name}, "
                   f"Prêts: {ready_containers}/{total_containers}, Statut: {item.status.phase}, "
                   f"Redémarrages: {restarts}\n")
    return output if items else "Aucun pod trouvé."

def get_deployments(apps_v1, namespace=None, **kwargs):
    items = apps_v1.list_deployment_for_all_namespaces().items if not namespace else apps_v1.list_namespaced_deployment(namespace).items
    output = "Déploiements:\n"
    for item in items:
        ready_replicas = item.status.ready_replicas or 0
        total_replicas = item.spec.replicas
        output += (f"- NS: {item.metadata.namespace}, Nom: {item.metadata.name}, "
                   f"Prêts: {ready_replicas}/{total_replicas}\n")
    return output if items else "Aucun déploiement trouvé."

def get_services(v1, namespace=None, **kwargs):
    items = v1.list_service_for_all_namespaces().items if not namespace else v1.list_namespaced_service(namespace).items
    output = "Services:\n"
    for item in items:
        output += (f"- NS: {item.metadata.namespace}, Nom: {item.metadata.name}, "
                   f"Type: {item.spec.type}, IP: {item.spec.cluster_ip}\n")
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
    deployment = apps_v1.read_namespaced_deployment(name=name, namespace=namespace)
    spec = deployment.spec
    status = deployment.status

    output = f"Détails du Déploiement '{name}' (NS: {namespace}):\n"
    output += f"  - Replicas: {status.replicas or 0} désirés | {status.updated_replicas or 0} à jour | {status.ready_replicas or 0} prêts | {status.available_replicas or 0} disponibles\n"
    output += f"  - Stratégie: {spec.strategy.type}\n"

    annotations = spec.template.metadata.annotations
    restarted_at = annotations.get('kubectl.kubernetes.io/restartedAt') if annotations else None
    if restarted_at:
        output += f"  - Redémarré le: {restarted_at}\n"

    output += "  - Conteneurs:\n"
    for container in spec.template.spec.containers:
        output += f"    - {container.name} (Image: {container.image})\n"

    return output

# --- Handlers pour les verbes d'ACTION ---
import datetime
import pytz

def restart_deployment(apps_v1, name, namespace, **kwargs):
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

def scale_deployment(apps_v1, name, namespace, replicas, **kwargs):
    """Met à l'échelle un déploiement à un nombre spécifique de réplicas."""
    try:
        replica_count = int(replicas)
    except (ValueError, TypeError):
        return f"Erreur: Le nombre de réplicas '{replicas}' n'est pas un entier valide."

    scale_body = client.V1Scale(
        spec=client.V1ScaleSpec(replicas=replica_count)
    )

    apps_v1.patch_namespaced_deployment_scale(
        name=name,
        namespace=namespace,
        body=scale_body
    )
    return f"Le déploiement '{name}' dans le namespace '{namespace}' a été mis à l'échelle à {replica_count} réplicas."

# --- Handlers pour le verbe 'LOGS' ---

def get_pod_logs(v1, name, namespace, **kwargs):
    pod = v1.read_namespaced_pod(name=name, namespace=namespace)
    if not pod.spec.containers:
        return f"Erreur: Le pod '{name}' n'a pas de conteneurs."

    container_name = pod.spec.containers[0].name

    logs = v1.read_namespaced_pod_log(
        name=name,
        namespace=namespace,
        container=container_name,
        tail_lines=50
    )

    output = f"Logs pour le pod '{name}' (conteneur: {container_name}):\n"
    output += "--------------------------------------------------\n"
    output += logs
    output += "\n--------------------------------------------------"
    return output
