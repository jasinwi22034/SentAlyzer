import sqlite3
import pytest
from models.database import get_db_connection

@pytest.fixture
def db():
    """ Erstellt eine temporäre Datenbankverbindung für Tests """
    conn = sqlite3.connect(":memory:")  # Nutzt eine In-Memory-Datenbank für Tests
    cursor = conn.cursor()

    # Erstelle Testtabellen
    cursor.execute("""
        CREATE TABLE analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE sentiment_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id INTEGER NOT NULL,
            review_text TEXT NOT NULL,
            sentiment TEXT NOT NULL,
            FOREIGN KEY (analysis_id) REFERENCES analysis(id)
        )
    """)

    conn.commit()
    yield conn  # Gibt die Verbindung für Tests zurück
    conn.close()

def test_insert_and_retrieve_analysis(db):
    """ Testet, ob ein Eintrag in die Tabelle 'analysis' korrekt gespeichert und abgerufen wird """
    cursor = db.cursor()
    cursor.execute("INSERT INTO analysis (product_name) VALUES (?)", ("Test Produkt",))
    db.commit()

    cursor.execute("SELECT * FROM analysis WHERE product_name = ?", ("Test Produkt",))
    row = cursor.fetchone()

    assert row is not None
    assert row[1] == "Test Produkt"
