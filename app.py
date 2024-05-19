from flask import Flask, request, render_template, redirect, url_for, session, flash, jsonify
from flask_mail import Mail, Message
from flask import send_from_directory
from datetime import datetime
import requests
from PIL import Image, ImageDraw, ImageFont
import json
import openai
import tempfile
import os
from dotenv import load_dotenv
import importlib
import test_python
import google_auth_oauthlib.flow
import google.oauth2.credentials
import googleapiclient.discovery
from googleapiclient.http import MediaFileUpload

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

# Google OAuth2 configuration
client_secrets_file = 'client_secret_127544895556-57153am15pq1cpmcpci35igj23nor1c7.apps.googleusercontent.com.json'
scopes = ['https://www.googleapis.com/auth/photoslibrary.appendonly']
redirect_uri = 'https://reminisceai-e0bc7357649b.herokuapp.com/oauth2callback'

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login')
def login():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        client_secrets_file,
        scopes=scopes
    )
    flow.redirect_uri = redirect_uri

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )

    session['state'] = state

    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    if 'state' not in session:
        return 'State not found in session', 400
    
    state = session['state']

    flow = Flow.from_client_secrets_file(client_secrets_file, scopes=scopes, state=state)
    flow.redirect_uri = url_for('oauth2callback', _external=True)
    
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)
    
    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)
    
    return jsonify(session['credentials'])

def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

def create_service():
    if 'credentials' not in session:
        return None

    credentials = google.oauth2.credentials.Credentials(
        **session['credentials']
    )

    return googleapiclient.discovery.build(
        'photoslibrary', 'v1', credentials=credentials
    )

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

            response = requests.get(image_url)
            temp_image_file = tempfile.NamedTemporaryFile(delete=False)
            temp_image_file.write(response.content)
            temp_image_file.flush()
            temp_image_file.close()

            framed_image_filename = create_polaroid_image(temp_image_file.name, 'static', caption=detailed_prompt)
            os.unlink(temp_image_file.name)

            session['framed_image_filename'] = os.path.relpath(framed_image_filename, 'static')

            # Upload to Google Photos
            upload_to_google_photos(framed_image_filename)
        
        except Exception as e:
            print(f"An error occurred while generating the image: {e}")

        return render_template('generated_image.html', image_filename=session.get('framed_image_filename'))

    else:
        return redirect(url_for('home'))

def upload_to_google_photos(image_path):
    service = create_service()
    if service is None:
        flash('Please log in with Google to upload photos.', 'error')
        return redirect(url_for('login'))

    media = MediaFileUpload(image_path, mimetype='image/jpeg')
    response = service.mediaItems().upload(
        body={'description': 'Generated Image'},
        media_body=media
    ).execute()

    print(f"Image uploaded successfully. URL: {response['productUrl']}")

# Existing routes and functions

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
