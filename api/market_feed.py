# import nest_asyncio
# nest_asyncio.apply()
# import asyncio
from utils import Utils
import json, traceback, pymongo, logging, os
from pathlib import Path
from datetime import datetime
from time import sleep
idx = ['13', '21', '25', '20', '51', '69']
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
# indexes.drop()
# options.drop()
# instruments = [(0, '13'), (0, '21'), (0, '25'), (0, '20'), (0, '51'), (0, '69')]
instruments = [(0, '13'), (0, '21'), (0, '25')]
subscription_code = marketfeed.Quote
# subscription_code = marketfeed.Ticker
oms = OMS() 
util = Utils()

file_path = Path(f"./logs/{tm}/market_feed.txt")
if not file_path.exists():
    with open(f"./logs/{tm}/market_feed.txt", "w") as fileStore:
        fileStore.close()

logging.basicConfig(
    level=logging.INFO, filename=f"./logs/{tm}/market_feed.log",
    filemode="a", format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()

feed_ids = []

index = 'NIFTY'; slab = 50; 
strike = oms.spotStrike(index)
if strike < 1: 
    print(f'Invalid strike for {index} {strike}')
    exit()
    # sleep(5)
    # strike = 22950

for i in range(12):
    _strike = int(str(round(strike + (slab*i))))
    out = util.securityId(index, _strike, 'CE')
    if out is None: continue
    security_id = out['s_id']
    symbol = out['symbol']
    instruments.append((2, security_id))
    feed_ids.append({'index': index, 'strike': _strike, 'security_id': security_id, 'symbol': symbol})

    out = util.securityId(index, _strike, 'PE')
    if out is None: continue
    security_id = out['s_id']
    symbol = out['symbol']
    instruments.append((2, security_id))
    feed_ids.append({'index': index, 'strike': _strike, 'security_id': security_id, 'symbol': symbol})

i=0 
for i in range(11):
    _strike = int(str(round(strike - (slab*(i+1)))))
    
    out = util.securityId(index, _strike, 'CE')
    if out is None: continue
    security_id = out['s_id']
    symbol = out['symbol']
    instruments.append((2, security_id))
    feed_ids.append({'index': index, 'strike': _strike, 'security_id': security_id, 'symbol': symbol})

    out = util.securityId(index, _strike, 'PE')
    if out is None: continue
    security_id = out['s_id']
    symbol = out['symbol']
    instruments.append((2, security_id))
    feed_ids.append({'index': index, 'strike': _strike, 'security_id': security_id, 'symbol': symbol})

index = 'BANKNIFTY'; slab = 100; i=0 
strike = oms.spotStrike(index)
if strike < 1: 
    print(f'Invalid strike for {index} {strike}')
    exit()
    # sleep(5)
    # strike = 49000
for i in range(12):
    _strike = int(str(round(strike + (slab*i))))

    out = util.securityId(index, _strike, 'CE')
    if out is None: continue
    security_id = out['s_id']
    symbol = out['symbol']
    instruments.append((2, security_id))
    feed_ids.append({'index': index, 'strike': _strike, 'security_id': security_id, 'symbol': symbol})
    

    out = util.securityId(index, _strike, 'PE')
    if out is None: continue
    security_id = out['s_id']
    symbol = out['symbol']
    instruments.append((2, security_id))
    feed_ids.append({'index': index, 'strike': _strike, 'security_id': security_id, 'symbol': symbol})

i=0 
for i in range(11):
    _strike = int(str(round(strike - (slab*(i+1)))))
    
    out = util.securityId(index, _strike, 'CE')
    if out is None: continue
    security_id = out['s_id']
    symbol = out['symbol']
    instruments.append((2, security_id))
    feed_ids.append({'index': index, 'strike': _strike, 'security_id': security_id, 'symbol': symbol})

    out = util.securityId(index, _strike, 'PE')
    if out is None: continue
    security_id = out['s_id']
    symbol = out['symbol']
    instruments.append((2, security_id))
    feed_ids.append({'index': index, 'strike': _strike, 'security_id': security_id, 'symbol': symbol})
# instruments = [(0, '13'), (0, '25'), (2, '38730'), (2, '46923')]
instruments = instruments + [(2, '37104'), (2, '43919')]
# instruments = [(2, '43889'), (2, '37051')]
# 37758
print(len(feed_ids))
print(len(instruments))
print(instruments)

feed.delete_many({})
# options.delete_many({})
indexes.delete_many({})
res = feed.insert_many(feed_ids)

async def on_connect(instance):
    print("Connected to websocket")

async def on_message(instance, message):
    print("Received:", message)
    try:
        saveData(message)
    except Exception:
            print(traceback.format_exc())
            logger.error(f"market_feed , on_message message: {message} {traceback.format_exc()}")
            sleep(2)

def saveData(message):

    db_obj = indexes if message['exchange_segment'] == 0 else options
        
    if message['type'] == 'Quote Data':
        if util.getTime() < conf["start_time"]:
            message['LTT'] = util.getDate() + ' ' + conf["start_time"] + ':00'
        elif util.getTime() > conf["exit_time"]:
            message['LTT'] = util.getDate() + ' ' + conf["exit_time"] + ':00'
        else: message['LTT'] = util.getDate() + ' ' + message['LTT'][:-3] + ':00'
        res = db_obj.find_one_and_update(
                { "security_id" : message['security_id'], "LTT" : message['LTT'] },
                { "$set": message },
                { "sort": { "_id" : -1 } },
                upsert=True
            )
        print(res)
    else:
        if 'OI' in message : message['oi'] = message['OI']
        res = db_obj.find_one_and_update(
                { "security_id" : message['security_id'] },
                { "$set": message },
                { "sort": { "_id" : -1 } },
                upsert=True
            )
        print(res)
    
feed = marketfeed.DhanFeed(conf['dhan_id'],
    conf['dhan_token'],
    instruments,
    subscription_code,
    on_connect=on_connect,
    on_message=on_message)

feed.run_forever()        
# asyncio.create_task(feed.run_forever())