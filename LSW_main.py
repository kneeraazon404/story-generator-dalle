import requests

# Data to be posted
data = {
    "image_urls": {
        "page_01": "https://cdn.discordapp.com/attachments/1151092434537807904/1192111966672650350/nagletti_The_brave_little_girl_dressed_in_an_astronaut_suit_sta_cec99592-677b-4196-91b6-7ce6c3c3a910.png?ex=65a7e3c9&is=65956ec9&hm=310d8957119e91e2dcdf34d61a3fc034878161cd7ba67ba4122979d4c570c635&",
        "tripettoId": "aaaaaa"
    }
}

# Headers (modify as needed based on your Postman setup)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    'Content-Type': 'application/json'
    # Add other headers here if necessary
}

# URL to which the data is to be posted
url = "http://littlestorywriter.com/process-story"

# Sending a POST request
response = requests.post(url, json=data, headers=headers)

# Printing the response
print(response.text)
