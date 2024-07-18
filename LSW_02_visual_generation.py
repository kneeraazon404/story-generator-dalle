import openai
import os
import time
import json
import logging
import dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load API key and initialize OpenAI client
dotenv.load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.Client()

assistant_id = os.getenv("VISUAL_ASSISTANT_ID")


def extract_json_from_string(json_string):
    """
    Extracts and parses JSON data from a JSON string.

    :param json_string: A string representing JSON data.
    :return: Parsed JSON data as a Python object (list or dict).
    """
    try:
        # Clean the markdown markers if they exist
        if json_string.startswith("```json") and json_string.endswith("```"):
            json_string = json_string[7:-3].strip()
        elif json_string.startswith("```") and json_string.endswith("```"):
            json_string = json_string[3:-3].strip()

        parsed_json = json.loads(json_string)
        return parsed_json
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON: {e}")
        logging.error(f"Invalid JSON string: {json_string}")
        return None


def convert_list_to_dict(json_list):
    """
    Converts a list of dictionaries into a single dictionary.

    :param json_list: A list of dictionaries.
    :return: A single dictionary.
    """
    combined_dict = {}
    for item in json_list:
        combined_dict.update(item)
    return combined_dict


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
        assistant_response = next(
            (msg.content[0].text.value for msg in messages if msg.role == "assistant"),
            None,
        )

        if assistant_response:
            logging.info(f"Assistant response received: {assistant_response}")
            assistant_response = extract_json_from_string(assistant_response)
            if assistant_response:
                logging.info("Visual description generated successfully.")
                assistant_response = convert_list_to_dict(assistant_response)
                return assistant_response
            else:
                raise ValueError("Error parsing assistant response JSON.")
        else:
            raise ValueError("No response from the assistant.")

    except Exception as e:
        logging.error(f"Error in generating visual description: {e}")
        return None
