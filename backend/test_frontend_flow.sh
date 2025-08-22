#!/bin/bash

echo "🧪 TESTING COMPLETE FRONTEND FLOW"
echo "================================="

# Step 1: Login
echo "1. 🔐 Testing login..."
LOGIN_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/auth/login/" \
  -H "Content-Type: application/json" \
  -H "X-Requested-With: XMLHttpRequest" \
  -d '{"email": "test@test.com", "password": "test123"}' \
  -c test_cookies.txt)

if echo "$LOGIN_RESPONSE" | grep -q '"email"'; then
  echo "   ✅ Login successful"
  HAS_COMPANY=$(echo "$LOGIN_RESPONSE" | jq -r '.user.company != null')
  echo "   📋 Has company: $HAS_COMPANY"
else
  echo "   ❌ Login failed"
  echo "$LOGIN_RESPONSE"
  exit 1
fi

# Step 2: Test all endpoints that useReportData calls
echo -e "\n2. 📊 Testing reports endpoint..."
REPORTS_RESPONSE=$(curl -s -X GET "http://localhost:8000/api/reports/reports/" \
  -H "Accept: application/json" \
  -H "X-Requested-With: XMLHttpRequest" \
  -b test_cookies.txt)

REPORTS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X GET "http://localhost:8000/api/reports/reports/" \
  -H "Accept: application/json" \
  -H "X-Requested-With: XMLHttpRequest" \
  -b test_cookies.txt)

echo "   Status: $REPORTS_STATUS"
if [ "$REPORTS_STATUS" = "200" ]; then
  REPORTS_COUNT=$(echo "$REPORTS_RESPONSE" | jq '.results | length // length')
  echo "   ✅ Reports: $REPORTS_COUNT items"
else
  echo "   ❌ Reports failed"
  echo "   Response: $REPORTS_RESPONSE"
fi

echo -e "\n3. 🏦 Testing accounts endpoint..."
ACCOUNTS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X GET "http://localhost:8000/api/banking/accounts/" \
  -H "Accept: application/json" \
  -H "X-Requested-With: XMLHttpRequest" \
  -b test_cookies.txt)

echo "   Status: $ACCOUNTS_STATUS"
if [ "$ACCOUNTS_STATUS" = "200" ]; then
  ACCOUNTS_RESPONSE=$(curl -s -X GET "http://localhost:8000/api/banking/accounts/" \
    -H "Accept: application/json" \
    -H "X-Requested-With: XMLHttpRequest" \
    -b test_cookies.txt)
  ACCOUNTS_COUNT=$(echo "$ACCOUNTS_RESPONSE" | jq 'length')
  echo "   ✅ Accounts: $ACCOUNTS_COUNT items"
else
  echo "   ❌ Accounts failed"
fi

echo -e "\n4. 📝 Testing categories endpoint..."
CATEGORIES_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X GET "http://localhost:8000/api/banking/categories/" \
  -H "Accept: application/json" \
  -H "X-Requested-With: XMLHttpRequest" \
  -b test_cookies.txt)

echo "   Status: $CATEGORIES_STATUS"
if [ "$CATEGORIES_STATUS" = "200" ]; then
  CATEGORIES_RESPONSE=$(curl -s -X GET "http://localhost:8000/api/banking/categories/" \
    -H "Accept: application/json" \
    -H "X-Requested-With: XMLHttpRequest" \
    -b test_cookies.txt)
  CATEGORIES_COUNT=$(echo "$CATEGORIES_RESPONSE" | jq 'length')
  echo "   ✅ Categories: $CATEGORIES_COUNT items"
else
  echo "   ❌ Categories failed"
fi

echo -e "\n📋 SUMMARY:"
echo "=========="
if [ "$REPORTS_STATUS" = "200" ] && [ "$ACCOUNTS_STATUS" = "200" ] && [ "$CATEGORIES_STATUS" = "200" ]; then
  echo "✅ ALL ENDPOINTS WORKING - Backend is functioning correctly"
  echo "🔍 The issue must be in the frontend code or browser environment"
  echo ""
  echo "💡 NEXT STEPS:"
  echo "   1. Check browser dev tools Network tab"
  echo "   2. Verify if cookies are being sent from frontend"
  echo "   3. Check if frontend is pointing to correct URL"
  echo "   4. Verify user is actually logged in on frontend"
else
  echo "❌ Some endpoints failed - issue is in backend"
fi

# Cleanup
rm -f test_cookies.txt

