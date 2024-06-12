
import traceback, pymongo, json, pymongo, logging, os
from datetime import datetime
from dateutil import parser
from time import sleep
from pathlib import Path
conf = json.load(open('./data/configuration.json'))
client = pymongo.MongoClient(conf['db_url_lcl'])
mydb = client['tradestore']
feed_runner = mydb['feed_runner']
from subprocess import *
now = datetime.now()
tm = now.strftime('%Y') + '-' + now.strftime('%m') + '-' + now.strftime('%d')
os.makedirs(f'./logs/{tm}', exist_ok=True)
os.makedirs(f'./data/', exist_ok=True)
logging.basicConfig(
    level=logging.INFO, filename=f"./logs/{tm}/market_feed.log", force=True,
    filemode="a", format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()

time_limit = 15

print('Feed Runner starting ...')
logger.info('Feed Runner starting ...')

while True:
    try:
        tm = datetime.now().strftime("%H:%M")
        if tm < '09:15' or tm > '15:30':
            print('Market Closed..')
            logger.info('Market Closed..')
            exit()
        res = feed_runner.find_one(
                { 'run_date' : str(datetime.now().date()) }
            )
        updated_at = parser.parse(res['updated_at'])
        dif = (datetime.now() - updated_at).total_seconds()
        if dif > time_limit/2:
            print(f'Market Feed Stopped from {dif}, restarting ...')
            logger.info(f'Market Feed Stopped from {dif}, restarting ...')
            Popen('python api/market_feed.py', creationflags=CREATE_NEW_CONSOLE, shell=True)
            print(f'market_feed tunner re-started ... {str(datetime.now())}')
            logger.info(f'market_feed tunner re-started ... {str(datetime.now())}')
        sleep(time_limit)
    except Exception:
        print('market_feed runner failed')
        logger.info('market_feed runner failed')
        print(f"market_feed runner: Exception execOrder response: {traceback.format_exc()}")
        logger.info(f"market_feed runner: Exception execOrder response: {traceback.format_exc()}")

