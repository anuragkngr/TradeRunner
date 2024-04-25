import json
conf = json.load(open("./data/configuration.json"))
cred={
    "APP_NAME": conf["app_name"],
    "APP_SOURCE": conf["app_source"],
    "USER_ID": conf["user_id"],
    "PASSWORD": conf["password"],
    "USER_KEY": conf["user_key"],
    "ENCRYPTION_KEY": conf["exception_key"]
    }

# import sys, time, json
# import sys
# sys.path.append("../TradeRunner")
# from api.order_management_system import OMS
# from dhanhq import dhanhq
# from utils.trading_app import TradingApp
# from .positions import Positions
# from .portfolio import Portfolio
# from .trade_book import TradeBook
# from .trade import Trade
# from .order import Order
# from .order_book import OrderBook
# from .instruments import *
# from .email_client import *
# from .broker_api import BrokerAPI
# from .historical_daily_data import *
# from .intraday_minute_data import *
# from .order_management_system import *
# from .risk_management_system import *
# from .reporting import *
# from .Holdings import Holdings
# import json
# import utils