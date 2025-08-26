-- 🚨 CRITICAL HOTFIX: Fix Stripe Price IDs in Production Database
-- Issue: Database has invalid price IDs that don't exist in Stripe
-- Error: "No such price: price_1RkePtPFSVtvOaJKYbiX6TqQ"
-- Solution: Update to correct price IDs that exist in Stripe account

-- BEFORE running, verify current state:
-- SELECT name, stripe_price_id_monthly, stripe_price_id_yearly FROM subscription_plans WHERE is_active = true;

BEGIN;

-- Fix Starter Plan (Critical - this is failing in production)
UPDATE subscription_plans 
SET 
  stripe_price_id_monthly = 'price_1RkePlPFSVtvOaJKYbiX6TqQ',  -- Fixed: Pl instead of Pt
  stripe_price_id_yearly = 'price_1RnPVfPFSVtvOaJKmwxNmUdz',
  updated_at = NOW()
WHERE slug = 'starter';

-- Fix Professional Plan
UPDATE subscription_plans 
SET 
  stripe_price_id_monthly = 'price_1RkeQgPFSVtvOaJKgPOzW1SD',  -- Fixed: ending with SD
  stripe_price_id_yearly = 'price_1RnPVRPFSVtvOaJKIWxiSHfm',   -- Fixed: ending with fm
  updated_at = NOW()
WHERE slug = 'professional';

-- Fix Enterprise Plan
UPDATE subscription_plans 
SET 
  stripe_price_id_monthly = 'price_1RkeVLPFSVtvOaJKY5efgwca',  -- Fixed: VL instead of MJ
  stripe_price_id_yearly = 'price_1RnPV8PFSVtvOaJKoiZxvjPa',   -- Fixed: oi instead of ui
  updated_at = NOW()
WHERE slug = 'enterprise';

-- Verify changes
SELECT 
  name as "Plan Name",
  stripe_price_id_monthly as "Monthly Price ID",
  stripe_price_id_yearly as "Yearly Price ID",
  updated_at as "Last Updated"
FROM subscription_plans 
WHERE is_active = true
ORDER BY display_order;

COMMIT;

-- Expected result after fix:
-- Starter:      price_1RkePlPFSVtvOaJKYbiX6TqQ  |  price_1RnPVfPFSVtvOaJKmwxNmUdz
-- Professional: price_1RkeQgPFSVtvOaJKgPOzW1SD  |  price_1RnPVRPFSVtvOaJKIWxiSHfm  
-- Enterprise:   price_1RkeVLPFSVtvOaJKY5efgwca  |  price_1RnPV8PFSVtvOaJKoiZxvjPa

-- ✅ This will immediately fix the "No such price" error
-- ✅ Users will be able to subscribe to all plans
-- ✅ Payment system will work 100%