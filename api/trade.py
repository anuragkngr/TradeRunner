import ast, traceback, numpy as np, json, logging, pandas as pd
conf = json.load(open("./data/configuration.json"))
from tabulate import tabulate, SEPARATING_LINE
from datetime import datetime, time
from time import sleep
now = datetime.now()
tm = now.strftime("%Y") + "-" + now.strftime("%m") + "-" + now.strftime("%d")
logging.basicConfig(
    level=logging.INFO, filename=f"./logs/{tm}/application{'_' + now.strftime("%H-%S")}.log",
    filemode="w", format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()
from utils import Utils
from vix import Vix
from position import Position
from order_management_system import OMS
oms = OMS()
util = Utils()

class Trade: 

    def __init__(self, positions, index=None, strategy = "IC"):
        self.pnl = 0.0
        self.pnlMax = 0.0
        self.pnlMin = 0.0
        self.pnlPercent = 0.0
        self.risk = conf["risk"]
        self.reward = conf["reward"]
        self.step = conf["step"]
        self.target = conf["profit"]
        self.sl = conf["loss"]
        # fund_limit = conf["fund_limit"]
        lots = conf["lots"]
        self.margin = 0.0
        self.status = "open"
        self.index = index
        self.spot = oms.ohlc(self.index, True)['close']
        # if self.index is None: self.index = util.getIndex(positions)
        quantity = 50 if self.index == "NIFTY" else 15 if self.index == "BANKNIFTY" else 40
        self.quantity = quantity * lots
        self.strategy = strategy
        # datetime.timestamp(datetime.now())
        self.tradeId = datetime.now().timestamp()
        self.start = datetime.now().timestamp()
        # self.marketId = "13" if self.index == "NIFTY" else "25" if self.index == "BANKNIFTY" else "27"
        self.positions = [pos for pos in positions if pos.index == self.index]
        # for pos in positions:
        #     if pos['symbolname'] == self.index:
        #         pos['netprice'] = oms.orderBook(pos['tradingsymbol'])
        #         self.positions.append(pos)
        if len(self.positions) == 1: self.strategy = "buying"
        # vix = oms.ohlc('INDIA VIX')
        # vix = Vix(vix)
        # self.vix_trend = vix.trend
        # self.vix_trend_trade = self.vix_trend
        # self.vix_trade_start = vix.close
        # self.vix = vix.close

    def updateIndex(self): 
        # vix = oms.ohlc('INDIA VIX')
        # self.vix_trend_trade = Vix(vix, self.vix_trade_start).trend
        # self.vix = vix['close']
        self.spot = oms.ohlc(self.index, True)['close']

    def addOrder(self, pos): self.positions.append(pos)

    def squareOff(self) -> bool: return oms.closeTrade(self)
    
    def get(self, key): return self.__dict__[key]

    def shiftLeg(self, position, price, hedgePosition, hedgePrice, direction) -> bool:
        if res := oms.execOrder(position, "BUY"):
            logger.info("closing leg position: ", position.to_dict())
            if res := oms.execOrder(hedgePosition, "SELL"):
                hedgePosition = oms.matchOrder(self.index, hedgePosition, hedgePrice, direction)
                if res := oms.execOrder(hedgePosition, "BUY"):
                    logger.info("opening leg hedgePosition: ", hedgePosition.to_dict())
                    position = oms.matchOrder(self.index, position, price, direction)
                    if res := oms.execOrder(position, "SELL"):
                        logger.info("opening leg position: ", position.to_dict())
                    # position.price = hedgePosition.price = 0.0
                    return True
                else:
                    logger.info(" failed opening leg hedgeOrder")
            logger.info("failed opening leg order")
        logger.info("failed closing leg order")
        return False

    def adjustLeg(self, position):   # sourcery skip: low-code-quality
        if self.status != "open":
            return -1
        inxPrice = oms.ohlc(self.index, True)['close']# .dailyPrice(self.index)
        hitSide = position['optiontype']
        strikeCE=strikePE=hedgeCE=hedgePE=[]
        for pos in self.positions:
            if pos.position_type == 'LONG':
                if pos.option_type == "CALL": hedgeCE = pos
                if pos.option_type == "PUT": hedgePE = pos
            elif pos.position_type == 'SHORT':
                if pos.option_type == "CALL": strikeCE = pos
                if pos.option_type == "PUT": strikePE = pos
        
        slab = 40 if self.index == "BANKNIFTY" else 20

#// TODO:Addjust leg - check condition 
        if (inxPrice + slab) < float(strikePE['strikeprice']): 
            self.shiftLeg(strikePE, strikeCE['ltp'], hedgePE, hedgeCE['ltp'], "DOWN")
#// TODO:Addjust leg - check condition                
        elif (inxPrice - slab) > float(strikeCE['strikeprice']):
            self.shiftLeg(strikeCE, strikePE['ltp'], hedgeCE,hedgePE['ltp'], "UP")
#// TODO:Addjust leg - check condition
        elif hitSide == "CE":
            self.shiftLeg(strikePE, strikeCE['ltp'], hedgePE, hedgeCE['ltp'], "UP")
#// TODO:Addjust leg - check condition
        elif hitSide == "PE":
            self.shiftLeg(strikeCE, strikePE['ltp'], hedgeCE, hedgePE['ltp'], "DOWN")
        
    def print(self):
        return [
            {
                1: f"{'Index: ' + str(self.index)}",
                2: f"{'Fund: ' + str(self.margin)}",
                3: f"{'P&L: ' + str(round(self.pnl, 2))}",
                4: f"{'SL: ' +str(round(self.sl, 2))}",
                5: f"{'Target: ' +str(round(self.target, 2))}",
                6: f"{'Spot: ' + str(round(self.spot, 2))}",
            },
            # {
            #     1: f"{'Spot: ' + str(round(self.spot, 2))}",
            #     2: f"{'Step: ' +str(round(self.step, 2))}",
            #     3: f"{'VIX: ' +str(round(self.vix_trade_start, 2))}",
            #     4: f"{'DIF: ' +str(round((self.vix_trade_start - self.vix), 2))}",
            #     5: f"{'TREND: ' +str(self.vix_trend_trade)}",
            # },
            {
                1: f"{'Strategy: ' + str(self.strategy)}",
                2: f"{'Status: ' + str(self.status)}",
                3: f"{'P&L %: ' + str(round(self.pnlPercent, 2))}",
                4: f"{'P&L_Max: ' + str(round(self.pnlMax, 2))}",
                5: f"{'P&L_Min: ' + str(round(self.pnlMin, 2))}",
                6: f"{'Step: ' +str(round(self.step, 2))}",
            }
        ]
    
    def clean(self):
        pos = self.positions
        for po in self.pos:
            if po.position not in ["LONG", "SHORT"]:
                    self.positions.remove(po)
        
    def positions(self):
        return json.loads(json.dumps(self.positions))
    
    def to_dict(self) -> dict:
        pos = self.positions;resp = []
        for po in pos:
            res = {
            # "INDEX": po.index,
            "SYMBOL": po.symbol,
            "QUANTITY": po.quantity,
            "POSITION": po.position_type,
            "COST": po.cost_price,
            "PRICE": po.price,
            "P&L": po.pnl,
            "REALISED": po.realized,
            # "UNREALISED": po['unrealised'],
            }
            resp.append(res)
        return resp

    def update(self, positions):#, priceUpdateFlag=False
        pnl = 0.0
        for pos in self.positions:
            for po in positions:
                if po.security_id == pos.security_id and po.position_type not in ['CLOSED']:
                    pos.update(po)
        self.pnl = sum(float(pos.pnl) for pos in self.positions if pos.position_type not in ['CLOSED'])
        self.pnlPercent = (self.pnl*100/float(self.margin)) if self.margin != 0.0 else 0.0
        if self.pnl > self.pnlMax: self.pnlMax = self.pnl
        if self.pnl < self.pnlMin or self.pnlMin == 0: self.pnlMin = self.pnl
        sleep(2)
        self.updateIndex()

        mins = int((datetime.now() - datetime.fromtimestamp(self.start)).total_seconds()/60)
        if mins > conf['timer1']:
            sl = self.pnl - abs(self.pnl*0.75)
            if sl > self.sl: self.sl = sl
        if mins > conf['timer2']:
            sl = self.pnl - abs(self.pnl*0.50)
            if sl > self.sl: self.sl = sl
        if mins > conf['timer3']:
            sl = self.pnl - abs(self.pnl*0.25)
            if sl > self.sl: self.sl = sl
        if self.pnl > 0:
            if self.pnl > 500 and self.sl < -1000: self.sl = -1000
            if self.pnl > 1000 and self.sl < -500: self.sl = -500
            if self.pnl > 1500 and self.sl < 500: self.sl = 500
            if self.pnl > 2000 and self.sl < 1500: self.sl = 1500
        # if mins > conf['timer4']:
        #     self.sl = self.pnl



#//TODO: this function   should  probably       
if __name__ == "__main__":
    # for po in pos: print(po)
    # "43887", "43927"
    pos = json.load(open('./data/positions.json'))['data']
    # poss = Positions(pos)
    # trd = Trade(poss.positions)
    # print(trd.positions_print())
    # # po = position(pos)
    # # trd = Trade(pos)
    # trd.adjustLeg(dhan, pos) 
    # print("----------------", trd)
