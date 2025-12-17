# app/listeners/proposal_listener.py

import time
import threading

from event_bus.mongo_bus import fetch_unprocessed_events, publish_event, mark_event_processed
from event_bus.event_types import PRICING_DONE, PROPOSAL_DONE

from services.agents.proposal_agent import ProposalAgent

proposal_agent = ProposalAgent()


def proposal_loop():
    while True:
        events = fetch_unprocessed_events(PRICING_DONE)

        for ev in events:
            data = ev["payload"]
            rfp_id = data["rfp_id"]
            pricing = data["pricing"]

            print(f"[ProposalAgent] Creating proposal for RFP {rfp_id}")

            proposal_url = proposal_agent.build_proposal(rfp_id, pricing)

            publish_event(PROPOSAL_DONE, {
                "rfp_id": rfp_id,
                "proposal_url": proposal_url
            })

            mark_event_processed(ev["_id"])

        time.sleep(1)


def start():
    threading.Thread(target=proposal_loop, daemon=True).start()
