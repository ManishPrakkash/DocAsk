#!/usr/bin/env python3
"""
Test script to verify MongoDB Atlas connection
"""
import asyncio
import logging
from app.database import connect_to_mongo, close_mongo_connection, get_users_collection
from app.auth import create_user, authenticate_user
from app.schemas import UserCreate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_mongodb_connection():
    """Test MongoDB Atlas connection"""
    try:
        logger.info("Testing MongoDB Atlas connection...")
        
        # Connect to MongoDB
        await connect_to_mongo()
        logger.info("✅ Successfully connected to MongoDB Atlas")
        
        # Test user creation
        test_user = UserCreate(
            email="test2@example.com",
            password="TestPass123"
        )
        
        logger.info("Testing user creation...")
        try:
            created_user = await create_user(test_user)
            
            if created_user:
                logger.info(f"✅ Successfully created user: {created_user.email}")
                
                # Test user authentication
                logger.info("Testing user authentication...")
                authenticated_user = await authenticate_user("test2@example.com", "TestPass123")
                
                if authenticated_user:
                    logger.info(f"✅ Successfully authenticated user: {authenticated_user.email}")
                else:
                    logger.error("❌ User authentication failed")
            else:
                logger.error("❌ User creation failed - user already exists or other error")
        except Exception as e:
            logger.error(f"❌ User creation error: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Test database operations
        users_collection = get_users_collection()
        user_count = await users_collection.count_documents({})
        logger.info(f"✅ Total users in database: {user_count}")
        
    except Exception as e:
        logger.error(f"❌ Connection test failed: {e}")
        raise
    finally:
        await close_mongo_connection()
        logger.info("Connection closed")

if __name__ == "__main__":
    asyncio.run(test_mongodb_connection())
