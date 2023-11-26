import robin_stocks.robinhood as r
import rmethods
import pyotp

# Login Functions
totp = pyotp.TOTP("ZZTFXAFBRVUQID4T").now()
login = r.login("ma.xxy11@protonmail.com","K@UE*wU#wKaUp8@$cxwhehn!ujWx4^i@CV5D2", mfa_code=totp)

# Access Current Holdings
current_holdings = r.build_holdings()
for key,value in current_holdings.items():
    print(key, value)

ticker_list = rmethods.extract_list()
print(ticker_list)
    
# # Trade
# positions_data = r.get_current_positions()

# # Note: This for loop adds the stock ticker to every order, since Robinhood
# # does not provide that information in the stock orders.
# # This process is very slow since it is making a GET request for each order.
# for item in positions_data:
#     item['symbol'] = r.get_symbol_by_url(item['instrument'])

# TSLAData = [item for item in positions_data if item['symbol'] == 'TSLA']

# # Ensure that TSLAData is not empty before accessing its contents
# if TSLAData:
#     sellQuantity = float(TSLAData[0]['quantity']) // 2.0
#     r.order_sell_limit('TSLA', sellQuantity, 200.00)

# # View Positions
# positions_data = r.get_all_open_crypto_orders()

# # Note: Again we are adding symbol to our list of orders because Robinhood
# # does not include this with the order information.
# for item in positions_data:
#     item['symbol'] = r.get_crypto_quote_from_id(item['currency_pair_id'], 'symbol')

# btcOrders = [item for item in positions_data if item['symbol'] == 'BTCUSD' and item['side'] == 'sell']

# for item in btcOrders:
#     r.cancel_crypto_order(item['id'])


    
    
# gtc = good till cancelled
# gfd = good for day
# ioc = immediate or cancel
# opg = execute on opening