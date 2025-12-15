# app/listeners/pricing_listener.py

import time
import threading

from event_bus.mongo_bus import fetch_unprocessed_events, publish_event, mark_event_processed
from event_bus.event_types import PRICING_DONE, RFP_RECEIVED

from services.agents.technical_agent import TechnicalAgent
from services.agents.pricing_agent import PricingAgent
from services.agents.proposal_agent import ProposalAgent
from services.agents.legal_agent import LegalAgent

technical_agent = TechnicalAgent()
pricing_agent = PricingAgent()
proposal_agent = ProposalAgent()
legal_agent = LegalAgent()

def sequenctial_processing():
    events = fetch_unprocessed_events(RFP_RECEIVED)

    # Sort by Priority if needed

    if events:
        for ev in events:
            data = ev["payload"]
            rfp_id = data["rfp_id"]
            
            # Technical Processing
            technical_status = technical_agent.process_rfp(rfp_id)

            # Pricing Processing
            pricing_status = pricing_agent.get_prices(rfp_id)

            # Proposal Processing
            proposal_status = proposal_agent.process_rfp(rfp_id)

            # Legal Processing
            legal_status = legal_agent.process_rfp(rfp_id)

            # Mark event as processed
            mark_event_processed(ev["_id"])


            
        time.sleep(1)


def start():
    threading.Thread(target=pricing_loop, daemon=True).start()
