import requests

# URL to which the data is to be posted
url = "https://littlestorywriter.com/img-upload"

# Data to be posted
data = """
{
    "image_urls": {
        "page_testjan": "https://media.discordapp.net/attachments/1151092434537807904/1192359749866487838/nagletti_A_cheerful_7-year-old_girl_with_medium_brown_skin_and__3aa85a01-d48c-420d-a80b-8b5236ab1770.png?ex=65a8ca8d&is=6596558d&hm=f561495fc8096898113d268a70d21de821d956ed405dab68f48f1cf6d73b02ad&=&format=webp&quality=lossless&width=665&height=665"
    },
    "tripettoId": "123456789"
}
"""

# Headers
headers = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0",  # Add the User-Agent you used in Postman
}

# Sending a POST request
response = requests.post(url, data=data, headers=headers)

# Printing the response
print(response.status_code)
print(response.text)
