import json
import requests
from typing import List, Dict
from datetime import datetime

from pymongo import MongoClient
import google.generativeai as genai


class LegalAgent:
    """
    Legal Agent:
    - Reviews the proposal for legal compliance
    - Ensures all terms and conditions are met
    """

    def __init__(
        self,
        api_key: str,
    ):
        
        genai.configure(api_key=api_key)

    # --------------------------------------------------
    # Legal Review
    # --------------------------------------------------
    def legal_review(self, rfp_doc) -> Dict | None:
        model = genai.GenerativeModel("gemini-pro")
        prompt = f"""
        Review the following RFP document for legal compliance and ensure all terms and conditions are met.
        RFP Document: {rfp_doc}
        """
        response = model.generate_content(prompt)
        return response.text.strip()