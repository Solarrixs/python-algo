import time
import logging
import cv2
import pytesseract
import numpy as np
from PIL import Image
from imagehash import average_hash
from .rate_limiter import RateLimiter
from .trading import BrokerAPI, SafetyManager, MarketDataManager
import pyautogui  # Importing pyautogui
from .utils import retry  # Importing the retry decorator
import os

class DiscordTraderBot:
    def __init__(self, broker_api, llm):
        self.broker = broker_api
        self.llm = llm
        self.previous_hash = None
        self.last_screenshot_time = time.time()

    @retry()
    def grab_screen_region(self, region):
        try:
            screenshot = pyautogui.screenshot(region=region)
            return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        except Exception as e:
            logging.error(f"Failed to capture screen region: {e}")
            return None

    def crop_to_message_section(self, image):
        if image is None:
            return None
        height, width = image.shape[:2]
        return image[int(height*0.2):int(height*0.8), int(width*0.1):int(width*0.9)]

    def compute_image_hash(self, image):
        if image is None:
            return None
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        pil_image = Image.fromarray(gray)
        return average_hash(pil_image)

    def has_screen_changed(self, image):
        if image is None:
            return False
        current_hash = self.compute_image_hash(image)
        if self.previous_hash is None or current_hash != self.previous_hash:
            self.previous_hash = current_hash
            return True
        return False

    def process_screenshot(self, image):
        if image is None:
            return ""
        try:
            return pytesseract.image_to_string(image)
        except Exception as e:
            logging.error(f"OCR failed: {e}")
            return ""

    def run(self):
        logging.info("Starting Discord Trader Bot")
        while True:
            try:
                if not self.broker.market_data.is_market_open():
                    time.sleep(300)
                    continue

                if time.time() - self.last_screenshot_time >= int(os.getenv('SCREEN_CHECK_INTERVAL', '10')):
                    screenshot = self.grab_screen_region(tuple(map(int, os.getenv('SCREEN_REGION', '0,0,800,600').split(','))))
                    if screenshot is not None and self.has_screen_changed(screenshot):
                        cropped = self.crop_to_message_section(screenshot)
                        if cropped is not None:
                            cv2.imwrite(os.getenv('SCREENSHOT_PATH', 'latest_screenshot.png'), cropped)
                            text = self.process_screenshot(cropped)
                            if text.strip():
                                trades = self.llm.parse_trade_command(text)
                                for trade in trades:
                                    self.broker.place_order(
                                        trade['ticker'],
                                        trade['command'],
                                        trade['amount']
                                    )
                        self.last_screenshot_time = time.time()

                time.sleep(1)

            except Exception as e:
                logging.error(f"Error in main loop: {e}")
                time.sleep(5)