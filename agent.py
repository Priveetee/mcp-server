import google.genai as genai
from google.genai import types
from k8s import client as k8s_client

SYSTEM_PROMPT = """
You are MCP, an intelligent and versatile Kubernetes copilot. Your mission is to assist the user by using the tools at your disposal to answer questions and execute tasks.

**Your Core Principles:**
1.  **Consult Your Tool's Documentation**: Before answering, always refer to the `docstring` of the `kubernetes_tool` to understand the full range of your capabilities (verbs and resources). Do not assume limitations.
2.  **Be Proactive**: If the user's request is ambiguous, use your 'get' capabilities to list resources and help them clarify.
3.  **Plan Complex Tasks**: For broad requests like "give me a full report", break it down into a sequence of tool calls and execute them.
4.  **Confirm Dangerous Actions**: Always ask for confirmation before executing any modifying action, including 'deploy', 'scale', 'restart', and 'undo'.
"""

def extract_text_from_response(response):
    """Safely extracts text from a Gemini API response."""
    if response and response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
        return ''.join(part.text for part in response.candidates[0].content.parts if hasattr(part, 'text'))
    return ""

class Agent:
    DANGEROUS_VERBS = {'restart', 'scale', 'undo', 'apply', 'delete', 'deploy'}

    def __init__(self, model_name='gemini-2.5-pro'):
        try:
            self.client = genai.Client()
        except Exception as e:
            raise RuntimeError(f"Impossible d'initialiser le client Google GenAI: {e}")

        self.model_name = model_name
        self.available_tools = [k8s_client.kubernetes_tool]
        self.tool_config = types.GenerateContentConfig(tools=self.available_tools)

        self.chat_history = [
            types.Content(role="user", parts=[types.Part.from_text(text=SYSTEM_PROMPT)]),
            types.Content(role="model", parts=[types.Part.from_text(text="Understood. I am a versatile Kubernetes copilot. I will consult my tool's documentation for every task and always ask for confirmation for dangerous actions. I am ready.")])
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

                if not response.candidates: return "Le modèle n'a pas fourni de réponse valide."
                candidate = response.candidates[0]
                if not candidate.content or not candidate.content.parts:
                    if candidate.content: self.chat_history.append(candidate.content)
                    return "Action terminée."

                part = candidate.content.parts[0]
                fc = getattr(part, 'function_call', None)

                if fc:
                    self.chat_history.append(candidate.content)
                    action_details = {k: v for k, v in fc.args.items()} if fc.args else {}

                    if action_details.get('verb') in self.DANGEROUS_VERBS:
                        self.pending_action = action_details
                        resource_name = action_details.get('application_name') or action_details.get('name')
                        return f"Confirmez-vous l'action : {action_details.get('verb')} {resource_name} ? (oui/non)"

                    tool_result = k8s_client.kubernetes_tool(**action_details)
                    self.chat_history.append(types.Content(role="model", parts=[
                        types.Part.from_function_response(name="kubernetes_tool", response={"result": tool_result})
                    ]))
                else:
                    response_text = extract_text_from_response(response)
                    self.chat_history.append(candidate.content)
                    return response_text
        except Exception as e:
            return f"Une erreur inattendue est survenue: {e}"
