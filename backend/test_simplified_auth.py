#!/usr/bin/env python3
"""
Test simplified authentication
"""
import requests
import json

def test_login():
    """Test login with simplified authentication"""
    base_url = "http://localhost:8000"
    
    # Test data
    login_data = {
        "email": "test@example.com",
        "password": "testpass123"
    }
    
    print("🧪 Testing simplified authentication...")
    
    try:
        # Test login
        response = requests.post(f"{base_url}/api/auth/login/", 
                               json=login_data,
                               headers={'Content-Type': 'application/json'})
        
        print(f"Login response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'access' in data and 'refresh' in data:
                print("✅ Login successful - Bearer tokens received")
                print(f"Access token length: {len(data['access'])}")
                print(f"Refresh token length: {len(data['refresh'])}")
                
                # Test authenticated request
                headers = {'Authorization': f'Bearer {data["access"]}'}
                profile_response = requests.get(f"{base_url}/api/auth/profile/", 
                                              headers=headers)
                
                if profile_response.status_code == 200:
                    print("✅ Authenticated request successful")
                else:
                    print(f"❌ Authenticated request failed: {profile_response.status_code}")
                
                return True
            else:
                print("❌ Login response missing tokens")
                print(f"Response: {data}")
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
    
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
    
    return False

if __name__ == '__main__':
    test_login()
