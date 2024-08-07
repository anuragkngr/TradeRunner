import ast, traceback, numpy as np, json, logging, pandas as pd, pymongo
conf = json.load(open("./data/configuration.json"))
from datetime import datetime, time
now = datetime.now()
tm = now.strftime("%Y") + "-" + now.strftime("%m") + "-" + now.strftime("%d")
logging.basicConfig(
    level=logging.INFO, filename=f"./logs/{tm}/application.log",
    filemode="a", format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()
from utils import Utils
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
        self.rnr = conf["rnr_flag"]
        if self.rnr: self.rnr = self.risk != 0.0 and self.reward != 0.0
        self.step = conf["step"]
        self.target = conf["profit"]
        self.sl = conf["loss"]
        if self.rnr: self.sl = self.sl ** 3
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

        # self.updated_at = self.created_at = datetime.now()
        # self.updateTrade()
        # util.addTradeStats({'index': self.index, 'trade_id': self.trade_id, 
        #             'sl': self.sl, 'target': self.target, 'margin': self.margin})

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
            "P&L": po.pnl,
            "COST": po.cost_price,
            "PRICE": po.price,
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

    def update(self, positions, finalFlag):

        set_pnl = util.getTradeDetails(self.trade_id)
        if set_pnl is not None:
            if self.sl < set_pnl['sl']:  self.sl = set_pnl['sl']
            if self.target > set_pnl['target']: self.target = set_pnl['target']
            if self.margin > 0:
                self.risk = (100*abs(self.sl))/self.margin
                self.reward = (100*abs(self.target))/self.margin
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
        # rnr = conf['rnr_retio'].split('-')
        sl = self.sl
        if not finalFlag:
            if self.pnl > 500:# and self.margin > 0:
                sl = self.pnl - 999#-(self.margin*self.risk)/(100*2)
            # elif self.pnl > self.target/2:
            #     sl = self.pnl/2
            elif self.pnl > self.target: 
                sl = self.pnl - 500
            if sl > self.sl: self.sl = sl

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
