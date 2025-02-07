import sqlite3
import pandas as pd

# Pfad zur CSV-Datei
csv_file_path = '../data/cleaned_amazon_product_reviews.csv'
db_file_path = 'amazon_reviews.db'

# Schritt 1: Verbindung zur SQLite-Datenbank herstellen (oder erstellen)
conn = sqlite3.connect(db_file_path)
cursor = conn.cursor()

# Schritt 2: Tabelle der Testdaten erstellen
cursor.execute('''
    CREATE TABLE IF NOT EXISTS reviews (
        product_id TEXT PRIMARY KEY,
        product_name TEXT,
        review_text TEXT,
        rating INTEGER
    )
''')

# Tabelle für Metadaten der Analysen
cursor.execute('''
    CREATE TABLE IF NOT EXISTS analysis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')

# Tabelle für die Sentiment-Analysen
cursor.execute('''
    CREATE TABLE IF NOT EXISTS sentiment_analysis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        analysis_id INTEGER NOT NULL,
        review_text TEXT NOT NULL,
        sentiment TEXT NOT NULL,
        FOREIGN KEY (analysis_id) REFERENCES analysis (id)
    )
''')

conn.commit()

# Schritt 3: CSV-Daten lesen
df = pd.read_csv(csv_file_path)

# Schritt 4: Daten in die Datenbank einfügen
df.to_sql('reviews', conn, if_exists='replace', index=False)

# Überprüfen, ob die Daten erfolgreich eingefügt wurden
cursor.execute('SELECT COUNT(*) FROM reviews')
record_count = cursor.fetchone()[0]
print(f"Die Datenbank enthält {record_count} Einträge.")

# Verbindung schließen
conn.close()
