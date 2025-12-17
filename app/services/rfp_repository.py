"""Repository for RFP MongoDB operations"""
import logging
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from bson.objectid import ObjectId
from app.db.database import get_database
from app.db.models import RFPStatus

logger = logging.getLogger(__name__)

class RFPRepository:
    """Handle all RFP database operations in MongoDB"""
    
    def __init__(self):
        self.db = get_database()
        self.rfp_collection = self.db['rfps']
    
    def create_rfp(self, rfp_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new RFP in MongoDB"""
        # Generate unique ID
        rfp_id = f"rfp_{uuid.uuid4().hex[:8]}"
        
        # Extract external_id if available (CPP ref number)
        external_id = rfp_data.get('external_id')
        
        # Check if RFP with this external_id already exists (deduplication)
        if external_id:
            existing = self.rfp_collection.find_one({'external_id': external_id})
            if existing:
                logger.info(f"RFP with external_id {external_id} already exists, skipping")
                return existing
        
        # Create RFP document
        rfp_doc = {
            '_id': rfp_id,
            'external_id': external_id,
            'title': rfp_data.get('title', 'Unknown'),
            'description': rfp_data.get('description', ''),
            'agency': rfp_data.get('agency', ''),
            'deadline': rfp_data.get('deadline'),
            'source_url': rfp_data.get('source_url', ''),
            'budget_range': rfp_data.get('budget_range'),
            'status': RFPStatus.DISCOVERED,
            'confidence_score': rfp_data.get('confidence_score', 0.0),
            'posted_date': rfp_data.get('posted_date'),
            'raw_data': rfp_data.get('raw_data', {}),
            'discovered_at': datetime.utcnow(),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        try:
            result = self.rfp_collection.insert_one(rfp_doc)
            logger.info(f"✓ Saved RFP to MongoDB: {rfp_id} - {rfp_doc['title']}")
            return rfp_doc
        except Exception as e:
            logger.error(f"Error saving RFP to MongoDB: {str(e)}")
            raise
    
    def get_rfp(self, rfp_id: str) -> Optional[Dict[str, Any]]:
        """Get RFP by ID"""
        return self.rfp_collection.find_one({'_id': rfp_id})
    
    def get_all_rfps(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all RFPs with pagination"""
        return list(self.rfp_collection.find().skip(skip).limit(limit))
    
    def get_rfps_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get RFPs by status"""
        return list(self.rfp_collection.find({'status': status}))
    
    def update_rfp_status(self, rfp_id: str, status: str) -> Optional[Dict[str, Any]]:
        """Update RFP status"""
        result = self.rfp_collection.find_one_and_update(
            {'_id': rfp_id},
            {
                '$set': {
                    'status': status,
                    'updated_at': datetime.utcnow()
                }
            },
            return_document=True
        )
        return result
    
    def bulk_create_rfps(self, rfps_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create multiple RFPs at once"""
        created_rfps = []
        for rfp_data in rfps_data:
            try:
                rfp = self.create_rfp(rfp_data)
                created_rfps.append(rfp)
            except Exception as e:
                logger.error(f"Error creating RFP: {str(e)}")
        return created_rfps
    
    def get_rfp_count(self) -> int:
        """Get total RFP count"""
        return self.rfp_collection.count_documents({})
    
    def get_rfp_by_external_id(self, external_id: str) -> Optional[Dict[str, Any]]:
        """Get RFP by external_id (CPP ref number)"""
        return self.rfp_collection.find_one({'external_id': external_id})
    
    def get_rfps_discovered_after(self, timestamp: datetime) -> List[Dict[str, Any]]:
        """Get RFPs discovered after a specific time"""
        return list(self.rfp_collection.find({'discovered_at': {'$gte': timestamp}}))
    
    def delete_rfp(self, rfp_id: str) -> bool:
        """Delete an RFP"""
        result = self.rfp_collection.delete_one({'_id': rfp_id})
        return result.deleted_count > 0
