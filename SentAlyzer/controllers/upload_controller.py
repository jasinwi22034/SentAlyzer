import pandas as pd

def handle_csv_upload(file):
    """
    Bearbeitet den Upload einer CSV-Datei.

    - Überprüft, ob die Datei eine gültige CSV ist
    - Prüft, ob die erforderlichen Spalten (product_name, review_text) vorhanden sind
    - Falls valide, gibt die Liste der Produkte zurück

    Args:
        file (FileStorage): Hochgeladene CSV-Datei

    Returns:
        dict: Status und Produktliste oder Fehlermeldung
    """
    if file and file.filename.endswith('.csv'):
        try:
            # CSV-Datei einlesen
            csv_data = pd.read_csv(file)

            # Benötigte Spalten definieren
            required_columns = {"product_name", "review_text"}

            # Überprüfen, ob alle erforderlichen Spalten in der Datei vorhanden sind
            if required_columns.issubset(csv_data.columns):
                # Produktnamen extrahieren und Duplikate entfernen
                products = csv_data["product_name"].dropna().unique().tolist()
                return {"status": "success", "products": products}
            else:
                return {"status": "error", "message": "Spalten fehlen."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    return {"status": "error", "message": "Ungültige Datei."}