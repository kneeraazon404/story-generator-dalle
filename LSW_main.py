import logging
import json
import requests
from threading import Thread
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import dotenv

# Import your custom modules
from LSW_00_Tripetto_to_List import convert_tripetto_json_to_lists
from LSW_01_story_generation import generate_story
from LSW_02_visual_configurator import generate_visual_description
from LSW_03_image_prompt_generation import generate_image_prompts
from LSW_04_image_generation import generate_images_from_prompts
from extract_visual_descriptions import extract_visual_description
from extract_images import extract_output_image_prompts

# Initialize Flask app
dotenv.load_dotenv()
app = Flask(__name__)

# Configure basic logging
logging.basicConfig(level=logging.INFO)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database model
class StoryData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tripettoId = db.Column(db.String(100), unique=True, nullable=False)
    order = db.Column(db.Text)
    story_configuration = db.Column(db.Text)
    visual_configuration = db.Column(db.Text)
    story = db.Column(db.Text)
    image_urls = db.Column(db.Text)

# Function to handle visual description, image prompt generation, and image generation
def generate_and_post_images(tripetto_id, story, visual_configuration):
    try:
        # Generate visual description
        visual_description = generate_visual_description(visual_configuration)
 

        # Extract image prompts from visual description
        visual_descriptions = extract_visual_description(visual_description)

        
        # Generate image prompts
        image_prompts = generate_image_prompts(story, visual_descriptions)

        # Extract image prompts from story
        extracted_image_prompts = extract_output_image_prompts(image_prompts)

        
        # Generate images from prompts
        image_urls = generate_images_from_prompts(extracted_image_prompts)


        # Post image URLs to another endpoint
        post_response = requests.post("https://littlestorywriter.com/process_story/", json={"image_urls": image_urls, "tripettoId": tripetto_id})
        print("Thread finished")

        post_response.raise_for_status()

        # Update the database with image URLs
        existing_story = StoryData.query.filter_by(tripettoId=tripetto_id).first()
        if existing_story:
            existing_story.image_urls = json.dumps(image_urls)
            db.session.commit()
        

    except Exception as e:
        logging.error(f"Error in generate_and_post_images: {e}")

# Process story endpoint
@app.route("/process-story", methods=["POST"])
def process_story():
    try:
        data = request.json
        tripetto_id = data.get('tripettoId')
        if not tripetto_id:
            return jsonify({'error': 'tripettoId is required'}), 400

        # Convert Tripetto JSON to lists
        order, story_configuration, visual_configuration = convert_tripetto_json_to_lists(data)

        # Generate story
        book_data = generate_story(story_configuration)

        # Save the initial story data to the database
        new_story_data = StoryData(
            tripettoId=tripetto_id,
            order=json.dumps(order),
            story_configuration=json.dumps(story_configuration),
            visual_configuration=json.dumps(visual_configuration),
            story=json.dumps(book_data),
            image_urls=json.dumps([])
        )

        db.session.add(new_story_data)
        db.session.commit()

        # Start the rest of the processing in a separate thread
        print("Starting thread")
        thread = Thread(target=generate_and_post_images, args=(tripetto_id, book_data, visual_configuration))
        thread.start()

        # Return immediate response with the story
        return jsonify({'tripettoId': tripetto_id, "order": order,"story_configuration": story_configuration,'story': book_data, })

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return jsonify({"error": str(e)}), 500

# Endpoint to retrieve story data
@app.route('/get-story-data/<tripetto_id>', methods=['GET'])
def get_story_data(tripetto_id):
    story_data = StoryData.query.filter_by(tripettoId=tripetto_id).first()
    if story_data:
        return jsonify({
            "tripettoId": tripetto_id,
            'order': json.loads(story_data.order),
            'story_configuration': json.loads(story_data.story_configuration),
            'visual_configuration': json.loads(story_data.visual_configuration),
            "story": json.loads(story_data.story),
            "image_urls": json.loads(story_data.image_urls)
        })
    else:
        return jsonify({'error': 'Data not found'}), 404

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True, host="localhost", port=5000)  # Run app
