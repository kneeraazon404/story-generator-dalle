import logging


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
        logging.info(f"=============================================")
        logging.info(f"Story Configuration: {story_configuration}")
        logging.info(f"=============================================")
        logging.info(f"Visual Configuration: {visual_configuration}")
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


# ! Example usage -> Uncomment to test
# data_example = {
#     "userid": "info@littlestorywriter.com",
#     "child_name": "Lilly",
#     "child_gender": "Girl",
#     "child_age": "5",
#     "companion_type": "Cat",
#     "companion_name": "Jay Jay",
#     "companion_gender": "female",
#     "language_tone": "Adventurous and Exciting",
#     "story_setting": "Outer Space",
#     "story_theme": "Teamwork and Cooperation",
#     "language": "british English",
#     "child_ethnic": "Caucasian",
#     "child_skin_tone": "bright white",
#     "child_hair_color": "Platinum Blonde",
#     "child_hair_length": "long",
#     "illustration_style": "cartoon clipart style, flat design style with simple shapes and bright colors",
#     "tripettoId": "ddddd",
#     "tripettoIndex": 1,
#     "tripettoCreateDate": "2024-05-27T11:02:15.000Z",
#     "tripettoFingerprint": "bdf3fc64828300c45a67668a202a0e562d0503e18bedc17f9b9d7660e713a376",
#     "tripettoFormReference": "c28a727a090f0de809baac3a242e4dec8fbd7cb055b6aee8ec400f6f91d3fda6",
#     "tripettoFormName": "Book Configurator (Beta Testing)",
# }


# !convert_tripetto_json_to_lists(data_example)
