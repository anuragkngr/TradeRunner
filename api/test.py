
from utils import Utils
import json, pandas as pd
import pandas_ta as ta, logging
from datetime import datetime, time, timedelta
conf = json.load(open("./data/configuration.json"))
from time import sleep
from dhanhq import dhanhq
dhan = dhanhq(conf['dhan_id'], conf['dhan_token'])
res = dhan.historical_daily_data(
    symbol='TCS',
    exchange_segment='NSE_EQ',
    instrument_type='EQUITY',
    expiry_code=0,
    from_date='2024-06-05',
    to_date='2024-06-01'
)
res = json.load(open('./data/historical_daily_data.json'))
df = pd.DataFrame(res['data'])
# df['data'] = dhan.convert_to_date_time(df['start_Time'])
# df = dropna(df)
tmp_list = []
for i in df['start_Time']:
    tmp = dhan.convert_to_date_time(i)
    tmp_list.append(tmp)
df['date'] = tmp_list
df['date'] = pd.to_datetime(df['date'])

# df = dropna(df)
# df_all = volume_weighted_average_price(high=df["high"], low=df['low'], close=df['close'], volume=df['volume'], window=14)
print(df)
# df_all.
df.set_index('date', inplace=True)
df['vwap'] = ta.overlap.vwap(df.high, df.low, df.close, df.volume)
df.reset_index(inplace=True)
print(df.to_markdown())
# help(ta.vwap)

def histPrice(self, index):
        slab = 100 if index == "BANKNIFTY" else 50
        historicParam={
        "symbol": "NSE",
        "exchange_segment": "3045",
        "instrument_type": "THREE_MINUTE",
        "expiry_code": 0,
        "from_date": ((datetime.now()) + timedelta(days=-7)).strftime("%Y-%m-%d"),
        "to_date": (datetime.now()).strftime("%Y-%m-%d")
        }
        res = self.dhan.historical_daily_data(historicParam)
        return res   