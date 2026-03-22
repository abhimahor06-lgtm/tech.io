"""
db_connect.py
Production-Ready Database Connection Module
"""

import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()


class Database:

    def __init__(self):
        self.connection = None
        self.config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'university_db'),
            'auth_plugin': 'mysql_native_password',
            'connection_timeout': 10
        }

    # ------------------ CONNECTION ------------------

    def connect(self):
        try:
            if self.connection and self.connection.is_connected():
                return True

            self.connection = mysql.connector.connect(**self.config)

            if self.connection.is_connected():
                return True

        except Error as e:
            print(f"Connection Error: {e}")
            return False

    def ensure_connection(self):
        """Make sure we have a live connection; reconnect if ping fails.
        Some versions of mysql-connector may raise odd errors (IndexError) during ping,
        so catch those and attempt a fresh connect.
        """
        try:
            if self.connection:
                try:
                    if self.connection.is_connected():
                        return True
                except Exception as e:
                    # ping/keepalive error - force reconnect
                    print(f"Ping error detected, reconnecting: {e}")
                    try:
                        self.connection.close()
                    except Exception:
                        pass
                    return self.connect()
            # no connection yet
            return self.connect()
        except Exception as e:
            print(f"ensure_connection outer exception: {e}")
            return self.connect()

    def disconnect(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()

    # ------------------ QUERY METHODS ------------------

    def execute_query(self, query, params=None):
        try:
            if not self.ensure_connection():
                raise Exception("Database not connected")

            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute(query, params or ())
                return cursor.fetchall()

        except Error as e:
            print(f"Query Error: {e}")
            raise

    def fetch_one(self, query, params=None):
        try:
            if not self.ensure_connection():
                raise Exception("Database not connected")

            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute(query, params or ())
                # consume remaining results to avoid "Unread result found" errors
                result = cursor.fetchone()
                cursor.fetchall()
                return result

        except Error as e:
            print(f"Query Error: {e}")
            raise

    def execute_insert(self, query, params):
        try:
            if not self.ensure_connection():
                raise Exception("Database not connected")

            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                self.connection.commit()
                return cursor.lastrowid

        except Error as e:
            print(f"Insert Error: {e}")
            self.connection.rollback()
            raise

    def execute_update(self, query, params):
        try:
            if not self.ensure_connection():
                raise Exception("Database not connected")

            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                self.connection.commit()
                return cursor.rowcount

        except Error as e:
            print(f"Update Error: {e}")
            self.connection.rollback()
            raise

    def execute_delete(self, query, params):
        try:
            if not self.ensure_connection():
                raise Exception("Database not connected")

            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                self.connection.commit()
                return cursor.rowcount

        except Error as e:
            print(f"Delete Error: {e}")
            self.connection.rollback()
            raise

    # ------------------ TRANSACTION CONTROL ------------------

    def commit(self):
        if self.connection and self.connection.is_connected():
            self.connection.commit()

    def rollback(self):
        if self.connection and self.connection.is_connected():
            self.connection.rollback()


# Global instance
db = Database()
