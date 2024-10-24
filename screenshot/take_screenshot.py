import os
import json
import requests
import base64
from typing import Generator, Optional, Union, List, Dict
from dataclasses import dataclass
import pyautogui
from PIL import Image

@dataclass
class APIResponse:
    text: str
    tool: Optional[str]
    command: Optional[str]

class AnthropicClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.anthropic.com/v1"
        self.headers = {
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "anthropic-beta": "computer-use-2024-10-22"
        }

    def _encode_image(self, image_path: str) -> tuple[str, str]:
        """
        Encode an image file to base64 and determine its media type
        """
        with open(image_path, 'rb') as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')

        # Determine media type based on file extension
        extension = image_path.lower().split('.')[-1]
        media_types = {
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'gif': 'image/gif',
            'webp': 'image/webp'
        }
        media_type = media_types.get(extension, 'image/jpeg')

        return image_data, media_type

    def create_message_content(self,
                             text: str,
                             image_paths: Optional[List[str]] = None) -> List[Dict]:
        """
        Create message content with both text and images
        """
        content = []

        # Add images if provided
        if image_paths:
            for image_path in image_paths:
                image_data, media_type = self._encode_image(image_path)
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_data
                    }
                })

        # Add text content
        content.append({
            "type": "text",
            "text": text
        })

        return content

    def stream_response(self,
                       message: str,
                       image_paths: Optional[List[str]] = None) -> Generator[APIResponse, None, None]:
        """
        Stream response from Claude with support for images and tools
        """
        data = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 1024,
            "stream": True,
            "tools": [
                {
                    "type": "computer_20241022",
                    "name": "computer",
                    "display_width_px": 1024,
                    "display_height_px": 768,
                    "display_number": 1
                },
                {
                    "type": "text_editor_20241022",
                    "name": "str_replace_editor"
                },
                {
                    "type": "bash_20241022",
                    "name": "bash"
                }
            ],
            "messages": [{
                "role": "user",
                "content": self.create_message_content(message, image_paths)
            }]
        }
        print(data)

        with requests.post(
            f"{self.base_url}/messages",
            headers=self.headers,
            json=data,
            stream=True
        ) as response:
            response.raise_for_status()

            text_response = ""
            json_response = ""
            tool = ""

            for line in response.iter_lines():
                if line and line.startswith(b'data: '):
                    try:
                        json_str = line[6:].decode('utf-8')
                        if json_str.strip() == "[DONE]":
                            break

                        chunk_data = json.loads(json_str)

                        if 'type' in chunk_data:
                            if (chunk_data['type'] == 'content_block_start' and
                                'content_block' in chunk_data and
                                chunk_data['content_block']['type'] == 'tool_use'):
                                tool = chunk_data['content_block']['name']

                            elif 'delta' in chunk_data:
                                delta = chunk_data['delta']
                                if not 'type' in delta:
                                    continue
                                if delta['type'] == 'text_delta' and 'text' in delta:
                                    chunk_text = delta['text']
                                    text_response += chunk_text
                                    yield APIResponse(chunk_text, None, None)
                                elif delta['type'] == 'input_json_delta' and 'partial_json' in delta:
                                    json_response += delta['partial_json']

                    except Exception as e:
                        print(f"Error processing chunk: {e}")
                        continue

            # Yield final complete response
            yield APIResponse(None, tool, json_response)

# Example usage
if __name__ == "__main__":
    client = AnthropicClient(api_key=os.getenv('ANTHROPIC_API_KEY'))

    # Example with just text
    # for response in client.stream_response("Hello, how are you?"):
    #     print(response.text or "", end="")

    # Example with image
    screenshot = pyautogui.screenshot()
    resized_image = screenshot.resize((1024, 768), Image.Resampling.LANCZOS)
    image_path = "screenshot.png"  # Path to your screenshot
    resized_image.save(image_path)


    for response in client.stream_response(
        "Open Chrome.",
        image_paths=[image_path]
    ):
        print(response.text or "", end="")
        if response.tool:
            print("\nTOOL:", response.tool or "", end="")
        if response.command:
            print("\nPAYLOAD:", response.command or "", end="")
