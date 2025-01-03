import time
import logging
import cv2
import numpy as np
import pytesseract
import pyautogui
import win32gui
import win32con
from dotenv import load_dotenv
import os

class DiscordCapture:
    def __init__(self):
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('discord_capture.log'),
                logging.StreamHandler()
            ]
        )
        
        # Load configuration
        load_dotenv()
        self.window_title = os.getenv('DISCORD_WINDOW', 'Discord')
        self.region = tuple(map(int, os.getenv('SCREEN_REGION', '0,0,800,600').split(',')))
        self.interval = int(os.getenv('SCREEN_CHECK_INTERVAL', '60'))
        
        # Initialize state
        self.last_image_hash = None
        self.last_capture_time = 0
        
    def focus_discord_window(self):
        """Focus the Discord window if it exists."""
        try:
            hwnd = win32gui.FindWindow(None, self.window_title)
            if hwnd:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.5)  # Allow window to gain focus
                return True
            return False
        except Exception as e:
            logging.error(f"Failed to focus Discord window: {e}")
            return False

    def capture_screen(self):
        """Capture the specified screen region."""
        try:
            screenshot = pyautogui.screenshot(region=self.region)
            return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        except Exception as e:
            logging.error(f"Screen capture failed: {e}")
            return None

    def compute_image_hash(self, image):
        """Compute a hash of the image for change detection."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        hasher = cv2.img_hash.AverageHash_create()
        return hasher.compute(gray)

    def has_image_changed(self, image):
        """Check if the image has changed from the previous capture."""
        if image is None:
            return False
        current_hash = self.compute_image_hash(image)
        if self.last_image_hash is None:
            self.last_image_hash = current_hash
            return True
        # Compute Hamming distance
        diff = cv2.norm(current_hash, self.last_image_hash, cv2.NORM_HAMMING)
        # Set a threshold for change detection
        if diff > 10:
            self.last_image_hash = current_hash
            return True
        return False

    def process_image(self, image):
        """Process the image with OCR and save to file."""
        try:
            text = pytesseract.image_to_string(image)
            if text.strip():
                # Log to console/log file
                logging.info(f"OCR Result: {text.strip()}")
                
                # Write to new text file with timestamp
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                with open("extracted_messages.txt", "a", encoding="utf-8") as f:
                    f.write(f"[{timestamp}]\n{text.strip()}\n")
            return text
        except Exception as e:
            logging.error(f"OCR processing failed: {e}")
            return ""

    def run(self):
        """Main loop for capturing and processing screenshots."""
        logging.info("Starting Discord capture")
        
        while True:
            try:
                current_time = time.time()
                
                # Check if it's time for next capture
                if current_time - self.last_capture_time < self.interval:
                    time.sleep(1)
                    continue

                # Focus Discord window and capture screen
                if self.focus_discord_window():
                    screenshot = self.capture_screen()
                    
                    # Process if image has changed
                    if screenshot is not None and self.has_image_changed(screenshot):
                        # Save screenshot for debugging
                        cv2.imwrite('screenshot.png', screenshot)
                        
                        # Process with OCR
                        self.process_image(screenshot)
                        
                    self.last_capture_time = current_time
                else:
                    logging.warning("Discord window not found")
                    time.sleep(5)

            except Exception as e:
                logging.error(f"Error in main loop: {e}")
                time.sleep(5)

if __name__ == "__main__":
    capture = DiscordCapture()
    capture.run()