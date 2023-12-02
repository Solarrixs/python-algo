import robin_stocks.robinhood as r
import pandas as pd
import os
import datetime, time
import pyotp
from dotenv import load_dotenv

def calculate_portfolio_returns():
    # All tickers in portfolio
    ticker_list = list(r.build_holdings().keys())
    
    # Get open price of all tickers
    open_prices = []

    for ticker in ticker_list:
        open_price_data = r.stocks.get_stock_historicals(ticker, span='day', bounds='regular')
        
        if open_price_data:
            open_price = open_price_data[0]['open_price']
            open_prices.append(open_price)
        else:
            open_prices.append(None)

    # Get latest price of all tickers
    latest_prices = r.get_latest_price(ticker_list)

    # Creating DataFrame for ticker, open prices and latest prices
    prices_df = pd.DataFrame({'Ticker': ticker_list, 'Open Price': open_prices, 'Latest Price': latest_prices})
    prices_df.set_index('Ticker', inplace=True)
    prices_df = prices_df.apply(pd.to_numeric)

    # Get data on current open positions
    holdings = r.build_holdings()
    holdings_df = pd.DataFrame.from_dict(holdings, orient='index')
    holdings_df['Buy-In Price'] = holdings_df['average_buy_price'].astype(float)
    holdings_df['Shares'] = holdings_df['quantity'].astype(float)

    # Merging holdings data with price data
    portfolio_data_df = pd.merge(prices_df, holdings_df[['Buy-In Price', 'Shares']], left_index=True, right_index=True)

    # Calculating returns
    portfolio_data_df['$ Total Return'] = (portfolio_data_df['Latest Price'] - portfolio_data_df['Buy-In Price']) * portfolio_data_df['Shares']
    portfolio_data_df['% Total Return'] = ((portfolio_data_df['Latest Price'] - portfolio_data_df['Buy-In Price']) / portfolio_data_df['Buy-In Price']) * 100
    portfolio_data_df['% Daily Change'] = ((portfolio_data_df['Latest Price'] - portfolio_data_df['Open Price']) / portfolio_data_df['Open Price']) * 100

    # Formatting
    portfolio_data_df = portfolio_data_df.round(2)
    portfolio_data_df['Shares'] = portfolio_data_df['Shares'].round(0)

    return portfolio_data_df

def total_return(df):
    return df['$ Total Return'].sum()

notified_stocks = {}

def check_price_change():
    portfolio_df = calculate_portfolio_returns()

    for index, row in portfolio_df.iterrows():
        # Latest price and buy-in details from your portfolio DataFrame
        latest_price = row['Latest Price']
        buy_in_price = row['Buy-In Price']
        shares = row['Shares']
        open_price = row['Open Price']

        # Calculate percentage change
        if open_price and latest_price:
            open_price = float(open_price)
            percentage_change = ((latest_price - open_price) / open_price) * 100

            # Check if the stock has changed by more than 10% and is not already notified
            if abs(percentage_change) > 10 and (index not in notified_stocks or abs(notified_stocks[index] - percentage_change) >= 10):
                change_type = "up" if percentage_change > 0 else "down"

                # Calculate total return
                total_return = (latest_price - buy_in_price) * shares

                message = f"From ${open_price} to ${latest_price}. Total return: ${total_return:.2f}."
                os.system(f"osascript -e 'display notification \"{message}\" with title \"{index} {change_type} by {abs(percentage_change):.2f}%\" sound name \"Hero\"'")
                notified_stocks[index] = percentage_change
                
def check_price_change_loop():
    while True:
        now = datetime.datetime.now()
        next_open_hours = r.get_market_next_open_hours("XNYS")

        if next_open_hours['is_open']:
            # Market is open, perform the price check
            check_price_change()
            # Sleep for a short period, e.g., 1 minute, before checking again
            time.sleep(60)
        else:
            # Calculate time until market opens
            opens_at = datetime.datetime.fromisoformat(next_open_hours['opens_at'])
            wait_seconds = (opens_at - now).total_seconds()
            time.sleep(wait_seconds)

def login():
    dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    load_dotenv(dotenv_path)
    username = os.environ.get("USERNAME")
    password = os.environ.get("PASSWORD")
    totp_key = os.environ.get("TOTP")
    
    if not all([username, totp_key, password]):
        raise ValueError("One or more required environment variables are not set")

    code = pyotp.TOTP(totp_key).now()
    r.login(username, password, mfa_code=code)