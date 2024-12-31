import os
import logging
from dotenv import load_dotenv
from .llm_handler import GLHFLLM
from .bot import DiscordTraderBot
from .trading import BrokerAPI

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)

def main():
    try:
        broker_api = BrokerAPI(
            username=os.getenv("ROBINHOOD_USERNAME"),
            password=os.getenv("ROBINHOOD_PASSWORD")
        )
        llm = GLHFLLM(model_name="hf:mistralai/Mistral-7B-Instruct-v0.3")
        bot = DiscordTraderBot(broker_api, llm)
        bot.run()
    except Exception as e:
        logging.critical(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    main()