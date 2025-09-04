import google.genai as genai
from google.genai import types
import k8s_tools

def extract_text_from_response(response):
    text_parts = []
    for part in response.candidates[0].content.parts:
        if hasattr(part, 'text') and part.text:
            text_parts.append(part.text)
    return ''.join(text_parts)

class Agent:
    def __init__(self, model_name='gemini-2.5-flash'):
        try:
            self.client = genai.Client()
        except Exception as e:
            raise RuntimeError(f"Impossible d'initialiser le client Google GenAI: {e}")

        self.model_name = model_name
        self.available_tools = [
            k8s_tools.kubernetes_tool
        ]
        self.tool_config = types.GenerateContentConfig(tools=self.available_tools)
        self.chat_history = []

    def execute_turn(self, user_input: str) -> str:
        try:
            contents_for_api = self.chat_history + [types.Content(role="user", parts=[types.Part.from_text(text=user_input)])]

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents_for_api,
                config=self.tool_config,
            )

            response_text = extract_text_from_response(response)

            self.chat_history.append(contents_for_api[-1])
            self.chat_history.append(response.candidates[0].content)

            return response_text

        except Exception as e:
            return f"Erreur: La communication avec l'API Gemini a échoué: {e}"
