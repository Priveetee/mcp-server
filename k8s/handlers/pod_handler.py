from ..router import register_handler

@register_handler('get', 'pods')
def get_pods(v1, namespace=None, **kwargs):
    items = v1.list_pod_for_all_namespaces().items if not namespace else v1.list_namespaced_pod(namespace).items
    output = "Pods:\n"
    for item in items:
        ready = sum(1 for s in item.status.container_statuses if s.ready) if item.status.container_statuses else 0
        total = len(item.spec.containers)
        restarts = sum(s.restart_count for s in item.status.container_statuses) if item.status.container_statuses else 0
        output += f"- NS: {item.metadata.namespace}, Nom: {item.metadata.name}, Prêts: {ready}/{total}, Statut: {item.status.phase}, Redémarrages: {restarts}\n"
    return output if items else "Aucun pod trouvé."

@register_handler('describe', 'pods')
def describe_pod(v1, name, namespace, **kwargs):
    pod = v1.read_namespaced_pod(name=name, namespace=namespace)
    output = f"Détails du Pod '{name}' (NS: {namespace}):\n"
    output += f"  - Nœud: {pod.spec.node_name}\n  - IP: {pod.status.pod_ip}\n  - Statut: {pod.status.phase}\n"
    output += "  - Conteneurs:\n"
    for c in pod.spec.containers:
        output += f"    - {c.name} (Image: {c.image})\n"
    return output

@register_handler('logs', 'pods')
def get_pod_logs(v1, name, namespace, **kwargs):
    container_name = v1.read_namespaced_pod(name=name, namespace=namespace).spec.containers[0].name
    logs = v1.read_namespaced_pod_log(name=name, namespace=namespace, container=container_name, tail_lines=50)
    output = f"Logs pour le pod '{name}' (conteneur: {container_name}):\n"
    output += "--------------------------------------------------\n"
    output += logs + "\n--------------------------------------------------"
    return output
