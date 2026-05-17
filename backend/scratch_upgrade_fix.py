import asyncio
from app.db.supabase_client import db
from app.services.subscription_service import subscription_service

async def fix():
    print('Fetching users with active starter plan and 0 requests...')
    response = db.table('user_subscriptions').select('*').eq('plan_name', 'starter').eq('plan_requests_remaining', 0).execute()
    users = response.data
    for u in users:
        print(f"Fixing user {u.get('user_id')}...")
        await subscription_service.start_subscription(
            user_id=u.get('user_id'),
            plan_name='starter',
            billing_cycle='monthly',
            stripe_customer_id='cus_mock',
            stripe_subscription_id='sub_mock',
            payment_completed=True
        )
        print('Fix complete.')

if __name__ == '__main__':
    asyncio.run(fix())
