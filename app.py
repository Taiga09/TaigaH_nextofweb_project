from flask import Flask, request, render_template, redirect, url_for
import openai
import os
import traceback
from dotenv import load_dotenv
from test_python import sentiment_percentage, generate_prompt

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)
openai_key = os.getenv('OPENAI_KEY')  # Get the OpenAI API key from environment variables
client = openai.OpenAI(api_key=openai_key)  # Instantiate the OpenAI client with the API key

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # Collect form data
        form_data = {
            'emotion': request.form.get('emotion', ''),
            'location': request.form.get('location', ''),
            'characters': request.form.get('characters', ''),
            'atmosphere': request.form.get('atmosphere', ''),
            'event': request.form.get('event', '')
        }

        # Perform sentiment analysis on the emotion
        sentiment, score = sentiment_percentage(form_data['emotion'])

        # Generate art styles based on sentiment (adjust this logic as needed)
        art_styles = ['Style 1', 'Style 2', 'Style 3', 'Style 4', 'Style 5']

        # Render the sentiment_and_styles template directly, passing the form data and sentiment analysis results
        return render_template('sentiment_and_styles.html', form_data=form_data, sentiment=sentiment, score=score, art_styles=art_styles)

    return render_template('index.html')


@app.route('/sentiment_and_styles', methods=['GET', 'POST'])
def sentiment_and_styles():
    if request.method == 'GET':
        # Retrieve sentiment analysis result passed from the previous page
        sentiment = request.args.get('sentiment')
        score = request.args.get('score')

        # Generate art styles based on sentiment (this part will be adjusted to actually generate the art styles)
        art_styles = ['Style 1', 'Style 2', 'Style 3', 'Style 4', 'Style 5']

        return render_template('sentiment_and_styles.html', sentiment=sentiment, score=score, art_styles=art_styles)

    elif request.method == 'POST':
        # Handle art style selection and redirect to the image generation page
        # You might need to pass selected_style and form_data (or its components) as parameters
        selected_style = request.form.get('selected_style')

        return redirect(url_for('generate_image', selected_style=selected_style))

@app.route('/generate_image', methods=['POST'])
def generate_image():
    # Extract the form data and the selected art style
    emotion = request.form.get('emotion')
    location = request.form.get('location')
    characters = request.form.get('characters')
    atmosphere = request.form.get('atmosphere')
    event = request.form.get('event')
    selected_style = request.form.get('selected_style')

    # Construct the prompt for image generation using the extracted data
    prompt = generate_prompt(emotion, location, characters, atmosphere, event, selected_style)

    # Call OpenAI's API to generate the image based on the prompt
    # Note: Implement the actual API call according to OpenAI's documentation
    # Make sure to handle exceptions and errors
    try:
        response = client.create_image(prompt)  # Adjust this to the actual API call
        image_url = response['data']['url']  # Adjust according to the actual response structure
    except Exception as e:
        print(f"An error occurred: {e}")
        image_url = None

    # Render a template to display the generated image
    return render_template('generated_image.html', image_url=image_url)
