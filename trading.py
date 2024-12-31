import time
import logging
import os
import robin_stocks.robinhood as rh
from pyotp import TOTP
from cachetools import TTLCache
from functools import wraps
from .rate_limiter import RateLimiter  # Assuming RateLimiter is in rate_limiter.py
from .utils import retry  # Importing the retry decorator
import atexit  # Importing atexit

class SafetyManager:
    def __init__(self):
        self.daily_loss_limit = float(os.getenv('DAILY_LOSS_LIMIT', '-1000'))
        self.position_size_limit = float(os.getenv('POSITION_SIZE_LIMIT', '0.1'))
        self.cooldown_period = int(os.getenv('TRADE_COOLDOWN_SECONDS', '300'))
        self.last_trade_time = None
        self.daily_pl = 0
        self.trade_count = 0

    def can_trade(self, broker, amount):
        if self.trade_count >= int(os.getenv('TRADE_LIMIT_PER_SESSION', '10')):
            logging.warning("Trade limit reached for session")
            return False

        if self.last_trade_time and time.time() - self.last_trade_time < self.cooldown_period:
            logging.warning("Trade cooldown period not elapsed")
            return False

        account = broker.get_account_info()
        if not account:
            logging.error("Could not fetch account information")
            return False

        portfolio_value = account['portfolio_value']
        if amount > portfolio_value * self.position_size_limit:
            logging.warning(f"Trade size {amount} exceeds position limit of {portfolio_value * self.position_size_limit}")
            return False

        if self.daily_pl < self.daily_loss_limit:
            logging.warning(f"Daily loss limit reached: {self.daily_pl}")
            return False

        return True

    def record_trade(self, pl):
        self.last_trade_time = time.time()
        self.daily_pl += pl
        self.trade_count += 1

class MarketDataManager:
    def __init__(self):
        self.cache = TTLCache(maxsize=100, ttl=5)
        self.rate_limiter = RateLimiter(max_calls=60, period=60)

    @retry(max_attempts=3)
    def get_quote(self, symbol):
        if symbol in self.cache:
            return self.cache[symbol]

        with self.rate_limiter:
            quote = rh.stocks.get_quotes(symbol)
            if quote and quote[0]:
                self.cache[symbol] = quote[0]
                return quote[0]
            return None

    def is_market_open(self):
        try:
            with self.rate_limiter:
                market_hours = rh.markets.get_market_hours()
                is_open = any(mkt['is_open'] for mkt in market_hours if mkt['market'] == 'NASDAQ')
                if not is_open:
                    next_open = min(mkt['next_open_hours'] for mkt in market_hours if mkt['market'] == 'NASDAQ')
                    logging.info(f"Market closed. Next open: {next_open}")
                return is_open
        except Exception as e:
            logging.error(f"Failed to check market hours: {e}")
            return False

class BrokerAPI:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.safety = SafetyManager()
        self.market_data = MarketDataManager()
        self.rate_limiter = RateLimiter(max_calls=60, period=60)
        self.login()
        atexit.register(self.logout)

    def login(self):
        totp = TOTP(os.getenv('ROBINHOOD_MFA')).now()
        with self.rate_limiter:
            login_response = rh.login(
                username=self.username,
                password=self.password,
                mfa_code=totp,
                store_session=False,
                expiresIn=86400,
                by_qr=False
            )
        if not login_response:
            raise Exception("Login failed")
        self.refresh_auth()
        logging.info("Successfully logged in to Robinhood")

    def refresh_auth(self):
        with self.rate_limiter:
            rh.authentication.refresh_token()

    def logout(self):
        with self.rate_limiter:
            rh.logout()
        logging.info("Successfully logged out of Robinhood")

    @retry(max_attempts=3)
    def place_order(self, ticker, command, amount, order_type="market", limit_price=None, stop_price=None):
        if not self.safety.can_trade(self, amount):
            logging.warning("Trade rejected by safety checks")
            return None

        quote = self.market_data.get_quote(ticker)
        if not quote or not quote.get('tradable', False):
            logging.error(f"Ticker {ticker} is not tradable")
            return None

        latest_price = float(quote['last_trade_price'])
        shares = round(amount / latest_price, 4)

        with self.rate_limiter:
            if command == "buy":
                if order_type == "market":
                    order = rh.orders.order_buy_market(
                        symbol=ticker,
                        quantity=shares,
                        timeInForce='gtc',
                        extendedHours=False
                    )
                elif order_type == "limit":
                    order = rh.orders.order_buy_limit(
                        symbol=ticker,
                        quantity=shares,
                        limitPrice=limit_price,
                        timeInForce='gtc',
                        extendedHours=False
                    )
            elif command == "sell":
                if order_type == "market":
                    order = rh.orders.order_sell_market(
                        symbol=ticker,
                        quantity=shares,
                        timeInForce='gtc',
                        extendedHours=False
                    )
                elif order_type == "limit":
                    order = rh.orders.order_sell_limit(
                        symbol=ticker,
                        quantity=shares,
                        limitPrice=limit_price,
                        timeInForce='gtc',
                        extendedHours=False
                    )

        if order and 'id' in order:
            logging.info(f"Order placed successfully: {order['id']}")
            return order
        else:
            logging.error(f"Order failed: {order}")
            return None

    def get_holdings(self):
        with self.rate_limiter:
            positions = rh.account.get_all_positions()
        holdings = {}

        for position in positions:
            quantity = float(position['quantity'])
            if quantity > 0:
                with self.rate_limiter:
                    instrument_data = rh.stocks.get_instrument_by_url(position['instrument'])
                    symbol = instrument_data['symbol']
                    quote = self.market_data.get_quote(symbol)

                holdings[symbol] = {
                    'quantity': quantity,
                    'average_buy_price': float(position['average_buy_price']),
                    'current_price': float(quote['last_trade_price']) if quote else None,
                    'intraday_pl_pct': float(position['intraday_percentage'])
                }
        return holdings

    def get_account_info(self):
        with self.rate_limiter:
            profile = rh.profiles.load_account_profile()
            portfolio = rh.profiles.load_portfolio_profile()

        return {
            'cash_available': float(profile['cash_available_for_investment']),
            'buying_power': float(profile['buying_power']),
            'portfolio_value': float(portfolio['equity']),
            'market_value': float(portfolio['market_value']),
            'day_pl_pct': float(portfolio['day_change_percent'])
        }