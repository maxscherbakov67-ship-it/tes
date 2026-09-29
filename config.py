import os
from dotenv import load_dotenv
from dataclasses import dataclass

load_dotenv()

@dataclass
class config():
    bot_token : str = os.getenv("TG_BOT_TOKEN")
def load_config() -> config:
    return config()