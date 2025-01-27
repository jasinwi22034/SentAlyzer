from flask import request, jsonify
import pandas as pd

def handle_csv_upload(file):
    """Bearbeitet den Upload der CSV-Datei."""
    if file and file.filename.endswith('.csv'):
        try:
            csv_data = pd.read_csv(file)
            required_columns = {"product_name", "review_text"}
            if required_columns.issubset(csv_data.columns):
                products = csv_data["product_name"].dropna().unique().tolist()
                return {"status": "success", "products": products}
            else:
                return {"status": "error", "message": "Spalten fehlen."}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    return {"status": "error", "message": "Ungültige Datei."}
