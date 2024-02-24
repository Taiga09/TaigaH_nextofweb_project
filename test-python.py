from textblob import TextBlob

# Example text
text = "I had a wonderful time at the park with my friends."

# Create a TextBlob object
blob = TextBlob(text)

# Analyze sentiment
sentiment = blob.sentiment.polarity  # returns a value between -1 (negative) and 1 (positive)

# Determine sentiment
if sentiment > 0:
    print("The sentiment of the text is positive.")
elif sentiment < 0:
    print("The sentiment of the text is negative.")
else:
    print("The sentiment of the text is neutral.")

