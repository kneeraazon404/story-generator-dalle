import logging
import re

import dotenv
import requests
from flask import Flask, jsonify, request

from extract_visual_descriptions import extract_visual_description

# Import your modules here
from LSW_00_Tripetto_to_List import convert_tripetto_json_to_lists
from LSW_01_story_generation import generate_story
from LSW_02_visual_configurator import generate_visual_description
from LSW_03_image_prompt_generation import generate_image_prompts
from LSW_04_image_generation import generate_images_from_prompts

# Initialize Flask app
app = Flask(__name__)

# Configure basic logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
dotenv.load_dotenv()


# Function to post to a webhook
def post_to_webhook(response):
    if isinstance(response, str):
        text_content = response
    else:
        text_content = response.text

    payload = {"response": text_content}
    requests.post("https://webhook.site/LSW-process-logging", json=payload)


def extract_output_image_prompts(input_text):
    matches = re.findall(r'"prompt_img_\d{2}": "(.*?)"', input_text)
    output_image_prompts = {
        f"prompt_img_{i:02}": prompt for i, prompt in enumerate(matches)
    }
    return output_image_prompts


@app.route("/process-story", methods=["POST"])
def process_story():
    try:
        data = request.json

        # Convert JSON data to lists
        (
            order,
            story_configuration,
            visual_configuration,
        ) = convert_tripetto_json_to_lists(data)

        # log the order, story_configuration, and visual_configuration
        logging.info(f"Order: {order}")
        logging.info(f"Story Configuration: {story_configuration}")
        logging.info(f"Visual Configuration: {visual_configuration}")

        # Process data
        logging.info("Generating story based on configuration...")
        book_data = generate_story(story_configuration)
        post_to_webhook(f"Book :  {book_data[0]} written.")
        logging.info("Story generation completed.")

        logging.info("Generating visual description based on configuration...")
        visual_description = generate_visual_description(visual_configuration)
        logging.info("Visual description generation completed.")

        logging.info("Generating image prompts...")
        image_prompts = generate_image_prompts(book_data, visual_description)
        logging.info("Image prompt generation completed.")

        prompts_for_images = extract_output_image_prompts(image_prompts)

        logging.info("Generating images from prompts...")
        image_urls = generate_images_from_prompts(prompts_for_images)
        post_to_webhook(f"Images generated for the book  {book_data[0]}")
        logging.info("Image generation completed.")

        # Prepare output data
        output_data = {
            "orders": order,
            "story_configurations": story_configuration,
            "visual_configurations": visual_configuration,
            "book_stories": book_data,
            "visual_descriptions": extract_visual_description(visual_description),
            "image_prompts": extract_output_image_prompts(image_prompts),
            "image_urls": image_urls,
        }

        return jsonify(output_data)

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
