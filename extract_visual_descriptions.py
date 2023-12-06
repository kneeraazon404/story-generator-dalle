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

            # Find the start and end of the visual_description array
            start_index = data_str.find("visual_description = [")
            end_index = data_str.find("]", start_index)

            # Extract the visual_description string
            if start_index != -1 and end_index != -1:
                visual_description_str = data_str[
                    start_index + len("visual_description = ") : end_index + 1
                ]
                return visual_description_str

    return None
