import json
import requests
from typing import List, Dict
from datetime import datetime

from pymongo import MongoClient
import google.generativeai as genai


class PricingAgent:
    """
    Pricing Agent:
    - Consumes Technical Agent structured requirements
    - Finds the exact match from the product db of the sku returned by the Technical Agent
    """

    def __init__(
        self,
        mongo_url: str,
        db_name: str = "asian_paints_db",
        product_collection: str = "products",
    ):
        
        self.client = MongoClient(mongo_url)
        self.db = self.client[db_name]
        self.products_col = self.db[product_collection]

    # --------------------------------------------------
    # Product Search
    # --------------------------------------------------
    def find_product_by_sku(self, sku: str) -> Dict | None:
        product = self.products_col.find_one({"sku": sku})
        return product