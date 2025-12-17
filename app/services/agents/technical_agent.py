import json
import requests
from typing import List, Dict
from datetime import datetime, timezone

from pymongo import MongoClient
import google.generativeai as genai

class TechnicalAgent:
    """
    Technical Agent:
    - Consumes Sales Agent structured requirements
    - Generates embeddings using Gemini
    - Performs vector search on products collection
    - Produces requirement-wise product recommendations
    """

    def __init__(
        self,
        mongo_url: str,
        db_name: str = "asian_paints_db",
        product_collection: str = "products",
        model_embedding: str = "models/text-embedding-004",
        api_key: str | None = None,
    ):

        self.client = MongoClient(mongo_url)
        self.db = self.client[db_name]
        self.products_col = self.db[product_collection]

        self.embedding_model = model_embedding

    # --------------------------------------------------
    # Embedding
    # --------------------------------------------------
    def generate_embedding(self, content: str) -> List[float] | None:

        # print("API KEY", genai.api_key)
        try:
            resp = genai.embed_content(
                model=self.embedding_model,
                content=content,
                request_options={"timeout": 120},
            )
            return resp["embedding"]
        except requests.exceptions.ReadTimeout as e:
            print("⏱️ Embedding timeout:", e)
            return None
        except Exception as e:
            print("❌ Embedding error:", e)
            return None

    # --------------------------------------------------
    # Product Embedding Bootstrap (run once)
    # --------------------------------------------------
    def ensure_product_embeddings(self) -> int:
        """
        Ensures all products have embeddings.
        Returns number of products updated.
        """
        updated = 0
        products = list(self.products_col.find({}))

        for product in products:
            if product.get("embedding"):
                continue

            desc = product.get("description", "")
            if not desc:
                continue

            emb = self.generate_embedding(desc)
            if emb is None:
                continue

            self.products_col.update_one(
                {"_id": product["_id"]},
                {"$set": {"embedding": emb}},
            )
            updated += 1

        return updated

    # --------------------------------------------------
    # Vector Search
    # --------------------------------------------------
    def search_products(
        self,
        query_embedding: List[float],
        top_k: int = 3,
    ) -> List[Dict]:
        if not query_embedding:
            return []

        pipeline = [
            {
                "$vectorSearch": {
                    "index": "default",
                    "queryVector": query_embedding,
                    "path": "embedding",
                    "numCandidates": 50,
                    "limit": top_k,
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "sku": 1,
                    "name": 1,
                    "description": 1,
                    "_score": {"$meta": "vectorSearchScore"},
                }
            },
        ]

        return list(self.products_col.aggregate(pipeline))

    # --------------------------------------------------
    # Main Processing Entry Point
    # --------------------------------------------------
    def process_rfp(self, sales_output: dict) -> dict:

        requirements = sales_output.get("requirements", [])
        technical_results = {}

        missing_requirements = []

        for req in requirements:

            print("Processing requirement:", req["requirement_id"], "\n Requirement text:", req["requirement_text"])
            embedding = self.generate_embedding(req["requirement_text"])
            print("Generate embedding output:", embedding)

            print("Generated embedding for requirement:", req["requirement_id"])
            matches = self.search_products(embedding)

            if not matches:
                missing_requirements.append(req["requirement_id"])

            technical_results[req["requirement_id"]] = {
                "item": req["item"],
                "quantity": req["quantity"],
                "recommendations": matches
            }

        # -------- Status decision --------
        if not technical_results:
            status = "FAILED"
            message = "No technical requirements could be processed"
        elif missing_requirements:
            status = "PARTIAL"
            message = f"Missing matches for requirements: {missing_requirements}"
        else:
            status = "COMPLETED"
            message = "All requirements matched successfully"

        return {
            "agent": "TECHNICAL",
            "status": status,
            "message": message,
            "data": technical_results,
            "missing_requirements": missing_requirements,
            "timestamp": datetime.now(timezone.utc),
        }