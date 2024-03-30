from flask import Flask, request, render_template, redirect, url_for, session
from flask_mail import Mail, Message
from flask import flash # send message after image generation
import json # Import the json module to serialize the form_data
import openai
import os
from dotenv import load_dotenv
from test_python import sentiment_percentage  # Ensure this function is implemented correctly
import os, secrets
#print(secrets.token_hex(16))

load_dotenv()

app = Flask(__name__)
openai_key = os.getenv('OPENAI_KEY')
app.secret_key = os.getenv('SECRET_KEY')

client = openai.OpenAI(api_key=openai_key)

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587  # Use 587 for TLS
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'taigah.spring24.accd@gmail.com'  # Your Gmail address
app.config['MAIL_PASSWORD'] = 'jfpywhwqtkeokbam'  # Your App Password
app.config['MAIL_DEFAULT_SENDER'] = 'taigah.spring24.accd@gmail.com'  # Your Gmail address (can be the same)

mail = Mail(app)


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

        session['form_data'] = json.dumps(form_data)

        # Redirect to the sentiment_and_styles route, passing the form data, sentiment, and score as query parameters
        return redirect(url_for('sentiment_and_styles', sentiment=sentiment, score=score))

    # Render the home page template
    return render_template('index.html')

@app.route('/sentiment_and_styles', methods=['GET', 'POST'])
def sentiment_and_styles():
    if request.method == 'POST':
        # Process form submission from the sentiment_and_styles page
        selected_style = request.form.get('selected_style')

        # Retrieve form_data from session and convert it back from JSON string to a dictionary
        form_data_json = session.get('form_data', '{}')
        form_data = json.loads(form_data_json) 
        
        form_data['selected_style'] = selected_style

        session['form_data'] = json.dumps(form_data)

        # Redirect to the image generation route with the selected style and form data
        return redirect(url_for('generate_image'))


    if request.method == 'GET':

        # Retreve form_data from session and conevrt it back from JSON string to a dicionary
        form_data_json = session.get('form_data')
        if form_data_json:
            form_data = json.loads(form_data_json)
        else:
            form_data = {}

        # Extract other query parameteres
        sentiment = request.args.get('sentiment')
        score = request.args.get('score')
        
        # Construct GPT prompt for art styles
        # Convert sentiment score (string) into float
        score = float(request.args.get('score', 0))
        gpt_prompt = f"Based on the provided emotion/mood '{sentiment}' and its sentiment score of ‘{score:.2f}’, suggest five art styles that complement this sentiment. Provide the names of the art styles in one sentence, being separated by commas. Aim for a diverse range of styles that capture the essence of '{sentiment}' while inspiring creativity and imagination in the generated images."
        print(gpt_prompt)

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
    image_url = None

    if request.method == 'POST':
        form_data_json = session.get('form_data', '{}')  # Default to empty JSON object
        form_data = json.loads(form_data_json) # Parse JSON string back to a Python dictionary

        # Access form_data values
        characters = form_data.get('characters', '')
        event = form_data.get('event', '')
        location = form_data.get('location', '')
        atmosphere = form_data.get('atmosphere', '')
        emotion = form_data.get('emotion', '')
        selected_style = request.form.get('selected_style', '')
        # Debugging
        print("Selected_style:", selected_style)

        # Construct the detailed prompt
        detailed_prompt = f"A digital painting of {characters} {event} in {location}, creating an {atmosphere}, evoking {emotion} in the style of {selected_style}."
        print(f"Combined Prompt: {detailed_prompt}")

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

        # Store the image URL in the session
        image_url = response.data[0].url
        # debug
        print("Storing image_url in session", image_url)
        session['image_url'] = image_url  
        
        return render_template('generated_image.html', image_url=image_url)
    

    else:
        return redirect(url_for('home'))


# Send email
@app.route('/send_email', methods=['POST'])
def send_email():
    user_email = request.form.get('user_email', '')
    image_url = session.get('image_url', None)  # Assuming you store the generated image URL in the session

    if user_email and image_url:
        try:
            msg = Message("Your Generated Image", recipients=[user_email])
            msg.html = f"<p>Here's your generated image:</p><img src='{image_url}' alt='Generated Image'>"
            
            # Send the email
            mail.send(msg)
            flash("Email sent successfully!", "success")  # Provide user feedback
            print("Email sent successfully to:", user_email)
        except Exception as e:
            flash(f"An error occurred while sending the email: {e}", "error")  # Provide user feedback on failure
            print(f"An error occurred while sending the email: {e}")


    return redirect(url_for('generate_image'))  # Redirect back to the image page or another confirmation page



if __name__ == '__main__':
    app.run(debug=True)
