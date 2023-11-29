"""
This script is designed to interact with the OpenAI API to generate stories based on a given configuration.
It also includes functionality to post responses to a webhook for further processing or logging.
"""

import json
import os
import time
import logging
import requests
import dotenv
import openai
from post_to_webhook import post_to_webhook

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
dotenv.load_dotenv()

# Load API key and initialize OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.Client()

# Define assistant IDs
assistant_id = "asst_XgNDfaqQSzWKi0pWPdBnPJpp"
second_assistant_id = "asst_7yhXnmwuWZlUoexb30l4hyv2"

# Create a new thread for communication with the assistant
threadResponse = openai.beta.threads.create()
thread = threadResponse


def generate_story(story_configuration):
    """
    Generates a story based on the provided story configuration using OpenAI's API.

    :param story_configuration: A string or JSON representing the story configuration.
    :return: Generated story as a string.
    """
    user_input = (
        json.dumps(story_configuration)
        if not isinstance(story_configuration, str)
        else story_configuration
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
        book_data = next(
            (
                m.content[0].text.value
                for m in messages
                if m.role == "assistant" and m.content
            ),
            None,
        )

        if book_data:
            logging.info("Posting story to webhook...")
            post_to_webhook(book_data)
            logging.info("Story posted to webhook.")
        else:
            logging.warning("No answer from OpenAI for story generation.")
            post_to_webhook("No answer from OpenAI for story generation.")

        return book_data
    except Exception as e:
        logging.error(f"Error in story generation: {e}")
        return None
