import pytest
from models.sentiment import translate_label

def test_sentiment_positive():
    """ Testet, ob ein positiver Satz als 'positive' erkannt wird. """
    result = translate_label("LABEL_2")  # Annahme: LABEL_2 bedeutet 'positive'
    assert result == "positive"

def test_sentiment_negative():
    """ Testet, ob ein negativer Satz als 'negative' erkannt wird. """
    result = translate_label("LABEL_0")  # Annahme: LABEL_0 bedeutet 'negative'
    assert result == "negative"

def test_sentiment_neutral():
    """ Testet, ob ein neutraler Satz als 'neutral' erkannt wird. """
    result = translate_label("LABEL_1")  # Annahme: LABEL_1 bedeutet 'neutral'
    assert result == "neutral"
