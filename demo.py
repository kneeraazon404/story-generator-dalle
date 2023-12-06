import json
import re


def extract_and_clean_data(book_data_str):
    """
    Extracts and cleans the JSON data from the book_data string.

    :param book_data_str: The string containing book_data JSON.
    :return: Cleaned data as a dictionary or None if extraction fails.
    """
    try:
        # Extract the JSON-like part using regular expressions
        match = re.search(r"book_data = ({.*})", book_data_str, re.DOTALL)
        if match:
            data_str = match.group(1)

            # Replace escaped characters
            data_str = data_str.replace("\\n", "")
            data_str = data_str.replace('\\"', '"')

            # Ensure property names are enclosed in double quotes
            data_str = re.sub(r'(?<!\\)"\s*:\s*"', r'":"', data_str)
            data_str = re.sub(r'{\s*"', r'{"', data_str)
            data_str = re.sub(r',\s*"', r',"', data_str)

            # Convert the string to a Python dictionary
            return json.loads(data_str)
        else:
            print("No match found in the book_data string.")
            return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None


# Example usage
book_data_str = """book_data = {
    "title": "Jay's Jungle Jaunt",
    "pages": {
        "page_01": "Once upon a time, in a cozy little house on the edge of a vast, green jungle, there lived a curious boy named Jay.",
        ...
    },
    "summary": "In 'Jay's Jungle Jaunt,' young Jay discovers the beauty of the jungle alongside his new friend, a parrot named Pippin. ..."
}"""

cleaned_data = extract_and_clean_data(book_data_str)
print(cleaned_data)
