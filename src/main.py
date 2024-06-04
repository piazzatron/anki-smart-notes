from .config import Config

from .open_ai_client import OpenAIClient
from .processor import Processor
from .hooks import setup_hooks

# TODO: sort imports...


config = Config()
client = OpenAIClient(config)
processor = Processor(client, config)

setup_hooks(processor)
