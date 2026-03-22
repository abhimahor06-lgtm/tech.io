"""
create_super_admin_quick.py
Safe Version with Transaction Handling
"""

from datetime import datetime
import os
import sys
from werkzeug.security import generate_password_hash
from db_connect import db


ADMIN_ID = os.getenv('SUPER_ADMIN_ID', 'ADM001')
USERNAME = os.getenv('SUPER_ADMIN_USERNAME', 'admin_abhi')
PASSWORD = os.getenv('SUPER_ADMIN_PASSWORD')
OFFICIAL_EMAIL = os.getenv('SUPER_ADMIN_EMAIL', 'admin_abhi@poornima.edu')


def main():

    # 🔐 Force password from env
    if not PASSWORD:
        print("❌ SUPER_ADMIN_PASSWORD not set in environment variables.")
        return 1

    try:
        if not db.connect():
            print('❌ Could not connect to database.')
            return 1
    except Exception as e:
        print("❌ Database connection error:", e)
        return 1

    try:
        # ------------------ START TRANSACTION ------------------
        db.connection.start_transaction()

        # Check username
        existing_user = db.fetch_one(
            'SELECT id FROM credentials WHERE username = %s',
            (USERNAME,)
        )
        if existing_user:
            print(f'❌ Username "{USERNAME}" already exists.')
            db.connection.rollback()
            return 1

        # Check email
        existing_email = db.fetch_one(
            'SELECT id FROM credentials WHERE email = %s',
            (OFFICIAL_EMAIL,)
        )
        if existing_email:
            print(f'❌ Email "{OFFICIAL_EMAIL}" already exists.')
            db.connection.rollback()
            return 1

        # Insert admin
        admin_query = '''
        INSERT INTO admins 
        (admin_id, official_email, access_level, security_pin_hash, status, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        '''

        admin_row_id = db.execute_insert(admin_query, (
            ADMIN_ID,
            OFFICIAL_EMAIL,
            'super',
            None,
            'approved',
            datetime.now()
        ))

        if not admin_row_id:
            print('❌ Failed to create admin record')
            db.connection.rollback()
            return 1

        # Insert credentials
        hashed_password = generate_password_hash(PASSWORD)

        cred_query = '''
        INSERT INTO credentials 
        (user_id, role, username, email, password_hash, created_date)
        VALUES (%s, %s, %s, %s, %s, %s)
        '''

        cred_id = db.execute_insert(cred_query, (
            admin_row_id,
            'super_admin',
            USERNAME,
            OFFICIAL_EMAIL,
            hashed_password,
            datetime.now()
        ))

        if not cred_id:
            print('❌ Failed to create credentials')
            db.connection.rollback()
            return 1

        # ------------------ COMMIT ------------------
        db.connection.commit()

        print('\n✅ Super Admin Created Successfully')
        print(f'   Username: {USERNAME}')
        print(f'   Email: {OFFICIAL_EMAIL}')
        print('\nLogin URL: http://localhost:8000/login/adminLogin.html')

        return 0

    except Exception as e:
        print('❌ Error creating super admin:', e)
        db.connection.rollback()
        return 1

    finally:
        db.disconnect()


if __name__ == '__main__':
    sys.exit(main())