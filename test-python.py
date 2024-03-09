from textblob import TextBlob
import openai

# Instantiate the OpenAI client
client = openai.OpenAI(api_key='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')

def generate_prompt(emotion, location, characters, atmosphere, event, art_style):
    # Construct the prompt
    prompt = f"A digital painting of {characters} {event} in {location}, creating an {atmosphere} mood, evoking {emotion}. Style: {art_style}"
    return prompt

def sentiment_percentage(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity  # Polarity score

    # Converting polarity to positive or negative percentage
    if polarity > 0:
        sentiment = "positive"
        percentage = polarity * 100  # Convert to percentage
    elif polarity < 0:
        sentiment = "negative"
        percentage = abs(polarity) * 100  # Convert to percentage, making it positive
    else:
        sentiment = "neutral"
        percentage = 0  # Neutral sentiment

    return sentiment, round(percentage, 2)  # Rounding off the percentage for readability

def main():
    # This function can be used to test the logic of generate_prompt and sentiment_percentage functions
    pass

if __name__ == '__main__':
    main()
