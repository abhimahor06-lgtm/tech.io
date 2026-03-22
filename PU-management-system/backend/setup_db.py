#!/usr/bin/env python3
"""
setup_db.py
Safe Database Setup Script
"""

import mysql.connector
import sys
from getpass import getpass
import os

DB_NAME = "university_db"
SQL_FILE = "database/university-db.sql"

try:
    # Secure password input
    password = getpass('Enter MySQL root password: ')

    # Connect to MySQL
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password=password,
        autocommit=False
    )

    cursor = conn.cursor()
    print('✅ MySQL connection successful')

    if not os.path.exists(SQL_FILE):
        raise FileNotFoundError(f'SQL file not found: {SQL_FILE}')

    print('📦 Creating database from schema file...')

    with open(SQL_FILE, 'r', encoding='utf-8') as f:
        sql_script = f.read()

    # Execute multi-statement safely
    for result in cursor.execute(sql_script, multi=True):
        try:
            pass  # Just execute
        except Exception as e:
            if "already exists" not in str(e):
                print(f'⚠️ Warning: {str(e)[:100]}')

    conn.commit()
    print('✅ SQL script executed successfully')

    # Verify database exists
    cursor.execute(f'SHOW DATABASES LIKE "{DB_NAME}"')
    if cursor.fetchone():
        print(f'✅ Database "{DB_NAME}" verified')

        cursor.execute(f'USE {DB_NAME}')
        cursor.execute('SHOW TABLES')
        tables = cursor.fetchall()
        print(f'   Tables created: {len(tables)}')
    else:
        print(f'⚠️ Database "{DB_NAME}" not found after execution')

    cursor.close()
    conn.close()

    print('')
    print('╔════════════════════════════════════════════════════════════════╗')
    print('║              ✅ Database Setup Complete!                      ║')
    print('╚════════════════════════════════════════════════════════════════╝')

except mysql.connector.Error as e:
    print(f'❌ MySQL Error: {e}')
    sys.exit(1)

except FileNotFoundError as e:
    print(f'❌ {e}')
    sys.exit(1)

except Exception as e:
    print(f'❌ Error: {e}')
    sys.exit(1)