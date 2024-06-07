import ast, traceback, numpy as np, json, logging, pandas as pd, pymongo
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
from index import Index
from position import Position
from order_management_system import OMS
oms = OMS()
util = Utils()
client = pymongo.MongoClient(conf['db_url_lcl'])
dblist = client.list_database_names()
mydb = client["tradestore"]
trades = mydb["trades"]
options = mydb["options"]
class Trade: 

    def __init__(self, positions, index=None, trade_id=None):
        self.pnl = 0.0
        self.pnlMax = 0.0
        self.pnlMin = 0.0
        self.pnlPercent = 0.0
        self.risk = conf["risk"]
        self.reward = conf["reward"]
        self.step = conf["step"]
        self.target = conf["profit"]
        self.sl = conf["loss"]
        lots = conf["lots"]
        self.margin = 0.0# if fund is None else fund
        self.status = "open"
        self.index = index
        quantity = 50 if self.index == "NIFTY" else 15 if self.index == "BANKNIFTY" else 40
        self.quantity = quantity * lots
        self.strategy = 'selling'
        self.trade_id = str(round(datetime.now().timestamp())) if trade_id is None else trade_id
        self.start = datetime.now().timestamp()
        self.positions = positions#oms.updateCostPrice(positions)
        buying_positions = [p.price for p in self.positions if p.position_type == 'LONG']
        buying_count = len(buying_positions) if buying_positions is not None else 0
        buying_sum = sum(p.price for p in self.positions if p.position_type == 'LONG')

        selling_positions = [p.price for p in self.positions if p.position_type == 'SHORT']
        selling_count = len(selling_positions) if selling_positions is not None else 0
        selling_sum = sum(p.price for p in self.positions if p.position_type == 'SHORT')

        if buying_sum > selling_sum:
            self.strategy = 'Buying (b=' + str(buying_count) + ', s=' + str(selling_count) + ')'
        else:
            self.strategy = 'Selling (b=' + str(buying_count) + ', s=' + str(selling_count) + ')'

        self.updated_at = self.created_at = datetime.now()
        self.updateTrade()
        util.addTradeStats({'index': self.index, 'trade_id': self.trade_id, 
                    'sl': self.sl, 'target': self.target})

    # def updateIndex(self): 
    #     price = oms.price_DB(self.index)
    #     self.spot = price['close']
    #     self.move = float(self.spot) - float(price['open'])
    #     self.movePercent = self.move * 100 / float(self.spot)
    
    def updateTrade(self): 
        self.updated_at = datetime.now()
        dict_trd = self.to_dict_obj()
        res = trades.find_one_and_replace({'trade_id':dict_trd['trade_id']}, dict_trd, upsert=True)

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
        inxPrice = oms.price_DB(self.index)# .dailyPrice(self.index)
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
                1: f"{str(self.index)[:4] + ': ' + str(self.strategy)}",
                2: f"{str(round(self.pnl)) + ' (' + str(round(self.pnlPercent, 1)) + '%)'}",# Fund:' + str(round(self.margin))}",
                3: f"{str(round(self.sl)) + ' (' + str(round(self.risk, 1)) + '%)'}",
                4: f"{str(round(self.target)) + ' (' + str(round(self.reward, 1)) + '%)'}",
                # 5: f"{str(self.margin)}",
                # 5: f"{str(round(self.pnlMin)) + ' / ' + str(round(self.pnlMax)) + ''}",
                
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
            "SECURITY": po.security_id,
            "SYMBOL": po.symbol,
            "QUANTITY": po.quantity,
            "COST": po.cost_price,
            "PRICE": po.price,
            "P&L": po.pnl,
            # "REALISED": po.realized,
            # "UNREALIZED": po.unrealized,
            # "OI": str(po.oi) + ' (' + str((po.oi - po.oi_pre) if po.oi_pre > 0 else 0) + ')',
            # "BUY": str(po.total_buy_quantity) + ' (' + str((po.total_buy_quantity - po.total_buy_quantity_pre) if po.total_buy_quantity_pre > 0 else 0) + ')',
            # "SELL": str(po.total_sell_quantity) + ' (' + str((po.total_sell_quantity - po.total_sell_quantity_pre) if po.total_sell_quantity_pre > 0 else 0) + ')'
            }
            resp.append(res)
        return resp
    
    def to_dict_obj(self) -> dict:
        pos = self.positions;resp = {'margin': self.margin, 'index': self.index, 'trade_id': self.trade_id,
                                     'strategy': self.strategy, 'sl': self.sl, 'target': self.target,
                                     'pnlMax': self.pnlMax, 'pnlMin': self.pnlMin, 'status': self.status}
        pos = [x.to_dict() for x in pos]
        resp['positions'] = pos
        return resp

    def update(self, positions):#, priceUpdateFlag=False
        set_pnl = util.getTradeDetails(self.trade_id)
        if set_pnl is not None:
            if self.sl < set_pnl['sl']:  self.sl = set_pnl['sl']
            if self.target > set_pnl['target']: self.target = set_pnl['target']
            
        # pnl = 0.0
        for pos in self.positions:
            for po in positions:
                if po.security_id == pos.security_id and po.position_type not in ['CLOSED']:
                    pos.update(po)
        self.pnl = sum(float(pos.pnl) for pos in self.positions if pos.position_type not in ['CLOSED'])
        self.pnlPercent = (self.pnl*100/float(self.margin)) if self.margin != 0.0 else 0.0
        if self.pnl > self.pnlMax or self.pnlMax == 0: self.pnlMax = self.pnl
        if self.pnl < self.pnlMin or self.pnlMin == 0: self.pnlMin = self.pnl
        
        # self.updateIndex()
        # util.updateTradeStats(self)
        self.updateTrade()

        # mins = int((datetime.now() - datetime.fromtimestamp(self.start)).total_seconds()/60)
        # if mins > conf['timer1']:
        #     sl = self.pnl - abs(self.pnl*0.75)
        #     if sl > self.sl: self.sl = sl
        if self.pnl > 0:
            # if self.pnl > 500 and self.sl < 200: self.sl = 200
            # if self.pnl > 1000 and self.sl < 800: self.sl = 800
            # if self.pnl > 1500 and self.sl < 1000: self.sl = 1000
            # if self.pnl > 2000 and self.sl < 1500: self.sl = 1500
            # if self.pnl > 3000 and self.sl < 2500: self.sl = 2500
            # if self.pnl > 3500 and self.sl < 3000: self.sl = 3000
            # if self.pnl > 4000 and self.sl < 3500: self.sl = 3500
            # if self.pnl > 4500 and self.sl < 4000: self.sl = 4000
            # if self.pnl > 5000 and self.sl < 4000: self.sl = 4000
            # if self.pnl > 6000 and self.sl < 5000: self.sl = 5000
            # if self.pnl > 7000 and self.sl < 6000: self.sl = 6000
            # if self.pnl > 8000 and self.sl < 8000: self.sl = 7000
            # if self.pnl > 22000 and self.sl < 20000: self.sl = 20000
            # if self.pnl > 25000 and self.sl < 20000: self.sl = 20000
            # if self.pnl > 30000 and self.sl < 25000: self.sl = 25000
            # if self.pnl > 35000 and self.sl < 30000: self.sl = 30000
            # if self.pnl > 40000 and self.sl < 35000: self.sl = 35000
            # if self.pnl > self.target:
                sl = float(self.pnl) - 500#float(self.pnl)*0.2
                logger.info(f"Trade, update Trade SL: {self.sl}, New SL: {sl}, self.pnl: {self.pnl}")
                if sl > self.sl > 0: self.sl = sl
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
