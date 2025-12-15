import google.generativeai as genai
from typing import Dict, List


class ProposalAgent:
    """
    Proposal Agent:
    - Consumes outputs from Sales, Technical, Pricing agents
    - Uses Gemini ONLY for narrative sections
    - Produces a structured proposal (Markdown / HTML ready)
    """

    def __init__(self, api_key: str, model: str = "gemini-1.5-pro"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

    # ---------------------------
    # Gemini helper
    # ---------------------------
    def _generate_text(self, prompt: str) -> str:
        response = self.model.generate_content(prompt)
        return response.text.strip()

    # ---------------------------
    # Section builders
    # ---------------------------

    def build_executive_summary(
        self,
        rfp_title: str,
        rfp_summary: str,
        matched_products: List[Dict],
    ) -> str:
        prompt = f"""
You are a senior FMCG proposal consultant.

Write a concise executive summary (5–6 lines) for an RFP proposal.

Rules:
- Use ONLY the provided information
- Do NOT invent prices, standards, or products
- Keep a professional, business tone

RFP Title:
{rfp_title}

RFP Summary:
{rfp_summary}

Recommended Products:
{', '.join([p['name'] for p in matched_products])}
"""
        return self._generate_text(prompt)

    def build_scope_understanding(self, rfp_summary: str) -> str:
        prompt = f"""
Rewrite the following RFP scope in a professional proposal tone.
Do not add or remove information.

RFP Scope:
{rfp_summary}
"""
        return self._generate_text(prompt)

    # ---------------------------
    # Deterministic tables
    # ---------------------------

    def build_technical_table(self, matched_products: List[Dict]) -> str:
        table = []
        table.append("| SKU | Product Name | Match Score |")
        table.append("|-----|--------------|-------------|")

        for p in matched_products:
            score_pct = round(p["score"] * 100, 2)
            table.append(
                f"| {p['sku']} | {p['name']} | {score_pct}% |"
            )

        return "\n".join(table)

    def build_assumptions(self) -> str:
        return """
- Surface preparation to be carried out as per standard application guidelines.
- Application to be executed by approved applicators.
- Prices are indicative and subject to final commercial negotiation.
- Site conditions are assumed to be suitable for recommended products.
"""

    # ---------------------------
    # Final proposal
    # ---------------------------

    def generate_proposal(
        self,
        rfp_title: str,
        rfp_summary: str,
        matched_products: List[Dict],
    ) -> Dict:
        """
        Returns proposal sections as structured output
        """

        executive_summary = self.build_executive_summary(
            rfp_title, rfp_summary, matched_products
        )

        scope = self.build_scope_understanding(rfp_summary)

        technical_table = self.build_technical_table(matched_products)

        assumptions = self.build_assumptions()

        proposal_markdown = f"""
# Proposal Response – {rfp_title}

## Executive Summary
{executive_summary}

## Understanding of Scope
{scope}

## Technical Recommendation
{technical_table}

## Assumptions & Exclusions
{assumptions}
"""

        return {
            "title": rfp_title,
            "executive_summary": executive_summary,
            "proposal_markdown": proposal_markdown,
        }
