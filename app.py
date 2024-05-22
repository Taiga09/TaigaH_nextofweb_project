from flask import Flask, request, render_template, redirect, url_for, session, flash, jsonify
from flask_mail import Mail, Message
from flask import flash
from flask import send_from_directory
from datetime import datetime
import requests
from PIL import Image, ImageDraw, ImageFont
import json
import base64
import openai
import tempfile
import os
from dotenv import load_dotenv
import importlib
import test_python
from google.oauth2 import service_account
from googleapiclient.discovery import build


importlib.reload(test_python)
load_dotenv()

app = Flask(__name__)
openai_key = os.getenv('OPENAI_KEY')
app.secret_key = os.getenv('SECRET_KEY')

client = openai.OpenAI(api_key=openai_key)

# Flask-Mail configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

mail = Mail(app)

# Decode the base64 encoded key from the environment variable
service_account_key_base64 = os.getenv('SERVICE_ACCOUNT_KEY_BASE64')
if service_account_key_base64 is None:
    raise ValueError("No service account key provided in the environment variable SERVICE_ACCOUNT_KEY_BASE64")

service_account_info = json.loads(base64.b64decode(service_account_key_base64))

credentials = service_account.Credentials.from_service_account_info(
    service_account_info,
    scopes=['https://www.googleapis.com/auth/photoslibrary.appendonly']
)

# Build the Google Photos API client
service = build('photoslibrary', 'v1', credentials=credentials)


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

        combined_text = f"{form_data['emotion']} {form_data['location']} {form_data['characters']} {form_data['atmosphere']} {form_data['event']}"
        print("Combined_text:", combined_text)
        # Perform sentiment analysis
        sentiment, score = test_python.sentiment_percentage(combined_text)
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
        score = float(request.args.get('score', 0))
        
        if 0 <= score < 20:
            gpt_prompt = f"For a sentiment score of {score:.2f}, which indicates a slightly {sentiment} emotion, suggest five art styles that delicately capture the subtle nuances of this sentiment. Provide the names of the art styles in one sentence, being separated by commas. Aim for a wide range of styles from different eras, cultures, and artistic movements that capture the nuances of '{sentiment}' at this particular score level. Ensure that the suggested art styles are distinctly different from those generated for other sentiment scores, even if the scores are relatively close. Inspire creativity and imagination in the generated images while maintaining a strong connection to the specific sentiment and score."
        elif 20 <= score < 40:
            gpt_prompt = f"For a sentiment score of {score:.2f}, which represents a moderately {sentiment} emotion, suggest five art styles that expressively convey the distinct flavors of this sentiment. Provide the names of the art styles in one sentence, being separated by commas. Aim for a wide range of styles from different eras, cultures, and artistic movements that capture the nuances of '{sentiment}' at this particular score level. Ensure that the suggested art styles are distinctly different from those generated for other sentiment scores, even if the scores are relatively close. Inspire creativity and imagination in the generated images while maintaining a strong connection to the specific sentiment and score."
        elif 40 <= score < 60:
            gpt_prompt = f"For a sentiment score of {score:.2f}, which signifies a strongly {sentiment} emotion, suggest five art styles that boldly embody the intense characteristics of this sentiment. Provide the names of the art styles in one sentence, being separated by commas. Aim for a wide range of styles from different eras, cultures, and artistic movements that capture the nuances of '{sentiment}' at this particular score level. Ensure that the suggested art styles are distinctly different from those generated for other sentiment scores, even if the scores are relatively close. Inspire creativity and imagination in the generated images while maintaining a strong connection to the specific sentiment and score."
        # Add more conditions for other score ranges
        else:
            gpt_prompt = f"For a sentiment score of {score:.2f}, which indicates an extremely {sentiment} emotion, suggest five art styles that vividly encapsulate the profound depths of this sentiment. Provide the names of the art styles in one sentence, being separated by commas. Aim for a wide range of styles from different eras, cultures, and artistic movements that capture the nuances of '{sentiment}' at this particular score level. Ensure that the suggested art styles are distinctly different from those generated for other sentiment scores, even if the scores are relatively close. Inspire creativity and imagination in the generated images while maintaining a strong connection to the specific sentiment and score."
        
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
    
# Function to construct the detailed prompt
import re

def construct_detailed_prompt(characters, event, location, atmosphere, emotion, selected_style):
    # Check if the location starts with a preposition
    preposition_pattern = r'^(in|at)\s+'
    location_has_preposition = bool(re.match(preposition_pattern, location, re.IGNORECASE))

    # Determine if the location starts with a vowel sound
    vowel_sounds = ['a', 'e', 'i', 'o', 'u']
    location_words = re.sub(preposition_pattern, '', location, flags=re.IGNORECASE).strip()
    location_starts_with_vowel = location_words.lower()[0] in vowel_sounds if location_words else False

    # Construct the detailed prompt
    detailed_prompt = f"A digital painting of {characters} {event} "

    if location:
        if location_has_preposition:
            detailed_prompt += f"{location}, "
        else:
            if location_starts_with_vowel:
                detailed_prompt += f"in an {location_words}, "
            else:
                detailed_prompt += f"in a {location_words}, "

    detailed_prompt += f"creating {atmosphere} atmosphere, evoking {emotion} in the style of {selected_style}."

    return detailed_prompt

