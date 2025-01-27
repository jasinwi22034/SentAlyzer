import sqlite3

def get_db_connection():
    """Stellt eine Verbindung zur SQLite-Datenbank her."""
    conn = sqlite3.connect('database/amazon_reviews.db')
    conn.row_factory = sqlite3.Row
    return conn
