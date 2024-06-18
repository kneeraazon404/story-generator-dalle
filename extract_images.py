import json


def extract_output_image_prompts(input_data):
    """
    Extracts image prompts from the provided dictionary.

    :param input_data: Dictionary containing image prompts.
    :return: List of extracted image prompts.
    """
    # Ensure input_data is a dictionary
    if isinstance(input_data, str):
        input_data = json.loads(input_data)

    # Extract image prompts from the dictionary
    image_prompts = input_data.get("image_prompts", [])

    # Create a list of prompt values
    output_image_prompts = [list(prompt.values())[0] for prompt in image_prompts]

    return output_image_prompts
