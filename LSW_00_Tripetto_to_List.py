import logging

from post_to_webhook import post_to_webhook


def convert_tripetto_json_to_lists(data):
    try:
        # Extracting order information
        order = [
            {
                "user_id": data.get("userid", ""),
                "date": data.get("tripettoCreateDate", ""),
                "tripettoId": data.get("tripettoId", ""),
            }
        ]

        # Parsing story configuration
        story_configuration = [
            {
                "child_name": data.get("child_name", ""),
                "child_age": data.get("child_age", ""),
                "child_gender": data.get("child_gender", ""),
                "companion_name": data.get("companion_name", ""),
                "companion_type": data.get("companion_type", ""),
                "companion_gender": data.get("companion_gender", ""),
                "language_tone": data.get("language_tone", ""),
                "story_setting": data.get("story_setting", ""),
                "story_theme": data.get("story_theme", ""),
                "language": data.get("language", ""),
            }
        ]

        # Parsing visual configuration
        visual_configuration = [
            {
                "child": {
                    "child_name": data.get("child_name", ""),
                    "child_gender": data.get("child_gender", ""),
                    "child_age": int(data.get("child_age", 0)),
                    "child_ethnic": data.get("child_ethnic", ""),
                    "child_skin_tone": data.get("child_skin_tone", ""),
                    "child_hair_color": data.get("child_hair_color", ""),
                    "child_hair_length": data.get("child_hair_length", ""),
                }
            },
            {
                "companion": {
                    "companion_name": data.get("companion_name", ""),
                    "companion_gender": data.get("companion_gender", ""),
                    "companion_type": data.get("companion_type", ""),
                }
            },
            {"illustration_style": [{"style": data.get("illustration_style", "")}]},
        ]
        logging.info("Data successfully converted to lists")
        logging.info(f"=============================================")
        logging.info(f"Order: {order}")
        post_to_webhook(f"Parsed Order: {order}")
        logging.info(f"=============================================")
        logging.info(f"Story Configuration: {story_configuration}")
        post_to_webhook(f"Parsed Story Configuration: {story_configuration}")
        logging.info(f"=============================================")
        logging.info(f"Visual Configuration: {visual_configuration}")
        post_to_webhook(f"Parsed Visual Configuration: {visual_configuration}")
        logging.info(f"=============================================")

        return order, story_configuration, visual_configuration

    except KeyError as e:
        logging.error(f"Key error: {e}")
        return [], [], []
    except ValueError as e:
        logging.error(f"Value error: {e}")
        return [], [], []
    except Exception as e:
        logging.error(f"Error in converting data to lists: {e}")
        return [], [], []
