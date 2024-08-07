import logging
import json
import os
import requests
import asyncio
from threading import Thread
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import dotenv

# Import custom modules
from image_generator import ImageGenerator
from LSW_00_Tripetto_to_List import convert_tripetto_json_to_lists
from LSW_01_story_generation import generate_story
from LSW_02_visual_generation import generate_visual_description
from LSW_03_image_prompt_generation import generate_image_prompts
from child_image_prompt_generator import generate_child_image_prompt
from extract_images import extract_output_image_prompts
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


def is_in_desired_format(visual_descriptions_dict):
    # Check if the visual descriptions are already in the desired format
    return (
        "child_character" in visual_descriptions_dict
        and "companion" in visual_descriptions_dict
        and "illustration_style" in visual_descriptions_dict
    )


def transform_to_desired_format(visual_descriptions_dict, child_image_uri=None):
    # Transform the visual descriptions to the desired format
    desired_format = {
        "child_character": None,
        "companion": None,
        "illustration_style": None,
    }

    if "characters" in visual_descriptions_dict:
        for character in visual_descriptions_dict.get("characters", []):
            if "child_character" in character:
                desired_format["child_character"] = character["child_character"]
                if child_image_uri:
                    desired_format["child_character"]["child_img_uri"] = child_image_uri
            if "companion" in character:
                desired_format["companion"] = character["companion"]
    else:
        if "child_character" in visual_descriptions_dict:
            desired_format["child_character"] = visual_descriptions_dict[
                "child_character"
            ]
            if child_image_uri:
                desired_format["child_character"]["child_img_uri"] = child_image_uri
        if "companion" in visual_descriptions_dict:
            desired_format["companion"] = visual_descriptions_dict["companion"]

    desired_format["illustration_style"] = visual_descriptions_dict.get(
        "illustration_style", []
    )

    return desired_format


def generate_and_post_images(tripetto_id, story, visual_configuration):
    try:
        visual_descriptions = generate_visual_description(visual_configuration)
        logging.info(f"Visual description generated: {visual_descriptions}")
        visual_descriptions_dict = json.loads(visual_descriptions)
        logging.debug(
            f"Visual descriptions dict before transformation: {visual_descriptions_dict}"
        )
        if not is_in_desired_format(visual_descriptions_dict):
            visual_descriptions_dict = transform_to_desired_format(
                visual_descriptions_dict
            )

        logging.info(f"Transformed visual descriptions: {visual_descriptions_dict}")

        child_prompt = generate_child_image_prompt(json.dumps(visual_descriptions_dict))
        logging.info(f"Child image prompt generated successfully: {child_prompt}")

        if child_prompt:
            post_to_webhook(f"Child image prompt: {child_prompt}")
            mid_api_key = os.getenv("MID_API_KEY")
            generator = ImageGenerator(mid_api_key)

            async def generate_and_post_child_image():
                child_image_uris = await generator.generate_images(child_prompt)
                logging.info("Child image generation complete")

                if child_image_uris and child_image_uris[0]:
                    child_image_uri = child_image_uris[0]
                    post_to_webhook(f"Child image URI generated: {child_image_uri}")
                    logging.info(f"Posted child image to webhook: {child_image_uri}")

                    updated_visual_descriptions = transform_to_desired_format(
                        visual_descriptions_dict, child_image_uri
                    )

                    logging.info(
                        f"Updated visual descriptions: {updated_visual_descriptions}"
                    )
                    post_to_webhook(
                        f"Updated visual descriptions: {updated_visual_descriptions}"
                    )

                    data = generate_image_prompts(story, updated_visual_descriptions)
                    image_prompts = extract_output_image_prompts(data)
                    post_to_webhook(f"Image prompts: {image_prompts}")
                    logging.info("Posted image prompts to webhook: %s", image_prompts)

                    async def run_async_tasks():
                        image_uris = await generator.generate_images(image_prompts)
                        page_labels_with_uris = {
                            f"page_{idx:02d}": image_uri
                            for idx, image_uri in enumerate(image_uris)
                            if image_uri
                        }

                        logging.info("Image generation complete")
                        post_to_webhook(
                            f"Image URIs generated: {page_labels_with_uris}"
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

                        post_to_webhook(post_payload)
                        response = requests.post(
                            url, json=post_payload, headers=headers
                        )
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

                else:
                    logging.warning("No valid child image URI generated.")

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(generate_and_post_child_image())
            loop.close()

        else:
            logging.warning("No valid child image prompt found.")
    except Exception as e:
        logging.error("An error occurred during image generation and posting: %s", e)


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
        return handle_exception(e)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=False)
