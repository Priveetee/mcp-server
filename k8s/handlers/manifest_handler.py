import yaml
from kubernetes import utils
from ..router import register_handler
from ..config import k8s_clients

@register_handler('apply', 'manifest')
def apply_manifest(manifest: str, **kwargs):
    """
    Applies a Kubernetes manifest from a YAML string.
    This function can handle multi-document YAML strings.
    """
    # Robustness check: Ensure the k8s client is available.
    if not k8s_clients.v1:
        return f"Erreur: Le client Kubernetes (CoreV1Api) n'est pas initialisé. {k8s_clients.error}"

    api_client = k8s_clients.v1.api_client

    try:
        yaml_objects = yaml.safe_load_all(manifest)
        valid_objects = [obj for obj in yaml_objects if obj is not None]

        if not valid_objects:
            return "Erreur: Le manifeste YAML est vide ou invalide."

        created_resources = []
        for doc in valid_objects:
            utils.create_from_dict(api_client, doc, verbose=False)
            kind = doc.get('kind', 'Resource')
            name = doc.get('metadata', {}).get('name', 'unnamed')
            created_resources.append(f"{kind}/{name}")

        return f"Manifeste appliqué avec succès. Ressources créées/mises à jour : {', '.join(created_resources)}."

    except yaml.YAMLError as e:
        return f"Erreur de parsing YAML: {e}"
    except utils.FailToCreateError as e:
        return f"Erreur lors de l'application du manifeste: {e}"
    except Exception as e:
        return f"Une erreur inattendue est survenue lors de l'application du manifeste: {e}"
