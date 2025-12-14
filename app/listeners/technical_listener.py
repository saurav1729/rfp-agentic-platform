# app/listeners/technical_listener.py

import time
import threading

from app.event_bus.mongo_bus import fetch_unprocessed_events, publish_event, mark_event_processed
from app.event_bus.event_types import RFP_RECEIVED, TECHNICAL_DONE

# from app.services.agents.technical_agent import TechnicalAgent

# tech_agent = TechnicalAgent()


def technical_loop():
    while True:
        events = fetch_unprocessed_events(RFP_RECEIVED)
        print("Technical Listener fetched events:", events)

        for ev in events:
            # rfp_id = ev["payload"]["rfp_id"]
            # content = ev["payload"]["content"]

            # print(f"[TechnicalAgent] Processing RFP {rfp_id}")

            # sku_list = tech_agent.extract_requirements(content)

            # publish_event(TECHNICAL_DONE, {
            #     "rfp_id": rfp_id,
            #     "sku_list": sku_list
            # })

            mark_event_processed(ev["_id"])

        time.sleep(1)


def start():
    threading.Thread(target=technical_loop, daemon=True).start()
