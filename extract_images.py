import re


def extract_output_image_prompts(input_text):
    # Use regular expressions to extract the image prompts in the specified format
    matches = re.findall(r'"prompt_img_\d{2}": "(.*?)"', input_text)

    # Create a dictionary of prompts
    output_image_prompts = {
        f"prompt_img_{i:02}": prompt for i, prompt in enumerate(matches)
    }

    return output_image_prompts
