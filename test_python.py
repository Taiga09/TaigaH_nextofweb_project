from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import re

def clean_text(text):
   # Remove URLs
    text = re.sub(r'http\S+', '', text)
    
    # Remove mentions
    text = re.sub(r'@\w+', '', text)
    
    # Remove hashtags
    text = re.sub(r'#\w+', '', text)
    
    # Remove punctuation
    text = re.sub(r'[^\w\s]', '', text)
    
    # Convert text to lowercase
    text = text.lower()
    
    # Remove extra whitespaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def generate_prompt(emotion, location, characters, atmosphere, event, art_style):
    # Construct the prompt
    prompt = f"A digital painting of {characters} {event} in {location}, creating an {atmosphere} mood, evoking {emotion}. Style: {art_style}"
    return prompt

def sentiment_percentage(text):
    cleaned_text = clean_text(text)
    analyzer = SentimentIntensityAnalyzer()
    scores = analyzer.polarity_scores(cleaned_text)
    polarity = scores['compound']

    # Converting polarity to positive or negative percentage
    if polarity > 0:
        sentiment = "positive"
        percentage = polarity * 100  # Convert to percentage
    elif polarity < 0:
        sentiment = "negative"
        percentage = abs(polarity) * 100
    else:
        sentiment = "neutral"
        percentage = 0  # Neutral sentiment

    #score = round(percentage, 2)
   

    return sentiment, round(percentage, 2)

def main():
    pass

if __name__ == '__main__':
    main()
