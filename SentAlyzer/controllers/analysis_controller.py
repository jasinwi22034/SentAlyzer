import pandas as pd
from flask import send_file
from models.database import get_db_connection
from models.sentiment import get_sentiment_pipeline, translate_label
import io

def perform_analysis(product):
    """Führt die Sentiment-Analyse durch."""
    conn = get_db_connection()
    reviews = pd.read_sql(
        "SELECT product_name, review_text FROM reviews WHERE product_name = ?",
        conn,
        params=(product,)
    )

    if reviews.empty:
        return None

    sentiment_pipeline = get_sentiment_pipeline()
    reviews['sentiment'] = reviews['review_text'].apply(
        lambda x: translate_label(sentiment_pipeline(x[:512])[0]['label'])
    )

    cursor = conn.cursor()
    cursor.execute("INSERT INTO analysis (product_name) VALUES (?)", (product,))
    analysis_id = cursor.lastrowid

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

    output = io.StringIO()
    reviews[['product_name', 'review_text', 'sentiment']].to_csv(output, index=False)
    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f"{product}_sentiment_analysis.csv"
    )
