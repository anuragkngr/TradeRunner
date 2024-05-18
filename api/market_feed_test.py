# import nest_asyncio
# nest_asyncio.apply()
# import asyncio
from utils import Utils
import json, pandas as pd, ast, traceback, pandas_ta as ta, logging, os, pymongo
from datetime import datetime
conf = json.load(open("./data/configuration.json"))
client = pymongo.MongoClient(conf['db_url_lcl'])
dblist = client.list_database_names()
if "tradestore" in dblist:
  print("The database exists.")
mydb = client["tradestore"]


now = datetime.now()
tm = now.strftime("%Y") + "-" + now.strftime("%m") + "-" + now.strftime("%d")
os.makedirs(f"./logs/{tm}", exist_ok=True)
os.makedirs(f"./data/", exist_ok=True)
logging.basicConfig(
    level=logging.INFO, filename=f"./logs/{tm}/application2.log",
    filemode="a", format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()
from time import sleep
from dhanhq import dhanhq, marketfeed
from order_management_system import OMS
oms = OMS()
dhan = dhanhq(conf['dhan_id'], conf['dhan_token'])
instruments = []
subscription_code = marketfeed.Quote
util = Utils()

index = 'NIFTY'; slab = 50; 

index = 'BANKNIFTY'; slab = 100; 

instruments = [(2, '41537')]
print(instruments)
# exit(0)

async def on_connect(instance):
    print("Connected to websocket")

async def on_message(instance, message):
    print("Received:", message)

feed = marketfeed.DhanFeed(conf['dhan_id'],
    conf['dhan_token'],
    instruments,
    subscription_code,
    on_connect=on_connect,
    on_message=on_message)

opts = mydb["options"]

mydict = { "name": "John", "address": "Highway 37" }
x = opts.insert_one(mydict)

# mylist = [
#   { "name": "Amy", "address": "Apple st 652"},
#   { "name": "Hannah", "address": "Mountain 21"}
# ]
# x = opts.insert_many(mylist)

for x in opts.find({},{ "name": 'John' }):
    print(x)
# feed.run_forever()        
# asyncio.create_task(feed.run_forever())