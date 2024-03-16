from flask import Flask, request, render_template
import openai
import os
import traceback
from dotenv import load_dotenv
from test_python import sentiment_percentage  # Assuming the file is renamed to test_python.py

load_dotenv()

app = Flask(__name__)
openai_key = os.getenv('OPENAI_KEY')
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

        # Old instruction
        #gpt_prompt = f"Based on the provided emotion/mood '{sentiment}' and its sentiment score of ‘{score:.2f}’, suggest five art styles that complement this sentiment. Aim for a diverse range of styles that capture the essence of '{sentiment}' while inspiring creativity and imagination in the generated images."
        gpt_prompt = f"Based on the provided emotion/mood '{sentiment}' and its sentiment score of ‘{score:.2f}’, suggest five art styles that complement this sentiment. Provide the names of the art styles in one sentence, being separated by commas. Aim for a diverse range of styles that capture the essence of '{sentiment}' while inspiring creativity and imagination in the generated images."

        print(f"GPT Prompt: {gpt_prompt}")  # Print the GPT prompt for debugging

        try:
             # Using the detailed prompt for image generation
            response = client.images.generate(
                model="dall-e-3",
                prompt=detailed_prompt,
                n=1,
                size="1024x1024"
            )

            # Query GPT for art styles
            gpt_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": gpt_prompt}],
                max_tokens=100,
                temperature=0.7
            )

            print(gpt_response);

            # Accessing the image URL correctly from the response object
            image_url = response.data[0].url  # Adjusted to use attribute access

            # Extract the art styles from the response
            #art_styles = [choice['message'].split(", ") for choice in gpt_response.choices]
            # New line
            art_styles = [choice.message.content.split(", ") for choice in gpt_response.choices]

            
            print("Suggested Art Styles:")
            for idx, style in enumerate(art_styles, start=1):
                print(f"{idx}. {style}")

        except Exception as e:
            print(f"An error occurred while generating the image: {e}")
            print(f"An error occurred while querying GPT: {e}")
            traceback.print_exc()

    return render_template('index.html', image_url=image_url)

if __name__ == '__main__':
    app.run(debug=True)
