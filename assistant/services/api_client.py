import os
import json
import requests
from typing import Generator, Optional
from dataclasses import dataclass

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

    def stream_response(self, message: str) -> Generator[APIResponse, None, None]:
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
            "messages": [{"role": "user", "content": message}]
        }

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