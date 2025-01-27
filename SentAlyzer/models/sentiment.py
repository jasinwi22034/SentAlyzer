from transformers import pipeline

def get_sentiment_pipeline():
    """Initialisiert das Sentiment-Analyse-Modell."""
    return pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment")

def translate_label(label):
    """Übersetzt die Labels des Sentiment-Modells."""
    if label == "LABEL_0":
        return "negative"
    elif label == "LABEL_1":
        return "neutral"
    elif label == "LABEL_2":
        return "positive"
    else:
        return "unknown"
