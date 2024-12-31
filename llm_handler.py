import openai
import json
import os
import logging

class GLHFLLM:
    def __init__(self, model_name):
        self.client = openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url="https://glhf.chat/api/openai/v1"
        )
        self.model_name = model_name

    def parse_trade_command(self, text):
        prompt = (
            "Extract any trade commands from the following text and return them "
            "as a JSON array of dictionaries with keys 'ticker', 'command', and 'amount'. "
            "Validate that tickers are valid stock symbols. "
            "Commands should only be 'buy' or 'sell'. "
            "If no valid trade commands are found, return an empty list.\n\nText: {}"
        ).format(text)
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a trading assistant. Only extract clear and explicit trade commands."},
                    {"role": "user", "content": prompt}
                ]
            )
            reply = response.choices[0].message.content
            trades = json.loads(reply)
            return trades
        except Exception as e:
            logging.error(f"LLM parsing error: {e}")
            return []