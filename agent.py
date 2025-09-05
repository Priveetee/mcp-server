# agent.py

import google.genai as genai
from google.genai import types
from k8s import client as k8s_client

SYSTEM_PROMPT = """
You are MCP, an intelligent Kubernetes copilot. Your primary mission is to assist the user in managing their cluster by being proactive and resourceful.

Follow these core principles:
1.  **Observe First, Ask Later**: If you lack information, use your tools to find it before asking the user.
2.  **Reason Step-by-Step**: For complex requests like "give me a full report", break it down into a sequence of tool calls. Execute them one by one until the full request is complete. Do not just present the plan; execute it.
3.  **Be a Copilot, Not a Machine**: Use the conversation history to inform your actions. Do not ask for the same information repeatedly.
4.  **Confirm Dangerous Actions**: Before executing any modifying action ('scale', 'restart', 'undo', 'apply', 'delete'), state your plan and ask for confirmation.
"""

def extract_text_from_response(response):
    """Safely extracts text from a Gemini API response."""
    if response and response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
        return ''.join(part.text for part in response.candidates[0].content.parts if hasattr(part, 'text'))
    return ""

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

        self.chat_history = [
            types.Content(role="user", parts=[types.Part.from_text(text=SYSTEM_PROMPT)]),
            types.Content(role="model", parts=[types.Part.from_text(text="Understood. I am MCP, the Kubernetes copilot. I am ready to assist.")])
        ]
        self.pending_action = None

    def execute_turn(self, user_input: str) -> str:
        if self.pending_action:
            action_to_execute = self.pending_action
            self.pending_action = None
            if user_input.lower() not in ['oui', 'yes', 'y']:
                return "Action annulée."

            tool_result = k8s_client.kubernetes_tool(**action_to_execute)
            self.chat_history.append(types.Content(role="model", parts=[
                types.Part.from_function_response(name="kubernetes_tool", response={"result": tool_result})
            ]))
        else:
            self.chat_history.append(types.Content(role="user", parts=[types.Part.from_text(text=user_input)]))

        try:
            while True:
                response = self.client.models.generate_content(
                    model=self.model_name, contents=self.chat_history, config=self.tool_config
                )

                if not response.candidates:
                    return "Le modèle n'a pas fourni de réponse valide."

                candidate = response.candidates[0]

                # If the model has nothing to say (e.g. safety block), stop.
                if not candidate.content or not candidate.content.parts:
                    return "Action terminée."

                # Check for a function call
                if hasattr(candidate.content.parts[0], 'function_call'):
                    fc = candidate.content.parts[0].function_call
                    self.chat_history.append(candidate.content)

                    action_details = {k: v for k, v in fc.args.items()} if fc.args else {}

                    if action_details.get('verb') in self.DANGEROUS_VERBS:
                        self.pending_action = action_details
                        return f"Confirmez-vous l'action : {action_details.get('verb')} {action_details.get('resource')} '{action_details.get('name')}' ? (oui/non)"

                    tool_result = k8s_client.kubernetes_tool(**action_details)
                    self.chat_history.append(types.Content(role="model", parts=[
                        types.Part.from_function_response(name="kubernetes_tool", response={"result": tool_result})
                    ]))
                    # Continue the loop to let the model process the tool result
                else:
                    # No function call, it's a final text response
                    response_text = extract_text_from_response(response)
                    self.chat_history.append(candidate.content)
                    return response_text
        except Exception as e:
            return f"Une erreur inattendue est survenue: {e}"
