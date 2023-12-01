import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QTextEdit, QLabel, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import Qt, QTimer, QFile
import logic as rlogic

class StockApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.start_auto_update()
        self.update_portfolio()
        self.load_stylesheet("styles.css")

    def initUI(self):
        self.setWindowTitle("Robinhood Stock Portfolio App")
        self.setGeometry(100, 100, 1000, 600)  # Adjusted window size
        
        # Table Widget
        self.tableWidget = QTableWidget(self)
        self.tableWidget.setGeometry(50, 100, 900, 400)
        self.tableWidget.setObjectName("tableWidget")
        self.load_stylesheet("styles.css")

        # Sum of Total Return Label
        self.label_total_return = QLabel("Sum of Total Return: $0.00", self)
        self.label_total_return.move(50, 510)
        self.label_total_return.resize(700, 30)

        # Buy Button
        self.btn_buy = QPushButton("Buy", self)
        self.btn_buy.setObjectName("buyButton")
        self.load_stylesheet("styles.css")
        self.btn_buy.move(50, 50)
        
        # Limit Buy Button
        self.btn_limit_buy = QPushButton("Limit Buy", self)
        self.btn_limit_buy.setObjectName("buyButton")
        self.load_stylesheet("styles.css")
        self.btn_limit_buy.move(160, 50)
        
        # Sell All Button
        self.btn_sell = QPushButton("Sell", self)
        self.btn_sell.setObjectName("quitButton")
        self.load_stylesheet("styles.css")
        self.btn_sell.move(270, 50)
        
        # Sell All Button
        self.btn_sell = QPushButton("Sell All", self)
        self.btn_sell.setObjectName("quitButton")
        self.load_stylesheet("styles.css")
        self.btn_sell.move(380, 50)

        # Stop Loss Button
        self.btn_stop_loss = QPushButton("Stop Loss", self)
        self.btn_stop_loss.setObjectName("quitButton")
        self.load_stylesheet("styles.css")
        self.btn_stop_loss.move(490, 50)
        
        # Trailing Stop Loss Button
        self.btn_trailing_stop_loss = QPushButton("TRL", self)
        self.btn_trailing_stop_loss.setObjectName("quitButton")
        self.load_stylesheet("styles.css")
        self.btn_trailing_stop_loss.move(600, 50)
        
        # Quit button
        self.btn_algo = QPushButton("Algo Trade", self)
        self.btn_algo.setObjectName("updateButton")
        self.load_stylesheet("styles.css")
        self.btn_algo.move(850, 50)
        
        # Update Button
        self.btn_update = QPushButton("Update", self)
        self.btn_update.setObjectName("buyButton")
        self.load_stylesheet("styles.css")
        self.btn_update.clicked.connect(self.update_portfolio)
        self.btn_update.move(740, 510)
        self.btn_update.resize(100, 30)

        # Quit button
        quit_button = QPushButton("Quit", self)
        quit_button.setObjectName("quitButton")
        self.load_stylesheet("styles.css")
        quit_button.clicked.connect(self.close)
        quit_button.move(850, 510)
        quit_button.resize(100, 30)

    def update_portfolio(self):
        portfolio_data_df = rlogic.calculate_portfolio_returns()

        # Set the number of rows and columns in QTableWidget
        num_rows, num_cols = portfolio_data_df.shape
        self.tableWidget.setRowCount(num_rows)
        self.tableWidget.setColumnCount(num_cols + 1)  # +1 for the ticker column

        # Set column headers
        headers = ["Ticker"] + list(portfolio_data_df.columns)
        self.tableWidget.setHorizontalHeaderLabels(headers)

        # Populate the QTableWidget with data from the DataFrame
        for row in range(num_rows):
            # Populate the first column with ticker data
            ticker_item = QTableWidgetItem(str(portfolio_data_df.index[row]))
            self.tableWidget.setItem(row, 0, ticker_item)

            for col in range(1, num_cols + 1):  # Start from 1 to skip the first column (ticker)
                item_text = str(portfolio_data_df.iat[row, col - 1])

                item = QTableWidgetItem(item_text)

                self.tableWidget.setItem(row, col, item)

        total_return_sum = rlogic.total_return(portfolio_data_df)
        # Update label_total_return text
        self.label_total_return.setText(f"Sum of Total Return: ${total_return_sum:.2f}")

        # Set column resizing mode to stretch the last section
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def start_auto_update(self):
        # Timer to auto-update portfolio every 5 minutes (300000 milliseconds)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_portfolio)
        self.timer.start(300000)
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_W and (event.modifiers() & Qt.ControlModifier):
            self.close()
            
    def load_stylesheet(self, stylesheet_file):
        style_file = QFile(stylesheet_file)
        style_file.open(QFile.ReadOnly | QFile.Text)
        stylesheet = style_file.readAll()
        self.setStyleSheet(str(stylesheet, encoding="utf-8"))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = StockApp()
    ex.show()
    sys.exit(app.exec_())