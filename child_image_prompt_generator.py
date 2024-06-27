import os
import time
import logging
import dotenv
import openai
import json

# Configure basic logging
logging.basicConfig(level=logging.INFO)

# Load API key
dotenv.load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = openai.OpenAI()

assistant_id = os.getenv("CHILD_ASSISTANT_ID")
# Create a new thread for communication with the assistant
thread_response = client.beta.threads.create()
thread = thread_response


def generate_child_image_prompt(story_configuration):
    """
    Generates a child image prompt based on the provided story configuration using OpenAI's API.

    :param story_configuration: A string or JSON representing the story configuration.
    :return: List of values from the generated story.
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
        story_response = next(
            (
                m.content[0].text.value
                for m in messages
                if m.role == "assistant" and m.content
            ),
            None,
        )

        if story_response:
            # Remove 'book_data = ' from the beginning of the response
            formatted_response = story_response.replace("book_data = ", "", 1).strip()
            story_data = json.loads(formatted_response)
            return list(story_data.values())
        else:
            logging.error("No story response received")
            return []

    except Exception as e:
        logging.error(f"Error in story generation: {e}")
        return []
