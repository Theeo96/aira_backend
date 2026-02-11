import os
import json
from openai import AzureOpenAI

# Load env variables
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")

class MemoryService:
    def __init__(self):
        if not AZURE_OPENAI_API_KEY or not AZURE_OPENAI_ENDPOINT:
            print("[Memory] Missing Azure OpenAI Credentials. Summarization disabled.")
            self.client = None
            return

        # Handle full URL in endpoint if present (AzureOpenAI client expects base)
        # But wait, checking .env: https://.../openai/v1/chat/completions
        # The SDK usually takes the base URL. Let's strip the path if needed or pass as is if using azure_endpoint.
        # Ideally, AZURE_OPENAI_ENDPOINT should be just `https://<resource>.openai.azure.com/`
        # I will assume standard format or try to parse.
        
        base_endpoint = AZURE_OPENAI_ENDPOINT
        if "/openai/v1" in base_endpoint:
            base_endpoint = base_endpoint.split("/openai/v1")[0]

        try:
            self.client = AzureOpenAI(
                api_key=AZURE_OPENAI_API_KEY,  
                api_version=AZURE_OPENAI_API_VERSION,
                azure_endpoint=base_endpoint
            )
            print("[Memory] Azure OpenAI Client initialized.")
        except Exception as e:
            print(f"[Memory] Client Init Error: {e}")
            self.client = None

    def summarize(self, transcript):
        if not self.client or not transcript.strip():
            return None

        system_prompt = """
        Summarize the following conversation transcript into a JSON structure.
        
        Instructions:
        - Summarize the conversation flow and context in full sentences.
        - Include specific entities (Names, Numbers, Dates, Locations) mentioned.
        - Identify the user's primary emotion/sentiment.
        - The summary output MUST be in KOREAN.

        Output JSON Format:
        {
            "context_summary": "...",
            "sentiment": "..."
        }
        """


        try:
            response = self.client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Transcript:\n{transcript}"}
                ],
                response_format={ "type": "json_object" }
            )
            
            result_json_str = response.choices[0].message.content
            return json.loads(result_json_str)

        except Exception as e:
            print(f"[Memory] Summarization Error: {e}")
            return None

memory_service = MemoryService()
