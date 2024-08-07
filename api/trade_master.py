import traceback, json, pandas as pd, logging,os, pymongo
conf = json.load(open("./data/configuration.json"))
# open("./data/pnl.txt", "w").close()
# subject = "open-nifty-sic-10".upper()
from datetime import datetime, time
from time import sleep
import warnings
warnings.filterwarnings('ignore')
client = pymongo.MongoClient(conf['db_url_lcl'])
mydb = client["tradestore"]
trades = mydb["trades"]
now = datetime.now()
tm = now.strftime("%Y") + "-" + now.strftime("%m") + "-" + now.strftime("%d")
os.makedirs(f"./logs/{tm}", exist_ok=True)
os.makedirs(f"./data/", exist_ok=True)
logging.basicConfig(
    level=logging.INFO, filename=f"./logs/{tm}/application.log",
    filemode="a", format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()
from order_management_system import OMS
from trade_book import TradeBook
from risk_management_system import RMS
from utils import Utils
conf = json.load(open("./data/configuration.json"))
util = Utils()
trade_book = TradeBook()
oms = OMS()
rms = RMS()

if __name__ == "__main__":
    try:
        # open("./data/pnl.txt", "w").close()
        # trades.delete_many({})
        while util.getTime() >= conf["start_time"] and util.getTime() < conf["end_time"]:
            trade_book.print()
            rms.verify(trade_book)
            if conf["intraday"] is True:
                if util.getTime() > conf["square_off_time"] and int(trade_book.openTrades) > 0:
                    trade_book.exitTrades()
                if util.getTime() > conf["final_sl"] and not trade_book.finalFlag:
                    trade_book.setFinalRisk()
            # sleep(conf["refresh_interval"])
    except Exception as e:
        print(traceback.format_exc())
        logger.error(f"Trade Master Exception response: ex {traceback.format_exc()}")
    finally:
        print("This is finally")

