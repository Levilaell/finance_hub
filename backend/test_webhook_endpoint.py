#!/usr/bin/env python
"""Test webhook endpoint accessibility"""
import requests
import json

webhook_url = "https://finance-backend-production-29df.up.railway.app/api/payments/webhooks/stripe/"

print(f"Testing webhook endpoint: {webhook_url}\n")

# Test GET (should return 405 Method Not Allowed)
print("1. Testing GET request:")
try:
    response = requests.get(webhook_url)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:100]}...")
except Exception as e:
    print(f"   Error: {e}")

# Test POST with empty body
print("\n2. Testing POST with empty body:")
try:
    response = requests.post(webhook_url, json={})
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:200]}...")
except Exception as e:
    print(f"   Error: {e}")

# Test OPTIONS (for CORS)
print("\n3. Testing OPTIONS (CORS):")
try:
    response = requests.options(webhook_url)
    print(f"   Status: {response.status_code}")
    print(f"   Headers: {dict(response.headers)}")
except Exception as e:
    print(f"   Error: {e}")

print("\n" + "="*50)
print("IMPORTANT:")
print("1. Make sure the webhook URL in Stripe dashboard is:")
print(f"   {webhook_url}")
print("2. Note the 's' in 'webhooks' (plural)")
print("3. Check that the endpoint ends with a trailing slash '/'")
print("4. The webhook secret should match what's in the .env file")