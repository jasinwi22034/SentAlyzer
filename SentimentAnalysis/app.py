from flask import Flask, render_template, request, send_file, jsonify
import sqlite3
import pandas as pd
from transformers import pipeline
import io
import matplotlib.pyplot as plt
import base64

app = Flask(__name__)

# Maximalgröße für den Upload festlegen
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

# Verbindung zur Datenbank herstellen
def get_db_connection():
    conn = sqlite3.connect('database/amazon_reviews.db')
    conn.row_factory = sqlite3.Row
    return conn

# Funktion zur Label-Übersetzung
def translate_label(label):
    if label == "LABEL_0":
        return "negative"
    elif label == "LABEL_1":
        return "neutral"
    elif label == "LABEL_2":
        return "positive"
    else:
        return "unknown"

# Route für die Startseite
@app.route('/', methods=['GET', 'POST'])
def index():
    products = []

    if request.method == 'POST':
        uploaded_file = request.files.get('csv-upload')
        if uploaded_file and uploaded_file.filename.endswith('.csv'):
            # CSV-Datei lesen und Produkte extrahieren
            csv_data = pd.read_csv(uploaded_file)
            if "product_name" in csv_data.columns:
                products = csv_data["product_name"].dropna().unique().tolist()
            else:
                products = []  # Leeres Dropdown, falls die CSV die Spalte nicht enthält
        else:
            print("Keine gültige CSV-Datei hochgeladen.")

    # Wenn keine CSV hochgeladen wurde, Produkte aus der DB laden
    if not products:
        conn = get_db_connection()
        products = [row['product_name'] for row in conn.execute('SELECT DISTINCT product_name FROM reviews')]
        conn.close()

    return render_template('index.html', products=products)

@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    uploaded_file = request.files.get('file')
    if uploaded_file and uploaded_file.filename.endswith('.csv'):
        try:
            # Debugging: Name der Datei anzeigen
            print(f"Dateiname: {uploaded_file.filename}")

            # CSV-Datei lesen
            csv_data = pd.read_csv(uploaded_file)
            print(f"CSV erfolgreich geladen: {csv_data.head()}")  # Debugging: Zeige erste Zeilen der CSV

            # Überprüfen, ob die erforderlichen Spalten vorhanden sind
            required_columns = {"product_name", "review_text"}
            if required_columns.issubset(csv_data.columns):
                # Eindeutige Produktnamen extrahieren
                products = csv_data["product_name"].dropna().unique().tolist()
                print(f"Eindeutige Produkte: {products}")  # Debugging: Zeige die extrahierten Produkte
                return jsonify({"status": "success", "products": products})
            else:
                print("Erforderliche Spalten fehlen.")  # Debugging: Spalten fehlen
                return jsonify({"status": "error", "message": "Spalte 'product_name' und/oder 'review_text' fehlt."})
        except Exception as e:
            print(f"Fehler beim Verarbeiten der CSV: {str(e)}")  # Debugging: Zeige Fehler
            return jsonify({"status": "error", "message": str(e)})
    print("Keine gültige Datei hochgeladen.")  # Debugging: Keine Datei
    return jsonify({"status": "error", "message": "Keine gültige CSV-Datei hochgeladen."})




# Route für die Analyse
@app.route('/analyze', methods=['POST'])
def analyze():
    product = request.form.get('product')
    if not product:
        return "Kein Produkt ausgewählt. Bitte zurückgehen und ein Produkt auswählen.", 400

    print(f"Produkt ausgewählt: {product}")
    conn = get_db_connection()

    # Rezensionen für das Produkt abrufen
    reviews = pd.read_sql(
        "SELECT product_name, review_text FROM reviews WHERE product_name = ?",
        conn,
        params=(product,)
    )

    print(f"Anzahl Rezensionen gefunden: {len(reviews)}")

    if reviews.empty:
        conn.close()
        return f"Keine Rezensionen für das Produkt '{product}' gefunden.", 404

    # Sentiment-Analyse
    sentiment_pipeline = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment")
    reviews['sentiment'] = reviews['review_text'].apply(lambda x: translate_label(sentiment_pipeline(x[:512])[0]['label']))
    print(f"Sentiment-Analyse abgeschlossen für {len(reviews)} Rezensionen.")

    # Ergebnisse speichern und CSV generieren
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

    # CSV generieren
    reviews = reviews[['product_name', 'review_text', 'sentiment']]
    output = io.StringIO()
    reviews.to_csv(output, index=False)
    output.seek(0)

    print("CSV generiert und bereitgestellt.")
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f"{product}_sentiment_analysis.csv"
    )

    # Weiterleitung zur Detailed Analysis Page
    return redirect(url_for('detailed_analysis', product=product))

@app.route('/detailed_analysis/<product>', methods=['GET'])
def detailed_analysis(product):
    conn = get_db_connection()

    # Daten für das Produkt abrufen
    sentiments = pd.read_sql(
        "SELECT sentiment FROM sentiment_analysis WHERE analysis_id IN (SELECT id FROM analysis WHERE product_name = ?)",
        conn,
        params=(product,)
    )
    conn.close()

    if sentiments.empty:
        return f"Keine Analyseergebnisse für das Produkt '{product}' gefunden.", 404

    # Sentiment-Zählungen berechnen
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

    # Diagramm in Base64 umwandeln
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()

    # HTML-Template rendern
    return render_template('detailed_analysis.html', product=product, plot_url=plot_url)

@app.route('/download_chart/<product>', methods=['GET'])
def download_chart(product):
    conn = get_db_connection()

    # Daten für das Produkt abrufen
    sentiments = pd.read_sql(
        "SELECT sentiment FROM sentiment_analysis WHERE analysis_id IN (SELECT id FROM analysis WHERE product_name = ?)",
        conn,
        params=(product,)
    )
    conn.close()

    if sentiments.empty:
        return "Keine Analyseergebnisse vorhanden.", 404

    # Sentiment-Zählungen berechnen
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

    # Diagramm als Datei bereitstellen
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()

    return send_file(
        io.BytesIO(img.getvalue()),
        mimetype='image/png',
        as_attachment=True,
        download_name=f"{product}_sentiment_chart.png"
    )


@app.route('/validate_csv', methods=['POST'])
def validate_csv():
    uploaded_file = request.files.get('file')
    if uploaded_file and uploaded_file.filename.endswith('.csv'):
        try:
            # CSV-Datei lesen
            csv_data = pd.read_csv(uploaded_file)
            # Überprüfen, ob die erforderlichen Spalten vorhanden sind
            required_columns = {"product_name", "review_text"}
            if required_columns.issubset(csv_data.columns):
                # Eindeutige Produktnamen extrahieren
                products = csv_data["product_name"].dropna().unique().tolist()
                return jsonify({"status": "success", "products": products})
            else:
                return jsonify({"status": "error", "message": "Spalte 'product_name' und/oder 'review_text' fehlt."})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
    return jsonify({"status": "error", "message": "Keine gültige CSV-Datei hochgeladen."})


if __name__ == '__main__':
    app.run(debug=True)
