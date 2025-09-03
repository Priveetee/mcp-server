from dotenv import load_dotenv
from agent import Agent

def main():
    load_dotenv()

    try:
        mcp_agent = Agent()
    except RuntimeError as e:
        print(e)
        return

    print("MCP Core Initialisé. Tapez 'help' ou 'exit'.")

    while True:
        try:
            user_input = input("MCP> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nArrêt.")
            break

        if not user_input:
            continue

        if user_input.lower() == 'exit':
            print("Arrêt.")
            break

        if user_input.lower() == 'help':
            print("Commandes: 'exit', 'help'.")
            print("Exemples: 'quel est le statut des nœuds ?', 'liste les pods dans kube-system', 'décris le pod coredns'")
            continue

        response_text = mcp_agent.execute_turn(user_input)
        print(response_text)

if __name__ == "__main__":
    main()
