import unittest
from unittest.mock import patch, MagicMock
from .trading import SafetyManager, MarketDataManager, BrokerAPI
from .bot import DiscordTraderBot
import os
import numpy as np

class TestSafetyManager(unittest.TestCase):
    def setUp(self):
        self.safety = SafetyManager()
        self.mock_broker = MagicMock()

    def test_position_size_limit(self):
        self.mock_broker.get_account_info.return_value = {'portfolio_value': 10000}
        self.assertTrue(self.safety.can_trade(self.mock_broker, 500))
        self.assertFalse(self.safety.can_trade(self.mock_broker, 2000))

    def test_trade_limit(self):
        self.mock_broker.get_account_info.return_value = {'portfolio_value': 10000}
        for _ in range(int(os.getenv('TRADE_LIMIT_PER_SESSION', '10'))):
            self.safety.record_trade(0)
        self.assertFalse(self.safety.can_trade(self.mock_broker, 100))

class TestMarketDataManager(unittest.TestCase):
    def setUp(self):
        self.market_data = MarketDataManager()

    @patch('robin_stocks.robinhood.markets.get_market_hours')
    def test_is_market_open(self, mock_hours):
        mock_hours.return_value = [{'market': 'NASDAQ', 'is_open': True}]
        self.assertTrue(self.market_data.is_market_open())

        mock_hours.return_value = [{'market': 'NASDAQ', 'is_open': False}]
        self.assertFalse(self.market_data.is_market_open())

class TestBrokerAPI(unittest.TestCase):
    @patch('robin_stocks.robinhood.login')
    def setUp(self, mock_login):
        self.broker = BrokerAPI("test_user", "test_pass")
        self.broker.market_data = MagicMock()
        mock_login.return_value = True

    @patch('robin_stocks.robinhood.orders.order_buy_market')
    def test_place_buy_order(self, mock_order):
        self.broker.market_data.get_quote.return_value = {
            'last_trade_price': '100.00',
            'tradable': True
        }
        mock_order.return_value = {'id': 'test_order_id'}

        order = self.broker.place_order("AAPL", "buy", 1000)
        self.assertIsNotNone(order)
        self.assertEqual(order['id'], 'test_order_id')

class TestDiscordTraderBot(unittest.TestCase):
    def setUp(self):
        self.mock_broker = MagicMock()
        self.mock_llm = MagicMock()
        self.bot = DiscordTraderBot(self.mock_broker, self.mock_llm)

    def test_screen_change_detection(self):
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        self.assertTrue(self.bot.has_screen_changed(test_image))
        self.assertFalse(self.bot.has_screen_changed(test_image))

    def test_image_processing(self):
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        cropped = self.bot.crop_to_message_section(test_image)
        self.assertIsNotNone(cropped)
        self.assertTrue(cropped.shape[0] < test_image.shape[0])

if __name__ == "__main__":
    unittest.main()