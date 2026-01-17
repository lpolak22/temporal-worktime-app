import psycopg2

def get_connection():
    return psycopg2.connect(
        host="localhost",
        port=5433,
        database="time_tracking",
        user="postgres",
        password="123"
    )