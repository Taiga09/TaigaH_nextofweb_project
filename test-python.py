from textblob import TextBlob

def sentiment_percentage(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity  # Polarity score

    # Converting polarity to positive or negative percentage
    if polarity > 0:
        sentiment = "Positive"
        percentage = polarity * 100  # Convert to percentage
    elif polarity < 0:
        sentiment = "Negative"
        percentage = abs(polarity) * 100  # Convert to percentage, making it positive
    else:
        sentiment = "Neutral"
        percentage = 0  # Neutral sentiment

    return sentiment, round(percentage, 2)  # Rounding off the percentage for readability

# Example usage
text = "I love sunny days, they make me feel so happy!"
sentiment, percentage = sentiment_percentage(text)
print(f"The sentiment of the text is {sentiment} ({percentage}%)")
