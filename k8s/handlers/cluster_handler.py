def get_nodes(v1, **kwargs):
    items = v1.list_node().items
    output = "Nœuds:\n"
    for item in items:
        status = next((c.status for c in item.status.conditions if c.type == 'Ready'), 'Inconnu')
        output += f"- {item.metadata.name} (Statut: {'Prêt' if status == 'True' else 'Non Prêt'})\n"
    return output

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
