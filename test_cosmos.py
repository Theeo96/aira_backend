import os
import sys

# Add backend path to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

# Load dotenv first before importing anything
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "backend/.env"))

from backend.modules.cosmos_db import cosmos_service

print("Testing upsert...")
profile = cosmos_service.upsert_user_profile(
    user_id="eth1004p@gmail.com", 
    profile_updates={"home_destination": "방구석"}
)
print("Result:", profile)

