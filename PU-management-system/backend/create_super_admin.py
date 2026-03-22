#!/usr/bin/env python3
"""
create_super_admin.py
Safe & Transaction-Protected Version
"""

import sys
import os
from getpass import getpass
from datetime import datetime
from werkzeug.security import generate_password_hash

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from db_connect import db


def create_super_admin():
    print("=" * 70)
    print("SUPER ADMIN ACCOUNT CREATION")
    print("=" * 70)

    try:
        if not db.connect():
            print("\n❌ Failed to connect to database.")
            return False
    except Exception as e:
        print("\n❌ Database connection error:", e)
        return False

    try:
        print("\n📝 Enter Super Admin Details:")

        admin_id = input("\nAdmin ID (e.g., ADM001): ").strip()
        if not admin_id:
            print("❌ Admin ID is required")
            return False

        official_email = input("Official Email: ").strip()
        if not official_email or '@' not in official_email:
            print("❌ Valid email is required")
            return False

        username = input("Username for login: ").strip()
        if not username or len(username) < 3:
            print("❌ Username must be at least 3 characters")
            return False

        password = getpass("Password (minimum 8 characters): ").strip()
        if not password or len(password) < 8:
            print("❌ Password must be at least 8 characters")
            return False

        confirm_password = getpass("Confirm Password: ").strip()
        if password != confirm_password:
            print("❌ Passwords do not match")
            return False

        # ------------------ START TRANSACTION ------------------
        db.connection.start_transaction()

        # Username check
        if db.fetch_one('SELECT id FROM credentials WHERE username = %s', (username,)):
            print(f"❌ Username '{username}' already exists")
            db.connection.rollback()
            return False

        # Email check
        if db.fetch_one('SELECT id FROM credentials WHERE email = %s', (official_email,)):
            print(f"❌ Email '{official_email}' already exists")
            db.connection.rollback()
            return False

        if db.fetch_one('SELECT id FROM admins WHERE official_email = %s', (official_email,)):
            print(f"❌ Email '{official_email}' already exists in admins")
            db.connection.rollback()
            return False

        print("\n🔐 Creating admin account...")

        # Insert admin
        admin_query = '''
        INSERT INTO admins 
        (admin_id, official_email, access_level, status, created_at)
        VALUES (%s, %s, %s, %s, %s)
        '''

        admin_row_id = db.execute_insert(admin_query, (
            admin_id,
            official_email,
            'super',
            'approved',
            datetime.now()
        ))

        if not admin_row_id:
            print("❌ Failed to create admin record")
            db.connection.rollback()
            return False

        # Hash password
        hashed_password = generate_password_hash(password)

        # Insert credentials
        credentials_query = '''
        INSERT INTO credentials 
        (user_id, role, username, email, password_hash, created_date)
        VALUES (%s, %s, %s, %s, %s, %s)
        '''

        cred_result = db.execute_insert(credentials_query, (
            admin_row_id,
            'super_admin',
            username,
            official_email,
            hashed_password,
            datetime.now()
        ))

        if not cred_result:
            print("❌ Failed to create credentials record")
            db.connection.rollback()
            return False

        # ------------------ COMMIT ------------------
        db.connection.commit()

        print("\n" + "=" * 70)
        print("✅ SUPER ADMIN ACCOUNT CREATED SUCCESSFULLY!")
        print("=" * 70)
        print(f"\n📋 Admin ID: {admin_id}")
        print(f"📧 Email: {official_email}")
        print(f"👤 Username: {username}")
        print("\n💡 Login at: http://localhost:8000/login/adminLogin.html")
        print("=" * 70 + "\n")

        return True

    except Exception as e:
        print(f"\n❌ Error creating super admin: {e}")
        db.connection.rollback()
        return False

    finally:
        db.disconnect()


if __name__ == '__main__':
    success = create_super_admin()
    sys.exit(0 if success else 1)