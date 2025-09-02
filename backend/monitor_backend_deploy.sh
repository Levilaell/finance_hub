#!/bin/bash

echo "🚀 MONITORING BACKEND DEPLOYMENT STATUS"
echo "======================================="
echo "Target commit: 9c3664e (ULTRA-DRASTIC FIX v2.0)"
echo "Previous commit: a03350d (old version)"
echo ""

# Check current backend commit
check_commit() {
    echo "⏰ $(date '+%H:%M:%S') - Checking backend commit..."
    
    CURRENT_COMMIT=$(railway status --json 2>/dev/null | jq -r '.services.edges[] | select(.node.name=="backend") | .node.serviceInstances.edges[0].node.latestDeployment.meta.commitHash' | cut -c1-7)
    
    if [ "$CURRENT_COMMIT" = "9c3664e" ]; then
        echo "✅ SUCCESS! Backend updated to commit 9c3664e"
        echo "🎯 ULTRA-DRASTIC FIX v2.0 is now active!"
        echo "🔥 Poison pill v2.0 should be working"
        echo "🛡️  RSA keys purged, HS256 forced"
        return 0
    elif [ "$CURRENT_COMMIT" = "a03350d" ]; then
        echo "⚠️  Backend still on old commit a03350d"
        echo "⏳ Waiting for Railway to process redeploy..."
        return 1
    else
        echo "❓ Unknown commit: $CURRENT_COMMIT"
        return 1
    fi
}

# Monitor for up to 5 minutes
for i in {1..10}; do
    if check_commit; then
        echo ""
        echo "🚀 READY TO TEST AUTHENTICATION!"
        echo "Expected behavior:"
        echo "  - Login should work with HS256 JWT"
        echo "  - No more RSA key conflicts" 
        echo "  - Poison pill should be silent (not executing)"
        exit 0
    fi
    
    if [ $i -lt 10 ]; then
        echo "   Attempt $i/10 - Next check in 30 seconds..."
        sleep 30
    fi
done

echo ""
echo "❌ TIMEOUT: Backend still not updated after 5 minutes"
echo "🚨 CRITICAL: Railway deployment system may be broken"
echo "Manual intervention required"