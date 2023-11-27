import robin_stocks.robinhood as r
import pandas as pd
import positions as pos
import pyotp

# Login Functions
totp = pyotp.TOTP("ZZTFXAFBRVUQID4T").now()
login = r.login("ma.xxy11@protonmail.com","K@UE*wU#wKaUp8@$cxwhehn!ujWx4^i@CV5D2", mfa_code=totp)

# Functions
portfolio = pos.calculate_portfolio_returns()
print(portfolio)

total_return_sum = pos.total_return(portfolio)
print("Sum of Total Return:", total_return_sum)