import robin_stocks.robinhood as r
import pandas as pd
import logic as rlogic
import os
import datetime

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
    ticker_latest_price = r.get_latest_price(ticker_list)
    latest_price_dict = {ticker: price for ticker, price in zip(ticker_list, ticker_latest_price)}

    # Get data on current open positions
    open_stock_position_info = r.get_open_stock_positions()
    combined_positions = [{'Buy-In Price': position['average_buy_price'], 'Shares': position['quantity']}
                          for position in open_stock_position_info
                          if 'average_buy_price' in position and 'quantity' in position]

    # Create Pandas DataFrame
    positions_price_df = pd.DataFrame.from_dict(latest_price_dict, orient='index', columns=['Latest Price'])
    positions_opendata_df = pd.DataFrame(combined_positions, index=ticker_list)
    open_price_df = pd.DataFrame({'Open Price': open_prices}, index=ticker_list)
    
    # Convert to Float Values
    positions_price_df['Latest Price'] = positions_price_df['Latest Price'].astype(float)
    positions_opendata_df['Buy-In Price'] = positions_opendata_df['Buy-In Price'].astype(float)
    positions_opendata_df['Shares'] = positions_opendata_df['Shares'].astype(float)
    open_price_df['Open Price'] = open_price_df['Open Price'].astype(float)

    # Merging All Data
    portfolio_data_df = pd.merge(positions_price_df, positions_opendata_df, left_index=True, right_index=True)
    portfolio_data_df = pd.merge(portfolio_data_df, open_price_df, left_index=True, right_index=True)
    portfolio_data_df['$ Total Return'] = (portfolio_data_df['Latest Price'] - portfolio_data_df['Buy-In Price']) * portfolio_data_df['Shares']
    portfolio_data_df['% Total Return'] = ((portfolio_data_df['Latest Price'] - portfolio_data_df['Buy-In Price']) / portfolio_data_df['Buy-In Price']) * 100
    portfolio_data_df['% Daily Change'] = ((portfolio_data_df['Latest Price'] - portfolio_data_df['Open Price']) / portfolio_data_df['Open Price']) * 100
    
    # Reorder the columns
    portfolio_data_df = portfolio_data_df[['Open Price', 'Latest Price', 'Buy-In Price', 'Shares', '$ Total Return', '% Total Return', '% Daily Change']]

    # Formatting
    portfolio_data_df['Open Price'] = portfolio_data_df['Open Price'].round(2)
    portfolio_data_df['Latest Price'] = portfolio_data_df['Latest Price'].round(2)
    portfolio_data_df['Buy-In Price'] = portfolio_data_df['Buy-In Price'].round(2)
    portfolio_data_df['Shares'] = portfolio_data_df['Shares'].round(0)
    portfolio_data_df['$ Total Return'] = portfolio_data_df['$ Total Return'].round(2)
    portfolio_data_df['% Total Return'] = portfolio_data_df['% Total Return'].round(2)
    portfolio_data_df['% Daily Change'] = portfolio_data_df['% Daily Change'].round(2)

    return portfolio_data_df

def total_return(df):
    return df['$ Total Return'].sum()

notified_stocks = {}

def check_price_change():
    portfolio_df = rlogic.calculate_portfolio_returns()

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
                
def wait_until_market_open():
    now = datetime.datetime.now()
    next_open_hours = r.get_market_next_open_hours("XNYS")
    
    if next_open_hours['is_open']:
        return 0 # Run NOW
    
    opens_at = datetime.datetime.fromisoformat(next_open_hours['opens_at'])
    wait_seconds = (opens_at - now).total_seconds()
    return wait_seconds