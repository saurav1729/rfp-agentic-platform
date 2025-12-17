# app/listeners/legal_listener.py

import time
import threading

from event_bus.mongo_bus import fetch_unprocessed_events, publish_event, mark_event_processed
from event_bus.event_types import PROPOSAL_DONE, LEGAL_APPROVED

from services.agents.legal_agent import LegalAgent

legal_agent = LegalAgent()


def legal_loop():
    while True:
        events = fetch_unprocessed_events(PROPOSAL_DONE)

        for ev in events:
            data = ev["payload"]
            rfp_id = data["rfp_id"]
            proposal_url = data["proposal_url"]

            print(f"[LegalAgent] Reviewing proposal for RFP {rfp_id}")

            result = legal_agent.verify(proposal_url)

            publish_event(LEGAL_APPROVED, {
                "rfp_id": rfp_id,
                "legal_ok": result
            })

            mark_event_processed(ev["_id"])

        time.sleep(1)


def start():
    threading.Thread(target=legal_loop, daemon=True).start()
