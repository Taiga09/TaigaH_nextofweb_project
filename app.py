from flask import Flask, request, render_template
from textblob import TextBlob
import openai
from openai import OpenAI
import os
import traceback

app = Flask(__name__)
openai_key = os.environ.get('OPENAI_KEY')
# Instantiate the OpenAI client
client = openai.OpenAI(api_key=openai_key)

@app.route('/', methods=['GET', 'POST'])
def analyze_and_generate_image():
    sentiment_result = None
    art_styles = None  # Placeholder for art style suggestions (to be implemented)
    image_url = None

    if request.method == 'POST':
        # Collecting data from all the input fields
        emotion = request.form['emotion']
        location = request.form['location']
        characters = request.form['characters']
        atmosphere = request.form['atmosphere']
        event = request.form['event']
        
        # Ensure all fields have values before proceeding
        if not all([emotion, location, characters, atmosphere, event]):
            return render_template('index.html', error="Please fill in all fields.")
            # Performing sentiment analysis on the emotion text
        blob = TextBlob(emotion)
        polarity = blob.sentiment.polarity

        # Classifying the sentiment
        if polarity > 0:
            sentiment = "positive"
        elif polarity < 0:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        sentiment_result = f"{sentiment.capitalize()} sentiment"

        # Creating a detailed prompt using all the input data
        detailed_prompt = f"A digital painting of {characters} {event} in {location}, creating an {atmosphere} atmosphere, evoking {emotion}."

        try:
            # Using the detailed prompt for image generation
            response = client.images.generate(
                model="dall-e-3",
                prompt=detailed_prompt,
                n=1,
                size="1024x1024"
            )
            image_url = response.data[0].url
        except Exception as e:
            print(f"An error occurred while generating the image: {e}")
            traceback.print_exc()
            sentiment_result += " - Error generating image."

    # Passing the sentiment_result, art_styles (to be implemented), and image_url to the template
    return render_template('index.html', sentiment_result=sentiment_result, art_styles=art_styles, image_url=image_url)

if __name__ == '__main__':
    app.run(debug=True)
