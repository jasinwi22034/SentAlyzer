import pandas as pd
from models.database import get_db_connection
import sqlite3

DB_PATH = "database/amazon_reviews.db"

def handle_csv_upload(file):
    """
    Bearbeitet den Upload einer CSV-Datei und speichert Rezensionen in die Tabelle 'reviews'.
    Falls eine Rezension bereits existiert, wird sie übersprungen.

    Args:
        file (FileStorage): Hochgeladene CSV-Datei

    Returns:
        dict: Status und Produktliste oder Fehlermeldung
    """
    if not file or file.filename == "":
        return {"status": "error", "message": "Keine Datei ausgewählt."}

    try:
        # CSV-Datei direkt aus dem Speicher lesen
        df = pd.read_csv(file)

        print(f"CSV eingelesen: {df.shape[0]} Zeilen")  # Debugging

        # Erwartete Spaltennamen
        required_columns = {"product_name", "review_text"}
        if not required_columns.issubset(df.columns):
            return {"status": "error", "message": "Die CSV muss 'product_name' und 'review_text' enthalten."}

        # Entferne Zeilen mit fehlenden Werten
        df = df.dropna(subset=["product_name", "review_text"])

        # Verbindung zur Datenbank über die bestehende Methode herstellen
        conn = get_db_connection()
        cursor = conn.cursor()

        inserted_products = 0
        inserted_reviews = 0

        for _, row in df.iterrows():
            product_name = row["product_name"]
            review_text = row["review_text"]

            # Überprüfen, ob das Produkt existiert, ansonsten hinzufügen
            cursor.execute("SELECT id FROM analysis WHERE product_name = ?", (product_name,))
            product = cursor.fetchone()

            if product is None:
                cursor.execute("INSERT INTO analysis (product_name) VALUES (?)", (product_name,))
                product_id = cursor.lastrowid
                inserted_products += 1
            else:
                product_id = product["id"]

            # Rezension **immer neu hinzufügen**, jetzt mit `product_name`
            cursor.execute(
                "INSERT INTO reviews (product_id, product_name, review_text) VALUES (?, ?, ?)",
                (product_id, product_name, review_text),
            )
            inserted_reviews += 1

            print(f"Neue Rezension hinzugefügt für {product_name}: {review_text}")  # Debugging

        conn.commit()
        conn.close()

        print(f"Produkte hinzugefügt: {inserted_products}")  # Debugging
        print(f"Rezensionen hinzugefügt: {inserted_reviews}")  # Debugging

        return {
            "status": "success",
            "message": f"Datei verarbeitet. {inserted_reviews} Rezensionen hinzugefügt.",
            "products": df['product_name'].dropna().unique().tolist()
        }

    except Exception as e:
        return {"status": "error", "message": f"Fehler beim Verarbeiten der Datei: {str(e)}"}
