#!/usr/bin/env python3
"""
Quick test to verify API endpoints
"""
import requests
import time

def test_api():
    base_url = "http://127.0.0.1:8000"
    
    print("Testing API endpoints...")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        print(f"Health check: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Health check failed: {e}")
    
    # Test registration
    try:
        data = {"email": "test5@example.com", "password": "TestPass123"}
        response = requests.post(f"{base_url}/api/auth/register", json=data, timeout=5)
        print(f"Registration: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Registration failed: {e}")
    
    # Test login
    try:
        data = {"email": "test5@example.com", "password": "TestPass123"}
        response = requests.post(f"{base_url}/api/auth/login", json=data, timeout=5)
        print(f"Login: {response.status_code} - {response.text}")
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            if token:
                # Test profile with token
                headers = {"Authorization": f"Bearer {token}"}
                profile_response = requests.get(f"{base_url}/api/user/profile", headers=headers, timeout=5)
                print(f"Profile: {profile_response.status_code} - {profile_response.text}")
    except Exception as e:
        print(f"Login/Profile failed: {e}")

if __name__ == "__main__":
    test_api()
