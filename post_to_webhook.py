import requests


# Function to post to a webhook
def post_to_webhook(response):
    # Check if response is an instance of requests.Response
    if isinstance(response, requests.Response):
        # If it's an HTTP response, extract the text content
        text_content = response.text
    elif isinstance(response, str):
        # If the response is already a string, use it directly
        text_content = response
    else:
        # For other types, convert to string
        text_content = str(response)

    # Prepare the payload
    payload = {"response": text_content}

    # Post the payload to the webhook
    requests.post("https://webhook.site/LSW-process-logging", json=payload)
