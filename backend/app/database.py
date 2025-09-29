import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

database_url = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
client = AsyncIOMotorClient(database_url)
db = client.notesdb

users_collection = db.users
notes_collection = db.notes
otps_collection = db.otps

print("Successfully connected to MongoDB with motor!")