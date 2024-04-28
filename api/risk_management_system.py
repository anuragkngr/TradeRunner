from datetime import datetime, timedelta
import pandas as pd, logging, json, ast, re, csv, time
from trade_book import TradeBook
from trade import Trade
from order_management_system import OMS
conf = json.load(open("./data/configuration.json"))
oms = OMS()
now = datetime.now()
tm = now.strftime("%Y") + "-" + now.strftime("%m") + "-" + now.strftime("%d")
logging.basicConfig(
    level=logging.INFO, filename=f"./logs/{tm}/application.log",
    filemode="a", format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()
class RMS: 
    # def __init__(self):
    def verify(self, book):
        logger.info("Verifying traded price")
        # trdVar = {};
        book.clean()
        for trd in book.trades:
            status = self.checkTrade(trd)
            # trdVar = trd
            logger.info(f"response received from checkTrade {status}")
            if status == 1:
                logger.info(f"loss booked. total Loss {trd.pnl}")
                if oms.closeTrade(trd):
                    book.exitTrade(trd)
                continue
            if status == 2:
                logger.info(f"profit increased. Profit {trd.pnl}")
            if status == 3:
                logger.info(f"profit booked. total Profit {trd.pnl}")
                if oms.closeTrade(trd):
                    book.exitTrade(trd)
            else: logger.info("Trade continue.. ")
            pos = self.checkAdjustment(trd)
            if pos != -11: 
                logger.info("response received, no adjustment required.")
                continue
            else:
                logger.info(f"skipping applying adjustment for pos {str(pos)}")    
                trd.adjustLeg(pos)
                time.sleep(2)
                # book.fundUpdate(trd)
    
    def checkTrade(self, trd) -> int:
        ####### RMS #######
        logger.info("Verifying SL check")
        if (trd.pnl < trd.sl or trd.pnlPercent < trd.risk) and trd.pnl > 0:
            return 3 #Profit book
        if trd.pnl < trd.sl or trd.pnlPercent < trd.risk:
            return 1 #SL hit 
        if trd.pnl > trd.target or trd.pnlPercent > trd.reward:
            trd.sl = trd.pnl - (trd.pnl*0.20)
            trd.target = trd.pnl + (trd.pnl*0.20)
            trd.risk = trd.reward - (trd.reward*0.20)
            trd.reward = trd.reward + (trd.reward*0.20)
            return 3
            # Profit continue
        else: return 4 # continue 
    
    def checkAdjustment(self, trade):
        sell_ce = [];sell_pe = []
        price_pe = 0; price_ce = 0;
        for po in trade.positions:
            if po.position_type == 'SHORT':
                if po.option_type == "CALL":
                    price_ce = price_ce + float(po.price)
                    sell_ce = po
                else:
                    price_pe = price_pe + float(po.price)
                    sell_pe = po
        p1 = round((price_ce + price_pe) * conf["price_adjustment"])
        if abs(price_ce - price_pe) > p1: return sell_ce if price_ce > price_pe else sell_pe
        return - 1

if __name__ == "__main__":
    trade = Trade([], "FINNIFTY")
    conf = json.load(open("./data/configuration.json"))
    # dhan =  dhanhq(conf["client_id"], conf["access_token"])
    # rms.checkTrade(trade)
    # reward = 0.8
    # jump = 0.2
    # slPercent = -1
    # temp = 1
    # print(f"temp = {temp}")
    # print(f"temp = {temp}")
    # rms = RMS()
    # pos = rms.dhan.get_order_list()
    # print(json.dumps(pos))
    exit()
    pos = json.load(open('./data/positions.json'))['data']
    pos = Positions(pos)
    trade = Trade(pos.positions)
    trade.update(pos)
    book.enterTrade(trade)
    res = RMS(dhan, book)
    rms.verify()

    # dframe = pd.DataFrame((trade.Orders()))

    # print(dframe)