import requests


# Function to post to a webhook
def post_to_webhook(response):
    if isinstance(response, str):
        # If the response is already a string, no need to extract text
        text_content = response
    else:
        # Access the text content directly
        text_content = response.text

    payload = {"response": text_content}
    requests.post("https://webhook.site/LSW-process-logging", json=payload)
