# image_generator.py
import aiohttp
import asyncio
import random
import time
import logging


class ImageGenerator:
    def __init__(self, api_key):
        self.api_key = api_key
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )

    async def mymidjourney_imagine(self, prompt, session):
        try:
            url = "https://api.mymidjourney.ai/api/v1/midjourney/imagine"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            data = {"prompt": prompt}

            async with session.post(url, headers=headers, json=data) as response:
                logging.info("Image generation request sent.")
                return await response.json()
        except Exception as e:
            logging.error(f"Error in image generation: {e}")
            return None

    async def check_image_status(self, message_id, session):
        try:
            url = f"https://api.mymidjourney.ai/api/v1/midjourney/message/{message_id}"
            headers = {"Authorization": f"Bearer {self.api_key}"}

            async with session.get(url, headers=headers) as response:
                logging.info("Image status check request sent.")
                return await response.json()
        except Exception as e:
            logging.error(f"Error checking image status: {e}")
            return None

    async def perform_button_action(self, message_id, session):
        try:
            buttons = ["U1", "U2", "U3", "U4"]
            selected_button = random.choice(buttons)
            url = "https://api.mymidjourney.ai/api/v1/midjourney/button"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            data = {"messageId": message_id, "button": selected_button}

            async with session.post(url, headers=headers, json=data) as response:
                logging.info(f"Button action '{selected_button}' applied.")
                resp_json = await response.json()
                new_message_id = resp_json.get("messageId", message_id)
                return new_message_id
        except Exception as e:
            logging.error(f"Error in button action: {e}")
            return None

    async def wait_for_image_ready(self, message_id, session, timeout=120, interval=10):
        start_time = time.time()
        while time.time() - start_time < timeout:
            status_result = await self.check_image_status(message_id, session)
            if status_result and status_result.get("progress") == 100:
                return status_result
            logging.info("Image not ready yet, waiting for more time.")
            await asyncio.sleep(interval)
        logging.error("Timed out waiting for the image to be ready.")
        return None

    async def generate_and_select_image(self, prompt, session):
        print("Generating image...")
        result = await self.mymidjourney_imagine(prompt, session)
        if not result or "messageId" not in result:
            logging.error("No messageId in the response from mymidjourney_imagine")
            return None

        if result:
            message_id = result["messageId"]
            status_result = await self.wait_for_image_ready(message_id, session)
            if status_result and status_result["progress"] == 100:
                new_message_id = await self.perform_button_action(message_id, session)
                if new_message_id:
                    updated_status = await self.wait_for_image_ready(
                        new_message_id, session
                    )
                    if updated_status and updated_status["progress"] == 100:
                        image_uri = updated_status["uri"]
                        logging.info(f"Image uri: {image_uri}")
                        return image_uri
                    else:
                        logging.error("Updated image not ready or status check failed.")
                else:
                    logging.error("No result from button action.")
            else:
                logging.error("Image not ready or status check failed.")
        else:
            logging.error("Initial image generation failed.")
        return None

    async def generate_images(self, prompts):
        image_uris = []
        async with aiohttp.ClientSession() as session:
            for prompt in prompts:
                try:
                    image_uri = await self.generate_and_select_image(prompt, session)
                    image_uris.append(image_uri)
                except Exception as e:
                    logging.error(f"Error in generating image: {e}")
        return image_uris
