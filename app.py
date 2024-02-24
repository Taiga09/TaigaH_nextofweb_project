from flask import Flask, request, render_template
from textblob import TextBlob
import openai
import traceback

app = Flask(__name__)

openai.api_key = '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'

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
            sentiment_result = "Positive sentiment"
        elif polarity < 0:
            sentiment = "negative"
            sentiment_result = "Negative sentiment"
        else:
            sentiment = "neutral"
            sentiment_result = "Neutral sentiment"

        try:
            response = openai.Image.create_generation(
                model="dall-e-3",
                prompt=f"A {sentiment} image reflecting the sentiment of '{text}'",
                n=1,
                size="1024x1024"
            )
            image_url = response['data'][0]['url']
        except Exception as e:
            print(f"An error occurred while generating the image: {e}")
            traceback.print_exc()
            sentiment_result += " - Error generating image."

    return render_template('index.html', sentiment_result=sentiment_result, image_url=image_url)

if __name__ == '__main__':
    app.run(debug=True)
