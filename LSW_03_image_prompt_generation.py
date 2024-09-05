"""
This script is designed to interact with the OpenAI API to generate stories based on a given configuration.
It also includes functionality to post responses to a webhook for further processing or logging.
"""

import json
import logging
import os
import time

import dotenv
import openai
from openai import OpenAI

from post_to_webhook import post_to_webhook

# Configure logging
logging.basicConfig(level=logging.INFO)


# Load API key
dotenv.load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI()

assistant_id = os.getenv("IMAGE_PROMPT_ASSISTANT_ID")


# Create a new thread for communication with the assistant
threadResponse = openai.beta.threads.create()
thread = threadResponse


def generate_image_prompts(book_data, visual_description):
    """
    Generates image prompts based on the provided book data and visual description using OpenAI's API.
    """
    # Convert inputs to JSON strings if they are not already strings
    if not isinstance(book_data, str):
        book_data = json.dumps(book_data)
    if not isinstance(visual_description, str):
        visual_description = json.dumps(visual_description)

    user_input = (
        f"{{'book_data': {book_data}, 'visual_description': {visual_description}}}"
    )

    post_to_webhook(f"Input Book Data for image prompt generation: {book_data}")
    post_to_webhook(
        f"Input Updated Visual Description for image prompt generation: {visual_description}"
    )

    try:
        # Add user input as a message to the thread
        client.beta.threads.messages.create(
            thread_id=thread.id, role="user", content=user_input
        )

        # Run the assistant and wait for completion
        run = client.beta.threads.runs.create(
            thread_id=thread.id, assistant_id=assistant_id
        )
        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread.id, run_id=run.id
            )
            if run_status.status == "completed":
                break
            time.sleep(1)

        # Retrieve the assistant's response
        messages = client.beta.threads.messages.list(thread_id=thread.id).data
        logging.info(f"Image Prompt Generation Response RAW: {messages}")
        post_to_webhook(f"Assistant Response RAW: {messages}")
        assistant_response = next(
            (msg.content[0].text.value for msg in messages if msg.role == "assistant"),
            None,
        )
        logging.info(f"Generated image prompts response: {assistant_response}")
        post_to_webhook(f"Generated image prompts response: {assistant_response}")
        if assistant_response:

            return json.loads(assistant_response)
        else:
            logging.error("No image prompts response received")
            post_to_webhook("No image prompts response received")
            return {}

    except Exception as e:
        logging.error(f"Error in image prompts generation: {e}")
        post_to_webhook(f"Error in image prompts generation: {e}")
        return {}
