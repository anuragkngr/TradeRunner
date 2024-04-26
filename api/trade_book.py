import ast, traceback, numpy as np, json, pandas as pd, logging
conf = json.load(open("./data/configuration.json"))
from tabulate import tabulate, SEPARATING_LINE
from datetime import datetime, time
# from logzero import logger
from trade import Trade
from utils import Utils
from order_management_system import OMS, idx_list, trade_headers
oms = OMS()
util = Utils()
now = datetime.now()
tm = now.strftime("%Y") + "-" + now.strftime("%m") + "-" + now.strftime("%d")
logging.basicConfig(
    level=logging.INFO, filename=f"./logs/{tm}/application.log",
    filemode="w", format="%(asctime)s - %(levelname)s - %(message)s")
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

    def enterTrade(self, trd): 
        self.trades.append(trd)
        self.totalTrades += 1
        self.openTrades += 1
        self.fundUpdate(trd)
        util.updateTrade(trd)
        # trd.update()

    def clean(self):
        trds = self.trades
        for trd in trds:
            if trd.status not in ["open"]:
                self.trades.remove(trd)
                self.totalTrades = self.totalTrades - 1
    
    def loadTrades(self, pos): 
        dic_data = [];posList=[]
        with open("./data/margin.txt", "r") as fileStore:
            dic_data = fileStore.readline()
            fileStore.close()
        if isinstance(dic_data, str) and dic_data.strip() != "": 
                dic_data = ast.literal_eval(dic_data)
        for idx in dic_data:
            posList = []
            if float(dic_data[idx]) > 0:
                for po in pos: 
                    if idx == po.index: 
                        for po_inn in pos: 
                            if idx == po_inn.index: posList.append(po_inn)
                        break
            if posList:
                trd = Trade(posList, idx)
                self.trades.append(trd)
                trd.margin = dic_data[idx]
                if float(trd.margin) <= 0.0:
                    trd.margin = self.fundUpdate(trd)
                self.totalTrades += 1
                self.openTrades += 1
            else: dic_data[idx] = 0.0
        try:
            with open("./data/margin.txt", "w") as fileStore:
                res = fileStore.write(str(dic_data))
                fileStore.close()
        except Exception:
            print(traceback.format_exc())
            logger.error(f"trade book, loadTrades {traceback.format_exc()}")

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
        time.sleep(conf["order_delay"])

    def validateTrade(self, pos):
        idxList = list(idx_list.keys())
        ids = idxList.copy()
        for trd in self.trades:
            if trd.index in ids:
                idxList.remove(trd.index)
        ids = idxList.copy()
        for idx in ids:
            flag = True
            for po in pos:
                if idx == po.index:
                    flag = False
                    break
            if flag: idxList.remove(idx)
        # flag = any((po.symbolname for po in pos) == (trd.index for trd in self.trades))
        return idxList

    def update(self):  # sourcery skip: low-code-quality
        pos = oms.positions()
        if len(self.trades) == 0: self.loadTrades(pos)
        # if len(self.trades) == 0: self.util.priceUpdateAPI(self.trades)
        pnl = 0.0
        resp = self.validateTrade(pos)
        if len(resp) > 0:
            for idx in resp:
                trade = Trade(pos, idx)
                self.enterTrade(trade)
        else:
            for trd in self.trades: 
                trd.update(pos)
        self.pnl = sum(trd.pnl for trd in self.trades if trd.status in ["open"])
        self.sl = sum(trd.sl for trd in self.trades if trd.status in ["open"])
        self.target = sum(float(trd.target) for trd in self.trades if trd.status in ["open"])
        self.pnlMin = sum(float(trd.pnlMin) for trd in self.trades if trd.status in ["open"])
        self.pnlMax = sum(float(trd.pnlMax) for trd in self.trades if trd.status in ["open"])
        self.pnlPercent = (self.pnl*100/float(self.utilized)) if float(self.utilized) > 0.0 else 0.0

    def fundUpdate(self, trd=None) -> None:
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
            if isinstance(trd, dict): 
                trd["margin"] = margin
            else: trd.margin = margin
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
                    trade.append(SEPARATING_LINE)
                    trade = trade + df.values.tolist()
                tmp = trd.print()
                df = pd.DataFrame(tmp)
                if not note: 
                    note = df.values.tolist()
                else: 
                    note.append(SEPARATING_LINE)
                    note = note + df.values.tolist()
        dframe = tabulate(trade, trade_headers, tablefmt="rounded_outline", floatfmt=".2f")
        logger.info('Trades response: ' + str(trade))
        print(dframe)
        dframe = tabulate(note, tablefmt="mixed_outline", floatfmt=".2f")
        logger.info('Notes response: ' + str(note))
        print(dframe)

    def print(self):
        self.update()
        for _ in range(4): print()
        self.printTrades()
        if self.openTrades > 0:
            data = f"""[['Open Trades: {str(self.openTrades)}', 'Fund: {str(round(float(self.utilized), 2))}', 
            'P&L: {str(round(float(self.pnl)))}', 'P&L %: ({str(round(float(self.pnlPercent), 2))})', 
            'Target: {str(round(float(self.target)))}', 'SL: ({str(round(float(self.sl), 2))})', 
            'P&L-Min: {str(round(float(self.pnlMin), 2))}', 'P&L-Max: {str(round(float(self.pnlMax), 2))}']]"""
            data = ast.literal_eval(data)
            dframe = tabulate(data, tablefmt="heavy_grid", floatfmt=".2f")
            print(dframe)
        
    def to_dict(self):
        return self.__dict__
    
if __name__ == "__main__": 
    pos = json.load(open('./data/positions.json'))['data']
    # poss = Positions(pos)
    # trd = Trade(poss.positions)
    # book.fundUpdate(dhan)
    # pos = dhan.get_fund_limits()
    # pos = json.load(open('./data/positions.json'))['data']
    # book = TradeBook()
    # book.enterTrade
    # print(pos)
    exit()
# {'Open Trades: ': str(self.openTrades)},
# {'Fund: ': str(round(float(self.utilized), 2))},
# {'P&L: ': str(round(float(self.pnl), 2))},
# {'P&L %: ': str(round(float(self.pnlPercent), 2))},
# {'SL: ': str(round(float(self.sl), 2))},
# {'Target: ': str(round(float(self.target), 2))},
# {'P&L-Min: ': str(round(float(self.pnlMin), 2))},
# {'P&L-Max: ': str(round(float(self.pnlMax), 2))},