from flask import Flask, request, render_template, redirect, url_for, session
from flask_mail import Mail, Message
from flask import flash # send message after image generation
from flask import send_from_directory
from datetime import datetime
import requests
from PIL import Image, ImageDraw, ImageFont
import json # Import the json module to serialize the form_data
import openai
import tempfile
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

            # Download the image to a temporary file
            response = requests.get(image_url)  # Use a different variable name to avoid confusion with the outer `response`
            temp_image_file = tempfile.NamedTemporaryFile(delete=False)
            temp_image_file.write(response.content)
            temp_image_file.flush()  # Ensure all data is written to the file
            temp_image_file.close()

            # Create a polaroid version of the image
            framed_image_filename = create_polaroid_image(temp_image_file.name, 'static', caption=detailed_prompt)
            
            # Cleanup the temporary original image file
            os.unlink(temp_image_file.name)

            # Update the session or context with the filename of the polaroid images
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
        font = ImageFont.truetype("./fonts/Caveat.ttf", size=int(frame_width* 0.5))
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

    try:
        draw_caption(draw, caption, text_position, font, max_text_width)
    except Exception as e:
        print(f"Error drawing caption: {e}")


    return framed_image_path


# Send email
@app.route('/send_email', methods=['POST'])
def send_email():
    user_email = request.form.get('user_email', '')
    framed_image_filename = session.get('framed_image_filename', None)  # Assuming you store the generated image URL in the session

    if user_email and framed_image_filename:
        try:
            msg = Message("Your Generated Image", recipients=[user_email])
            with app.open_resource(os.path.join('static', framed_image_filename)) as img:
                msg.attach(framed_image_filename, "image/jpeg", img.read())
            # Send the email
            mail.send(msg)
            flash("Email sent successfully!", "success")  # Provide user feedback
        except Exception as e:
            flash(f"An error occurred while sending the email: {e}", "error")  # Provide user feedback on failure

    return render_template('feedback.html')  # Render feedback template

if __name__ == '__main__':
    app.run(debug=True)
