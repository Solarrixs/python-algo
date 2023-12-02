import sys
import webbrowser
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QHBoxLayout, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QTimer, QFile, QThread, pyqtSignal
import portfoliologic as pl
import operationlogic as ol
import algologic as al

class DataFetcher(QThread):
    dataFetched = pyqtSignal(object)
    
    def run(self):
        portfolio_data_df = pl.calculate_portfolio_returns()
        self.dataFetched.emit(portfolio_data_df)

class StockApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.start_auto_update()
        
        # Background data fetcher
        self.dataFetcher = DataFetcher()
        self.dataFetcher.dataFetched.connect(self.update_portfolio)
        self.dataFetcher.start()

    def initUI(self):
        self.setWindowTitle("Robinhood Stock Portfolio App")
        self.setGeometry(100, 100, 1000, 600)
        
        # Table Widget
        self.tableWidget = QTableWidget(self)
        self.tableWidget.setGeometry(50, 100, 900, 400)
        self.tableWidget.setObjectName("tableWidget")

        # Header Buttons
        hboxHeader = QHBoxLayout()
        
        self.btn_buy = self.createButton("Risk-Set Buy", "buyButton", ol.on_buy)
        hboxHeader.addWidget(self.btn_buy)

        self.btn_limit_buy = self.createButton("Limit Buy", "buyButton", ol.on_limit_buy)
        hboxHeader.addWidget(self.btn_limit_buy)

        self.btn_sell = self.createButton("Sell", "quitButton", ol.on_sell)
        hboxHeader.addWidget(self.btn_sell)

        self.btn_sell_all = self.createButton("Sell All", "quitButton", ol.on_sell_all)
        hboxHeader.addWidget(self.btn_sell_all)

        self.btn_stop_loss = self.createButton("Stop Loss", "quitButton", ol.on_stop_loss)
        hboxHeader.addWidget(self.btn_stop_loss)

        self.btn_trailing_stop_loss = self.createButton("TSL", "quitButton", ol.on_trailing_stop_loss)
        hboxHeader.addWidget(self.btn_trailing_stop_loss)

        self.btn_algo = self.createButton("Algo Trade", "updateButton", al.on_algo_trade)
        hboxHeader.addWidget(self.btn_algo)
        
        # Footer Buttons and Label
        hboxFooter = QHBoxLayout()
        
        self.label_total_return = QLabel("Sum of Total Return: $0.00", self)
        hboxFooter.addWidget(self.label_total_return)
        
        hboxFooter.addStretch(1)
        self.btn_update = self.createButton("Update", "buyButton", self.start_data_fetch)
        hboxFooter.addWidget(self.btn_update)
        
        quit_button = self.createButton("Quit", "quitButton", self.close)
        hboxFooter.addWidget(quit_button)
        
        # Main Layout
        vboxMain = QVBoxLayout()
        vboxMain.addLayout(hboxHeader)
        vboxMain.addWidget(self.tableWidget)
        vboxMain.addLayout(hboxFooter)  # Footer layout added here

        # Set central widget
        centralWidget = QWidget()
        centralWidget.setLayout(vboxMain)
        self.setCentralWidget(centralWidget)

        # Load stylesheet
        self.load_stylesheet("resources/styles.css")

    def update_portfolio(self):
        portfolio_data_df = pl.calculate_portfolio_returns()

        # Set the number of rows and columns in QTableWidget
        num_rows, num_cols = portfolio_data_df.shape
        self.tableWidget.setRowCount(num_rows)
        self.tableWidget.setColumnCount(num_cols + 2)  # +2 for the ticker and chart columns

        # Set column headers
        headers = ["Ticker"] + list(portfolio_data_df.columns) + ["Chart"]
        self.tableWidget.setHorizontalHeaderLabels(headers)

        # Populate the QTableWidget with data from the DataFrame
        for row in range(num_rows):
            
            # Create a QPushButton with the ticker name in First Column
            ticker = str(portfolio_data_df.index[row])
            ticker = str(portfolio_data_df.index[row])
            ticker_button = QPushButton(ticker)
            ticker_button.setProperty("ticker", ticker)
            ticker_button.clicked.connect(lambda _, ticker=ticker: self.open_stock_webpage(ticker))

            self.tableWidget.setCellWidget(row, 0, ticker_button)

            for col in range(1, num_cols + 1):
                item_text = str(portfolio_data_df.iat[row, col - 1])
                item = QTableWidgetItem(item_text)
                self.tableWidget.setItem(row, col, item)

            # Add a button to the "Chart" column
            chart_button = QPushButton("View")
            self.tableWidget.setCellWidget(row, num_cols + 1, chart_button)
            chart_button.clicked.connect(lambda _, row=row: self.show_chart(row))

        total_return_sum = pl.total_return(portfolio_data_df)

        # Update label_total_return text
        self.label_total_return.setText(f"Sum of Total Return: ${total_return_sum:.2f}")

        # Set column resizing mode to stretch the last section
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def open_stock_webpage(self, ticker):
        url = f"https://robinhood.com/stocks/{ticker}"
        webbrowser.open(url)
            
    def show_chart(self, row):
        ticker_button = self.tableWidget.cellWidget(row, 0)
        if ticker_button:
            ticker = ticker_button.property("ticker")
            print(f"Displaying chart for {ticker}")

    def start_data_fetch(self):
        # Restart the data fetcher thread
        if self.dataFetcher.isRunning():
            self.dataFetcher.terminate()
        self.dataFetcher.start()
        
    def start_auto_update(self):
        # Timer to auto-update portfolio every 5 minutes (300000 milliseconds)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.start_data_fetch)
        self.timer.start(300000)
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_W and (event.modifiers() & Qt.ControlModifier):
            self.close()
            
    def load_stylesheet(self, stylesheet_file):
        style_file = QFile(stylesheet_file)
        style_file.open(QFile.ReadOnly | QFile.Text)
        stylesheet = style_file.readAll()
        self.setStyleSheet(str(stylesheet, encoding="utf-8"))
        
    def createButton(self, text, object_name, click_function=None, x=None, y=None):
        button = QPushButton(text)
        button.setObjectName(object_name)
        if x is not None and y is not None:
            button.move(x, y)
        if click_function is not None:
            button.clicked.connect(click_function)
        return button

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = StockApp()
    ex.show()
    sys.exit(app.exec_())