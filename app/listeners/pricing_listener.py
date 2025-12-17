# app/listeners/pricing_listener.py

import time
import threading

from event_bus.mongo_bus import fetch_unprocessed_events, publish_event, mark_event_processed
from event_bus.event_types import TECHNICAL_DONE, PRICING_DONE

from services.agents.pricing_agent import PricingAgent

pricing_agent = PricingAgent()


def pricing_loop():
    while True:
        events = fetch_unprocessed_events(TECHNICAL_DONE)

        for ev in events:
            data = ev["payload"]
            rfp_id = data["rfp_id"]
            sku_list = data["sku_list"]

            print(f"[PricingAgent] Pricing for RFP {rfp_id}")

            pricing_data = pricing_agent.get_prices(sku_list)

            publish_event(PRICING_DONE, {
                "rfp_id": rfp_id,
                "pricing": pricing_data
            })

            mark_event_processed(ev["_id"])

        time.sleep(1)


def start():
    threading.Thread(target=pricing_loop, daemon=True).start()
