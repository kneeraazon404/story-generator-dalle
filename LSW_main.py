""" Module Description
This script is the main orchestrator for a story and image generation process.
It takes input from a JSON file, generates a story, a visual description, and images based on the provided data.

"""
import dotenv
import logging
import requests

# Configure basic logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
dotenv.load_dotenv()

from LSW_00_Tripetto_to_List import convert_tripetto_json_to_lists
from LSW_01_story_generation import generate_story
from LSW_02_visual_configurator import generate_visual_description
from LSW_03_image_prompt_generation import generate_image_prompts
from LSW_04_image_generation import generate_images_from_prompts

import re


# Function to post to a webhook
def post_to_webhook(response):
    if isinstance(response, str):
        # If the response is already a string, no need to extract text
        text_content = response
    else:
        # Access the text content directly
        text_content = response.text

    payload = {"response": text_content}
    requests.post("https://webhook.site/LSW-process-logging", json=payload)


def extract_output_image_prompts(input_text):
    # Use regular expressions to extract the image prompts in the specified format
    matches = re.findall(r'"prompt_img_\d{2}": "(.*?)"', input_text)

    # Create a dictionary of prompts
    output_image_prompts = {
        f"prompt_img_{i:02}": prompt for i, prompt in enumerate(matches)
    }

    return output_image_prompts


def main():
    logging.info("Starting the process...")

    # Constants for file paths
    FILE_PATH = r"JSON-Input_Tripetto.json"

    # Convert JSON data to lists
    order, story_configuration, visual_configuration = convert_tripetto_json_to_lists(
        FILE_PATH
    )
    logging.info("Received new data lists: 'Order' and 'story_configuration'")

    # Log the entire lists
    logging.info(f"Order List: {order}")
    logging.info(f"Story Configuration: {story_configuration}")
    logging.info(f"Visual Description: {visual_configuration}")

    # Generating the story
    logging.info("Generating story based on configuration...")
    book_data = generate_story(story_configuration)
    logging.info("Story generation completed.")

    # Log the generated story
    logging.info(f"Generated Story: {book_data}")

    # Generating visual description
    logging.info("Generating visual description based on configuration...")
    visual_description = generate_visual_description(visual_configuration)
    logging.info("Visual description generation completed.")

    # Log the generated visual description
    logging.info(f"Generated Visual Description: {visual_description}")

    # Generate image prompts
    logging.info("Generating image prompts...")
    image_prompts = generate_image_prompts(book_data, visual_description)
    logging.info("Image prompt generation completed.")

    #  Log the generated image prompts
    logging.info(f"Generated Image Prompts: {image_prompts}")

    prompts_for_images = extract_output_image_prompts(image_prompts)
    logging.info("Prompts for Images:", prompts_for_images)
    # Generate images from prompts
    logging.info("Generating images from prompts...")
    generate_images_from_prompts(prompts_for_images)
    logging.info("Image generation completed.")


if __name__ == "__main__":
    main()
