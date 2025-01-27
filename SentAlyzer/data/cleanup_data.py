import pandas as pd

# Pfad zur CSV-Datei
file_path = 'amazon_product_reviews.csv'

# Schritt 1: CSV-Datei laden
df = pd.read_csv(file_path)

# Schritt 2: Relevante Spalten auswählen und umbenennen
selected_columns = {
    "id": "product_id",
    "name": "product_name",
    "reviews.text": "review_text",
    "reviews.rating": "rating"
}

# Neue DataFrame mit ausgewählten und umbenannten Spalten
df_filtered = df[list(selected_columns.keys())].rename(columns=selected_columns)

# Schritt 3: Entfernen von Datensätzen ohne review_text oder rating
df_filtered = df_filtered.dropna(subset=["review_text", "rating"])

# Speichern der bereinigten Daten
output_path = 'cleaned_amazon_product_reviews.csv'
df_filtered.to_csv(output_path, index=False)
print(f"Bereinigte Daten wurden gespeichert unter: {output_path}")
