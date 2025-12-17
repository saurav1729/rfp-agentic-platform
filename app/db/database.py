from pymongo import MongoClient
from pymongo.collection import Collection
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)

# MongoDB client and database
_client: MongoClient = None
_db = None

def get_mongodb_client() -> MongoClient:
    """Get MongoDB client instance"""
    global _client
    if _client is None:
        try:
            print(settings.MONGO_URI)
            _client = MongoClient(settings.MONGO_URI)
            # Test connection
            _client.admin.command('ping')
            logger.info(f"✓ Connected to MongoDB at {settings.MONGO_URI}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
    return _client

def get_database():
    """Get MongoDB database instance"""
    global _db
    if _db is None:
        client = get_mongodb_client()
        _db = client[settings.MONGODB_DB]
        logger.info(f"✓ Using database: {settings.MONGODB_DB}")
    return _db

def init_db():
    """Initialize database collections and indexes"""
    db = get_database()
    
    # Create collections if they don't exist
    collections_to_create = {
        "rfps": [
            ("external_id", 1),
            ("title", 1),
            ("status", 1),
            ("discovered_at", -1),
            ("source_url", 1),
        ]
    }
    
    for collection_name, indexes in collections_to_create.items():
        if collection_name not in db.list_collection_names():
            db.create_collection(collection_name)
            logger.info(f"✓ Created collection: {collection_name}")
        
        collection = db[collection_name]
        
        # Create indexes
        for field_name, direction in indexes:
            try:
                collection.create_index(field_name, direction)
            except:
                pass
        
        logger.info(f"✓ Indexes created for {collection_name}")

def close_db():
    """Close MongoDB connection"""
    global _client
    if _client:
        _client.close()
        _client = None
        logger.info("MongoDB connection closed")
