import datetime
import pytz
from kubernetes import client

def get_deployments(apps_v1, namespace=None, **kwargs):
    items = apps_v1.list_deployment_for_all_namespaces().items if not namespace else apps_v1.list_namespaced_deployment(namespace).items
    output = "Déploiements:\n"
    for item in items:
        ready = item.status.ready_replicas or 0
        total = item.spec.replicas
        output += f"- NS: {item.metadata.namespace}, Nom: {item.metadata.name}, Prêts: {ready}/{total}\n"
    return output if items else "Aucun déploiement trouvé."

def describe_deployment(apps_v1, name, namespace, **kwargs):
    dep = apps_v1.read_namespaced_deployment(name=name, namespace=namespace)
    output = f"Détails du Déploiement '{name}' (NS: {namespace}):\n"
    output += f"  - Replicas: {dep.status.replicas or 0} désirés | {dep.status.ready_replicas or 0} prêts\n"
    restarted_at = dep.spec.template.metadata.annotations.get('kubectl.kubernetes.io/restartedAt') if dep.spec.template.metadata.annotations else None
    if restarted_at:
        output += f"  - Redémarré le: {restarted_at}\n"
    return output

def restart_deployment(apps_v1, name, namespace, **kwargs):
    restarted_at = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC).isoformat()
    body = {"spec": {"template": {"metadata": {"annotations": {"kubectl.kubernetes.io/restartedAt": restarted_at}}}}}
    apps_v1.patch_namespaced_deployment(name=name, namespace=namespace, body=body)
    return f"Le redémarrage du déploiement '{name}' a été initié."

def scale_deployment(apps_v1, name, namespace, replicas, **kwargs):
    """Met à l'échelle un déploiement à un nombre spécifique de réplicas."""
    try:
        replica_count = int(replicas)
    except (ValueError, TypeError):
        return f"Erreur: Le nombre de réplicas '{replicas}' n'est pas un entier valide."

    scale_body = client.V1Scale(
        metadata=client.V1ObjectMeta(name=name, namespace=namespace),
        spec=client.V1ScaleSpec(replicas=replica_count)
    )

    apps_v1.patch_namespaced_deployment_scale(
        name=name,
        namespace=namespace,
        body=scale_body
    )
    return f"Le déploiement '{name}' a été mis à l'échelle à {replica_count} réplicas."

def undo_deployment_rollout(apps_v1, name, namespace, **kwargs):
    """Annule le dernier déploiement (rollout) pour revenir à la version précédente."""
    all_replicasets = apps_v1.list_namespaced_replica_set(namespace=namespace, label_selector=f"app={name}")

    revisions = {}
    for rs in all_replicasets.items:
        revision = rs.metadata.annotations.get('deployment.kubernetes.io/revision')
        if revision:
            revisions[int(revision)] = rs

    if len(revisions) < 2:
        return f"Erreur: Pas d'historique de révision trouvé pour le déploiement '{name}'."

    sorted_revisions = sorted(revisions.keys(), reverse=True)
    previous_revision_number = sorted_revisions[1]
    previous_replicaset = revisions[previous_revision_number]

    patch_body = {"spec": {"template": previous_replicaset.spec.template}}

    apps_v1.patch_namespaced_deployment(name=name, namespace=namespace, body=patch_body)
    return f"Le rollback du déploiement '{name}' vers la révision {previous_revision_number} a été initié."
