import datetime
import pytz
from kubernetes import client
from kubernetes.client import ApiClient
from ..router import register_handler

@register_handler('get', 'deployments')
def get_deployments(apps_v1, namespace=None, **kwargs):
    """List deployments in a specific namespace or in all namespaces."""
    if namespace:
        items = apps_v1.list_namespaced_deployment(namespace).items
    else:
        items = apps_v1.list_deployment_for_all_namespaces().items

    output = "Déploiements:\n"
    for item in items:
        ready = item.status.ready_replicas or 0
        total = item.spec.replicas
        output += f"- NS: {item.metadata.namespace}, Nom: {item.metadata.name}, Prêts: {ready}/{total}\n"

    return output if items else "Aucun déploiement trouvé."

@register_handler('history', 'deployments')
def get_deployment_history(apps_v1, name, namespace, **kwargs):
    """Get the rollout history of a deployment."""
    try:
        deployment = apps_v1.read_namespaced_deployment(name=name, namespace=namespace)
    except client.ApiException as e:
        if e.status == 404:
            return f"Error: Deployment '{name}' not found in namespace '{namespace}'."
        raise

    all_replicasets = apps_v1.list_namespaced_replica_set(namespace=namespace).items
    owned_replicasets = []
    for rs in all_replicasets:
        if rs.metadata.owner_references:
            for owner in rs.metadata.owner_references:
                if owner.uid == deployment.metadata.uid:
                    owned_replicasets.append(rs)
                    break

    if not owned_replicasets:
        return f"No rollout history found for deployment '{name}'."

    revisions = {}
    for rs in owned_replicasets:
        revision = rs.metadata.annotations.get('deployment.kubernetes.io/revision')
        if revision:
            change_cause = rs.metadata.annotations.get('kubernetes.io/change-cause', '<none>')
            revisions[int(revision)] = change_cause

    if not revisions:
        return f"No rollout history found for deployment '{name}'."

    output = f"Historique des déploiements pour '{name}':\n"
    output += "REVISION  CHANGE-CAUSE\n"
    for rev in sorted(revisions.keys()):
        output += f"{rev:<9} {revisions[rev]}\n"

    return output

@register_handler('describe', 'deployments')
def describe_deployment(apps_v1, name, namespace, **kwargs):
    dep = apps_v1.read_namespaced_deployment(name=name, namespace=namespace)
    output = f"Détails du Déploiement '{name}' (NS: {namespace}):\n"
    output += f"  - Replicas: {dep.status.replicas or 0} désirés | {dep.status.ready_replicas or 0} prêts\n"
    restarted_at = dep.spec.template.metadata.annotations.get('kubectl.kubernetes.io/restartedAt') if dep.spec.template.metadata.annotations else None
    if restarted_at:
        output += f"  - Redémarré le: {restarted_at}\n"
    return output

@register_handler('restart', 'deployments')
def restart_deployment(apps_v1, name, namespace, **kwargs):
    restarted_at = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC).isoformat()
    body = {"spec": {"template": {"metadata": {"annotations": {"kubectl.kubernetes.io/restartedAt": restarted_at}}}}}
    apps_v1.patch_namespaced_deployment(name=name, namespace=namespace, body=body)
    return f"Le redémarrage du déploiement '{name}' a été initié."

@register_handler('scale', 'deployments')
def scale_deployment(apps_v1, name, namespace, replicas, **kwargs):
    replica_count = int(replicas)
    scale_body = client.V1Scale(
        metadata=client.V1ObjectMeta(name=name, namespace=namespace),
        spec=client.V1ScaleSpec(replicas=replica_count)
    )
    apps_v1.patch_namespaced_deployment_scale(name=name, namespace=namespace, body=scale_body)
    return f"Le déploiement '{name}' a été mis à l'échelle à {replica_count} réplicas."

@register_handler('undo', 'deployments')
def undo_deployment_rollout(apps_v1, name, namespace, **kwargs):
    """Annule le dernier déploiement (rollout) pour revenir à la version précédente."""
    all_replicasets = apps_v1.list_namespaced_replica_set(namespace=namespace).items

    owned_replicasets = []
    deployment_uid = apps_v1.read_namespaced_deployment(name=name, namespace=namespace).metadata.uid
    for rs in all_replicasets:
        if rs.metadata.owner_references:
            for owner in rs.metadata.owner_references:
                if owner.uid == deployment_uid:
                    owned_replicasets.append(rs)
                    break

    revisions = {}
    for rs in owned_replicasets:
        revision = rs.metadata.annotations.get('deployment.kubernetes.io/revision')
        if revision:
            revisions[int(revision)] = rs

    if len(revisions) < 2:
        return f"Erreur: Pas d'historique de révision suffisant pour annuler le déploiement '{name}'. Une action 'undo' n'est possible qu'après un changement d'image, pas après un 'scale'."

    sorted_revisions = sorted(revisions.keys(), reverse=True)
    previous_revision_number = sorted_revisions[1]
    previous_replicaset = revisions[previous_revision_number]

    api_client = client.ApiClient()
    template_dict = api_client.sanitize_for_serialization(previous_replicaset.spec.template)
    patch_body = {"spec": {"template": template_dict}}

    apps_v1.patch_namespaced_deployment(name=name, namespace=namespace, body=patch_body)
    return f"Le rollback du déploiement '{name}' vers la révision {previous_revision_number} a été initié."
