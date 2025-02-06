import pytest
import io
from werkzeug.datastructures import FileStorage
from controllers.upload_controller import handle_csv_upload

def test_valid_csv_upload():
    """ Testet den Upload einer gültigen CSV-Datei mit den richtigen Spalten. """
    csv_content = "product_name,review_text\nProdukt 1,Das ist großartig!\nProdukt 2,Es ist okay."
    file = FileStorage(stream=io.BytesIO(csv_content.encode()), filename="test.csv", content_type="text/csv")

    result = handle_csv_upload(file)
    assert result["status"] == "success"
    assert "products" in result
    assert "Produkt 1" in result["products"]

def test_invalid_csv_missing_columns():
    """ Testet den Upload einer ungültigen CSV-Datei ohne die richtigen Spalten. """
    csv_content = "name,description\nProdukt 1,Das ist großartig!"
    file = FileStorage(stream=io.BytesIO(csv_content.encode()), filename="test_invalid.csv", content_type="text/csv")

    result = handle_csv_upload(file)
    assert result["status"] == "error"
    assert result["message"] == "Spalten fehlen."
