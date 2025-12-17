from pymongo import MongoClient
from datetime import datetime
from datetime import timezone


class SalesAgent:
    def __init__(self, mongo_url: str, db_name: str = "rfp", collection_name: str = "rfps"):
        self.client = MongoClient(mongo_url)
        self.db = self.client[db_name]
        self.rfps_col = self.db[collection_name]

    def push_dummy_rfp(self):
        dummy_rfp = {
            "status": "RFP_RECEIVED",

            # -------------------------
            # Source / discovery info
            # -------------------------
            "rfp_source": {
                "source_type": "DUMMY",
                "source_url": "https://dummy-rfp-portal.com/rfp/123",
                "discovered_at": datetime.now(timezone.utc),
            },

            # -------------------------
            # Sales agent output
            # -------------------------
            "sales_output": {
                "title": "Waterproofing Works for Commercial Complex",
                "client_name": "ABC Infrastructure Pvt Ltd",
                "due_date": "2024-12-30",
                "location": "Mumbai",
                "category": "Waterproofing",

                # High-level summary (human-readable)
                "rfp_summary": """
                    The client is inviting bids for supply and application of
                    high-performance waterproofing systems for basement and terrace areas
                    of a commercial complex. The solution must ensure long-term durability,
                    UV resistance, and compliance with relevant standards.
                    """,

                # Raw content (PDF / HTML text later)
                "rfp_raw_text": """
                    Basement waterproofing required for 5000 sq.m.
                    Terrace waterproofing required for 3000 sq.m.
                    System must comply with IS standards.
                    Warranty minimum 10 years.
                    """,

                # -------------------------
                # 🔥 Structured requirements (machine-readable)
                # -------------------------
                "requirements": [
                    {
                        "requirement_id": "REQ-1",
                        "item": "Basement waterproofing system",
                        "application_area": "Basement",
                        "quantity": "5000 sq.m",
                        "requirement_text": "High-performance waterproofing system suitable for basement areas with long-term durability and water resistance"
                    },
                    {
                        "requirement_id": "REQ-2",
                        "item": "Terrace waterproofing system",
                        "application_area": "Terrace",
                        "quantity": "3000 sq.m",
                        "requirement_text": "UV-resistant waterproofing system suitable for terrace application with minimum 10-year performance warranty"
                    }
                ]
            },

            # -------------------------
            # Placeholders for next agents
            # -------------------------
            "technical_output": None,
            "pricing_output": None,
            "proposal_output": None,

            # indian standard timezone
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        result = self.rfps_col.insert_one(dummy_rfp)

        print("Sales result",result)

        print("✅ Dummy RFP pushed by Sales Agent")
        print("Mongo _id:", result.inserted_id)

        return result.inserted_id
