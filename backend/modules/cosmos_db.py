import os
from azure.cosmos import CosmosClient
from datetime import datetime
import uuid
import pytz

# Load env variables (handled by main app, but safety check here)
ENDPOINT = os.getenv("AZURE_COSMOS_DB_ENDPOINT")
KEY = os.getenv("AZURE_COSMOS_DB_KEY")
DATABASE_NAME = "samantha_db" # Reusing existing DB name from reference
CONTAINER_NAME = "UserMemories"

class CosmosDBService:
    def __init__(self):
        if not ENDPOINT or not KEY:
            print("[CosmosDB] Missing Credentials. Memory feature disabled.")
            self.container = None
            return

        try:
            # [Fix] Set connection timeout to prevent zombie processes (5 seconds)
            self.client = CosmosClient(ENDPOINT, KEY, connection_timeout=5000)
            self.database = self.client.create_database_if_not_exists(id=DATABASE_NAME)
            self.container = self.database.create_container_if_not_exists(
                id=CONTAINER_NAME,
                partition_key="/user_id"
            )
            print(f"[CosmosDB] Connected to container '{CONTAINER_NAME}'.")
        except Exception as e:
            print(f"[CosmosDB] Connection Error: {e}")
            self.container = None

    def save_memory(self, user_id, full_transcript, summary_json):
        if not self.container: return

        # Korea Time (UTC+9)
        kst = pytz.timezone('Asia/Seoul')
        now = datetime.now(kst).isoformat()

        memory_item = {
            "id": str(uuid.uuid4()),
            "doc_type": "memory",
            "user_id": user_id,
            "date": now,
            "full_transcript": full_transcript,
            "summary": summary_json
        }

        try:
            self.container.create_item(body=memory_item)
            print(f"[CosmosDB] Memory saved for {user_id}")
        except Exception as e:
            print(f"[CosmosDB] Save Error: {e}")

    def get_all_memories(self, user_id):
        if not self.container: return []

        query = (
            "SELECT * FROM c WHERE c.user_id = @user_id "
            "AND (NOT IS_DEFINED(c.doc_type) OR c.doc_type = 'memory') "
            "ORDER BY c.date ASC"
        )
        params = [{"name": "@user_id", "value": user_id}]

        try:
            items = list(self.container.query_items(
                query=query,
                parameters=params,
                enable_cross_partition_query=False
            ))
            return items
        except Exception as e:
            print(f"[CosmosDB] Fetch Error: {e}")
            return []

    def get_user_profile(self, user_id):
        if not self.container:
            return None
        profile_id = f"profile:{user_id}"
        try:
            return self.container.read_item(item=profile_id, partition_key=user_id)
        except Exception:
            return None

    def upsert_user_profile(self, user_id, profile_updates: dict):
        if not self.container:
            return None
        kst = pytz.timezone("Asia/Seoul")
        now = datetime.now(kst).isoformat()
        profile_id = f"profile:{user_id}"

        current = self.get_user_profile(user_id) or {
            "id": profile_id,
            "doc_type": "profile",
            "user_id": user_id,
            "created_at": now,
        }
        current.update(profile_updates or {})
        current["updated_at"] = now

        try:
            self.container.upsert_item(body=current)
            print(f"[CosmosDB] Profile upserted for {user_id}")
            return current
        except Exception as e:
            print(f"[CosmosDB] Profile Upsert Error: {e}")
            return None

cosmos_service = CosmosDBService()
