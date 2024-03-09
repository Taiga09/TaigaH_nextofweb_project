from flask import Flask, request, render_template
from textblob import TextBlob
import openai
from openai import OpenAI
import os
import traceback

app = Flask(__name__)

# Instantiate the OpenAI client
client = OpenAI(api_key='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')

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

@app.route('/', methods=['GET', 'POST'])
def analyze_and_generate_image():
    sentiment_result = None
    image_url = None

    if request.method == 'POST':
        emotion = request.form['emotion']
        location = request.form['location']
        characters = request.form['characters']
        atmosphere = request.form['atmosphere']
        event = request.form['event']
        art_style = request.form['art_style']  # New: Get selected art style from form

        # Sentiment analysis on the input emotion
        sentiment, percentage = sentiment_percentage(emotion)
        sentiment_result = f"The sentiment of the emotion is {sentiment} ({percentage}%)"

        # Generate prompt for OpenAI API
        prompt = generate_prompt(emotion, location, characters, atmosphere, event, art_style)

        try:
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                n=1,
                size="1024x1024"
            )
            image_url = response.data[0].url
        except Exception as e:
            print(f"An error occurred while generating the image: {e}")
            traceback.print_exc()
            sentiment_result = "Error generating image."

    # Pass art styles to the template
    art_styles = ['Impressionism', 'Surrealism', 'Abstract Expressionism', 'Cubism', 'Pop Art']
    return render_template('index.html', sentiment_result=sentiment_result, image_url=image_url, art_styles=art_styles)

if __name__ == '__main__':
    app.run(debug=True)
