import yaml
from kubernetes import utils
from ..router import register_handler
from ..config import k8s_clients

def _generate_manifest(application_name: str, image: str, replicas: int, port: int) -> str:
    """Internal function to generate a deployment manifest."""
    return f"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {application_name}
  labels:
    app: {application_name}
spec:
  replicas: {replicas}
  selector:
    matchLabels:
      app: {application_name}
  template:
    metadata:
      labels:
        app: {application_name}
    spec:
      containers:
      - name: {application_name}
        image: {image}
        ports:
        - containerPort: {port}
""".strip()

@register_handler('deploy', 'application')
def deploy_application(
    application_name: str,
    image: str,
    replicas: int = 1,
    port: int = 80,
    **kwargs
):
    """
    Deploys an application by generating a standard manifest and applying it.
    This is a high-level tool for simple deployments.
    """
    manifest = _generate_manifest(application_name, image, replicas, port)

    if not k8s_clients.v1:
        return f"Erreur: Le client Kubernetes n'est pas initialisé. {k8s_clients.error}"

    api_client = k8s_clients.v1.api_client

    try:
        utils.create_from_yaml(api_client, yaml_objects=yaml.safe_load_all(manifest))
        return f"Application '{application_name}' déployée avec succès."
    except utils.FailToCreateError as e:
        return f"Erreur lors du déploiement de '{application_name}': {e}"
    except Exception as e:
        return f"Une erreur inattendue est survenue: {e}"
