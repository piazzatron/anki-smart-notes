from .config import Config

import aiohttp


class OpenAIClient:
    """Client for OpenAI's chat API."""

    def __init__(self, config: Config):
        self.config = config
        self.api_key = config.openai_api_key

    async def async_get_chat_response(self, prompt: str):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                },
                json={
                    "model": self.config.openai_model,
                    "messages": [{"role": "user", "content": prompt}],
                },
            ) as response:
                resp = await response.json()
                msg = resp["choices"][0]["message"]["content"]
                return msg
