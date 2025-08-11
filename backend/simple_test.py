#!/usr/bin/env python3
"""
Simple test script to verify API endpoints using requests
"""
import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"

def test_health_endpoint():
    """Test health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Health check passed: {data}")
            return True
        else:
            logger.error(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Health check error: {e}")
        return False

def test_register_endpoint():
    """Test registration endpoint"""
    try:
        test_user = {
            "email": "test4@example.com",
            "password": "TestPass123"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json=test_user,
            timeout=10
        )
        
        if response.status_code == 201:
            data = response.json()
            logger.info(f"✅ Registration successful: {data}")
            return True
        else:
            error_data = response.text
            logger.error(f"❌ Registration failed: {response.status_code} - {error_data}")
            return False
    except Exception as e:
        logger.error(f"❌ Registration error: {e}")
        return False

def test_login_endpoint():
    """Test login endpoint"""
    try:
        test_credentials = {
            "email": "test4@example.com",
            "password": "TestPass123"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=test_credentials,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Login successful: {data}")
            return data.get("access_token")
        else:
            error_data = response.text
            logger.error(f"❌ Login failed: {response.status_code} - {error_data}")
            return None
    except Exception as e:
        logger.error(f"❌ Login error: {e}")
        return None

def test_profile_endpoint(token):
    """Test profile endpoint with authentication"""
    if not token:
        logger.error("❌ No token provided for profile test")
        return False
        
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/user/profile",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Profile fetch successful: {data}")
            return True
        else:
            error_data = response.text
            logger.error(f"❌ Profile fetch failed: {response.status_code} - {error_data}")
            return False
    except Exception as e:
        logger.error(f"❌ Profile fetch error: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("🚀 Starting API tests...")
    
    # Test health endpoint
    health_ok = test_health_endpoint()
    if not health_ok:
        logger.error("❌ Health check failed - server may not be running")
        return
    
    # Test registration
    register_ok = test_register_endpoint()
    if not register_ok:
        logger.error("❌ Registration test failed")
        return
    
    # Test login
    token = test_login_endpoint()
    if not token:
        logger.error("❌ Login test failed")
        return
    
    # Test profile with token
    profile_ok = test_profile_endpoint(token)
    if not profile_ok:
        logger.error("❌ Profile test failed")
        return
    
    logger.info("🎉 All API tests passed!")

if __name__ == "__main__":
    main()
