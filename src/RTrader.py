import portfoliologic as pl
import sys, threading, gui
        
def run():
    pl.login()
    app = gui.QApplication(sys.argv)
    ex = gui.StockApp()

    threading.Thread(target=pl.check_price_change_loop, daemon=True).start()

    ex.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run()