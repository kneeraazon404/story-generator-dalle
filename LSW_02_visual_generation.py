import openai
import os
import time
import json
import logging
import dotenv
from post_to_webhook import post_to_webhook

# Configure logging
logging.basicConfig(level=logging.INFO)


# Load API key and initialize OpenAI client
dotenv.load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.Client()

assistant_id = "asst_O4XGZ5j4OICeFT2bF3NiwXDQ"


def generate_visual_description(visual_configuration):
    """
    Generates a visual description based on the provided visual configuration using OpenAI's API.

    :param visual_configuration: A string or JSON representing the visual configuration.
    :return: Generated visual description as a string.
    """
    try:
        # Create a new thread for communication with the assistant
        thread = client.beta.threads.create()

        # Ensure the visual configuration is a JSON string
        user_input = (
            json.dumps(visual_configuration)
            if not isinstance(visual_configuration, str)
            else visual_configuration
        )

        post_to_webhook(f"Input Visual Configuration: {visual_configuration}")
        client.beta.threads.messages.create(
            thread_id=thread.id, role="user", content=user_input
        )

        # Run assistant and wait for completion
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
        assistant_response = next(
            (
                m.content[0].text.value
                for m in messages
                if m.role == "assistant" and m.content
            ),
            None,
        )

        if assistant_response:
            # logging.info(f"Assistant Response: {assistant_response}")
            return assistant_response
        else:
            logging.warning("No response from the assistant.")
            return "No response from the assistant."

    except Exception as e:
        logging.error(f"Error in generating visual description: {e}")
        return None


#! Example usage -> Uncomment the following lines to test the function
# visual_configuration = {
#     "child_character": {
#         "child_name": "Lilly",
#         "child_gender": "Girl",
#         "child_age": "5",
#         "visuals": {
#             "clothing": "She wears a bright pink dress with white polka dots and white sneakers with pink laces.",
#             "other_features": "She wears a white headband with a bow on it.",
#             "ethnicity": "Caucasian",
#             "hair_color": "Platinum Blonde",
#             "hair_length": "Long",
#             "skin_tone": "Bright White",
#         },
#     },
#     "companion": {
#         "companion_name": "Jay Jay",
#         "companion_gender": "Female",
#         "companion_type": "Cat",
#         "visuals": {
#             "appearance": "Jay Jay is a fluffy gray cat with big green eyes and a small pink nose.",
#             "other_features": "She has a white-tipped tail and white socks on her paws.",
#         },
#     },
#     "illustration_style": [
#         {
#             "style": "cartoon clipart style, flat design with simple shapes and bright colors"
#         }
#     ],
# }

# generate_visual_description(visual_configuration)
