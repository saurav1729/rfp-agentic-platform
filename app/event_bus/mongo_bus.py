# app/event_bus/mongo_bus.py

from pymongo import MongoClient
from bson import ObjectId
import datetime
import os


MONGO_URL = os.getenv("MONGO_URI", "mongodb://localhost:27017")

client = MongoClient(MONGO_URL)
db = client["rfp"]

events = db["events"]  # Event queue
rfps = db["rfps"]      # RFP state storage


def publish_event(event_type: str, payload: dict):
    event = {
        "event_type": event_type,
        "payload": payload,
        "timestamp": datetime.datetime.utcnow(),
        "processed": False,
    }
    events.insert_one(event)
    print(f"[EVENT EMIT] {event_type} → {payload}")


def fetch_unprocessed_events(event_type: str):
    return list(events.find(
        {"event_type": event_type, "processed": False}
    ))
def fetch_rpfs(status_type: str):
    return list(rfps.find(
        {"status": status_type}
    ))


def mark_event_processed(event_id):
    events.update_one({ "_id": ObjectId(event_id) }, { "$set": { "processed": True } })
