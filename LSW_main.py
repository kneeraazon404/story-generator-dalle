""" Module Description
This script is the main orchestrator for a story and image generation process.
It takes input from a JSON file, generates a story, a visual description, and images based on the provided data.

"""
import json
import logging

import dotenv
import requests

# Configure basic logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
dotenv.load_dotenv()

import re

from LSW_00_Tripetto_to_List import convert_tripetto_json_to_lists
from LSW_01_story_generation import generate_story
from LSW_02_visual_configurator import generate_visual_description
from LSW_03_image_prompt_generation import generate_image_prompts
from LSW_04_image_generation import generate_images_from_prompts
from extract_visual_descriptions import extract_visual_description


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
    post_to_webhook(f"Book :  {book_data[0]} written.")
    logging.info("Story generation completed.")

    # Generating visual description
    logging.info("Generating visual description based on configuration...")
    visual_description = generate_visual_description(visual_configuration)
    logging.info("Visual description generation completed.")

    # Generate image prompts
    # logging.info("Generating image prompts...")
    # image_prompts = generate_image_prompts(book_data, visual_description)
    # logging.info("Image prompt generation completed.")

    # prompts_for_images = extract_output_image_prompts(image_prompts)

    # Generate images from prompts
    # logging.info("Generating images from prompts...")
    # image_urls = generate_images_from_prompts(prompts_for_images)
    # post_to_webhook(f"Images generated for the book  {book_data[0]}")
    # logging.info("Image generation completed.")
    # Write the outputs to a JSON file
    # extracted_stories = extract_visual_description(visual_description)
    output_data = {
        "orders": order,
        "story_configurations": story_configuration,
        "visual_configurations": visual_configuration,
        "book_stories": book_data,
        "visual_descriptions": extract_visual_description(visual_description),
        # "image_prompts": extract_output_image_prompts(image_prompts),
        # "image_urls": image_urls,
    }
    with open("JSON-Output.json", "w") as outfile:
        json.dump(output_data, outfile, indent=4)

    logging.info("All data saved to output_data.json")


if __name__ == "__main__":
    main()
