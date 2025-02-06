import pandas as pd
from flask import send_file
from models.database import get_db_connection
from models.sentiment import get_sentiment_pipeline, translate_label
import io

def perform_analysis(product):
    """
    Führt die Sentiment-Analyse für ein bestimmtes Produkt durch.
    - Lädt die Rezensionen aus der Datenbank
    - Führt die Sentiment-Analyse mit einem NLP-Modell durch
    - Speichert die Ergebnisse in der Datenbank
    - Gibt eine CSV-Datei mit den Ergebnissen zurück

    Args:
        product (str): Der Name des zu analysierenden Produkts

    Returns:
        send_file: Eine CSV-Datei mit den analysierten Sentiment-Daten
    """
    conn = get_db_connection()

    # Rezensionen aus der Datenbank abrufen
    reviews = pd.read_sql(
        "SELECT product_name, review_text FROM reviews WHERE product_name = ?",
        conn,
        params=(product,)
    )

    if reviews.empty:
        return None  # Falls keine Rezensionen vorhanden sind

    # NLP-Sentiment-Analysemodell abrufen
    sentiment_pipeline = get_sentiment_pipeline()

    # Anwendung des Sentiment-Analysemodells auf die Rezensionstexte
    reviews['sentiment'] = reviews['review_text'].apply(
        lambda x: translate_label(sentiment_pipeline(x[:512])[0]['label'])
    )

    # Eintrag in die 'analysis'-Tabelle erstellen
    cursor = conn.cursor()
    cursor.execute("INSERT INTO analysis (product_name) VALUES (?)", (product,))
    analysis_id = cursor.lastrowid

    # Ergebnisse in der 'sentiment_analysis'-Tabelle speichern
    for _, row in reviews.iterrows():
        cursor.execute(
            '''
            INSERT INTO sentiment_analysis (analysis_id, review_text, sentiment)
            VALUES (?, ?, ?)
            ''',
            (analysis_id, row['review_text'], row['sentiment'])
        )

    conn.commit()
    conn.close()

    # CSV-Datei mit den analysierten Sentiments erstellen
    output = io.StringIO()
    reviews[['product_name', 'review_text', 'sentiment']].to_csv(output, index=False)
    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f"{product}_sentiment_analysis.csv"
    )
