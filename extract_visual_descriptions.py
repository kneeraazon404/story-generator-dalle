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
            data_str = content.text.value

            # Find the start of the visual_description array
            start_index = data_str.find("visual_description = ")

            # Extract the visual_description string
            visual_description_str = data_str[start_index:]

            return visual_description_str

    return None
