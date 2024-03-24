from flask import Flask, request, render_template, redirect, url_for
import json # Import the json module to serialize the form_data
import openai
import os
from dotenv import load_dotenv
from test_python import sentiment_percentage  # Ensure this function is implemented correctly

load_dotenv()

app = Flask(__name__)
openai_key = os.getenv('OPENAI_KEY')
client = openai.OpenAI(api_key=openai_key)

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

        # Perform sentiment analysis
        sentiment, score = sentiment_percentage(form_data['emotion'])
        print(f"Sentiment: {sentiment}, Score: {score}%")

        #Serialize form_data to JSON srting
        form_data_json = json.dumps(form_data)

        # Redirect to the sentiment_and_styles route, passing the form data, sentiment, and score as query parameters
        return redirect(url_for('sentiment_and_styles', form_data=form_data_json, sentiment=sentiment, score=score))

    # Render the home page template
    return render_template('index.html')

@app.route('/sentiment_and_styles', methods=['GET', 'POST'])
def sentiment_and_styles():
    if request.method == 'POST':
        # Process form submission from the sentiment_and_styles page
        selected_style = request.form.get('selected_style')
        form_data = request.form.get('form_data') 

        # Redirect to the image generation route with the selected style and form data
        return redirect(url_for('generate_image', selected_style=selected_style, form_data=form_data))

    if request.method == 'GET':
        # Extract query parameters from the URL
        sentiment = request.args.get('sentiment')
        score = request.args.get('score')
        form_data = request.args.get('form_data')

        # Construct GPT prompt for art styles
        gpt_prompt = f"Based on the provided emotion/mood '{sentiment}' and its sentiment score of '{score}', suggest five art styles that complement this sentiment with just the style name, comma separated value format for example: Deco,Nuevo,Contemporary,Traditional,Modern"

        try:
            # Query GPT for art styles using the chat API
            gpt_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "Please suggest art styles."},
                          {"role": "user", "content": gpt_prompt}],
                max_tokens=100,
                temperature=0.7
            )
            print(gpt_response)   
            # Extract art styles from the GPT response and flatten the list
            art_styles =  gpt_response.choices[0].message.content.split(",")
            # print(art_styles)   

        except Exception as e:
            print(f"An error occurred while querying GPT: {e}")
            art_styles = ['Error fetching styles']

        # Render the sentiment and styles template with the data
        return render_template('sentiment_and_styles.html', form_data=form_data, sentiment=sentiment, score=score, art_styles=art_styles)

@app.route('/generate_image', methods=['GET', 'POST'])
def generate_image():
    if request.method == 'POST':
        # Process form submission from the generate_image page
        # Extract all necessary data for image generation
        form_data = request.form.get('form_data')  # Make sure to parse this correctly
        selected_style = request.form.get('selected_style')

        # Implement your image generation logic here
        # For now, we'll just print the data
        print(f"Form Data: {form_data}, Selected Style: {selected_style}")

        # Redirect back to home as a placeholder
        return redirect(url_for('home'))

    # If the method is GET, redirect to home as this route expects POST to process data
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
