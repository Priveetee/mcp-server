# MCP Server – Agent Conversationnel Kubernetes

## Description

MCP Server est un assistant conversationnel pour Kubernetes (K3s/K8s). Il permet de discuter en langage naturel avec votre cluster pour :
*   Consulter l'état des ressources (nœuds, pods, déploiements, services, namespaces).
*   Effectuer des diagnostics (bilans de santé, descriptions détaillées, logs).
*   Gérer des actions (mise à l'échelle, redémarrage, annulation de déploiements), avec demande de confirmation pour la sécurité.

Il est propulsé par le modèle Gemini via le Google Gen AI SDK et la librairie Python officielle de Kubernetes.

## Prérequis

*   **Python 3.10+** (recommandé pour la compatibilité)
*   Un **cluster Kubernetes** (K3s/K8s) accessible depuis votre machine.
*   Un fichier **kubeconfig** valide pour ce cluster.
*   Une **clé API Gemini** (pour le Google Gen AI SDK).

## Installation

Suivez ces étapes dans votre terminal :

1.  **Créez et activez un environnement virtuel :**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```
    *(Si vous utilisez `fish` shell, remplacez `source .venv/bin/activate` par `source .venv/bin/activate.fish`.)*

2.  **Installez les dépendances :**
    ```bash
    pip install --upgrade pip
    pip install -r requirements.txt
    ```

3.  **Configurez votre kubeconfig :**
    Copiez votre fichier kubeconfig (par exemple `~/.kube/config` ou celui de K3s sur votre VM) dans le répertoire `mcp-server` et renommez-le `k3s.yaml`.
    ```bash
    # Exemple si votre kubeconfig est à ~/.kube/config
    cp ~/.kube/config ./k3s.yaml
    ```
    *(Alternativement, vous pouvez définir la variable d'environnement `KUBECONFIG` vers le chemin de votre fichier : `export KUBECONFIG=/chemin/vers/votre/fichier.yaml`.)*

4.  **Définissez votre clé API Gemini :**
    ```bash
    export GOOGLE_API_KEY="VOTRE_CLE_API_GEMINI"
    ```
    *(Remplacez `"VOTRE_CLE_API_GEMINI"` par votre vraie clé API. Pour une persistance entre les sessions, ajoutez cette ligne à votre `.bashrc`, `.zshrc` ou `.config/fish/config.fish`.)*

## Lancement

Une fois l'installation et la configuration terminées, démarrez l'agent :

```bash
python3 mcp_core.py
```

## Utilisation

L'agent MCP est maintenant interactif. Tapez vos commandes en langage naturel.

### Exemples :

*   **Observer l'état :**
    *   `liste les namespaces`
    *   `quels sont les nœuds ?`
    *   `liste les pods dans kube-system`
    *   `décris le déploiement traefik dans kube-system`
    *   `montre les logs du pod coredns-xyz dans kube-system` (remplacez le nom du pod)
    *   `fais un bilan de santé du cluster`

*   **Agir (demande de confirmation) :**
    *   `scale le déploiement coredns à 2 réplicas dans kube-system`
    *   `redémarre le déploiement traefik dans kube-system`
    *   `annule le déploiement coredns dans kube-system` (fonctionne si l'historique de révision est suffisant)

*   **Aide et sortie :**
    *   `help`
    *   `exit`

---
