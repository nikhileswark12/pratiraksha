import datetime
import logging
from django.conf import settings
from pymongo import MongoClient

logger = logging.getLogger(__name__)

_mongo_client = None
_db = None

def get_mongo_db():
    global _mongo_client, _db
    if _db is not None:
        return _db

    try:
        _mongo_client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
        _db = _mongo_client.get_default_database()
    except Exception:
        try:
            _mongo_client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
            db_name = settings.MONGO_URI.split('/')[-1].split('?')[0] or 'pratiraksha'
            _db = _mongo_client[db_name]
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            _mongo_client = None
            _db = None

    return _db

def log_activity(actor, action, resource_type=None, resource_id=None, extra_data=None):
    """
    Logs an activity to the system-wide MongoDB ActivityLog.
    """
    db = get_mongo_db()
    if db is None:
        logger.error(f"Cannot log activity '{action}': MongoDB is unavailable.")
        return False
        
    doc = {
        "actor": actor,
        "action": action,
        "resource_type": resource_type,
        "resource_id": str(resource_id) if resource_id else None,
        "timestamp": datetime.datetime.utcnow(),
    }
    if extra_data:
        doc["extra_data"] = extra_data
        
    try:
        db.activity_log.insert_one(doc)
        return True
    except Exception as e:
        logger.error(f"Failed to log activity to MongoDB: {e}")
        return False

def log_compliance_event(actor, action, resource_type=None, resource_id=None, extra_data=None):
    """
    Logs compliance-sensitive events to the MongoDB compliance_logs collection.
    Matches EHRAccessLog precedent: no TTL, strictly retention-locked.
    """
    db = get_mongo_db()
    if db is None:
        logger.error(f"Cannot log compliance event '{action}': MongoDB is unavailable.")
        return False
        
    doc = {
        "actor": actor,
        "action": action,
        "resource_type": resource_type,
        "resource_id": str(resource_id) if resource_id else None,
        "timestamp": datetime.datetime.utcnow(),
    }
    if extra_data:
        doc["extra_data"] = extra_data
        
    try:
        db.compliance_logs.insert_one(doc)
        return True
    except Exception as e:
        logger.error(f"Failed to log compliance event to MongoDB: {e}")
        return False
