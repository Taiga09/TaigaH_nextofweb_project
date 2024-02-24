from flask import Flask, request, render_template
from textblob import TextBlob
import openai
from openai import OpenAI
import os
import traceback

app = Flask(__name__)

# Instantiate the OpenAI client
client = OpenAI(api_key='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')

@app.route('/', methods=['GET', 'POST'])
def analyze_and_generate_image():
    sentiment_result = None
    image_url = None

    if request.method == 'POST':
        text = request.form['text']
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity

        if polarity > 0:
            sentiment = "positive"
        elif polarity < 0:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        sentiment_result = f"{sentiment.capitalize()} sentiment"

        try:
            response = client.images.generate(
                model="dall-e-3",
                prompt=f"A {sentiment} image reflecting the sentiment of '{text}'",
                n=1,
                size="1024x1024"
            )
            print(response.data[0].url)
            # if isinstance(response, OpenAI):
            #     response = response.to_dict()
            image_url = response.data[0].url
        except Exception as e:
            print(f"An error occurred while generating the image: {e}")
            traceback.print_exc()
            sentiment_result += " - Error generating image."

    return render_template('index.html', sentiment_result=sentiment_result, image_url=image_url)

if __name__ == '__main__':
    app.run(debug=True)
