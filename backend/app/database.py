from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from decouple import config
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Updated MongoDB connection string with correct parameters
MONGODB_URL = config(
    'MONGODB_URL',
    default='mongodb+srv://manishprakkash:xV9Y03RpU5RBFS9k@cluster0.skvvuc9.mongodb.net/clausewise?retryWrites=true&w=majority&appName=Cluster0'
)

# MongoDB client
client: Optional[AsyncIOMotorClient] = None
sync_client: Optional[MongoClient] = None

async def connect_to_mongo():
    """Create database connection"""
    global client, sync_client
    try:
        # Connection options optimized for MongoDB Atlas
        client_options = {
            'serverSelectionTimeoutMS': 30000,  # Increased timeout for Atlas
            'connectTimeoutMS': 30000,
            'socketTimeoutMS': 30000,
            'maxPoolSize': 50,  # Increased pool size for Atlas
            'minPoolSize': 5,
            'maxIdleTimeMS': 30000,
            'retryWrites': True,
            'w': 'majority',
            'retryReads': True,  # Enable retry reads for Atlas
            'compressors': ['zlib'],  # Enable compression for Atlas
            'zlibCompressionLevel': 6
        }
        
        logger.info(f"Attempting to connect to MongoDB Atlas...")
        client = AsyncIOMotorClient(MONGODB_URL, **client_options)
        sync_client = MongoClient(MONGODB_URL, **client_options)
        
        # Test the connection
        await client.admin.command('ping', maxTimeMS=10000)
        logger.info("Successfully connected to MongoDB Atlas")
        
        # Test database access
        db = client.clausewise
        await db.command('ping')
        logger.info("Database access confirmed")
        
        return client
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB Atlas: {e}")
        # Try alternative connection with minimal options
        try:
            logger.info("Attempting connection with minimal options...")
            client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=30000)
            sync_client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=30000)
            
            await client.admin.command('ping', maxTimeMS=10000)
            logger.info("Successfully connected to MongoDB Atlas with minimal options")
            return client
        except Exception as alt_e:
            logger.error(f"Alternative connection also failed: {alt_e}")
            logger.error("Please check your MongoDB Atlas connection string and network connectivity")
            raise

async def close_mongo_connection():
    """Close database connection"""
    global client, sync_client
    if client:
        client.close()
    if sync_client:
        sync_client.close()
    logger.info("MongoDB connection closed")

def get_database():
    """Get database instance"""
    if not client:
        raise RuntimeError("Database not connected. Call connect_to_mongo() first.")
    return client.clausewise

def get_sync_database():
    """Get synchronous database instance"""
    if not sync_client:
        raise RuntimeError("Database not connected. Call connect_to_mongo() first.")
    return sync_client.clausewise

# Database collections
def get_users_collection():
    """Get users collection"""
    return get_database().users

def get_documents_collection():
    """Get documents collection"""
    return get_database().documents

def get_clauses_collection():
    """Get clauses collection"""
    return get_database().clauses

def get_legal_playbooks_collection():
    """Get legal playbooks collection"""
    return get_database().legal_playbooks