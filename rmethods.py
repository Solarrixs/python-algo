import robin_stocks.robinhood as r

def extract_list():
    ticker_list = list(r.build_holdings().keys())
    return ticker_list