"""
Main module for the Story Generator application.

This module contains the Flask application and the main logic for processing
stories, generating images, and interacting with the database. It integrates
various components such as story generation, visual description generation,
and image prompt generation.

The application provides endpoints for processing stories and retrieving
story data, and uses SQLAlchemy for database operations.
"""

import asyncio
import json
import logging
import os
from threading import Thread
from typing import Dict, Tuple

import dotenv
import requests
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import HTTPException

from child_image_prompt_generator import generate_child_image_prompt
from extract_images import extract_output_image_prompts
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

# Constants
WEBHOOK_URL = "https://littlestorywriter.com/img-upload"
PROCESS_STORY_URL = "https://littlestorywriter.com/process-story"


class StoryData(db.Model):
    """
    Database model for storing story data.

    Attributes:
        id (int): Primary key for the story data.
        tripetto_id (str): Unique identifier for the story.
        order (str): JSON string representing the order of story elements.
        story_configuration (str): JSON string representing the story configuration.
        visual_configuration (str): JSON string representing the visual configuration.
        story (str): JSON string representing the generated story.
        image_urls (str): JSON string representing the URLs of generated images.
    """

    id = db.Column(db.Integer, primary_key=True)
    tripetto_id = db.Column(db.String(100), unique=True, nullable=False)
    order = db.Column(db.Text)
    story_configuration = db.Column(db.Text)
    visual_configuration = db.Column(db.Text)
    story = db.Column(db.Text)
    image_urls = db.Column(db.Text)


def generate_and_post_images(
    tripetto_id: str, story: Dict, visual_configuration: Dict
) -> None:
    """
    Generate and post images based on the story and visual configuration.

    This function generates visual descriptions, child image prompts, and story images.
    It then posts these images to a webhook and updates the database.

    Args:
        tripetto_id (str): The unique identifier for the story.
        story (Dict): The generated story data.
        visual_configuration (Dict): The visual configuration for image generation.
    """
    try:
        visual_descriptions = generate_visual_description(visual_configuration)
        logging.info("Visual description generated: %s", visual_descriptions)

        child_prompt = generate_child_image_prompt(str(visual_descriptions))
        logging.info("Child image prompt generated successfully: %s", child_prompt)

        if child_prompt:
            post_to_webhook(f"Child image prompt: {child_prompt}")
            mid_api_key = os.getenv("MID_API_KEY")
            generator = ImageGenerator(mid_api_key)

            async def generate_and_post_child_image() -> None:
                child_image_uris = await generator.generate_images(child_prompt)
                logging.info("Child image generation complete")

                if child_image_uris and child_image_uris[0]:
                    child_image_uri = child_image_uris[0]
                    post_to_webhook(f"Child image URI generated: {child_image_uri}")
                    logging.info("Posted child image to webhook: %s", child_image_uri)

                    updated_visual_descriptions = {
                        **visual_descriptions,
                        "child_image_uri": child_image_uri,
                    }

                    logging.info(
                        "Updated visual descriptions: %s", updated_visual_descriptions
                    )
                    post_to_webhook(
                        f"Updated visual descriptions: {updated_visual_descriptions}"
                    )

                    data = generate_image_prompts(story, updated_visual_descriptions)
                    image_prompts = extract_output_image_prompts(data)
                    post_to_webhook(f"Image prompts: {image_prompts}")
                    logging.info("Posted image prompts to webhook: %s", image_prompts)

                    async def run_async_tasks() -> None:
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

                        post_to_webhook(post_payload)
                        response = requests.post(
                            WEBHOOK_URL,
                            json=post_payload,
                            headers=headers,
                            timeout=60,
                        )
                        response.raise_for_status()

                    def thread_target() -> None:
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
    except requests.RequestException as e:
        post_to_webhook(f"An error occurred during image generation and posting: {e}")
        logging.error(
            "An error occurred during image generation and posting: %s", str(e)
        )
    except asyncio.TimeoutError:
        post_to_webhook("Timeout error occurred during image generation and posting")
        logging.error("Timeout error occurred during image generation and posting")
    except Exception as e:
        post_to_webhook(
            f"An unexpected error occurred during image generation and posting: {e}"
        )
        logging.error(
            "An unexpected error occurred during image generation and posting: %s",
            str(e),
        )


@app.errorhandler(Exception)
def handle_exception(e: Exception) -> Tuple[Dict, int]:
    """
    Global exception handler for the Flask app.

    Args:
        e (Exception): The exception that was raised.

    Returns:
        Tuple[Dict, int]: A JSON response with the error message and a 500 status code.
    """
    logging.error("An error occurred: %s", str(e))
    if isinstance(e, HTTPException):
        return jsonify({"error": str(e)}), e.code
    return jsonify({"error": "An internal error occurred"}), 500


@app.route("/process-story", methods=["POST"])
def process_story() -> Tuple[Dict, int]:
    """
    Endpoint to process a story.

    This function handles the POST request to process a story. It generates
    the story, saves it to the database, and initiates image generation.

    Returns:
        Tuple[Dict, int]: A JSON response containing the processed story data
        or an error message, along with an HTTP status code.
    """
    try:
        post_to_webhook("=" * 60)
        data = request.json
        tripetto_id = data.get("tripettoId")
        if not tripetto_id:
            return jsonify({"error": "tripettoId is required"}), 400

        post_to_webhook(f"Logs for the new entry with id: {tripetto_id}")
        post_to_webhook("=" * 60)

        with app.app_context():
            if StoryData.query.filter_by(tripetto_id=tripetto_id).first():
                return jsonify({"error": "tripettoId already exists"}), 400

            order, story_configuration, visual_configuration = (
                convert_tripetto_json_to_lists(data)
            )
            book_data = generate_story(story_configuration)
            logging.info("=" * 45)
            logging.info("Book data generated: %s", book_data)
            post_to_webhook(f"Book data generated: {book_data}")
            logging.info("=" * 45)

            new_story_data = StoryData(
                tripetto_id=tripetto_id,
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

        # Post the story to the webhook endpoint before returning
        try:
            response = requests.post(PROCESS_STORY_URL, json=response_data, timeout=60)
            logging.info("Response from webhook: %s", response.text)
            response.raise_for_status()
        except requests.RequestException as e:
            logging.error("Failed to post to webhook: %s", str(e))
            return jsonify({"error": "Failed to post to webhook"}), 500

        return jsonify(
            {
                "tripettoId": tripetto_id,
                "story": book_data,
            }
        )
    except Exception as e:
        logging.error("An error occurred: %s", str(e))
        post_to_webhook(f"An error occurred: {e}")
        return jsonify({"error": "An internal error occurred"}), 500


@app.route("/get-story-data/<tripetto_id>", methods=["GET"])
def get_story_data(tripetto_id: str) -> Tuple[Dict, int]:
    """
    Endpoint to retrieve story data.

    This function handles the GET request to retrieve story data for a given
    tripetto_id.

    Args:
        tripetto_id (str): The unique identifier for the story.

    Returns:
        Tuple[Dict, int]: A JSON response containing the story data or an error message,
        along with an HTTP status code.
    """
    try:
        with app.app_context():
            story_data = StoryData.query.filter_by(
                tripetto_id=tripetto_id
            ).first_or_404()
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
        logging.error("An error occurred: %s", str(e))
        post_to_webhook(f"An error occurred: {e}")
        return handle_exception(e)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=False)
