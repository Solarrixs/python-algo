import robin_stocks.robinhood as r
import logic as rlogic
import pyotp
import time
import sys
import threading
import gui
import os
from dotenv import load_dotenv

def login():
    load_dotenv()
    r.login(
        os.environ.get("USERNAME"),
        os.environ.get("PASSWORD"),
        mfa_code=pyotp.TOTP(os.environ.get("TOTP")).now()
    )

def check_price_change_loop():
    while True:
        wait_seconds = rlogic.wait_until_market_open()
        if wait_seconds == 0:
            rlogic.check_price_change()
            time.sleep(60)
        else:
            time.sleep(wait_seconds)
        
def run():
    login()
    app = gui.QApplication(sys.argv)
    ex = gui.StockApp()

    # Start the price check loop in a separate thread
    threading.Thread(target=check_price_change_loop, daemon=True).start()

    ex.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run()