#!/usr/bin/env python3
"""
Test script for dashboard functionality
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_authentication():
    """Test authentication with test user"""
    login_url = f"{BASE_URL}/api/auth/login/"
    
    # First try to register a new user
    register_url = f"{BASE_URL}/api/auth/register/"
    register_data = {
        "email": "test-api@example.com",
        "password": "test123456",
        "password2": "test123456",
        "first_name": "API",
        "last_name": "Test",
        "phone": "11987654321",
        "company_name": "Test API Company",
        "cnpj": "98765432109876",
        "company_type": "mei",
        "business_sector": "services"
    }
    
    print("Trying to register a new user...")
    register_response = requests.post(register_url, json=register_data)
    print(f"Register response: {register_response.status_code}")
    
    # Now try to login with existing user
    credentials = {
        "email": "test@example.com",
        "password": "test123"
    }
    
    print(f"Trying to authenticate with: {credentials}")
    print(f"URL: {login_url}")
    
    response = requests.post(login_url, json=credentials)
    
    print(f"Response status: {response.status_code}")
    print(f"Response headers: {response.headers}")
    print(f"Response text: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        return data.get('tokens', {}).get('access')
    else:
        print(f"Authentication failed: {response.status_code}")
        print(response.text)
        return None

def test_dashboard_endpoints(token):
    """Test all dashboard endpoints"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    endpoints = [
        "/api/banking/dashboard/",
        "/api/banking/dashboard/enhanced/",
        "/api/banking/analytics/time-series/",
        "/api/banking/analytics/expense-trends/",
        "/api/banking/budgets/",
        "/api/banking/goals/",
    ]
    
    results = {}
    
    for endpoint in endpoints:
        print(f"\nTesting endpoint: {endpoint}")
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
            results[endpoint] = {
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "data_keys": list(response.json().keys()) if response.status_code == 200 else None,
                "error": response.text if response.status_code != 200 else None
            }
            
            if response.status_code == 200:
                print(f"✅ SUCCESS - Status: {response.status_code}")
                data = response.json()
                if isinstance(data, dict):
                    print(f"   Data keys: {list(data.keys())}")
                elif isinstance(data, list):
                    print(f"   Items count: {len(data)}")
            else:
                print(f"❌ FAILED - Status: {response.status_code}")
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)}")
            results[endpoint] = {
                "status_code": None,
                "success": False,
                "error": str(e)
            }
    
    return results

def test_budget_creation(token):
    """Test budget creation"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    budget_data = {
        "name": "Test Budget",
        "description": "Budget de teste para alimentação",
        "budget_type": "monthly",
        "amount": "1000.00",
        "start_date": "2024-05-01",
        "end_date": "2024-05-31",
        "alert_threshold": 80,
        "is_alert_enabled": True
    }
    
    print(f"\nTesting budget creation...")
    try:
        response = requests.post(f"{BASE_URL}/api/banking/budgets/", 
                               json=budget_data, headers=headers)
        
        if response.status_code == 201:
            print(f"✅ Budget created successfully")
            return response.json()
        else:
            print(f"❌ Budget creation failed - Status: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ EXCEPTION during budget creation: {str(e)}")
        return None

def test_goal_creation(token):
    """Test financial goal creation"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    goal_data = {
        "name": "Emergency Fund",
        "description": "Build emergency fund of R$ 10,000",
        "goal_type": "savings",
        "target_amount": "10000.00",
        "target_date": "2024-12-31",
        "is_automatic_tracking": True,
        "send_reminders": True
    }
    
    print(f"\nTesting financial goal creation...")
    try:
        response = requests.post(f"{BASE_URL}/api/banking/goals/", 
                               json=goal_data, headers=headers)
        
        if response.status_code == 201:
            print(f"✅ Financial goal created successfully")
            return response.json()
        else:
            print(f"❌ Goal creation failed - Status: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ EXCEPTION during goal creation: {str(e)}")
        return None

def main():
    """Main test function"""
    print("🔍 Testing Dashboard Functionality")
    print("=" * 50)
    
    # Test authentication
    print("\n1. Testing Authentication...")
    token = test_authentication()
    
    if not token:
        print("❌ Authentication failed. Cannot proceed with tests.")
        sys.exit(1)
    
    print("✅ Authentication successful")
    
    # Test dashboard endpoints
    print("\n2. Testing Dashboard Endpoints...")
    results = test_dashboard_endpoints(token)
    
    # Test budget creation
    print("\n3. Testing Budget Management...")
    budget = test_budget_creation(token)
    
    # Test goal creation
    print("\n4. Testing Goal Management...")
    goal = test_goal_creation(token)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    successful_endpoints = sum(1 for result in results.values() if result['success'])
    total_endpoints = len(results)
    
    print(f"Dashboard Endpoints: {successful_endpoints}/{total_endpoints} successful")
    print(f"Budget Creation: {'✅' if budget else '❌'}")
    print(f"Goal Creation: {'✅' if goal else '❌'}")
    
    if successful_endpoints == total_endpoints and budget and goal:
        print("\n🎉 ALL TESTS PASSED! Dashboard is fully functional.")
    else:
        print("\n⚠️  Some tests failed. Check the logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main()