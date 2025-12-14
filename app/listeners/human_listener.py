# app/listeners/human_listener.py

import time
import threading

from event_bus.mongo_bus import fetch_unprocessed_events, publish_event, mark_event_processed
from event_bus.event_types import LEGAL_APPROVED, HUMAN_APPROVED

from services.agents.human_agent import HumanAgent

human_agent = HumanAgent()


def human_loop():
    while True:
        events = fetch_unprocessed_events(LEGAL_APPROVED)

        for ev in events:
            rfp_id = ev["payload"]["rfp_id"]

            print(f"[HumanAgent] Final human approval for RFP {rfp_id}")

            decision = human_agent.final_approve(rfp_id)

            publish_event(HUMAN_APPROVED, {
                "rfp_id": rfp_id,
                "status": decision
            })

            mark_event_processed(ev["_id"])

        time.sleep(1)


def start():
    threading.Thread(target=human_loop, daemon=True).start()
