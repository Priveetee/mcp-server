import os
from typing import Optional
from kubernetes import client, config

class K8sClientManager:
    _instance = None

    v1: Optional[client.CoreV1Api]
    apps_v1: Optional[client.AppsV1Api]
    error: Optional[Exception]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # Empêche la ré-initialisation
        if hasattr(self, '_initialized'):
            return
        self._initialized = True

        self.v1 = None
        self.apps_v1 = None
        self.error = None

        try:
            kubeconfig_file = os.getenv('KUBECONFIG', 'k3s.yaml')
            if not os.path.exists(kubeconfig_file):
                raise FileNotFoundError(f"Fichier de configuration '{kubeconfig_file}' introuvable.")

            config.load_kube_config(config_file=kubeconfig_file)
            self.v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()

        except Exception as e:
            self.error = e

k8s_clients = K8sClientManager()
