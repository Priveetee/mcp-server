# MCP Server – Agent Conversationnel Kubernetes

## Description

MCP Server est un assistant conversationnel pour Kubernetes (K3s/K8s), propulsé par le modèle Gemini 2.5 Pro. Il permet de discuter en langage naturel avec votre cluster pour :
*   **Déployer** de nouvelles applications simplement.
*   **Consulter** l'état des ressources (nœuds, pods, déploiements, namespaces).
*   **Inspecter** en profondeur avec les descriptions, les logs et l'historique des déploiements.
*   **Gérer** le cycle de vie des applications (mise à l'échelle, redémarrage, retour en arrière).
*   **Diagnostiquer** l'état général du cluster.

Toutes les actions modifiant le cluster sont sécurisées par une demande de confirmation.

## Prérequis

*   **Python 3.10+**
*   Un **cluster Kubernetes** (K3s/K8s) accessible.
*   Un fichier **kubeconfig** valide.
*   Une **clé API Gemini**.

## Installation

1.  **Créez et activez un environnement virtuel :**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

2.  **Installez les dépendances :**
    ```bash
    pip install --upgrade pip
    pip install -r requirements.txt
    ```

3.  **Configurez votre kubeconfig :**
    Copiez votre fichier `kubeconfig` dans le répertoire du projet et renommez-le `k3s.yaml`.
    ```bash
    # Exemple
    cp ~/.kube/config ./k3s.yaml
    ```
    *(Alternativement, définissez la variable d'environnement `KUBECONFIG`.)*

4.  **Définissez votre clé API Gemini :**
    ```bash
    export GOOGLE_API_KEY="VOTRE_CLE_API_GEMINI"
    ```
    *(Pour une persistance, ajoutez cette ligne à votre `.bashrc` ou `.zshrc`.)*

## Lancement

Une fois la configuration terminée, démarrez l'agent :
```bash
python3 mcp_core.py
```

## Commandes et Exemples

Voici une liste complète des actions que vous pouvez demander au MCP.

### Déploiement d'Applications

Le MCP peut déployer une nouvelle application en utilisant une image de conteneur.

*   **Déployer une nouvelle application :**
    > `déploie une application nginx nommée 'webapp' avec 2 réplicas`

### Consultation et Inspection (Actions non-modifiantes)

*   **Lister les ressources (dans tous les namespaces) :**
    > `liste les pods`
    > `montre-moi tous les déploiements`

*   **Lister les ressources (dans un namespace spécifique) :**
    > `liste les pods dans kube-system`

*   **Lister les ressources du cluster :**
    > `quels sont les nœuds ?`
    > `liste les namespaces`

*   **Obtenir des détails sur une ressource :**
    > `décris le déploiement traefik dans kube-system`
    > `donne-moi les détails du pod coredns-xyz`

*   **Consulter les logs d'un pod :**
    > `montre les logs du pod coredns-xyz dans kube-system`

*   **Consulter l'historique d'un déploiement :**
    > `quel est l'historique du déploiement coredns ?`

*   **Effectuer un bilan de santé :**
    > `fais un bilan de santé du cluster`

### Gestion des Applications (Actions modifiantes, avec confirmation)

*   **Mettre à l'échelle un déploiement :**
    > `scale le déploiement coredns à 3 réplicas dans kube-system`

*   **Redémarrer un déploiement :**
    > `redémarre le déploiement traefik`

*   **Annuler le dernier changement d'un déploiement :**
    > `annule le déploiement coredns dans kube-system`

### Aide et Sortie

*   **Afficher l'aide :**
    > `help`

*   **Quitter le programme :**
    > `exit`
