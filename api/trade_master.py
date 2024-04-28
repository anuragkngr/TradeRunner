import traceback, json, logging,os
conf = json.load(open("./data/configuration.json"))
from datetime import datetime, time
from time import sleep
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
        subject = "open-nifty-sic-10".upper()
        subs = subject.split('-') 
        entry = True
        while True:
            trade_book.print()
            rms.verify(trade_book)
            sleep(10)
            # sleep(conf["refresh_interval"])
    except Exception as e:
        print(traceback.format_exc())
        logger.error(f"Trade Master Exception response: ex {traceback.format_exc()}")
    finally:
        print("This is finally")

