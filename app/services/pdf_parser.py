import PyPDF2
from io import BytesIO
from typing import Dict, Any, List
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class PDFParser:
    """Extract RFP details from PDF attachments"""
    
    @staticmethod
    async def parse_pdf(pdf_content: bytes) -> Dict[str, Any]:
        """Parse PDF to extract RFP information"""
        
        try:
            pdf_file = BytesIO(pdf_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ''
            metadata = pdf_reader.metadata
            
            # Extract text from all pages
            for page_num in range(min(10, len(pdf_reader.pages))):  # First 10 pages
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + '\n'
            
            # Extract structured information
            title = PDFParser._extract_title(text, metadata)
            description = PDFParser._extract_description(text)
            deadline = PDFParser._extract_deadline(text)
            budget = PDFParser._extract_budget(text)
            
            return {
                'title': title,
                'description': description,
                'deadline': deadline,
                'budget_max': budget,
                'keywords': PDFParser._extract_keywords(text),
                'raw_text': text[:2000],  # First 2000 chars
            }
            
        except Exception as e:
            logger.error(f"PDF parsing error: {str(e)}")
            return {
                'title': 'Unparseable RFP',
                'description': 'Could not parse PDF',
                'deadline': None,
                'budget_max': 0,
                'keywords': [],
            }
    
    @staticmethod
    def _extract_title(text: str, metadata: Any) -> str:
        """Extract RFP title"""
        if metadata and metadata.get('/Title'):
            return metadata.get('/Title', 'RFP Document')
        
        lines = text.split('\n')
        for line in lines[:10]:
            if line.strip() and len(line.strip()) > 10:
                return line.strip()[:100]
        
        return 'RFP Document'
    
    @staticmethod
    def _extract_description(text: str) -> str:
        """Extract RFP description"""
        lines = text.split('\n')
        description = []
        
        for i, line in enumerate(lines[:50]):
            if line.strip():
                description.append(line.strip())
            if len('\n'.join(description)) > 500:
                break
        
        return '\n'.join(description)[:1000]
    
    @staticmethod
    def _extract_deadline(text: str) -> datetime:
        """Extract deadline from PDF text"""
        patterns = [
            r'deadline[:\s]+([^\n]+)',
            r'due\s+(?:date)?[:\s]+([^\n]+)',
            r'closes?[:\s]+([^\n]+)',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    return datetime.strptime(match, '%m/%d/%Y')
                except:
                    try:
                        return datetime.strptime(match, '%m-%d-%Y')
                    except:
                        pass
        
        return datetime.utcnow().replace(day=1) + timedelta(days=32)
    
    @staticmethod
    def _extract_budget(text: str) -> float:
        """Extract budget from PDF text"""
        patterns = [
            r'budget[:\s]*\$?([\d,]+(?:\.\d{2})?)',
            r'contract\s+(?:value|amount)[:\s]*\$?([\d,]+(?:\.\d{2})?)',
            r'estimated\s+(?:cost|value|budget)[:\s]*\$?([\d,]+(?:\.\d{2})?)',
            r'\$?([\d,]+(?:\.\d{2})?)\s*(?:million|thousand|k|M)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    amount = float(match.replace(',', ''))
                    if 'thousand' in text[max(0, text.find(match)-50):text.find(match)] or 'K' in text:
                        amount *= 1000
                    elif 'million' in text[max(0, text.find(match)-50):text.find(match)] or 'M' in text:
                        amount *= 1000000
                    return amount
                except:
                    pass
        
        return 0
