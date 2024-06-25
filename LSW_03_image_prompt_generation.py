import openai
import os
import time
import logging
import dotenv
from openai import OpenAI
from post_to_webhook import post_to_webhook

# Configure basic logging
logging.basicConfig(level=logging.INFO)

# Load API key
dotenv.load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI()

assistant_id = "asst_rzk3LObUHyZh93kkJCtZMQeG"

"""
This script is designed to interact with the OpenAI API to generate stories based on a given configuration.
It also includes functionality to post responses to a webhook for further processing or logging.
"""

import json
import os
import time
import logging
import dotenv
import openai
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
dotenv.load_dotenv()


# Load API key and initialize OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI()

# Define assistant IDs
assistant_id = "asst_rzk3LObUHyZh93kkJCtZMQeG"
# second_assistant_id = "asst_7yhXnmwuWZlUoexb30l4hyv2"

# Create a new thread for communication with the assistant
threadResponse = openai.beta.threads.create()
thread = threadResponse


def generate_image_prompts(book_data, visual_description):
    """
    Generates a story based on the provided story configuration using OpenAI's API.

    :param book_data: A string or JSON representing the story configuration.
    :param visual_description: A string or JSON representing the visual description.
    :return: Generated story as a dictionary.
    """

    # Convert inputs to JSON strings if they are not already strings
    if not isinstance(book_data, str):
        book_data = json.dumps(book_data)
    if not isinstance(visual_description, str):
        visual_description = json.dumps(visual_description)

    user_input = (
        f"{{'book_data': {book_data}, 'visual_description': {visual_description}}}"
    )

    post_to_webhook(f"Input Book Data: {book_data}")
    post_to_webhook(f"Input Updated Visual Description: {visual_description}")

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
        post_to_webhook(f"Assistant Response RAW: {messages}")
        # logging.info(f"Messages: {messages}")
        story_response = next(
            (
                m.content[0].text.value
                for m in messages
                if m.role == "assistant" and m.content
            ),
            None,
        )
        logging.info(f"Generated story response: {story_response}")
        if story_response:
            # Remove 'book_data = ' from the beginning of the response
            formatted_response = story_response.replace("book_data = ", "", 1).strip()
            return json.loads(formatted_response)
        else:
            logging.error("No story response received")
            return {}

    except Exception as e:
        logging.error(f"Error in story generation: {e}")
        return {}
