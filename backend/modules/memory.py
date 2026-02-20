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
                azure_endpoint=base_endpoint,
                timeout=5.0 # [Fix] Set timeout to prevent zombie processes
            )
            print("[Memory] Azure OpenAI Client initialized (Timeout: 5s).")
        except Exception as e:
            print(f"[Memory] Client Init Error: {e}")
            self.client = None

    def summarize(self, transcript):
        if not self.client or not transcript.strip():
            return None

        system_prompt = """
        You are an AI assistant that summarizes conversation transcripts into a JSON format.
        
        [Instructions]
        1. Analyze the provided conversation transcript.
        2. Summarize the context and flow in Korean.
           (IMPORTANT: Explicitly record nouns, names, object names, and numbers in the summary.)
        3. Identify the user's primary emotion and target from the lists below.
        4. If the transcript is empty or contains only noise, return empty strings.

        [Emotion List] (Select one)
        Positive: Excited, Proud, Grateful, Impressed, Hopeful, Confident, Joyful, Content, Prepared, Caring, Trusting, Faithful
        Negative/Complex: Surprised, Angry, Sad, Annoyed, Lonely, Afraid, Terrified, Guilty, Disgusted, Furious, Anxious, Anticipating, Nostalgic, Disappointed, Jealous, Devastated, Embarrassed, Sentimental, Ashamed, Apprehensive

        [Target List] (Select one)
        Options: "나" (Self), "친구", "지인", "직장동료", "가족", "타인"

        [Output JSON Format]
        {
            "context_summary": "Summary in Korean",
            "sentiment": "Selected Emotion Tag",
            "status": "Positive" or "Negative",
            "target": "Selected Target"
        }
        """


        try:
            response = self.client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"<transcript>\n{transcript}\n</transcript>"}
                ],
                response_format={ "type": "json_object" }
            )
            
            result_json_str = response.choices[0].message.content
            return json.loads(result_json_str)

        except Exception as e:
            print(f"[Memory] Summarization Error: {e}")
            return None

    def summarize_dual(self, transcript):
        """
        Generates two separate summaries (Lumi/Rami) for context, 
        but a unified User Sentiment Analysis.
        """
        if not self.client or not transcript.strip():
            return None

        system_prompt = """
        You are an AI assistant that summarizes conversation transcripts into a JSON format for TWO different personas.
        
        [Input]
        - Transcript of a conversation where lines are prefixed with speakers: "USER: ", "LUMI: ", or "RAMI: ".
        - ONLY lines starting with "USER: " represent the User's factual words and emotions.
        - DO NOT attribute words spoken by "LUMI: " or "RAMI: " to the User.
        - IMPORTANT: Lumi and Rami are the AI assistants. The USER is the human.
        
        [Goal]
        - Generate TWO summaries based on the distinct perspectives of Lumi and Rami.
        - Analyze the User's overall sentiment, status, and target (based ONLY on what the "USER: " said).
        
        [Persona Definitions]
        1. **Lumi**: 따뜻하고 감성적인 '너'('친구')를 챙기는 반말투 페르소나. 요약 작성 시 이 말투와 관점을 100% 유지해.
        2. **Rami**: 직설적이고 이성적이며 팩트와 일정을 챙기는 반말투 페르소나. 요약 작성 시 이 말투와 관점을 100% 유지해.
        
        [Instructions]
        - 반드시 "USER" 단어 대신 "사용자"라는 단어를 사용해서 요약할 것.
        - lumi_summary와 rami_summary 안에 기록하는 모든 문장(요약)은 각자의 페르소나 성격에 완전히 부합하는 '한국어 반말'로 자연스럽게 작성할 것. (예: "사용자가 날씨를 물어보길래 우산을 챙기라고 말해줬어.")
        - Identify the user's primary emotion from the predefined groups.
        - Determine the status (Positive/Negative).
        - Identify the target of the emotion.

        [Output JSON Format]
        {
            "lumi_summary": "Summary focused on emotions/feelings (Korean)",
            "rami_summary": "Summary focused on facts/tasks (Korean)",
            "sentiment": "One of 32 Emotion Tags (e.g., Excited, Sad, Grateful, etc.)",
            "status": "Positive or Negative (Group Name)",
            "target": "Target (Self/Friend/etc)"
        }
        """

        try:
            response = self.client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"<transcript>\n{transcript}\n</transcript>"}
                ],
                response_format={ "type": "json_object" }
            )
            
            result_json_str = response.choices[0].message.content
            return json.loads(result_json_str)

        except Exception as e:
            print(f"[Memory] Dual Summarization Error: {e}")
            return None

memory_service = MemoryService()
