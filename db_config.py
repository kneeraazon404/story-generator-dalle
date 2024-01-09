import logging
import json
import requests
from threading import Thread
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import dotenv
from image_generator import ImageGenerator
import asyncio

# Import your custom modules
from LSW_00_Tripetto_to_List import convert_tripetto_json_to_lists
from LSW_01_story_generation import generate_story
from LSW_02_visual_configurator import generate_visual_description
from LSW_03_image_prompt_generation import generate_image_prompts
from extract_visual_descriptions import extract_visual_description
from extract_images import extract_output_image_prompts

# Initialize Flask app
dotenv.load_dotenv()
app = Flask(__name__)

# Configure basic logging
logging.basicConfig(level=logging.INFO)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
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
        print("Visual description generated")
        print(visual_description)

        # Extract image prompts from visual description
        visual_descriptions = extract_visual_description(visual_description)
        print("Visual descriptions extracted")
        print(visual_descriptions)

        # Generate image prompts
        image_prompts = generate_image_prompts(story, visual_descriptions)
        print("Image prompts generated")
        print(image_prompts)

        # Extract image prompts from story
        extracted_image_prompts = extract_output_image_prompts(image_prompts)
        print("Image prompts extracted")
        print(extracted_image_prompts)

        # Generate images
        api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6NTgxMSwiZW1haWwiOiJuYWdlbC5icmVtZW5AZ21haWwuY29tIiwidXNlcm5hbWUiOiJuYWdlbC5icmVtZW5AZ21haWwuY29tIiwiaWF0IjoxNzAyODkzODIxfQ.FK9cfnILlaBYot1MRguTdt1_cBGTC0z92WikYoNtYd8"
        generator = ImageGenerator(api_key)
        # Define the headers to be used in the POST request
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",  # Replace with your actual User-Agent
        }
        url = "https://littlestorywriter.com/img-upload"

        # Function to run the asynchronous tasks
        async def run_async_tasks():
            prompts = list(extracted_image_prompts.values())
            image_uris = await generator.generate_images(prompts)

            for idx, image_uri in enumerate(image_uris):
                if image_uri:
                    page_label = f"page_{idx+1:02d}"
                    post_payload = {
                        "image_urls": {page_label: image_uri},
                        "tripettoId": tripetto_id,
                    }

                    # Use requests to send the POST request
                    response = requests.post(url, json=post_payload, headers=headers)
                    response.raise_for_status()
                else:
                    print(f"Failed to generate image for prompt: {prompts[idx]}")

        # Run the asynchronous tasks
        asyncio.run(run_async_tasks())
        print("All images processed and posted")

    except Exception as e:
        logging.error(f"Error in generate_and_post_images: {e}")


# Process story endpoint
@app.route("/process-story", methods=["POST"])
def process_story():
    try:
        data = request.json
        tripetto_id = data.get("tripettoId")
        if not tripetto_id:
            return jsonify({"error": "tripettoId is required"}), 400

        if StoryData.query.filter_by(tripettoId=tripetto_id).first():
            return jsonify({"error": "tripettoId already exists"}), 400

        # Convert Tripetto JSON to lists
        (
            order,
            story_configuration,
            visual_configuration,
        ) = convert_tripetto_json_to_lists(data)

        # Generate story
        book_data = generate_story(story_configuration)

        # Save the initial story data to the database
        new_story_data = StoryData(
            tripettoId=tripetto_id,
            order=json.dumps(order),
            story_configuration=json.dumps(story_configuration),
            visual_configuration=json.dumps(visual_configuration),
            story=json.dumps(book_data),
            image_urls=json.dumps([]),
        )

        db.session.add(new_story_data)
        db.session.commit()

        # Start the rest of the processing in a separate thread
        print("Starting thread")
        thread = Thread(
            target=generate_and_post_images,
            args=(tripetto_id, book_data, visual_configuration),
        )
        thread.start()

        # Return immediate response with the story
        return jsonify(
            {
                "tripettoId": tripetto_id,
                "order": order,
                "story_configuration": story_configuration,
                "story": book_data,
            }
        )

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return jsonify({"error": str(e)}), 500


# Endpoint to retrieve story data
@app.route("/get-story-data/<tripetto_id>", methods=["GET"])
def get_story_data(tripetto_id):
    story_data = StoryData.query.filter_by(tripettoId=tripetto_id).first()
    if story_data:
        return jsonify(
            {
                "tripettoId": tripetto_id,
                "order": json.loads(story_data.order),
                "story_configuration": json.loads(story_data.story_configuration),
                "visual_configuration": json.loads(story_data.visual_configuration),
                "story": json.loads(story_data.story),
                "image_urls": json.loads(story_data.image_urls),
            }
        )
    else:
        return jsonify({"error": "Data not found"}), 404


if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True, host="localhost", port=5000)  # Run app
