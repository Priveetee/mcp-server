# agent.py

import google.genai as genai
from google.genai import types
from k8s import client as k8s_client

# The System Prompt to define the agent's mission and behavior.
SYSTEM_PROMPT = """
You are MCP, an intelligent Kubernetes copilot. Your primary mission is to assist the user in managing their cluster by being proactive and resourceful.

Follow these core principles:
1.  **Observe First, Ask Later**: If you lack information to fulfill a request (e.g., a resource name, a namespace), your first step is to use your tools to find it. For example, use the 'get' verb on 'deployments' or 'pods' across all namespaces. Only ask the user for clarification if you cannot find the information yourself.
2.  **Reason Step-by-Step**: If a user's request is ambiguous, break it down. If a command fails, analyze the error and suggest a correction. Don't just report failure.
3.  **Be a Copilot, Not a Machine**: You have a memory. Use the conversation history to inform your actions. If the user mentions a resource, remember its context (like its namespace). Do not ask for the same information repeatedly.
4.  **Confirm Dangerous Actions**: Before executing any action that modifies the state of the cluster (like 'scale', 'restart', 'undo', 'apply', 'delete'), always state your plan and ask for confirmation.
"""

def extract_text_from_response(response):
    """Extracts text from a Gemini API response."""
    if not response.candidates or not response.candidates[0].content.parts:
        return ""
    return ''.join(part.text for part in response.candidates[0].content.parts if hasattr(part, 'text'))

class Agent:
    DANGEROUS_VERBS = {'restart', 'scale', 'undo', 'apply', 'delete'}

    def __init__(self, model_name='gemini-1.5-flash-latest'):
        try:
            self.client = genai.Client()
        except Exception as e:
            raise RuntimeError(f"Impossible d'initialiser le client Google GenAI: {e}")

        self.model_name = model_name
        self.available_tools = [k8s_client.kubernetes_tool]
        self.tool_config = types.GenerateContentConfig(tools=self.available_tools)

        # Initialize the chat history with the system prompt.
        self.chat_history = [
            types.Content(role="user", parts=[types.Part.from_text(text=SYSTEM_PROMPT)]),
            types.Content(role="model", parts=[types.Part.from_text(text="Understood. I am MCP, the Kubernetes copilot. I am ready to assist.")])
        ]
        self.pending_action = None

    def execute_turn(self, user_input: str) -> str:
        if self.pending_action:
            action_to_execute = self.pending_action
            self.pending_action = None
            if user_input.lower() in ['oui', 'yes', 'y']:
                return k8s_client.kubernetes_tool(**action_to_execute)
            else:
                return "Action annulée."

        try:
            contents_for_api = self.chat_history + [types.Content(role="user", parts=[types.Part.from_text(text=user_input)])]

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents_for_api,
                config=self.tool_config,
            )

            if response.function_calls:
                fc = response.function_calls[0]
                action_details = {k: v for k, v in fc.args.items()}

                if action_details.get('verb') in self.DANGEROUS_VERBS:
                    self.pending_action = action_details
                    self.chat_history.append(contents_for_api[-1])
                    # We don't add the function call to history until it's confirmed
                    return f"Confirmez-vous l'action : {action_details.get('verb')} {action_details.get('resource')} '{action_details.get('name')}' ? (oui/non)"
                else:
                    # For safe actions, execute immediately
                    result = k8s_client.kubernetes_tool(**action_details)
                    # Here, you might want to send the result back to the model for a more natural response
                    # For now, we just return the direct result.
                    return result

            response_text = extract_text_from_response(response)
            self.chat_history.append(contents_for_api[-1])
            self.chat_history.append(response.candidates[0].content)
            return response_text

        except Exception as e:
            return f"Erreur: La communication avec l'API Gemini a échoué: {e}"
