import robin_stocks.robinhood as r
import pandas as pd

def calculate_portfolio_returns():
    # All tickers in portfolio
    ticker_list = list(r.build_holdings().keys())

    # Get latest price of all tickers
    ticker_latest_price = r.get_latest_price(ticker_list) 

    # Get data on current open positions
    open_stock_position_info = r.get_open_stock_positions()
    combined_positions = [{'Buy-In Price': position['average_buy_price'], 'Quantity': position['quantity']}
                          for position in open_stock_position_info
                          if 'average_buy_price' in position and 'quantity' in position]

    # Pandas DataFrame
    positions_price_df = pd.DataFrame(ticker_latest_price, index=ticker_list, columns=['Latest Price'])
    positions_price_df['Latest Price'] = positions_price_df['Latest Price'].astype(float)

    positions_opendata_df = pd.DataFrame(combined_positions, index=ticker_list)
    positions_opendata_df['Buy-In Price'] = positions_opendata_df['Buy-In Price'].astype(float)
    positions_opendata_df['Quantity'] = positions_opendata_df['Quantity'].astype(float)

    # Merging All Data
    merged_df = pd.merge(positions_price_df, positions_opendata_df, left_index=True, right_index=True)
    merged_df['Total Return'] = (merged_df['Latest Price'] - merged_df['Buy-In Price']) * merged_df['Quantity']
    merged_df['% Increase'] = ((merged_df['Latest Price'] - merged_df['Buy-In Price']) / merged_df['Buy-In Price']) * 100

    # Rounding
    merged_df['Latest Price'] = merged_df['Latest Price'].round(3)
    merged_df['Buy-In Price'] = merged_df['Buy-In Price'].round(3)
    merged_df['Quantity'] = merged_df['Quantity'].round(2)
    merged_df['Total Return'] = merged_df['Total Return'].round(2)
    merged_df['% Increase'] = merged_df['% Increase'].round(2)

    return merged_df

def total_return(df):
    return df['Total Return'].sum()
