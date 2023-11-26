import json


def convert_tripetto_json_to_lists(file_path):
    """
    Converts data from a JSON file at the given file path into structured lists
    for order, story configuration, and visual configuration.

    :param file_path: Path to the JSON file containing the data.
    :return: A tuple containing three lists: order, story_configuration, and visual_configuration.
    """
    try:
        with open(file_path, "r") as file:
            data = json.load(file)

        # Extracting order information
        order = [
            {
                "user_id": data.get("userid", ""),
                "date": data.get("tripettoCreateDate", ""),
            }
        ]

        # Parsing story configuration
        story_configuration = [
            {
                "child_name": data.get(
                    "So, who is the brave hero of our story? Could you share the name?",
                    "",
                ),
                "child_age": data.get(
                    "How many candles will be on ___’s birthday cake? In other words, how old is ___?",
                    "",
                ),
                "child_gender": data.get(
                    "Marvelous! And is ___ a daring little girl or a courageous little boy?",
                    "",
                ),
                "companion_name": data.get(
                    "What a charming choice! \n\nAnd what is this loyal ___'s name?", ""
                ),
                "companion_type": data.get(
                    "Heroes often have companions. \nWho will share ___s adventures in the story?",
                    "",
                ),
                "companion_gender": data.get(
                    "Just to make sure I picture ___ correctly, is this companion a 'he' or 'she'?",
                    "",
                ),
            }
        ]

        # Parsing visual configuration
        visual_configuration = [
            {
                "child": {
                    "child_name": data.get(
                        "So, who is the brave hero of our story? Could you share the name?",
                        "",
                    ),
                    "child_gender": data.get(
                        "Marvelous! And is ___ a daring little girl or a courageous little boy?",
                        "",
                    ),
                    "child_age": int(
                        data.get(
                            "How many candles will be on ___’s birthday cake? In other words, how old is ___?",
                            0,
                        )
                    ),
                    "child_ethnic": data.get(
                        "Now, let’s get a glimpse of our hero. \nWhat is ___'s ethnicity?",
                        "",
                    ),
                    "child_skin_tone": data.get(
                        "And to add more detail to her portrait, what is the shade of ___’s skin?",
                        "",
                    ),
                    "child_hair_color": data.get(
                        "What is the color of ___'s hair that catches the sunlight in our story?",
                        "",
                    ),
                    "child_hair_length": data.get(
                        "And for the artist drawing ___'s courageous moments, how long should the hair be?",
                        "",
                    ),
                },
                "companion": {
                    "companion_name": data.get(
                        "What a charming choice! \n\nAnd what is this loyal ___'s name?",
                        "",
                    ),
                    "companion_gender": data.get(
                        "Just to make sure I picture ___ correctly, is this companion a 'he' or 'she'?",
                        "",
                    ),
                    "companion_type": data.get(
                        "Heroes often have companions. \nWho will share ___s adventures in the story?",
                        "",
                    ),
                },
            }
        ]

        return order, story_configuration, visual_configuration

    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return [], [], []
    except json.JSONDecodeError:
        print(f"Error decoding JSON from file: {file_path}")
        return [], [], []
