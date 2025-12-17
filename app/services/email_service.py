import imaplib
import email
from email.header import decode_header
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
import re

logger = logging.getLogger(__name__)

class EmailService:
    """Monitor emails for RFP alerts and notifications"""
    
    def __init__(self, email_address: str, email_password: str, imap_server: str = "imap.gmail.com"):
        self.email_address = email_address
        self.email_password = email_password
        self.imap_server = imap_server
        self.imap_port = 993
        # Use a thread pool executor because imaplib is blocking (synchronous)
        self.executor = ThreadPoolExecutor(max_workers=2)
    
    async def check_rfp_emails(self) -> List[Dict[str, Any]]:
        """Check for RFP alert emails (Async wrapper)"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self._sync_check_emails)
    
    def _sync_check_emails(self) -> List[Dict[str, Any]]:
        """Synchronous email checking logic"""
        rfps = []
        
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.email_address, self.email_password)
            mail.select('INBOX')
            
            # Keywords to search for in Subject OR Body
            rfp_keywords = ['RFP', 'bid', 'proposal', 'tender', 'opportunity', 'solicitation', 'contract']
            
            # Get emails from last 7 days
            since_date = (datetime.utcnow() - timedelta(days=7)).strftime('%d-%b-%Y')
            
            # We search ALL emails by date first to be safe, then filter in Python
            status, messages = mail.search(None, f'SINCE {since_date}')
            
            if status == 'OK':
                email_ids = messages[0].split()
                
                # Process only the last 50 emails to prevent timeouts on large inboxes
                for email_id in email_ids[-5:]: 
                    try:
                        # Fetch the email content (RFC822 format)
                        _, msg_data = mail.fetch(email_id, '(RFC822)')
                        
                        if not msg_data or not msg_data[0]:
                            continue

                        raw_email = msg_data[0][1]
                        msg = email.message_from_bytes(raw_email)
                        
                        # 1. Decode Subject
                        subject = self._decode_header(msg.get('Subject', ''))
                        sender = msg.get('From', '')
                        
                        # 2. Extract Body (Plain Text preference)
                        body = self._extract_email_body(msg)
                        
                        # 3. Check for Keywords in BOTH Subject and Body
                        # Combining them ensures we don't miss "RFP" hidden in the body
                        content_to_scan = (subject + " " + body).lower()
                        
                        if any(kw.lower() in content_to_scan for kw in rfp_keywords):
                            rfp = self._construct_rfp_from_data(subject, body, sender)
                            if rfp:
                                rfps.append(rfp)
                                
                    except Exception as e:
                        logger.warning(f"Error processing individual email ID {email_id}: {str(e)}")
                        continue
            
            mail.close()
            mail.logout()
            
            return rfps
            
        except Exception as e:
            logger.error(f"Email service global error: {str(e)}")
            return []
    
    def _extract_email_body(self, msg) -> str:
        """Helper to extract plain text body from email message"""
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                # Look for text/plain content
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    payload = part.get_payload(decode=True)
                    if payload:
                        body = payload.decode('utf-8', errors='ignore')
                        break # Found the text body, stop looking
        else:
            # Not multipart, plain email
            payload = msg.get_payload(decode=True)
            if payload:
                body = payload.decode('utf-8', errors='ignore')
        return body

    def _decode_header(self, header_text: str) -> str:
        """Decode internationalized headers"""
        try:
            decoded_parts = decode_header(header_text)
            decoded_text = ''
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    decoded_text += part.decode(encoding or 'utf-8', errors='ignore')
                else:
                    decoded_text += str(part)
            return decoded_text
        except:
            return header_text

    def _construct_rfp_from_data(self, subject: str, body: str, sender: str) -> Dict[str, Any]:
        """Create the standardized RFP dictionary from extracted data"""
        deadline = self._extract_deadline_from_text(body)
        budget_max = self._extract_budget_from_text(body)
        
        # Create a unique ID based on subject + timestamp to prevent duplicates on re-runs
        unique_hash = abs(hash(subject + sender + str(deadline)))
        
        return {
            'title': subject,
            'description': body[:2000], # Store up to 2000 chars of the body
            'source': 'Email',
            'source_url': f'mailto:{sender}', # Helper link to reply
            'posted_date': datetime.utcnow(),
            'deadline': deadline,
            'budget_max': budget_max,
            'sender': sender,
            'keywords': self._extract_keywords(subject + ' ' + body),
            'external_id': f"email_{unique_hash}", 
        }

    def _extract_deadline_from_text(self, text: str) -> Optional[datetime]:
        """Attempt to find a date in the text using regex"""
        patterns = [
            r'deadline[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'due[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'close date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            r'until[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                # Try common formats
                for fmt in ['%m/%d/%Y', '%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y']:
                    try:
                        return datetime.strptime(date_str, fmt)
                    except ValueError:
                        continue
                        
        # Default deadline if none found (30 days out)
        return datetime.utcnow() + timedelta(days=30)

    def _extract_budget_from_text(self, text: str) -> float:
        """Attempt to find a currency amount in the text"""
        # Look for currency patterns
        patterns = [
            r'\$\s?([\d,]+(?:\.\d{2})?)', # $10,000.00
            r'budget[:\s]+\$?([\d,]+)',    # Budget: 50000
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    amount = match.group(1).replace(',', '')
                    val = float(amount)
                    # Simple heuristic filter: 
                    # Ignore values < 1000 (likely not a budget) 
                    # Ignore values > 100,000,000 (likely a phone number or error)
                    if 1000 < val < 100000000: 
                        return val
                except:
                    pass
        return 0.0

    def _extract_keywords(self, text: str) -> List[str]:
        """Simple keyword matching"""
        keywords = []
        terms = [
            'manufacturing', 'industrial', 'components', 'assembly',
            'parts', 'materials', 'automation', 'precision', 'coating',
            'welding', 'fabrication', 'machining', 'logistics', 'software', 'ai',
            'cloud', 'database', 'api'
        ]
        
        text_lower = text.lower()
        for term in terms:
            if term in text_lower:
                keywords.append(term)
        
        return keywords[:5]