@app.route('/generate_image', methods=['GET', 'POST'])
def generate_image():
    image_url = None

    if request.method == 'POST':
        form_data_json = session.get('form_data', '{}')
        form_data = json.loads(form_data_json)

        characters = form_data.get('characters', '')
        event = form_data.get('event', '')
        location = form_data.get('location', '')
        atmosphere = form_data.get('atmosphere', '')
        emotion = form_data.get('emotion', '')
        selected_style = request.form.get('selected_style', '')

        detailed_prompt = construct_detailed_prompt(characters, event, location, atmosphere, emotion, selected_style)
        print(f"Combined Prompt: {detailed_prompt}")

        try:
            response = client.images.generate(
                model="dall-e-3",
                prompt=detailed_prompt,
                n=1,
                size="1024x1024"
            )

            image_url = response.data[0].url
            print(f"Generated image URL: {image_url}")

            response = requests.get(image_url)
            temp_image_file = tempfile.NamedTemporaryFile(delete=False)
            temp_image_file.write(response.content)
            temp_image_file.flush()
            temp_image_file.close()

            framed_image_filename = create_polaroid_image(temp_image_file.name, 'static', caption=detailed_prompt)
            os.unlink(temp_image_file.name)

            session['framed_image_filename'] = os.path.relpath(framed_image_filename, 'static')

        except Exception as e:
            print(f"An error occurred while generating the image: {e}")

        return render_template('generated_image.html', image_filename=session.get('framed_image_filename'))

    else:
        return redirect(url_for('home'))

    
# Define the function to draw text within a specified width
def draw_caption(draw, text, position, font, max_width):
    # Break the text into lines that fit within the specified width
    lines = []
    words = text.split()
    line = ''

    while words:
        word = words.pop(0)
        potential_line = line + word + ' '
        potential_line_width = font.getlength(potential_line)
        if potential_line_width > max_width:
            if line:
                lines.append(line.strip())
            line = word + ' '
        else:
            line = potential_line

    if line:
        lines.append(line.strip())

    y = position[1]
    # Draw each line on the image, adjusting the vertical position for each line
    for line in lines:
        line_width = font.getlength(line)
        ascent, descent = font.getmetrics()
        line_height = ascent + descent        
        x = position[0] + (max_width - line_width) // 2
        draw.text((x, y), line, fill="black", font=font)
        y += line_height

# Making polaroidscreate_polaroid_image
def create_polaroid_image(original_image_path, output_directory, caption=None):
    # Load the original image
    original_image = Image.open(original_image_path)
    print("Original imazge loaded successfully.")


    # Calculate the new size with the frame, assuming the frame width is 10% of the original image width
    frame_width = int(original_image.width * 0.08)
    new_width = original_image.width + 2 * frame_width
    # Make the frame's height larger to mimic a Polaroid (for the bottom part)
    new_height = original_image.height + 4 * frame_width

    # Create a new image with white background
    polaroid_image = Image.new("RGB", (new_width, new_height), "white")
    polaroid_image.paste(original_image, (frame_width, frame_width))

    # Optionally add a caption to the bottom part of the frame
    if caption:
        draw = ImageDraw.Draw(polaroid_image)

        try:
            font = ImageFont.truetype("static/fonts/Caveat-Regular.ttf", size=int(frame_width * 0.5))
            print("Font loaded successfully.")
        except Exception as e:
            print(f"Error loading font: {e}")

        max_text_width = new_width - 2 * frame_width  # Maximum width for the text
        caption_height = font.getmask(caption).size[1] # Get the height of caption

        image_bottom = original_image.height + frame_width
        frame_bottom = new_height - frame_width
        available_space = frame_bottom - image_bottom
        text_y = image_bottom + (available_space - caption_height) // 2
        text_position = ((new_width - max_text_width) // 2, text_y)


        draw_caption(draw, caption, text_position, font, max_text_width)


    # Generate a unique filename for the framed image using a timestamp
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    framed_image_filename = f'{timestamp}.jpg'
    framed_image_path = os.path.join(output_directory, framed_image_filename)
    polaroid_image.save(framed_image_path)
    print("timestamp was created")

    try:
        draw_caption(draw, caption, text_position, font, max_text_width)
        print("Caption drawn successfully.")

    except Exception as e:
        print(f"Error drawing caption: {e}")

    return framed_image_path


@app.route('/send_email', methods=['POST'])
def send_email():
    user_email = request.form.get('user_email', '')
    framed_image_filename = session.get('framed_image_filename', None)

    if user_email and framed_image_filename:
        try:
            body_text = """
Hi,
The attached is your generated image.
Hope you are enjoying our grad show. Thank you for visiting!

Best regards,
Taiga Haruyama (he|him|his)
Interaction Design Spring Graduate '24
ArtCenter College of Design

Portfolio: https://www.taigahdesign.com/
LinkedIn: https://www.linkedin.com/in/taiga-haruyama-976820164/
Professional Email: taigaharuyama09@gmail.com
Phone: +1 626-429-2951
"""
            msg = Message("Your Generated Image", recipients=[user_email], body=body_text)

            with app.open_resource(os.path.join('static', framed_image_filename)) as img:
                msg.attach(framed_image_filename, "image/jpeg", img.read())
            
            mail.send(msg)
            flash("Email sent successfully!", "success")
        except Exception as e:
            flash(f"An error occurred while sending the email: {e}", "error")

    return render_template('feedback.html')

if __name__ == '__main__':
    app.run(debug=True)
