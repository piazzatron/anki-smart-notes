from .config import Config

import aiohttp


class OpenAIClient:
    """Client for OpenAI's chat API."""

    def __init__(self, config: Config):
        self.config = config

    async def async_get_chat_response(self, prompt: str) -> str:
        """Gets a chat response from OpenAI's chat API. This method can throw; the caller should handle with care."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer self.config.openai_api_key",
                },
                json={
                    "model": self.config.openai_model,
                    "messages": [{"role": "user", "content": prompt}],
                },
            ) as response:
                response.raise_for_status()
                resp = await response.json()
                msg = resp["choices"][0]["message"]["content"]
                return msg
