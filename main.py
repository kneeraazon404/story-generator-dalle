import asyncio
import json
import logging
import os
import traceback
from threading import Thread

import dotenv
import requests
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

from child_image_prompt_generator import generate_child_image_prompt
from extract_images import extract_output_image_prompts

# Import custom modules
from image_generator import ImageGenerator
from LSW_00_Tripetto_to_List import convert_tripetto_json_to_lists
from LSW_01_story_generation import generate_story
from LSW_02_visual_generation import generate_visual_description
from LSW_03_image_prompt_generation import generate_image_prompts
from post_to_webhook import post_to_webhook

# Initialize Flask app and load environment variables
dotenv.load_dotenv()
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Configure the database
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


def generate_and_post_images(tripetto_id, story, visual_configuration):
    try:
        visual_descriptions = generate_visual_description(visual_configuration)
        cleaned_str = (
            visual_descriptions.replace("```json", "").replace("```", "").strip()
        )
        updated_visual_description = json.loads(cleaned_str)
        logging.info(
            "Visual description Jsonified successfully: %s", updated_visual_description
        )
        post_to_webhook(
            f"Visual description Jsonified successfully: {updated_visual_description}"
        )

        # Generate the child image prompts
        child_prompt = generate_child_image_prompt(
            json.dumps(updated_visual_description)
        )
        logging.info("Child image prompt generated successfully: %s", child_prompt)

        if child_prompt:
            post_to_webhook("Child image prompt: %s" % child_prompt)
            mid_api_key = os.getenv("MID_API_KEY")
            if not mid_api_key:
                raise EnvironmentError("MID_API_KEY environment variable not found.")

            generator = ImageGenerator(mid_api_key)

            async def generate_and_post_child_image():
                try:
                    child_image_uris = await generator.generate_images(child_prompt)
                    logging.info("Child image generation complete")

                    if child_image_uris and child_image_uris[0]:
                        child_image_uri = child_image_uris[0]
                        post_to_webhook(
                            "Child image URI generated: %s" % child_image_uri
                        )
                        logging.info(
                            "Posted child image to webhook: %s", child_image_uri
                        )

                        # Assuming the updated_visual_descriptions dict is updated later
                        updated_visual_descriptions = updated_visual_description
                        updated_visual_descriptions[2] = {
                            "child_image_uri": child_image_uri
                        }
                        logging.info(
                            "Updated visual descriptions: %s",
                            updated_visual_descriptions,
                        )
                        post_to_webhook(
                            "Updated visual descriptions: %s"
                            % updated_visual_descriptions
                        )

                        generated_response = generate_image_prompts(
                            story, updated_visual_descriptions
                        )

                        # logging.info("Image prompts RAW: %s", image_prompts)
                        post_to_webhook("Image prompts RAW: %s" % generated_response)

                        image_prompts = list(
                            generated_response["image_prompts"].values()
                        )

                        logging.info("Image prompts list: %s", image_prompts)
                        post_to_webhook("Image prompts list: %s" % image_prompts)
                        image_uris = await generator.generate_images(image_prompts)
                        page_labels_with_uris = {
                            f"page_{idx:02d}": image_uri
                            for idx, image_uri in enumerate(image_uris)
                            if image_uri
                        }

                        logging.info("Image generation complete")
                        post_to_webhook(
                            "Image URIs generated: %s" % page_labels_with_uris
                        )
                        post_payload = {
                            "image_urls": page_labels_with_uris,
                            "tripettoId": tripetto_id,
                        }
                        headers = {
                            "Content-Type": "application/json",
                            "User-Agent": "Mozilla/5.0",
                        }
                        url = "https://littlestorywriter.com/img-upload"
                        response = requests.post(
                            url, json=post_payload, headers=headers
                        )
                        if response.status_code == 200:
                            logging.info("Image posting complete")
                            post_to_webhook("Image posting complete")
                        else:
                            logging.error(
                                "Failed to post image URIs. Status: %d, Response: %s",
                                response.status_code,
                                response.content,
                            )

                    else:
                        logging.warning("No valid child image URI generated.")
                        post_to_webhook("No valid child image URI generated.")

                except Exception as e:
                    logging.error(
                        "An error occurred during image generation and posting: %s", e
                    )
                    post_to_webhook("An error occurred: %s" % e)

            asyncio.run(generate_and_post_child_image())

        else:
            logging.warning("No valid child image prompt found.")
            post_to_webhook("No valid child image prompt found.")
    except Exception as e:
        logging.error("An error occurred during image generation and posting: %s", e)
        logging.error("Traceback: %s", traceback.format_exc())
        post_to_webhook(
            "An error occurred: %s\nTraceback: %s" % (e, traceback.format_exc())
        )


# Global exception handler for the Flask app
@app.errorhandler(Exception)
def handle_exception(e):
    logging.error("An error occurred: %s", e)
    return jsonify({"error": str(e)}), 500


# Endpoint to process a story
@app.route("/process-story", methods=["POST"])
def process_story():
    try:
        post_to_webhook("===========================================================")
        post_to_webhook(
            f"Logs for the new entry with id: {request.json.get('tripettoId')}"
        )
        post_to_webhook("===========================================================")
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
        logging.info("==============================================")
        logging.info(f"Book data generated: {book_data}")
        post_to_webhook(f"Book data generated: {book_data}")
        logging.info("==============================================")

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

        thread = Thread(
            target=generate_and_post_images,
            args=(tripetto_id, book_data, visual_configuration),
        )
        thread.start()

        response_data = {
            "tripettoId": tripetto_id,
            "order": order,
            "story_configuration": story_configuration,
            "visual_configuration": visual_configuration,
            "story": book_data,
        }

        # logging.info(jsonify(response_data))

        # Post the story to the webhook endpoint before returning
        endpoint_url = "https://littlestorywriter.com/process-story"
        response = requests.post(endpoint_url, json=response_data)
        logging.info(f"Response from webhook: {response.text}")
        if response.status_code != 200:
            return jsonify({"error": "Failed to post to webhook"}), 500

        return jsonify(
            {
                "tripettoId": tripetto_id,
                "story": book_data,
            }
        )
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        post_to_webhook(f"An error occurred: {e}")
        return jsonify({"error": "An internal error occurred"}), 500


# Endpoint to retrieve story data
@app.route("/get-story-data/<tripetto_id>", methods=["GET"])
def get_story_data(tripetto_id):
    try:
        story_data = StoryData.query.filter_by(tripettoId=tripetto_id).first_or_404()
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

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        post_to_webhook(f"An error occurred: {e}")
        return handle_exception(e)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=False)
