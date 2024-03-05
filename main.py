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
from post_to_webhook import post_to_webhook

# Initialize Flask app and load environment variables
dotenv.load_dotenv()
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Configure the database using environment variables
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# Database model for story data
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
    visual_desc = generate_visual_description(visual_configuration)
    logging.info("Visual description generated")

    visual_descriptions = extract_visual_description(visual_desc)
    logging.info("Visual descriptions extracted")

    post_to_webhook(visual_descriptions)
    logging.info(f"Posted to Webhook: {visual_descriptions}")

    img_prompts = generate_image_prompts(story, visual_descriptions)
    logging.info("Image prompts generated")

    image_prompts = extract_output_image_prompts(img_prompts)
    logging.info("Image prompts extracted")

    post_to_webhook(image_prompts)
    logging.info(f"Posted prompts to webhook: {image_prompts}")

    api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6NTgxMSwiZW1haWwiOiJuYWdlbC5icmVtZW5AZ21haWwuY29tIiwidXNlcm5hbWUiOiJuYWdlbC5icmVtZW5AZ21haWwuY29tIiwiaWF0IjoxNzAyODkzODIxfQ.FK9cfnILlaBYot1MRguTdt1_cBGTC0z92WikYoNtYd8"

    generator = ImageGenerator(api_key)
    headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
    url = "https://littlestorywriter.com/img-upload"

    async def run_async_tasks():
        prompts = list(image_prompts.values())
        image_uris = await generator.generate_images(prompts)

        page_labels_with_uris = {
            f"page_{idx:02d}": image_uri
            for idx, image_uri in enumerate(image_uris)
            if image_uri
        }

        logging.info("Image generation complete")

        post_payload = {
            "image_urls": page_labels_with_uris,
            "tripettoId": tripetto_id,
        }

        post_to_webhook(post_payload)
        response = requests.post(url, json=post_payload, headers=headers)
        response.raise_for_status()

    def thread_target():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_async_tasks())
        loop.close()

    thread = Thread(target=thread_target)
    thread.start()
    thread.join()
    logging.info("Image posting complete")


# Global exception handler for the Flask app
@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"An error occurred: {e}")
    return jsonify({"error": str(e)}), 500


# Endpoint to process a story
@app.route("/process-story", methods=["POST"])
def process_story():
    try:
        data = request.json
        tripetto_id = data.get("tripettoId")
        if not tripetto_id:
            return jsonify({"error": "tripettoId is required"}), 400

        if StoryData.query.filter_by(tripettoId=tripetto_id).first():
            return jsonify({"error": "tripettoId already exists"}), 400

        order, story_configuration, visual_configuration = (
            convert_tripetto_json_to_lists(data)
        )
        book_data = generate_story(story_configuration)

        new_story_data = StoryData(
            tripettoId=tripetto_id,
            order=json.dumps(order),
            story_configuration=json.dumps(story_configuration),
            visual_configuration=json.dumps(visual_configuration),
            story=json.dumps(book_data),
            image_urls=json.dumps([]),
        )
        post_to_webhook(
            {
                "tripettoId": tripetto_id,
                "order": order,
                "story_configuration": story_configuration,
                "visual_configuration": visual_configuration,
                "story": book_data,
            }
        )
        db.session.add(new_story_data)
        db.session.commit()

        thread = Thread(
            target=generate_and_post_images,
            args=(tripetto_id, book_data, visual_configuration),
        )
        thread.start()

        return jsonify(
            {
                "tripettoId": tripetto_id,
                "order": order,
                "story_configuration": story_configuration,
                "story": book_data,
            }
        )

    except Exception as e:
        return handle_exception(e)


# Endpoint to retrieve story data
@app.route("/get-story-data/<tripetto_id>", methods=["GET"])
def get_story_data(tripetto_id):
    try:
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

    except Exception as e:
        return handle_exception(e)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=False)
