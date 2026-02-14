-- Migration: Add subscription plan and request tracking
-- Date: 2026-02-09
-- Description: Adds support for free trial requests and subscription-based request limits

-- Add new columns to user_subscriptions table
ALTER TABLE user_subscriptions 
ADD COLUMN IF NOT EXISTS stripe_subscription_id TEXT,
ADD COLUMN IF NOT EXISTS plan_name TEXT DEFAULT 'free',
ADD COLUMN IF NOT EXISTS billing_cycle TEXT,
ADD COLUMN IF NOT EXISTS subscription_status TEXT DEFAULT 'inactive',
ADD COLUMN IF NOT EXISTS trial_start_date TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS trial_end_date TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS trial_requests_total INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS trial_requests_remaining INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS plan_requests_total INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS plan_requests_remaining INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS plan_requests_reset_date TIMESTAMPTZ;

-- Update existing records to have default values
UPDATE user_subscriptions 
SET 
    plan_name = COALESCE(plan_name, 'free'),
    subscription_status = COALESCE(subscription_status, 'inactive'),
    trial_requests_total = COALESCE(trial_requests_total, 0),
    trial_requests_remaining = COALESCE(trial_requests_remaining, 0),
    plan_requests_total = COALESCE(plan_requests_total, 0),
    plan_requests_remaining = COALESCE(plan_requests_remaining, 0)
WHERE plan_name IS NULL OR subscription_status IS NULL;

-- Add comment to table
COMMENT ON TABLE user_subscriptions IS 'Stores user subscription information including free trial and plan-based request limits';

-- Add comments to new columns
COMMENT ON COLUMN user_subscriptions.stripe_subscription_id IS 'Stripe subscription ID for recurring billing';
COMMENT ON COLUMN user_subscriptions.plan_name IS 'Subscription plan name: free, starter, professional, enterprise, enterprise_plus';
COMMENT ON COLUMN user_subscriptions.billing_cycle IS 'Billing cycle: monthly or annual';
COMMENT ON COLUMN user_subscriptions.subscription_status IS 'Subscription status: inactive, trial, active, canceled, past_due';
COMMENT ON COLUMN user_subscriptions.trial_start_date IS 'Start date of 14-day free trial';
COMMENT ON COLUMN user_subscriptions.trial_end_date IS 'End date of 14-day free trial';
COMMENT ON COLUMN user_subscriptions.trial_requests_total IS 'Total free requests allocated for trial period';
COMMENT ON COLUMN user_subscriptions.trial_requests_remaining IS 'Remaining free trial requests';
COMMENT ON COLUMN user_subscriptions.plan_requests_total IS 'Total requests included in subscription plan per billing cycle';
COMMENT ON COLUMN user_subscriptions.plan_requests_remaining IS 'Remaining requests from subscription plan';
COMMENT ON COLUMN user_subscriptions.plan_requests_reset_date IS 'Date when plan requests will be reset (monthly/annual)';
