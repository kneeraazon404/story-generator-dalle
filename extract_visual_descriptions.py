import json

class Text:
    def __init__(self, annotations, value):
        self.annotations = annotations
        self.value = value

class MessageContentText:
    def __init__(self, text, type):
        self.text = text
        self.type = type

def extract_visual_description(data):
    # Assuming 'data' is a list of MessageContentText objects
    for content in data:
        if content.type == "text":
            try:
                # Parse the JSON string
                data_json = json.loads(content.text.value)
                # Extract and return the visual_description list
                return data_json.get("visual_description", None)
            except json.JSONDecodeError:
                # Handle JSON parsing error
                return None

    return None

