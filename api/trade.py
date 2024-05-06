import ast, traceback, numpy as np, json, logging, pandas as pd
conf = json.load(open("./data/configuration.json"))
from tabulate import tabulate, SEPARATING_LINE
from datetime import datetime, time
from time import sleep
now = datetime.now()
tm = now.strftime("%Y") + "-" + now.strftime("%m") + "-" + now.strftime("%d")
logging.basicConfig(
    level=logging.INFO, filename=f"./logs/{tm}/application.log",
    filemode="a", format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()
from utils import Utils
from vix import Vix
from position import Position
from order_management_system import OMS
oms = OMS()
util = Utils()

class Trade: 

    def __init__(self, positions, index=None, fund=None, trade_id=None):
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
        self.margin = 0.0 if fund is None else fund
        self.status = "open"
        self.index = index
        price = oms.price(self.index, True)
        self.spot = price['close']
        self.move = float(self.spot) - float(price['open'])
        self.movePercent = self.move * 100 / float(self.spot)
        # if self.index is None: self.index = util.getIndex(positions)
        quantity = 50 if self.index == "NIFTY" else 15 if self.index == "BANKNIFTY" else 40
        self.quantity = quantity * lots
        self.strategy = 'selling'
        self.trade_id = str(round(datetime.now().timestamp())) if trade_id is None else trade_id
        self.start = datetime.now().timestamp()
        self.positions = [pos for pos in positions]
        if len(self.positions) == 1: self.strategy = "buying"
        self.straddle_price = 0
        self.vwap = 0
        self.sma_22 = 0
        self.sma_44 = 0
        self.ema_22 = 0
        self.ema_44 = 0


    def updateIndex(self): 
        price = oms.price(self.index, True)
        self.spot = price['close']
        self.move = float(self.spot) - float(price['open'])
        self.movePercent = self.move * 100 / float(self.spot)

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
        inxPrice = oms.price(self.index, True)['close']# .dailyPrice(self.index)
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
                1: f"{str(self.index)[:3] + ' ' + str(round(self.spot)) + ': (' + str(round(self.movePercent, 1)) + '%) ' + str(round(self.move))}",
                2: f"{'P&L: ' + str(round(self.pnl)) + ' (' + str(round(self.pnlPercent, 1)) + '%)'}",# Fund:' + str(round(self.margin))}",
                3: f"{'SL: ' + str(round(self.sl)) + ' (' + str(round(self.risk, 1)) + '%)'}",
                4: f"{'TARGET: ' + str(round(self.target)) + ' (' + str(round(self.reward, 1)) + '%)'}",
                5: f"{str(round(self.pnlMax)) + '(x)/' + str(round(self.pnlMin)) + '(n)'}",
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
            # "SECURITY": po.security_id,
            "QUANTITY": po.quantity,
            # "POSITION": po.position_type,
            "COST": po.cost_price,
            "PRICE": po.price,
            "P&L": po.pnl,
            "REALISED": po.realized,
            "UNREALIZED": po.unrealized,
            }
            resp.append(res)
        return resp
    
    def to_dict_obj(self) -> dict:
        pos = self.positions;resp = {'margin': self.margin, 'trade_id': self.trade_id}
        pos = [x.to_dict() for x in pos]
        resp['position'] = pos
        return resp

    def update(self, positions):#, priceUpdateFlag=False
        pnl = 0.0
        for pos in self.positions:
            for po in positions:
                if po.security_id == pos.security_id and po.position_type not in ['CLOSED']:
                    pos.update(po)
        self.pnl = sum(float(pos.pnl) for pos in self.positions if pos.position_type not in ['CLOSED'])
        self.pnlPercent = (self.pnl*100/float(self.margin)) if self.margin != 0.0 else 0.0
        if self.pnl > self.pnlMax or self.pnlMax == 0: self.pnlMax = self.pnl
        if self.pnl < self.pnlMin or self.pnlMin == 0: self.pnlMin = self.pnl
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
            if self.pnl > 1000 and self.sl < 500: self.sl = 500
            if self.pnl > 1500 and self.sl < 1000: self.sl = 1000
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
