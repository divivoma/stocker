import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

nltk.download("vader_lexicon", quiet=True)

sia = SentimentIntensityAnalyzer()

def sentiment_score(text: str) -> float:
    return sia.polarity_scores(text)["compound"]
