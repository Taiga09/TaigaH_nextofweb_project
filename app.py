from flask import Flask, request, render_template
import openai
import os
import traceback
from test_python import sentiment_percentage  # Assuming the file is renamed to test_python.py

app = Flask(__name__)
openai_key = os.environ.get('OPENAI_KEY')
# Instantiate the OpenAI client
client = openai.OpenAI(api_key=openai_key)

@app.route('/', methods=['GET', 'POST'])
def analyze_and_generate_image():
    image_url = None

    if request.method == 'POST':
        emotion = request.form.get('emotion', '')
        location = request.form.get('location', '')
        characters = request.form.get('characters', '')
        atmosphere = request.form.get('atmosphere', '')
        event = request.form.get('event', '')

        # Perform sentiment analysis on the emotion input
        sentiment, score = sentiment_percentage(emotion)
        print(f"Sentiment: {sentiment}, Score: {score}%")  # Print the sentiment result and its score

        detailed_prompt = f"A digital painting of {characters} {event} in {location}, creating an {atmosphere} atmosphere, evoking {emotion}."
        print(f"Combined Prompt: {detailed_prompt}")

        try:
            # Using the detailed prompt for image generation
            response = client.images.generate(
                model="dall-e-3",
                prompt=detailed_prompt,
                n=1,
                size="1024x1024"
            )
            # Accessing the image URL correctly from the response object
            image_url = response.data[0].url  # Adjusted to use attribute access
        except Exception as e:
            print(f"An error occurred while generating the image: {e}")
            traceback.print_exc()


    return render_template('index.html', image_url=image_url)

if __name__ == '__main__':
    app.run(debug=True)
