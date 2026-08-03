#!/usr/bin/env python3
"""Rename the Slack Stripe product so Discord managers aren't confused at checkout.

Stripe Checkout renders its header from the PRODUCT name ("Try Slack League"),
not from anything we send. Discord maps to plan_type='slack' and buys the exact
same product, so a Discord manager was being told they were subscribing to
Slack.

Renames the product referenced by admin_config['stripe_product_slack'] to
"Slack/Discord League". Read-only on prices; only the product name changes, so
existing subscriptions and price IDs are untouched.

Run once per environment (the key decides which):

    # staging / sandbox
    STRIPE_SECRET_KEY="sk_test_..." DATABASE_URL="<staging_url>" python rename_stripe_products.py

    # production / live
    STRIPE_SECRET_KEY="sk_live_..." DATABASE_URL="<prod_url>" python rename_stripe_products.py

Pass --dry-run to see what would change without writing.
"""
import os
import sys
import stripe
import psycopg2

NEW_NAME = "Slack/Discord League"


def main():
    dry_run = '--dry-run' in sys.argv

    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
    database_url = os.environ.get('DATABASE_URL')
    if not stripe.api_key:
        raise SystemExit("STRIPE_SECRET_KEY not set")
    if not database_url:
        raise SystemExit("DATABASE_URL not set")

    mode = 'LIVE' if stripe.api_key.startswith('sk_live_') else 'TEST'
    print(f"Stripe mode: {mode}")

    conn = psycopg2.connect(database_url)
    cur = conn.cursor()
    cur.execute("SELECT value FROM admin_config WHERE key = 'stripe_product_slack'")
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row or not row[0]:
        raise SystemExit("No stripe_product_slack configured in admin_config")

    product_id = row[0]
    product = stripe.Product.retrieve(product_id)
    print(f"Product {product_id}")
    print(f"  current name: {product['name']}")
    print(f"  new name    : {NEW_NAME}")

    if product['name'] == NEW_NAME:
        print("Already named correctly — nothing to do.")
        return

    if dry_run:
        print("(dry run — no changes written)")
        return

    stripe.Product.modify(product_id, name=NEW_NAME)
    print("Renamed. Stripe Checkout will now read 'Try Slack/Discord League'.")


if __name__ == '__main__':
    main()
