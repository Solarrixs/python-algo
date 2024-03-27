import matplotlib.pyplot as plt
from openbb import obb
import pandas as pd

stock = 'NVDA'

def overlay_stock_data_normalized(symbol):
    plt.figure(figsize=(14, 7))
    years = range(2000, 2024)
    
    for year in years:
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        
        df_daily = obb.equity.price.historical(
            symbol=symbol, 
            start_date=start_date, 
            end_date=end_date,
            provider="yfinance"
        ).to_df()
        
        if not df_daily.empty:
            # Normalize the 'close' prices to show percent gain from the year's opening
            normalized = ((df_daily['close'] - df_daily['close'].iloc[0]) / df_daily['close'].iloc[0]) * 100
            plt.plot(df_daily.index, normalized, label=f'{year}')

    plt.title(f"Normalized Stock Data for {symbol} (2000-2023)")
    plt.xlabel("Date")
    plt.ylabel("Percent Gain from Opening")
    plt.legend(title="Year", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.show()

def analyze_stock_data(symbol):
    analysis_results = []
    
    for year in range(2000, 2024):
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        
        df_daily = obb.equity.price.historical(
            symbol=symbol, 
            start_date=start_date, 
            end_date=end_date,
            provider="yfinance"
        ).to_df()
        
        if not df_daily.empty:
            min_price = df_daily['close'].min()
            max_price = df_daily['close'].max()
            percent_diff = (max_price - min_price) / min_price * 100
            
            analysis_results.append({
                'Year': year,
                'Lowest Price': min_price,
                'Highest Price': max_price,
                'Yearly %': percent_diff,
            })
    
    # Convert the list of dictionaries to a DataFrame for easy viewing
    analysis_df = pd.DataFrame(analysis_results)
    return analysis_df

df_analysis = analyze_stock_data(stock)
print(df_analysis)
overlay_stock_data_normalized(stock)