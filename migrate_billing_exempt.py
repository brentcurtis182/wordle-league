"""
Add users.billing_exempt and mark the owner account.

A billing-exempt account's leagues are always free — every league it owns, now
and in future. Separate from `role = 'admin'` on purpose: promoting someone to
admin should not quietly hand them free leagues.

Idempotent. Safe to run more than once, and safe to run against staging or prod.

    python migrate_billing_exempt.py                      # uses DATABASE_URL
    python migrate_billing_exempt.py "<connection-url>"   # or an explicit URL
"""
import os
import sys

import psycopg2

EXEMPT_EMAILS = ['brentcurtis182@hotmail.com']


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('DATABASE_URL')
    if not url:
        print("ERROR: pass a connection URL or set DATABASE_URL")
        return 1

    conn = psycopg2.connect(url)
    conn.autocommit = False
    cur = conn.cursor()

    try:
        cur.execute("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS billing_exempt BOOLEAN NOT NULL DEFAULT FALSE
        """)
        print("  OK   users.billing_exempt exists")

        for email in EXEMPT_EMAILS:
            cur.execute(
                "UPDATE users SET billing_exempt = TRUE WHERE email = %s AND billing_exempt IS NOT TRUE",
                (email,),
            )
            if cur.rowcount:
                print(f"  SET  {email} -> billing_exempt = TRUE")
            else:
                cur.execute("SELECT 1 FROM users WHERE email = %s", (email,))
                if cur.fetchone():
                    print(f"  keep {email} (already exempt)")
                else:
                    print(f"  WARN {email} not found — nothing marked")

        conn.commit()

        cur.execute("SELECT id, email FROM users WHERE billing_exempt IS TRUE ORDER BY id")
        rows = cur.fetchall()
        print(f"\n  billing-exempt accounts ({len(rows)}):")
        for uid, email in rows:
            print(f"    {uid}  {email}")

        return 0
    except Exception as e:
        conn.rollback()
        print(f"ERROR: {e}")
        return 1
    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    raise SystemExit(main())
