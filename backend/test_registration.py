#!/usr/bin/env python3
"""
Test registration with proper validation
"""
import requests
import json

def test_registration():
    base_url = "http://127.0.0.1:8000"
    
    # Test with valid data
    valid_user = {
        "email": "test7@example.com",
        "password": "TestPass123"
    }
    
    print("Testing registration with valid data...")
    try:
        response = requests.post(f"{base_url}/api/auth/register", json=valid_user, timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ Registration successful!")
            
            # Test login with the same credentials
            print("\nTesting login with registered credentials...")
            login_response = requests.post(f"{base_url}/api/auth/login", json=valid_user, timeout=5)
            print(f"Login Status: {login_response.status_code}")
            print(f"Login Response: {login_response.text}")
            
        elif response.status_code == 422:
            print("❌ Validation error - check the response for details")
            error_data = response.json()
            print(f"Error details: {json.dumps(error_data, indent=2)}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_registration()
