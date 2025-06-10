import psycopg2
import sys

def dbconnect():
    try:
        conn = psycopg2.connect(
            user="postgres",
            password="2002",  #"password1",
            host="192.168.0.39",
            port=12345,
            database="Eksamen"
        )
        conn.autocommit = True
    except psycopg2.Error as e:
        print(f"Error connecting to PostgreSQL: {e}")
        sys.exit(1)
    return conn