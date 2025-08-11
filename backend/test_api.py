#!/usr/bin/env python3
"""
Test script to verify API endpoints
"""
import asyncio
import aiohttp
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"

async def test_health_endpoint():
    """Test health endpoint"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/api/health") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Health check passed: {data}")
                    return True
                else:
                    logger.error(f"❌ Health check failed: {response.status}")
                    return False
    except Exception as e:
        logger.error(f"❌ Health check error: {e}")
        return False

async def test_register_endpoint():
    """Test registration endpoint"""
    try:
        test_user = {
            "email": "test3@example.com",
            "password": "TestPass123"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BASE_URL}/api/auth/register",
                json=test_user
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    logger.info(f"✅ Registration successful: {data}")
                    return True
                else:
                    error_data = await response.text()
                    logger.error(f"❌ Registration failed: {response.status} - {error_data}")
                    return False
    except Exception as e:
        logger.error(f"❌ Registration error: {e}")
        return False

async def test_login_endpoint():
    """Test login endpoint"""
    try:
        test_credentials = {
            "email": "test3@example.com",
            "password": "TestPass123"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BASE_URL}/api/auth/login",
                json=test_credentials
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Login successful: {data}")
                    return data.get("access_token")
                else:
                    error_data = await response.text()
                    logger.error(f"❌ Login failed: {response.status} - {error_data}")
                    return None
    except Exception as e:
        logger.error(f"❌ Login error: {e}")
        return None

async def test_profile_endpoint(token):
    """Test profile endpoint with authentication"""
    if not token:
        logger.error("❌ No token provided for profile test")
        return False
        
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{BASE_URL}/api/user/profile",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Profile fetch successful: {data}")
                    return True
                else:
                    error_data = await response.text()
                    logger.error(f"❌ Profile fetch failed: {response.status} - {error_data}")
                    return False
    except Exception as e:
        logger.error(f"❌ Profile fetch error: {e}")
        return False

async def main():
    """Run all tests"""
    logger.info("🚀 Starting API tests...")
    
    # Test health endpoint
    health_ok = await test_health_endpoint()
    if not health_ok:
        logger.error("❌ Health check failed - server may not be running")
        return
    
    # Test registration
    register_ok = await test_register_endpoint()
    if not register_ok:
        logger.error("❌ Registration test failed")
        return
    
    # Test login
    token = await test_login_endpoint()
    if not token:
        logger.error("❌ Login test failed")
        return
    
    # Test profile with token
    profile_ok = await test_profile_endpoint(token)
    if not profile_ok:
        logger.error("❌ Profile test failed")
        return
    
    logger.info("🎉 All API tests passed!")

if __name__ == "__main__":
    asyncio.run(main())
