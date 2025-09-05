from ..router import register_handler

@register_handler('get', 'nodes')
def get_nodes(v1, **kwargs):
    items = v1.list_node().items
    output = "Nœuds:\n"
    for item in items:
        status = next((c.status for c in item.status.conditions if c.type == 'Ready'), 'Inconnu')
        output += f"- {item.metadata.name} (Statut: {'Prêt' if status == 'True' else 'Non Prêt'})\n"
    return output

@register_handler('get', 'namespaces')
def get_namespaces(v1, **kwargs):
    """Liste tous les namespaces disponibles dans le cluster. Ne prend aucun argument."""
    items = v1.list_namespace().items
    output = "Namespaces:\n"
    for item in items:
        output += f"- {item.metadata.name} (Statut: {item.status.phase})\n"
    return output

@register_handler('check', 'health')
def check_cluster_health(v1, apps_v1, **kwargs):
    """Effectue un bilan de santé du cluster en recherchant les problèmes courants."""
    problems = []

    try:
        pods = v1.list_pod_for_all_namespaces().items
        for pod in pods:
            pod_status = getattr(pod, 'status', None)
            pod_phase = getattr(pod_status, 'phase', 'Inconnu')

            if pod_phase not in ['Running', 'Succeeded']:
                problems.append(
                    f"- Pod '{pod.metadata.name}' (NS: {pod.metadata.namespace}) est en état '{pod_phase}'."
                )
    except Exception as e:
        problems.append(f"- Impossible de vérifier l'état des pods: {e}")

    try:
        deployments = apps_v1.list_deployment_for_all_namespaces().items
        for dep in deployments:
            desired = getattr(dep.spec, 'replicas', 0)
            available = getattr(getattr(dep, 'status', None), 'available_replicas', 0)

            if desired > available:
                problems.append(
                    f"- Déploiement '{dep.metadata.name}' (NS: {dep.metadata.namespace}) a seulement {available}/{desired} réplicas disponibles."
                )
    except Exception as e:
        problems.append(f"- Impossible de vérifier l'état des déploiements: {e}")

    if not problems:
        return "Le bilan de santé du cluster n'a révélé aucune anomalie."

    return "Bilan de santé du cluster:\n" + "\n".join(problems)
