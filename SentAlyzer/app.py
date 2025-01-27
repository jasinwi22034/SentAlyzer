from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file
from controllers.upload_controller import handle_csv_upload
from controllers.analysis_controller import perform_analysis
from models.database import get_db_connection
from os import abort
import pandas as pd
import base64
import io
import matplotlib.pyplot as plt

app = Flask(__name__)

@app.route('/')
def index():
    conn = get_db_connection()
    products = [row['product_name'] for row in conn.execute('SELECT DISTINCT product_name FROM reviews')]
    conn.close()
    return render_template('index.html', products=products)

@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    result = handle_csv_upload(request.files.get('file'))
    return jsonify(result)

@app.route('/analyze', methods=['POST'])
def analyze():
    product = request.form.get('product')
    if not product:
        return "Kein Produkt ausgewählt.", 400
    return perform_analysis(product)

@app.route('/detailed_analysis/<product>')
def detailed_analysis(product):
    conn = get_db_connection()

    # Daten für das Produkt abrufen
    sentiments = pd.read_sql(
        """
        SELECT sentiment, review_text
        FROM sentiment_analysis
        WHERE analysis_id IN (
            SELECT id
            FROM analysis
            WHERE product_name = ?
        )
        """,
        conn,
        params=(product,)
    )
    conn.close()

    if sentiments.empty:
        abort(404, description=f"Keine Analyseergebnisse für das Produkt '{product}' gefunden.")

    # Sentiment-Zählungen berechnen
    sentiment_counts = sentiments['sentiment'].value_counts()
    total_reviews = sentiments.shape[0]

    # Prozentuale Verteilung der Sentimente
    sentiment_percentages = (sentiment_counts / total_reviews * 100).round(2)

    # Durchschnittliche Länge der Rezensionen
    avg_review_length = sentiments['review_text'].apply(lambda x: len(x.split())).mean().round(0)

    # Dominierendes Sentiment
    dominant_sentiment = sentiment_counts.idxmax()

    # Kreisdiagramm erstellen
    plt.figure(figsize=(6, 6))
    plt.pie(
        sentiment_counts,
        labels=sentiment_counts.index,
        autopct='%1.1f%%',
        startangle=140,
        colors=['#4CAF50', '#FFC107', '#F44336']
    )
    plt.title(f"Sentiment-Verteilung für '{product}'")

    # Kreisdiagramm in Base64 umwandeln
    circle_img = io.BytesIO()
    plt.savefig(circle_img, format='png')
    circle_img.seek(0)
    circle_plot_url = base64.b64encode(circle_img.getvalue()).decode()
    plt.close()

    # Balkendiagramm erstellen
    plt.figure(figsize=(6, 4))
    sentiment_counts.plot(kind='bar', color=['#4CAF50', '#FFC107', '#F44336'])
    plt.title(f"Sentiment-Häufigkeit für '{product}'")
    plt.xlabel("Sentiment")
    plt.ylabel("Anzahl")
    plt.xticks(rotation=0)
    plt.tight_layout()

    # Balkendiagramm in Base64 umwandeln
    bar_img = io.BytesIO()
    plt.savefig(bar_img, format='png')
    bar_img.seek(0)
    bar_plot_url = base64.b64encode(bar_img.getvalue()).decode()
    plt.close()

    # Statistiken an das Template übergeben
    stats = {
        "total_reviews": total_reviews,
        "sentiment_counts": sentiment_counts.to_dict(),
        "sentiment_percentages": sentiment_percentages.to_dict(),
        "avg_review_length": avg_review_length,
        "dominant_sentiment": dominant_sentiment,
    }

    # Diagramm-URLs an das Template übergeben
    return render_template(
        'detailed_analysis.html',
        product=product,
        circle_plot_url=circle_plot_url,
        bar_plot_url=bar_plot_url,
        stats=stats
    )

@app.route('/download_circle_chart/<product>')
def download_circle_chart(product):
    conn = get_db_connection()

    # Sentiment-Daten abrufen
    sentiments = pd.read_sql(
        "SELECT sentiment FROM sentiment_analysis WHERE analysis_id IN (SELECT id FROM analysis WHERE product_name = ?)",
        conn,
        params=(product,)
    )
    conn.close()

    sentiment_counts = sentiments['sentiment'].value_counts()

    # Kreisdiagramm erstellen
    plt.figure(figsize=(6, 6))
    plt.pie(
        sentiment_counts,
        labels=sentiment_counts.index,
        autopct='%1.1f%%',
        startangle=140,
        colors=['#4CAF50', '#FFC107', '#F44336']
    )
    plt.title(f'Sentiment-Verteilung für "{product}"')

    # Kreisdiagramm speichern
    circle_chart_path = f"static/circle_chart.png"
    plt.savefig(circle_chart_path)
    plt.close()

    # Kreisdiagramm als Datei bereitstellen
    return send_file(circle_chart_path, mimetype='image/png', as_attachment=True, download_name=f"{product}_circle_chart.png")


@app.route('/download_bar_chart/<product>')
def download_bar_chart(product):
    conn = get_db_connection()

    # Sentiment-Daten abrufen
    sentiments = pd.read_sql(
        "SELECT sentiment FROM sentiment_analysis WHERE analysis_id IN (SELECT id FROM analysis WHERE product_name = ?)",
        conn,
        params=(product,)
    )
    conn.close()

    sentiment_counts = sentiments['sentiment'].value_counts()

    # Balkendiagramm erstellen
    plt.figure(figsize=(6, 4))
    sentiment_counts.plot(kind='bar', color=['#4CAF50', '#FFC107', '#F44336'])
    plt.title(f'Sentiment-Häufigkeit für "{product}"')
    plt.xlabel("Sentiment")
    plt.ylabel("Anzahl")
    plt.xticks(rotation=0)
    plt.tight_layout()

    # Diagramm speichern
    bar_chart_path = f"static/bar_chart.png"
    plt.savefig(bar_chart_path)
    plt.close()

    # Diagramm als Datei bereitstellen
    return send_file(bar_chart_path, mimetype='image/png', as_attachment=True, download_name=f"{product}_bar_chart.png")


if __name__ == '__main__':
    app.run(debug=True)
