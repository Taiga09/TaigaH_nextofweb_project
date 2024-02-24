from flask import Flask, request, render_template
from textblob import TextBlob

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def analyze():
    sentiment_result = None
    if request.method == 'POST':
        text = request.form['text']
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity

        # Converting polarity to a sentiment percentage and textual representation
        if polarity > 0:
            sentiment = "Positive"
            percentage = polarity * 100
        elif polarity < 0:
            sentiment = "Negative"
            percentage = abs(polarity) * 100
        else:
            sentiment = "Neutral"
            percentage = 0

        sentiment_result = f"The sentiment of the text is {sentiment} ({round(percentage, 2)}%)"

    return render_template('index.html', sentiment_result=sentiment_result)

if __name__ == '__main__':
    app.run(debug=True)
