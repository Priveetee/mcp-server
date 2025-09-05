# k8s/router.py

HANDLER_REGISTRY = {}

def register_handler(verb, resource):
    """A decorator to register a handler function for a specific verb and resource."""
    def decorator(func):
        HANDLER_REGISTRY[(verb, resource)] = func
        return func
    return decorator

def dispatch(verb, resource, **kwargs):
    """Finds and executes the appropriate handler from the registry."""
    handler = HANDLER_REGISTRY.get((verb, resource))
    if handler:
        return handler(**kwargs)
    else:
        return f"Erreur: Combinaison non supportée: {verb} {resource}."

# NO LONGER NEEDED HERE - This was causing the circular dependency.
# from .handlers import cluster_handler, deployment_handler, pod_handler
