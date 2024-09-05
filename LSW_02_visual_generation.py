import json
import logging
import os
import time

import dotenv
import openai

from post_to_webhook import post_to_webhook

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load API key and initialize OpenAI client
dotenv.load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.Client()

assistant_id = os.getenv("VISUAL_ASSISTANT_ID")


def generate_visual_description(visual_configuration):
    """
    Generates a visual description based on the provided visual configuration using OpenAI's API.

    :param visual_configuration: A string or JSON representing the visual configuration.
    :return: Generated visual description as a string.
    """
    try:
        # Create a new thread for communication with the assistant
        thread = client.beta.threads.create()

        user_input = (
            json.dumps(visual_configuration)
            if not isinstance(visual_configuration, str)
            else visual_configuration
        )
        client.beta.threads.messages.create(
            thread_id=thread.id, role="user", content=user_input
        )

        # Run assistant and wait for completion
        run = client.beta.threads.runs.create(
            thread_id=thread.id, assistant_id=assistant_id
        )
        loop_counter = 0

        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread.id, run_id=run.id
            )
            if run_status.status == "completed":
                break
            if loop_counter % 3 == 0:
                logging.info("...writing...")
            loop_counter += 1
            time.sleep(1)

        # Retrieve the assistant's response
        messages = client.beta.threads.messages.list(thread_id=thread.id).data
        logging.info("Raw Visual description messages: %s", messages)
        post_to_webhook(f"Raw Visual description messages: {messages}")
        assistant_response = next(
            (msg.content[0].text.value for msg in messages if msg.role == "assistant"),
            None,
        )
        logging.info("Parsed Visual description response: %s", assistant_response)
        post_to_webhook(f"Parsed Visual description response: {assistant_response}")

        return (
            assistant_response
            if assistant_response
            else "No response from the assistant."
        )

    except Exception as e:
        logging.error(f"Error in generating visual description: {e}")
        post_to_webhook(f"Error in generating visual description: {e}")
        return None
