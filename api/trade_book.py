import ast, traceback, numpy as np, json, pandas as pd, logging, pymongo
conf = json.load(open("./data/configuration.json"))
from tabulate import tabulate, SEPARATING_LINE
from datetime import datetime, time
from time import sleep
from index import Index
from trade import Trade
from utils import Utils
from order_management_system import OMS, trade_headers, trade_columns, idx_list
oms = OMS()
util = Utils()
now = datetime.now()
tm = now.strftime("%Y") + "-" + now.strftime("%m") + "-" + now.strftime("%d")
logging.basicConfig(
    level=logging.INFO, filename=f"./logs/{tm}/application.log",
    filemode="a", format="%(asctime)s - %(levelname)s - %(message)s")
client = pymongo.MongoClient(conf['db_url_lcl'])
dblist = client.list_database_names()
if "tradestore" in dblist:
  print("Trade Book 'tradestore' database exists.")
mydb = client["tradestore"]
trades = mydb["trades"]
indexes = mydb["indexes"]
logger = logging.getLogger()

class TradeBook: 
    def __init__(self): 
        self.totalTrades = 0
        self.openTrades = 0
        self.closeTrades = 0
        self.pnl = 0.0
        self.pnlMax = 0.0
        self.pnlMin = 0.0
        self.utilized = 0.0
        self.available = 0.0                
        self.pnlPercent = 0.0
        self.trades = []        
        self.summary = "My Trade Book Runner"
        self.fundUpdate()
        self.finalFlag = False
        self.finalRisk = conf["final_risk"]
        self.target = 0
        self.sl = 0
        self.vix = indexes.find_one({'security_id': int(idx_list['INDIA VIX'])})
        self.nifty = Index('NIFTY')
        self.bank_nifty = Index('BANKNIFTY')
        self.risk = conf["risk"]
        self.reward = conf["reward"]

    def enterTrade(self, trd, fund=None): 
        self.trades.append(trd)
        self.totalTrades += 1
        self.openTrades += 1
        self.fundUpdate(trd, fund)

    def clean(self):
        trds = self.trades
        for trd in trds:
            if trd.status not in ["open"]:
                self.trades.remove(trd)
                self.totalTrades = self.totalTrades - 1
    
    def loadTrades(self, pos): 
        posList=pos.copy()
        s_ids = [x.security_id for x in pos]

        trades_dict = trades.find({'status': 'open'})

        for trd in trades_dict:
            positions = trd['positions']
            trd_pos = []; trd_flag = False
            for position in positions:
                if trd_flag or position['security_id'] in s_ids: trd_flag = True
                if trd_flag:
                    for po in pos:
                        if po.security_id == position['security_id']:
                            po.cost_price = position['cost_price']
                            trd_pos.append(po)
                            if po in posList: posList.remove(po)
                            break
                else: 
                    trades.delete_one({'trade_id': trd['trade_id']})
                    # trades.remove({'trade_id': trd['trade_id']})
            if trd_flag: 
                _trade = Trade(trd_pos, trd['index'], trd['trade_id'])
                self.enterTrade(_trade, trd['margin'])
        return posList

    def setFinalRisk(self):
        if self.finalFlag is False:
            for trd in self.trades:
                if trd.status in ["open"]:
                    trd.sl = float(trd.pnl) - 100.00
                    # trd.step = self.finalRisk
            self.finalFlag = True

    def exitTrade(self, trd):
        trd.status = "close"
        self.openTrades -= 1
        self.closeTrades += 1
        self.trades.remove(trd)
        self.fundUpdate(trd)
        util.deleteTradeStats(trd.trade_id)
        sleep(conf["order_delay"])

    def validateTrade(self, index, pos):
        s_id = [];
        pos_idx = [x for x in pos if x.index == index]
        copy_pos_idx = pos_idx.copy()
        trades_idx = [x for x in self.trades if (x.index == index and x.status == 'open')]
        for trd_idx in trades_idx:
            s_id += [po.security_id for po in trd_idx.positions]

        for i, po in enumerate(copy_pos_idx): 
            if po.security_id in s_id: pos_idx.remove(po)
        if pos_idx:
            trade = Trade(pos_idx, index)
            self.enterTrade(trade)

    def updateIndex(self):
        self.vix = indexes.find_one({'security_id': int(idx_list['INDIA VIX'])})
        self.nifty = Index('NIFTY')
        self.bank_nifty = Index('BANKNIFTY')

    def update(self):  # sourcery skip: low-code-quality
        self.updateIndex()
        pos = oms.positions()
        if len(self.trades) == 0: 
            pos = self.loadTrades(pos)
        # tt = [td.index for td in self.trades if td.status == 'open']
        idx = list(set([po.index for po in pos]))
        if idx: 
            for idx in idx: self.validateTrade(idx, pos)
        for trd in self.trades: 
            trd.update(pos)
        self.pnl = sum(trd.pnl for trd in self.trades if trd.status in ["open"])
        self.sl = sum(trd.sl for trd in self.trades if trd.status in ["open"])
        self.target = sum(float(trd.target) for trd in self.trades if trd.status in ["open"])
        self.pnlMin = sum(float(trd.pnlMin) for trd in self.trades if trd.status in ["open"])
        self.pnlMax = sum(float(trd.pnlMax) for trd in self.trades if trd.status in ["open"])
        self.pnlPercent = (self.pnl*100/float(self.utilized)) if float(self.utilized) > 0.0 else 0.0

    def fundUpdate(self, trd=None, fund=None) -> None:
        margin = 0.0
        limit = oms.getFundLimits()
        # print(limit)
        utilized = limit['utilizedAmount'] if 'utilizedAmount' in limit else -1
        if trd is None or self.openTrades == 1:
            margin = self.utilized = utilized
        else:
            othertrade = self.utilized
            self.utilized = float(utilized)
            margin = self.utilized - float(othertrade)
        self.available = float(limit['availabelBalance'])
        if trd is not None: 
            trd.margin = fund if fund is not None else margin
        return margin

    def printTrades(self):  # sourcery skip: extract-duplicate-method
        trade = note = []
        for trd in self.trades:
            if trd.status == "open":
                tmp = trd.to_dict()
                df = pd.DataFrame(tmp)
                if not trade: 
                    trade = df.values.tolist()
                else: 
                    # trade.append(SEPARATING_LINE)
                    trade = trade + df.values.tolist()
                tmp = trd.print()
                df = pd.DataFrame(tmp)
                if not note: 
                    note = df.values.tolist()
                else: 
                    # note.append(SEPARATING_LINE)
                    note = note + df.values.tolist()
        if len(note) > 0:
            dframe = tabulate(note, trade_columns, tablefmt="simple_outline", floatfmt=".2f")
            logger.info('Notes response: ' + str(note))
            print(dframe)

        dframe = tabulate(trade, trade_headers, tablefmt="rounded_outline", floatfmt=".2f")
        logger.info('Trades response: ' + str(trade))
        if self.openTrades < 4: print(dframe)

    def print(self):
        self.update()
        for _ in range(4): print()
        # self.printTrades()
        if self.openTrades > 0:
            data = [
                {
                    1: f"{'VIX: ' + str(round(float(self.vix['LTP']), 2)) + ' (' + str(round((float(self.vix['LTP']) - float(self.vix['open'])), 2)) + ')'}",
                    2: f"{'NIFTY: ' + str(round(float(self.nifty.ltp), 2)) + ' (' + str(round(float(self.nifty.move), 2)) + ') (' + str(self.nifty.pcr) + ')'}",
                    3: f"{'BANKNIFTY: ' + str(round(float(self.bank_nifty.ltp), 2)) + ' (' + str(round(float(self.bank_nifty.move), 2)) + ') (' + str(self.bank_nifty.pcr) + ')'}",
                    # 4: f"{'FINNIFTY: ' + str(round(self.fin_nifty.spot, 2)) + ' (' + str(round(self.fin_nifty.move, 2)) + ')'}",
                },
                {
                    1: f"{'P&L(' + str(round(self.openTrades)) + '): ' + str(round(self.pnl)) + ' (' + str(round(self.pnlPercent, 1)) + '%)'}",
                    2: f"{'SL: ' + str(round(self.sl)) + ' (' + str(round(self.risk, 1)) + '%)'}",
                    3: f"{'TARGET: ' + str(round(self.target)) + ' (' + str(round(self.reward, 1)) + '%)'}",
                    # 4: f"{'MAX/MIN: (' + str(round(self.pnlMax)) + ' / ' + str(round(self.pnlMin)) + ')'}",
                }
            ]
            df = pd.DataFrame(data)
            dframe = tabulate(df.values.tolist(), tablefmt="mixed_grid", floatfmt=".2f")
            print(dframe)
            self.printTrades()
        
    def to_dict(self):
        return self.__dict__
    
if __name__ == "__main__": 
    pos = json.load(open('./data/positions.json'))['data']
