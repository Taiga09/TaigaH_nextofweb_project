from flask import Flask, request, render_template
# from textblob import TextBlob  # Commented out since sentiment analysis is not needed for now
import openai
import os
import traceback

app = Flask(__name__)
openai_key = os.environ.get('OPENAI_KEY')
# Instantiate the OpenAI client
client = openai.OpenAI(api_key=openai_key)

@app.route('/', methods=['GET', 'POST'])
def analyze_and_generate_image():
    # sentiment_result = None  # Commented out since sentiment analysis is not needed for now
    # art_styles = None  # Placeholder for art style suggestions (to be implemented), commented out for now
    image_url = None

    if request.method == 'POST':
        # Collecting data from all the input fields
        emotion = request.form.get('emotion', '')
        location = request.form.get('location', '')
        characters = request.form.get('characters', '')
        atmosphere = request.form.get('atmosphere', '')
        event = request.form.get('event', '')
    
        # Creating a detailed prompt using all the input data
        detailed_prompt = f"A digital painting of {characters} {event} in {location}, creating an {atmosphere} atmosphere, evoking {emotion}."

        # Print the combined prompt in the terminal
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

    # Passing only the image_url to the template, as the other variables are commented out for now
    return render_template('index.html', image_url=image_url)

if __name__ == '__main__':
    app.run(debug=True)
