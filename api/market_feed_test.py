# import nest_asyncio
# nest_asyncio.apply()
# import asyncio
from utils import Utils
import random
import json, pandas as pd, ast, traceback, pymongo, pandas_ta as ta, logging, os#, bson
# from bson.raw_bson import RawBSONDocument
from pathlib import Path
from datetime import datetime
from time import sleep
idx = ['13', '21', '25', '20', '51', '69']
# from bson import encode
# from pymongo import InsertOne, DeleteMany, DeleteOne, ReplaceOne
from dhanhq import dhanhq, marketfeed
from order_management_system import OMS
conf = json.load(open("./data/configuration.json"))
dhan = dhanhq(conf['dhan_id'], conf['dhan_token'])

now = datetime.now()
tm = now.strftime("%Y") + "-" + now.strftime("%m") + "-" + now.strftime("%d")
os.makedirs(f"./logs/{tm}", exist_ok=True)
os.makedirs(f"./data/", exist_ok=True)
client = pymongo.MongoClient(conf['db_url_lcl'])
dblist = client.list_database_names()
mydb = client["tradestore"]
options = mydb["options"]
feed = mydb["feed"]
indexes = mydb["indexes"]
instruments = [(0, '13'), (0, '21'), (0, '25'), (0, '20'), (0, '51'), (0, '69')]
subscription_code = marketfeed.Quote
# subscription_code = marketfeed.Ticker
oms = OMS() 
util = Utils()

file_path = Path(f"./logs/{tm}/market_feed.txt")
# if not file_path.exists():
#     with open(f"./logs/{tm}/market_feed.txt", "w") as fileStore:
#         fileStore.close()

# logging.basicConfig(
#     level=logging.INFO, filename=f"./logs/{tm}/market_feed.log",
#     filemode="a", format="%(asctime)s - %(levelname)s - %(message)s")
# logger = logging.getLogger()

feed_ids = []

index = 'NIFTY'; slab = 50; 

# instruments = [(0, '13'), (0, '25'), (2, '38730'), (2, '46923')]
# instruments = instruments + [(2, '43889'), (2, '37051')]
instruments = [(2, '37051')]

# print(instruments)

async def on_connect(instance):
    print("Connected to websocket")

async def on_message(instance, message):
    print("Received:", message)
    try:
         print()
        # res = indexes.find_one({'security_id': {'$eq': int('13')}}, sort=[('_id', -1)])
        # print({'Item 1: open': res['open'], 'high':res['high'], 'low':res['low'], 'close':res['close']})
        # res = indexes.find_one({'security_id': {'$eq': int('13')}}, sort=[('_id', 1)])
        # print({'Item 2: open': res['open'], 'high':res['high'], 'low':res['low'], 'close':res['close']})
        
        # saveData(message)
    except Exception:
            print(traceback.format_exc())
            # logger.error(f"market_feed , on_message message: {message} {traceback.format_exc()}")
            sleep(.2)

feed = marketfeed.DhanFeed(conf['dhan_id'],
    conf['dhan_token'],
    instruments,
    subscription_code,
    on_connect=on_connect,
    on_message=on_message)

feed.run_forever()        
# asyncio.create_task(feed.run_forever())