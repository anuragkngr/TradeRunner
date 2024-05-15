# import nest_asyncio
# nest_asyncio.apply()
# import asyncio
from utils import Utils
import json, pandas as pd, ast, traceback
import pandas_ta as ta, logging, os
from datetime import datetime
conf = json.load(open("./data/configuration.json"))
now = datetime.now()
tm = now.strftime("%Y") + "-" + now.strftime("%m") + "-" + now.strftime("%d")
os.makedirs(f"./logs/{tm}", exist_ok=True)
os.makedirs(f"./data/", exist_ok=True)
with open(f"./logs/{tm}/market_feed.txt", "w") as fileStore:
    fileStore.close()
logging.basicConfig(
    level=logging.INFO, filename=f"./logs/{tm}/application.log",
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
strk = oms.spotStrike(index)
for i in range(11):
    instruments.append((2, str(util.securityId(index, (strk + (slab*i)), 'CE'))))
    instruments.append((2, str(util.securityId(index, (strk + (slab*i)), 'PE'))))
for i in range(10):
    instruments.append((2, str(util.securityId(index, (strk - (slab*(i+1))), 'CE'))))
    instruments.append((2, str(util.securityId(index, (strk - (slab*(i+1))), 'PE'))))

index = 'BANKNIFTY'; slab = 100; 
strk = oms.spotStrike(index)
for i in range(11):
    instruments.append((2, str(util.securityId(index, (strk + (slab*i)), 'CE'))))
    instruments.append((2, str(util.securityId(index, (strk + (slab*i)), 'PE'))))
for i in range(10):
    instruments.append((2, str(util.securityId(index, (strk - (slab*(i+1))), 'CE'))))
    instruments.append((2, str(util.securityId(index, (strk - (slab*(i+1))), 'PE'))))

# instruments = [(1, '25')]
print(instruments)

async def on_connect(instance):
    print("Connected to websocket")

async def on_message(instance, message):
    print("Received:", message)
    saveData(message)

def saveData(message):
    writeFlag = True
    security_id = message['security_id']
    if security_id is None: return
    security_id = str(security_id)
    trd_data = read()
    if trd_data is None or trd_data == '': trd_data = {}
    # print(type(trd_data[0]))
    # print(type(security_id))
    if security_id in trd_data:
        if message['type'] == 'Quote Data':
            msg = trd_data[security_id]
            oi = msg['oi'] if 'oi' in msg else 0
            message['oi'] = oi
        else:
            msg = trd_data[security_id]
            msg['oi'] = message['OI']
            message = msg
    else:
        if message['type'] == 'Quote Data':
            message['OI'] = 0
        else: writeFlag = False
    trd_data[security_id] = message
    if writeFlag: write(trd_data)
    
def read():
    trd_data = None
    try:
        with open(f"./logs/{tm}/market_feed.txt", "r") as fileStore:
            trd_data = fileStore.readline()
            fileStore.close()
            if isinstance(trd_data, str) and trd_data.strip() != "": 
                trd_data = ast.literal_eval(trd_data)
    except Exception:
        print(traceback.format_exc())
        logger.error(f"Market Feed , read {traceback.format_exc()}")
        try:
            sleep(1)
            with open(f"./logs/{tm}/market_feed{tm}.txt", "r") as fileStore:
                trd_data = fileStore.readline()
                fileStore.close()
                if isinstance(trd_data, str) and trd_data.strip() != "": 
                    trd_data = ast.literal_eval(trd_data)
        except Exception:
            print(traceback.format_exc())
            logger.error(f"Market Feed , read 2 {traceback.format_exc()}")
    return trd_data
    
def write(trd_data):
    try:
        with open(f"./logs/{tm}/market_feed.txt", "w") as fileStore:
            fileStore.write(str(trd_data))
            fileStore.close()
    except Exception:
        print(traceback.format_exc())
        logger.error(f"Market Feed , write {traceback.format_exc()}")
        try:
            sleep(1)
            with open(f"./logs/{tm}/market_feed.txt", "w") as fileStore:
                fileStore.write(str(trd_data))
                fileStore.close()
        except Exception:
            print(traceback.format_exc())
            logger.error(f"Market Feed , write 2 {traceback.format_exc()}")
feed = marketfeed.DhanFeed(conf['dhan_id'],
    conf['dhan_token'],
    instruments,
    subscription_code,
    on_connect=on_connect,
    on_message=on_message)

feed.run_forever()        
# asyncio.create_task(feed.run_forever())