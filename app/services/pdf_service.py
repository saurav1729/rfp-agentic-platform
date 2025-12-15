from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib import colors
import re


class ProposalPDFService:
    """
    Converts proposal markdown/text into a professional PDF
    """

    def __init__(self, output_dir: str = "generated_pdfs"):
        self.output_dir = output_dir

    def generate_pdf(self, proposal_markdown: str, file_name: str) -> str:
        """
        Returns path of generated PDF
        """

        file_path = f"{self.output_dir}/{file_name}.pdf"

        doc = SimpleDocTemplate(
            file_path,
            pagesize=A4,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name="TitleStyle",
            fontSize=16,
            leading=20,
            alignment=TA_CENTER,
            spaceAfter=20,
            fontName="Helvetica-Bold"
        ))

        styles.add(ParagraphStyle(
            name="HeaderStyle",
            fontSize=12,
            leading=16,
            spaceBefore=12,
            spaceAfter=8,
            fontName="Helvetica-Bold"
        ))

        styles.add(ParagraphStyle(
            name="BodyStyle",
            fontSize=10,
            leading=14,
            alignment=TA_LEFT
        ))

        elements = []

        # -------- Parse Markdown --------
        lines = proposal_markdown.split("\n")

        table_buffer = []
        in_table = False

        for line in lines:
            line = line.strip()

            if not line:
                elements.append(Spacer(1, 8))
                continue

            # Title
            if line.startswith("# "):
                elements.append(Paragraph(line[2:], styles["TitleStyle"]))
                continue

            # Section headers
            if line.startswith("## "):
                elements.append(Spacer(1, 12))
                elements.append(Paragraph(line[3:], styles["HeaderStyle"]))
                continue

            # Markdown table handling
            if line.startswith("|"):
                in_table = True
                row = [cell.strip() for cell in line.strip("|").split("|")]
                table_buffer.append(row)
                continue

            if in_table and not line.startswith("|"):
                elements.append(self._build_table(table_buffer))
                table_buffer = []
                in_table = False

            # Normal paragraph
            elements.append(Paragraph(self._escape(line), styles["BodyStyle"]))

        # Flush remaining table
        if table_buffer:
            elements.append(self._build_table(table_buffer))

        doc.build(elements)

        return file_path

    # -------------------------
    # Helpers
    # -------------------------

    def _build_table(self, data):
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
        ]))
        return table

    def _escape(self, text: str) -> str:
        """
        Escape special XML characters for ReportLab
        """
        return re.sub(r"[&<>]", lambda x: {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;"
        }[x.group()], text)
