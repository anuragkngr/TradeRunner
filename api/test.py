# import nest_asyncio
# nest_asyncio.apply()
# import asyncio
from utils import Utils
import warnings, pymongo, json
conf = json.load(open("./data/configuration.json"))
client = pymongo.MongoClient(conf['db_url_lcl'])
mydb = client['tradestore']
options = mydb['options']
warnings.filterwarnings('ignore')
import json, pandas as pd, ast, traceback
import pandas_ta as ta, logging
# from alphaVantageAPI.alphavantage import AlphaVantage
# import watchlist
from datetime import datetime, time, timedelta

now = datetime.now()
tm = now.strftime("%Y") + "-" + now.strftime("%m") + "-" + now.strftime("%d")
logging.basicConfig(
    level=logging.INFO, filename=f"./logs/{tm}/application.log",
    filemode="a", format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()
# from time import sleep
from dhanhq import dhanhq, marketfeed
# from order_management_system import OMS
# oms = OMS()
dhan = dhanhq(conf['dhan_id'], conf['dhan_token'])
instruments = []#[(1, "1333"),(0,"13")]
# subscription_code = marketfeed.Ticker
# subscription_code = marketfeed.Quote
# util = Utils()
# res = json.load(open('./data/market_feed.json'))
# df = pd.DataFrame(res['data'])
# tmp_list = []
# for i in df["start_Time"]:
#     tmp = dhan.convert_to_date_time(i)
#     tmp_list.append(tmp)
# df['date'] = tmp_list

# res = dhan.get_order_list()
_dt = datetime.today().replace(hour=0,minute=0,second=0,microsecond=0)
print(type(_dt))
print(_dt)
_dt = str(_dt)
print(type(_dt))
print(_dt)
exit()
res = dhan.get_positions()
res = [x for x in res['data'] if x['positionType'] != 'CLOSED']
print(json.dumps(res))

# res = list(options.find_one(
#                 { 'security_id' : 43889 },
#                 sort=[('_id', -1)]
#                 # { 'sort': { '_id' : -1 } },
#             ))
# print(res)
exit()
# CommonStrategy = ta.CommonStrategy
# CommonStrategy = ta.AllStrategy
# print("name =", CommonStrategy.name)
# print("description =", CommonStrategy.description)
# print("created =", CommonStrategy.created)
# print("ta =", CommonStrategy.ta)

# custom_a = ta.Strategy(name="A", ta=[{"kind": "sma", "length": 50}, {"kind": "sma", "length": 200}])
# print(custom_a)

def priceBankNifty(symbol = "13"):
        
    return dhan.intraday_minute_data(
        security_id='25',
        exchange_segment='IDX_I',
        instrument_type='OPTIDX'
    )
# if symbol == "BANKNIFTY" else "OPTIDX",
        # expiry_code=0,# if symbol == "BANKNIFTY" else expiry[symbol],
        # from_date=from_d,
        # to_date=datetime.now().strftime("%Y-%m-%d")
        # )

custom_b = ta.Strategy(name="B", ta=[{"kind": "ema", "length": 8}, {"kind": "ema", "length": 21}, {"kind": "log_return", "cumulative": True}, {"kind": "rsi"}, {"kind": "supertrend"}])
print(custom_b)

# dhan.historical_daily_data('25','IDX_I',instrument_type,expiry_code,from_date,to_date)
res = priceBankNifty()
print(res)
exit(0)
# exit(0)
#DJZHJP90NULY10EW
df.set_index('date', inplace=True)
df['vwap'] = ta.vwap(df.high, df.low, df.close, df.volume)
df['sma_10'] = ta.sma(df.close, 10, min_periods=1)
df['sma_20'] = ta.sma(df.close, 20, min_periods=1)

# df['ema_10'] = ta.ema(df.close, 10, min_periods=1)
# df['ema_20'] = ta.ema(df.close, 20, min_periods=1)

df['sma_10_above_20'] = (df["sma_10"] >= df["sma_20"]).astype(int)
df['10_20_co'] = df['sma_10_above_20'].diff().astype('Int64')

df.reset_index(inplace=True)
print(df)
print("Bullish crossovers")
print(df.loc[df['10_20_co'] == 1])
print("Bearish crossovers")
print(df.loc[df['10_20_co'] == -1])

# print(df)
# print(help(ta.sma))
# av = AlphaVantage(
#     api_key="DJZHJP90NULY10EW", premium=False,
#     output_size='full', clean=True,
#     export_path=".", export=True
# )

# data_source = "av" # Default
# data_source = "yahoo"
# watch = watchlist(["SPY", "IWM"], ds_name=av, timed=False)
# print(watch)
# ta.VolumeWeightedAveragePrice(High=df['high'], Low=df['low'], Close=df['close'], Volume=df['volume'])

# print(help(ta.sma)) 
# d = df.close
# d = df['close']
# d = list(d)
# # d = df['close'][-1]
# # d = df.close[-1]
# print(list(df.vwap)[-1])

