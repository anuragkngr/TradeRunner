import ast, traceback, numpy as np, json, pandas as pd, logging
conf = json.load(open("./data/configuration.json"))
from tabulate import tabulate, SEPARATING_LINE
from datetime import datetime, time
from time import sleep
from index import Index
from trade import Trade
from utils import Utils
from order_management_system import OMS, trade_headers, trade_columns
oms = OMS()
util = Utils()
now = datetime.now()
tm = now.strftime("%Y") + "-" + now.strftime("%m") + "-" + now.strftime("%d")
logging.basicConfig(
    level=logging.INFO, filename=f"./logs/{tm}/application.log",
    filemode="a", format="%(asctime)s - %(levelname)s - %(message)s")
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
        spot = oms.price('INDIA VIX', True)
        self.vix = Index(spot)
        spot = oms.price('NIFTY', True)
        self.nifty = Index(spot)
        spot = oms.price('BANKNIFTY', True)
        self.bank_nifty = Index(spot)
        # spot = oms.price('FINNIFTY', True)
        # self.fin_nifty = Index(spot)
        self.risk = conf["risk"]
        self.reward = conf["reward"]

    def enterTrade(self, trd, fund=None): 
        self.trades.append(trd)
        self.totalTrades += 1
        self.openTrades += 1
        self.fundUpdate(trd, fund)
        util.updateTrade(trd)

    def clean(self):
        trds = self.trades
        for trd in trds:
            if trd.status not in ["open"]:
                self.trades.remove(trd)
                self.totalTrades = self.totalTrades - 1
    
    def loadTrades(self, pos): 
        dic_data = [];
        posList=pos.copy()
        s_ids = [x.security_id for x in pos]
        with open("./data/margin.txt", "r") as fileStore:
            dic_data = fileStore.readline()
            fileStore.close()
        if isinstance(dic_data, str) and dic_data.strip() != "": 
            dic_data = ast.literal_eval(dic_data)
        else: dic_data = {'NIFTY': {'margin': 0, 'trades': []}, 'BANKNIFTY': {'margin': 0, 'trades': []}, 
                          'FINNIFTY': {'margin': 0, 'trades': []}, 'NIFTYMCAP50': {'margin': 0, 'trades': []}, 
                          'SENSEX': {'margin': 0, 'trades': []}, 'BANKEX': {'margin': 0, 'trades': []}}
        for idx in dic_data:
            idxPosList = [x for x in pos if x.index == idx]
            idx_trades = dic_data[idx]['trades']
            _copy_idx_trades = idx_trades.copy()
            for idx_trd in idx_trades:
                trd_pos = []
                trd_flag = False
                for _po in idx_trd['position']:
                    if _po['security_id'] not in s_ids: trd_flag = True
                    if not trd_flag and _po['security_id'] in s_ids:
                        for po in idxPosList:
                            if po.security_id == _po['security_id']:
                                if po.quantity == _po['quantity']:
                                    po.cost_price = _po['cost_price']
                                    trd_pos.append(po)
                                    if po in posList: posList.remove(po)
                                else:
                                    trd_flag = True
                                    break
                    if trd_flag: 
                        break
                if trd_flag: 
                    _copy_idx_trades.remove(idx_trd)
                    break
                else:
                    _trade = Trade(trd_pos, idx, idx_trd['trade_id'])
                    self.enterTrade(_trade, idx_trd['margin'])
            dic_data[idx]['trades'] = _copy_idx_trades
        try:
            with open("./data/margin.txt", "w") as fileStore:
                res = fileStore.write(str(dic_data))
                fileStore.close()
        except Exception:
            print(traceback.format_exc())
            logger.error(f"trade book, loadTrades {traceback.format_exc()}")
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
        sleep(conf["order_delay"])

    def validateTrade(self, index, pos):
        s_id = [];
        pos_idx = [x for x in pos if x.index == index]
        copy_pos_idx = pos_idx.copy()
        trades_idx = [x for x in self.trades if x.index == index]
        for trd_idx in trades_idx:
            s_id += [po.security_id for po in trd_idx.positions]

        for i, po in enumerate(copy_pos_idx): 
            if po.security_id in s_id: pos_idx.remove(po)
        if pos_idx:
            trade = Trade(pos_idx, index)
            self.enterTrade(trade)

    def updateIndex(self):
        spot = oms.price('INDIA VIX', True)
        self.vix = Index(spot)
        spot = oms.price('NIFTY', True)
        self.nifty = Index(spot)
        spot = oms.price('BANKNIFTY', True)
        self.bank_nifty = Index(spot)
        # spot = oms.price('FINNIFTY', True)
        # self.fin_nifty = Index(spot)

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
                    1: f"{'VIX: ' + str(round(self.vix.spot, 2)) + ' (' + str(round(self.vix.move, 2)) + ')'}",
                    2: f"{'NIFTY: ' + str(round(self.nifty.spot, 2)) + ' (' + str(round(self.nifty.move, 2)) + ')'}",
                    3: f"{'BANKNIFTY: ' + str(round(self.bank_nifty.spot, 2)) + ' (' + str(round(self.bank_nifty.move, 2)) + ')'}",
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
