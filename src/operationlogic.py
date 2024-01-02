import robin_stocks.robinhood as r
import portfoliologic as pl
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QRadioButton, QHBoxLayout, QMessageBox, QCompleter
from PyQt5.QtCore import QTimer, Qt

def on_buy():
    buy_dialog = BuyDialog()
    buy_dialog.exec_()
    print("Buy button clicked")

def on_sell():
    sell_dialog = SellDialog()
    sell_dialog.exec_()
    print("Sell button clicked")
    
class BuyDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.debounce_timer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self.calculate_and_update_equity)
        self.debounce_delay = 250

    def initUI(self):
        self.setWindowTitle("Buy Stock")
        layout = QVBoxLayout()

        # Stock Ticker Input
        self.ticker_input = QLineEdit(self)
        layout.addWidget(QLabel("Stock Ticker:"))
        layout.addWidget(self.ticker_input)
        
        # Fetch List of Tickers
        ticker_list = pl.get_filtered_ticker_list()
        completer = QCompleter(ticker_list, self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.ticker_input.setCompleter(completer)
        
        # Connect ticker input change to update ask and bid prices
        self.ticker_input.textChanged.connect(self.update_ask_bid_prices)

        # Share Quantity Input
        self.quantity_input = QLineEdit(self)
        layout.addWidget(QLabel("Share Quantity:"))
        layout.addWidget(self.quantity_input)
        self.quantity_input.textChanged.connect(self.on_input_changed)

        # Price to Buy Input
        self.price_input = QLineEdit(self)
        layout.addWidget(QLabel("Price to Buy:"))
        layout.addWidget(self.price_input)
        self.price_input.textChanged.connect(self.on_input_changed)
        
        # Display Stock Equity
        self.equity_label = QLabel("Value: Not Available", self)
        layout.addWidget(self.equity_label)

        # Expiration Setting Radio Buttons
        self.expiration_layout = QHBoxLayout()
        self.gfd_radio = QRadioButton("Good for Day")
        self.gtc_radio = QRadioButton("Good for 90 Days")
        self.gfd_radio.setChecked(True)
        self.expiration_layout.addWidget(self.gfd_radio)
        self.expiration_layout.addWidget(self.gtc_radio)
        layout.addLayout(self.expiration_layout)
        
        # Labels for displaying ask and bid prices
        self.ask_price_label = QLabel("Ask Price: Not Available", self)
        self.bid_price_label = QLabel("Bid Price: Not Available", self)
        layout.addWidget(self.ask_price_label)
        layout.addWidget(self.bid_price_label)

        # Submit Button
        self.submit_button = QPushButton("Submit", self)
        self.submit_button.clicked.connect(self.onBuySubmit)
        layout.addWidget(self.submit_button)

        self.setLayout(layout)

    def onBuySubmit(self):
        ticker = self.ticker_input.text()
        quantity = self.quantity_input.text()
        price = self.price_input.text()
        time_in_force = 'gtc' if self.gtc_radio.isChecked() else 'gfd'

        # Place the buy order
        response = r.orders.order_buy_limit(ticker, quantity, price, timeInForce=time_in_force, extendedHours=True, jsonify=True)
        if response:
            order_status = response.get('state', 'No status available')
            QMessageBox.information(self, "Order Status", f"Order placed. Status: {order_status}")
        else:
            QMessageBox.warning(self, "Order Failed", "Failed to place the order.")
                
    def update_ask_bid_prices(self):
        ticker = self.ticker_input.text()
        if ticker:
            quote = r.stocks.get_stock_quote_by_symbol(ticker)
            if quote:
                ask_price = round(float(quote['ask_price']), 2)
                bid_price = round(float(quote['bid_price']), 2)
                
                # Update labels with colors
                self.ask_price_label.setText(f"Ask Price: {ask_price}")
                self.ask_price_label.setStyleSheet("color: red")
                
                self.bid_price_label.setText(f"Bid Price: {bid_price}")
                self.bid_price_label.setStyleSheet("color: green")
            else:
                self.ask_price_label.setText("Ask Price: Not Available")
                self.bid_price_label.setText("Bid Price: Not Available")
                self.ask_price_label.setStyleSheet("")
                self.bid_price_label.setStyleSheet("")
                
    def calculate_and_update_equity(self):
        try:
            price_to_buy = float(self.price_input.text())
            share_quantity = float(self.quantity_input.text())
            current_stock_equity = price_to_buy * share_quantity

            # Get total portfolio value
            holdings = r.account.build_holdings()
            total_portfolio_value = sum(float(holding['equity']) for holding in holdings.values())
            cash_amount_str = self.get_cash_on_hand()
            try:
                cash_amount = float(cash_amount_str)
            except ValueError:
                cash_amount = 0

            # Calculate equity as a percentage of total holdings
            equity_percentage = (current_stock_equity / total_portfolio_value) * 100 if total_portfolio_value else 0
            self.equity_label.setText(f"Value: ${current_stock_equity:.2f}/${cash_amount:.2f}, {equity_percentage:.2f}%")
            if current_stock_equity >= cash_amount:
                self.equity_label.setStyleSheet("color: red")
            else:
                self.equity_label.setStyleSheet("color: white")  

        except ValueError:
            self.equity_label.setText("Value: Invalid")
            self.equity_label.setStyleSheet("color: red") 
    
    def on_input_changed(self):
        self.debounce_timer.start(self.debounce_delay)
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_W and event.modifiers() & Qt.ControlModifier:
            self.close()
        else:
            super().keyPressEvent(event)
            
    def get_cash_on_hand(self):
        profile = r.profiles.load_account_profile(info='cash')
        cash_on_hand = profile if profile else "Unable to fetch cash amount"
        return cash_on_hand
    
class SellDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.debounce_timer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self.calculate_and_update_equity)
        self.debounce_delay = 250

    def initUI(self):
        self.setWindowTitle("Sell Stock")
        layout = QVBoxLayout()

        # Stock Ticker Input
        self.ticker_input = QLineEdit(self)
        layout.addWidget(QLabel("Stock Ticker:"))
        layout.addWidget(self.ticker_input)
        
        # Fetch List of Tickers
        ticker_list = pl.get_filtered_ticker_list()
        completer = QCompleter(ticker_list, self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.ticker_input.setCompleter(completer)
        
        # Connect ticker input change to update ask and bid prices
        self.ticker_input.textChanged.connect(self.update_ask_bid_prices)

        # Share Quantity Input
        self.quantity_input = QLineEdit(self)
        layout.addWidget(QLabel("Share Quantity:"))
        layout.addWidget(self.quantity_input)
        self.quantity_input.textChanged.connect(self.on_input_changed)

        # Price to Sell Input
        self.price_input = QLineEdit(self)
        layout.addWidget(QLabel("Price to Sell:"))
        layout.addWidget(self.price_input)
        self.price_input.textChanged.connect(self.on_input_changed)
        
        # Display Stock Equity
        self.equity_label = QLabel("Value: Not Available", self)
        layout.addWidget(self.equity_label)

        # Expiration Setting Radio Buttons
        self.expiration_layout = QHBoxLayout()
        self.gfd_radio = QRadioButton("Good for Day")
        self.gtc_radio = QRadioButton("Good for 90 Days")
        self.gfd_radio.setChecked(True)
        self.expiration_layout.addWidget(self.gfd_radio)
        self.expiration_layout.addWidget(self.gtc_radio)
        layout.addLayout(self.expiration_layout)
        
        # Labels for displaying ask and bid prices
        self.ask_price_label = QLabel("Ask Price: Not Available", self)
        self.bid_price_label = QLabel("Bid Price: Not Available", self)
        layout.addWidget(self.ask_price_label)
        layout.addWidget(self.bid_price_label)

        # Submit Button
        self.submit_button = QPushButton("Submit", self)
        self.submit_button.clicked.connect(self.onSubmit)
        layout.addWidget(self.submit_button)

        self.setLayout(layout)

    def onSubmit(self):
        ticker = self.ticker_input.text()
        quantity = self.quantity_input.text()
        price = self.price_input.text()
        time_in_force = 'gtc' if self.gtc_radio.isChecked() else 'gfd'

        # Place the buy order
        response = r.orders.order_buy_limit(ticker, quantity, price, timeInForce=time_in_force, extendedHours=True, jsonify=True)
        if response:
            order_status = response.get('state', 'No status available')
            QMessageBox.information(self, "Order Status", f"Order placed. Status: {order_status}")
        else:
            QMessageBox.warning(self, "Order Failed", "Failed to place the order.")
                
    def update_ask_bid_prices(self):
        ticker = self.ticker_input.text()
        if ticker:
            quote = r.stocks.get_stock_quote_by_symbol(ticker)
            if quote:
                ask_price = round(float(quote['ask_price']), 2)
                bid_price = round(float(quote['bid_price']), 2)
                
                # Update labels with colors
                self.ask_price_label.setText(f"Ask Price: {ask_price}")
                self.ask_price_label.setStyleSheet("color: red")
                
                self.bid_price_label.setText(f"Bid Price: {bid_price}")
                self.bid_price_label.setStyleSheet("color: green")
            else:
                self.ask_price_label.setText("Ask Price: Not Available")
                self.bid_price_label.setText("Bid Price: Not Available")
                self.ask_price_label.setStyleSheet("")
                self.bid_price_label.setStyleSheet("")
                
    def calculate_and_update_equity(self):
        try:
            price_to_buy = float(self.price_input.text())
            share_quantity = float(self.quantity_input.text())
            current_stock_equity = price_to_buy * share_quantity

            # Get total portfolio value
            holdings = r.account.build_holdings()
            total_portfolio_value = sum(float(holding['equity']) for holding in holdings.values())
            cash_amount_str = self.get_cash_on_hand()
            try:
                cash_amount = float(cash_amount_str)
            except ValueError:
                cash_amount = 0

            # Calculate equity as a percentage of total holdings
            equity_percentage = (current_stock_equity / total_portfolio_value) * 100 if total_portfolio_value else 0
            self.equity_label.setText(f"Value: ${current_stock_equity:.2f}/${cash_amount:.2f}, {equity_percentage:.2f}%")
            if current_stock_equity >= cash_amount:
                self.equity_label.setStyleSheet("color: red")
            else:
                self.equity_label.setStyleSheet("color: white")  

        except ValueError:
            self.equity_label.setText("Value: Invalid")
            self.equity_label.setStyleSheet("color: red") 
    
    def on_input_changed(self):
        self.debounce_timer.start(self.debounce_delay)
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_W and event.modifiers() & Qt.ControlModifier:
            self.close()
        else:
            super().keyPressEvent(event)
            
    def get_cash_on_hand(self):
        profile = r.profiles.load_account_profile(info='cash')
        cash_on_hand = profile if profile else "Unable to fetch cash amount"
        return cash_on_hand