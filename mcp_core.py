from dotenv import load_dotenv
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import google.genai as genai
from google.genai import types

def list_kubernetes_nodes() -> str:
    try:
        config.load_kube_config(config_file="k3s.yaml")
        v1 = client.CoreV1Api()
        node_list = v1.list_node()

        output = "Statut des Nœuds:\n"
        for node in node_list.items:
            status = "Inconnu"
            for condition in node.status.conditions:
                if condition.type == "Ready":
                    status = "Prêt" if condition.status == "True" else "Non Prêt"
            output += f"- {node.metadata.name}: {status}\n"
        return output

    except FileNotFoundError:
        return "Erreur: k3s.yaml introuvable. Impossible de se connecter au cluster."
    except ApiException as e:
        return f"Erreur: L'appel à l'API Kubernetes a échoué avec le statut {e.status}: {e.reason}"
    except Exception as e:
        return f"Une erreur inattendue est survenue: {e}"

def extract_text_from_response(response):
    """Extrait seulement le texte de la réponse sans générer de warnings."""
    text_parts = []
    for part in response.candidates[0].content.parts:
        if hasattr(part, 'text') and part.text:
            text_parts.append(part.text)
    return ''.join(text_parts)

def main():
    load_dotenv()

    try:
        client = genai.Client()
    except Exception as e:
        print(f"Erreur: Impossible d'initialiser le client Google GenAI: {e}")
        return

    tools = [list_kubernetes_nodes]
    model_name = 'gemini-2.5-flash'

    tool_config = types.GenerateContentConfig(tools=tools)

    print("MCP Core Initialisé. Tapez 'exit' pour quitter.")

    chat_history = []

    while True:
        try:
            user_input = input("MCP> ")
        except KeyboardInterrupt:
            print("\nArrêt.")
            break
        except EOFError:
            print("\nFin de la session.")
            break

        if user_input.lower() == 'exit':
            print("Arrêt.")
            break

        if not user_input:
            continue

        try:
            contents_for_api = chat_history + [types.Content(role="user", parts=[types.Part.from_text(text=user_input)])]

            response = client.models.generate_content(
                model=model_name,
                contents=contents_for_api,
                config=tool_config,
            )

            # Utiliser notre fonction personnalisée au lieu de response.text
            response_text = extract_text_from_response(response)
            print(response_text)

            chat_history.append(contents_for_api[-1])
            chat_history.append(response.candidates[0].content)

        except Exception as e:
            print(f"Erreur: La communication avec l'API Gemini a échoué: {e}")
            break

if __name__ == "__main__":
    main()
