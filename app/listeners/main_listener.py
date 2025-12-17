# app/listeners/pricing_listener.py

import time
import threading
import os


from app.event_bus.mongo_bus import fetch_rpfs
from app.event_bus.event_types import PRICING_DONE, RFP_RECEIVED

from app.services.agents.technical_agent import TechnicalAgent
from app.services.agents.pricing_agent import PricingAgent
from app.services.agents.proposal_agent import ProposalAgent
from app.services.agents.legal_agent import LegalAgent
from app.services.agents.sales_agent import SalesAgent

sales_agent = SalesAgent(os.getenv("MONGO_URI", "mongodb://localhost:27017/"), db_name="rfp")
print("gen ai api key:", os.getenv("GENAI_API_KEY", None))
technical_agent = TechnicalAgent(
    mongo_url=os.getenv("MONGO_URI", "mongodb://localhost:27017/"),
    db_name="rfp",
    product_collection="products",
    api_key=os.getenv("GENAI_API_KEY", None),
)
pricing_agent = PricingAgent(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
proposal_agent = ProposalAgent("abcd-1234-efgh-5678")  # Dummy API key
legal_agent = LegalAgent("abcd-1234-efgh-5678")  # Dummy API key

def sequenctial_processing():

    # Temporarily calling the sales agent manually for demo 
    # sales_result = sales_agent.push_dummy_rfp()
    # print("Sales Agent pushed RFP again:", sales_result)

    rfps = fetch_rpfs(RFP_RECEIVED)
    print("Main Listener fetched events:", len(rfps))

    for rfp_doc in rfps:

        print("Processing RFP ID:", rfp_doc["_id"])
        tech_result = technical_agent.process_rfp(rfp_doc["sales_output"])
        print("Technical Agent processed RFP:", tech_result)

        break
        # save_output(rfp_doc["_id"], "technical_output", tech_result)

        if tech_result["status"] == "FAILED":
            mark_event_processed(ev["_id"])
            continue  # STOP PIPELINE

        pricing_result = pricing_agent.get_prices(tech_result)
        # save_output(rfp_doc["_id"], "pricing_output", pricing_result)

        proposal_result = proposal_agent.find_products_by_sku(rfp_doc)
        # save_output(rfp_doc["_id"], "proposal_output", proposal_result)

        mark_event_processed(ev["_id"])


def start():
    threading.Thread(target=sequenctial_processing, daemon=True).start()
