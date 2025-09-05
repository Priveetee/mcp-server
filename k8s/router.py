HANDLER_REGISTRY = {}

def register_handler(verb, resource):
    """A decorator to register a handler function for a specific verb and resource."""
    def decorator(func):
        HANDLER_REGISTRY[(verb, resource)] = func
        return func
    return decorator

def dispatch(verb, resource, **kwargs):
    """Finds and executes the appropriate handler from the registry."""
    v1 = kwargs.pop('v1', None)
    apps_v1 = kwargs.pop('apps_v1', None)

    handler_kwargs = {k: v for k, v in kwargs.items() if v is not None}

    if v1:
        handler_kwargs['v1'] = v1
    if apps_v1:
        handler_kwargs['apps_v1'] = apps_v1

    handler = HANDLER_REGISTRY.get((verb, resource))
    if handler:
        return handler(**handler_kwargs)
    else:
        return f"Erreur: Combinaison non supportée: {verb} {resource}."
