import os
import json
from datetime import datetime
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

    def analyze_unified_memory(self, conversation_id: str, user_id: str, started_at: str, ended_at: str, messages: list):
        if not self.client or not messages:
            return None

        system_prompt = """
        You are an advanced AI assistant analyzing a conversation transcript to extract overall summaries and turn-by-turn memories based STRICTLY on specific emotional and relational categories.

        [Input]
        - A JSON array of message objects. Each object has `message_id`, `speaker_type`, `ai_persona` (if ai), `text`, and `created_at`.
        - The user is `speaker_type: "user"`, while AI is `speaker_type: "ai"` with a specific persona.

        [Output Requirements]
        Return ONLY valid JSON matching this exact structure:
        {
          "summary": {
            "context_summary": "Brief overall summary in Korean",
            "sentiment": "positive" | "neutral" | "negative"
          },
          "memories": [
            {
              "utterance_id": "Unique string ID per turn (e.g. TURN_01)",
              "user_message_id": "msg_id of the user's triggering text",
              "ai_message_ids": ["msg_ids of AI responses correlated to this turn"],
              "emotion_code": "Must be EXACTLY ONE of the 32 Emotion Codes below",
              "sentiment": "positive" | "neutral" | "negative",
              "relation": "친구" | "지인" | "직장 동료",
              "full_text": "One sentence summary of this specific turn in Korean",
              "ts": "Timestamp of this turn (typically the user's created_at)"
            }
          ]
        }

        [32 Emotion Codes - YOU MUST USE EXACTLY ONE OF THESE FOR emotion_code]
        E01_JOY, E02_HAPPINESS, E03_EXCITEMENT, E04_SATISFACTION, E05_GRATITUDE, E06_PRIDE,
        E07_LOVE, E08_AFFECTION, E09_FLUTTER, E10_CLOSENESS,
        E11_SADNESS, E12_DEPRESSED, E13_LONELY, E14_HURT, E15_REGRET, E16_GUILT,
        E17_ANGER, E18_IRRITATION, E19_UNFAIRNESS, E20_HATRED, E21_CONTEMPT,
        E22_ANXIETY, E23_FEAR, E24_TENSION, E25_PRESSURE,
        E26_SURPRISE, E27_EMBARRASSED, E28_CONFUSION, E29_DISAPPOINTED,
        E30_DISGUST, E31_AVERSION,
        E32_NEUTRAL

        [Important Rules]
        - DO NOT invent emotion codes.
        - Ensure "sentiment" is exactly 'positive', 'neutral', or 'negative'.
        - Ensure "relation" is exactly '친구', '지인', or '직장 동료'.
        - Only generate a memory turn if it represents a distinct point/shift in the conversation. Do not create one for every single message. Group related consecutive messages into one turn.
        """

        try:
            response = self.client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(messages, ensure_ascii=False)}
                ],
                response_format={ "type": "json_object" }
            )
            
            result_json_str = response.choices[0].message.content
            ai_data = json.loads(result_json_str)

            # Define static mappings for the 32 emotions
            EMOTION_MAP = {
                "E01_JOY": {"id": "E01", "label_ko": "기쁨", "family_7": "JOY"},
                "E02_HAPPINESS": {"id": "E02", "label_ko": "행복", "family_7": "JOY"},
                "E03_EXCITEMENT": {"id": "E03", "label_ko": "신남/흥분", "family_7": "JOY"},
                "E04_SATISFACTION": {"id": "E04", "label_ko": "만족", "family_7": "JOY"},
                "E05_GRATITUDE": {"id": "E05", "label_ko": "감사", "family_7": "JOY"},
                "E06_PRIDE": {"id": "E06", "label_ko": "자랑스러움", "family_7": "JOY"},
                "E07_LOVE": {"id": "E07", "label_ko": "사랑", "family_7": "JOY"},
                "E08_AFFECTION": {"id": "E08", "label_ko": "애정", "family_7": "JOY"},
                "E09_FLUTTER": {"id": "E09", "label_ko": "설렘", "family_7": "JOY"},
                "E10_CLOSENESS": {"id": "E10", "label_ko": "친밀감", "family_7": "JOY"},
                "E11_SADNESS": {"id": "E11", "label_ko": "슬픔", "family_7": "SADNESS"},
                "E12_DEPRESSED": {"id": "E12", "label_ko": "우울", "family_7": "SADNESS"},
                "E13_LONELY": {"id": "E13", "label_ko": "외로움", "family_7": "SADNESS"},
                "E14_HURT": {"id": "E14", "label_ko": "상처/아픔", "family_7": "HURT"},
                "E15_REGRET": {"id": "E15", "label_ko": "후회", "family_7": "SADNESS"},
                "E16_GUILT": {"id": "E16", "label_ko": "죄책감", "family_7": "SADNESS"},
                "E17_ANGER": {"id": "E17", "label_ko": "분노", "family_7": "ANGER"},
                "E18_IRRITATION": {"id": "E18", "label_ko": "짜증", "family_7": "ANGER"},
                "E19_UNFAIRNESS": {"id": "E19", "label_ko": "억울함", "family_7": "ANGER"},
                "E20_HATRED": {"id": "E20", "label_ko": "증오/미움", "family_7": "ANGER"},
                "E21_CONTEMPT": {"id": "E21", "label_ko": "경멸", "family_7": "ANGER"},
                "E22_ANXIETY": {"id": "E22", "label_ko": "불안", "family_7": "ANXIETY_FEAR"},
                "E23_FEAR": {"id": "E23", "label_ko": "두려움/공포", "family_7": "ANXIETY_FEAR"},
                "E24_TENSION": {"id": "E24", "label_ko": "긴장", "family_7": "ANXIETY_FEAR"},
                "E25_PRESSURE": {"id": "E25", "label_ko": "부담", "family_7": "ANXIETY_FEAR"},
                "E26_SURPRISE": {"id": "E26", "label_ko": "놀람", "family_7": "SURPRISE_CONFUSION"},
                "E27_EMBARRASSED": {"id": "E27", "label_ko": "당황", "family_7": "SURPRISE_CONFUSION"},
                "E28_CONFUSION": {"id": "E28", "label_ko": "혼란", "family_7": "SURPRISE_CONFUSION"},
                "E29_DISAPPOINTED": {"id": "E29", "label_ko": "실망", "family_7": "SADNESS"},
                "E30_DISGUST": {"id": "E30", "label_ko": "역겨움/불쾌", "family_7": "ANGER"},
                "E31_AVERSION": {"id": "E31", "label_ko": "혐오/거부감", "family_7": "ANGER"},
                "E32_NEUTRAL": {"id": "E32", "label_ko": "중립", "family_7": "NEUTRAL"}
            }

            final_memories = []
            graph_nodes = []
            graph_edges = []
            seen_emotions = set()
            seen_relations = set()

            for i, mem in enumerate(ai_data.get("memories", [])):
                mem_key = f"mem:{conversation_id}_{(i):05d}"
                emo_code = mem.get("emotion_code", "E32_NEUTRAL")
                if emo_code not in EMOTION_MAP:
                    emo_code = "E32_NEUTRAL"
                
                emo_data = EMOTION_MAP[emo_code]
                relation_val = mem.get("relation", "친구")

                final_memories.append({
                    "memory_key": mem_key,
                    "conversation_id": conversation_id,
                    "utterance_id": f"{conversation_id}_{(i):05d}",
                    "turn_index": i,
                    "user_message_id": mem.get("user_message_id", ""),
                    "ai_message_ids": mem.get("ai_message_ids", []),
                    "emotion": {
                        "id": emo_data["id"],
                        "code": emo_code,
                        "label_ko": emo_data["label_ko"],
                        "family_7": emo_data["family_7"]
                    },
                    "sentiment": mem.get("sentiment", "neutral"),
                    "relation": relation_val,
                    "full_text": mem.get("full_text", ""),
                    "ts": mem.get("ts", "")
                })

                # Graph Nodes & Edges
                emo_node_key = f"emo:{emo_code}"
                rel_node_key = f"rel:{relation_val}"

                if emo_node_key not in seen_emotions:
                    seen_emotions.add(emo_node_key)
                    graph_nodes.append({
                        "key": emo_node_key,
                        "type": "emotion",
                        "label": f"{emo_data['label_ko']} ({emo_code})",
                        "group": emo_data["family_7"],
                        "size": 8
                    })
                
                if rel_node_key not in seen_relations:
                    seen_relations.add(rel_node_key)
                    graph_nodes.append({
                        "key": rel_node_key,
                        "type": "relation",
                        "label": relation_val,
                        "size": 7
                    })

                graph_nodes.append({
                    "key": mem_key,
                    "type": "memory",
                    "label": mem.get("full_text", "")[:15] + "...",
                    "emotion": f"{emo_data['label_ko']} ({emo_code})",
                    "relation": relation_val,
                    "full_text": mem.get("full_text", ""),
                    "ts": mem.get("ts", ""),
                    "emotion_score": 0.8
                })

                graph_edges.append({
                    "source": mem_key, "target": emo_node_key, "type": "memory_emotion", "weight": 1
                })
                graph_edges.append({
                    "source": mem_key, "target": rel_node_key, "type": "memory_relation", "weight": 1
                })

            final_payload = {
                "schema_version": "1.0.0",
                "generated_at": datetime.utcnow().isoformat() + "Z", # We need from datetime import datetime here, will add at top
                "conversation_id": conversation_id,
                "user_id": user_id,
                "started_at": started_at,
                "ended_at": ended_at,
                "summary": ai_data.get("summary", {"context_summary": "", "sentiment": "neutral"}),
                "messages": messages,
                "memories": final_memories,
                "graph": {
                    "nodes": graph_nodes,
                    "edges": graph_edges
                }
            }
            return final_payload

        except Exception as e:
            print(f"[Memory] evaluate_unified_memory Error: {e}")
            return None

memory_service = MemoryService()
