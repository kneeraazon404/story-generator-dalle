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


def generate_and_post_images(tripetto_id, story, visual_configuration):
    try:
        visual_descriptions = generate_visual_description(visual_configuration)
        logging.info(f"Visual description generated: {visual_descriptions}")

        post_to_webhook(
            f"Visual descriptions stage 1 with tripetto id: {tripetto_id} and Visual Descriptions: {visual_descriptions}"
        )

        child_prompt = generate_child_image_prompt(visual_descriptions)
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
                    child_image_payload = {
                        "tripettoId": tripetto_id,
                        "child_image_url": child_image_uri,
                    }
                    post_to_webhook(child_image_payload)
                    logging.info(f"Posted child image to webhook: {child_image_uri}")

                    visual_descriptions_dict = json.loads(visual_descriptions)
                    logging.debug(
                        f"Visual descriptions dict before update: {visual_descriptions_dict}"
                    )

                    if "child_character" in visual_descriptions_dict:
                        visual_descriptions_dict["child_character"][
                            "child_img_uri"
                        ] = child_image_uri
                    else:
                        logging.error(
                            "'child_character' key not found in visual_descriptions_dict"
                        )

                    logging.info(
                        f"Updated visual descriptions: {visual_descriptions_dict}"
                    )
                    post_to_webhook(
                        f"Updated visual descriptions: {visual_descriptions_dict}"
                    )

                    data = generate_image_prompts(story, visual_descriptions_dict)
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
        logging.info("==============================================")

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
                "visual_configuration": visual_configuration,
                "story": book_data,
            }
        )

    except Exception as e:
        return handle_exception(e)


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
