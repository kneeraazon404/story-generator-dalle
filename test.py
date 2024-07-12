import json


def extract_details(json_string):
    data = json.loads(json_string)

    # Extracting child character information
    child_character = data["characters"][0]["child_character"]
    child_name = child_character["child_name"]
    child_gender = child_character["child_gender"]
    child_age = child_character["child_age"]
    child_visuals = child_character["visuals"]

    # Extracting companion information
    companion = data["characters"][1]["companion"]
    companion_name = companion["companion_name"]
    companion_gender = companion["companion_gender"]
    companion_type = companion["companion_type"]
    companion_visuals = companion["visuals"]

    # Extracting illustration style
    illustration_style = data["illustration_style"][0]["style"]

    result = {
        "child_character": {
            "name": child_name,
            "gender": child_gender,
            "age": child_age,
            "visuals": child_visuals,
        },
        "companion": {
            "name": companion_name,
            "gender": companion_gender,
            "type": companion_type,
            "visuals": companion_visuals,
        },
        "illustration_style": illustration_style,
    }

    return json.dumps(result, indent=4)


# # Example usage
# json_input = """{
#     "characters": [
#         {
#             "child_character": {
#                 "child_name": "Bobby",
#                 "child_gender": "Boy",
#                 "child_age": "5",
#                 "visuals": {
#                     "clothing": "Green striped t-shirt, blue denim shorts, red sneakers with white laces",
#                     "other_features": "Small ears, wide bright eyes, a big smile",
#                     "ethnicity": "African",
#                     "hair_color": "Platinum Blonde",
#                     "hair_length": "Long",
#                     "skin_tone": "Bright White"
#                 }
#             }
#         },
#         {
#             "companion": {
#                 "companion_name": "Rocky Jay",
#                 "companion_gender": "Female",
#                 "companion_type": "Dog",
#                 "visuals": {
#                     "appearance": "Fluffy golden retriever with floppy ears",
#                     "other_features": "Wears a red collar with a small gold tag"
#                 }
#             }
#         }
#     ],
#     "illustration_style": [
#         {
#             "style": "Cartoon clipart style, flat design style with simple shapes and bright colors"
#         }
#     ]
# }"""

# result_json = extract_details(json_input)
# print(result_json)
