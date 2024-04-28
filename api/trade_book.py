import ast, traceback, numpy as np, json, pandas as pd, logging
conf = json.load(open("./data/configuration.json"))
from tabulate import tabulate, SEPARATING_LINE
from datetime import datetime, time
from vix import Vix
from trade import Trade
from utils import Utils
from order_management_system import OMS, idx_list, trade_headers
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
        vix = oms.ohlc('INDIA VIX')
        self.vix = Vix(vix)
        self.risk = conf["risk"]
        self.reward = conf["reward"]

    def enterTrade(self, trd, fund=None): 
        self.trades.append(trd)
        self.totalTrades += 1
        self.openTrades += 1
        self.fundUpdate(trd, fund)
        util.updateTrade(trd)
        # trd.update()

    def clean(self):
        trds = self.trades
        for trd in trds:
            if trd.status not in ["open"]:
                self.trades.remove(trd)
                self.totalTrades = self.totalTrades - 1
    
    def loadTrades(self, pos): 
        dic_data = [];posList=pos.copy()
        s_ids = [x.security_id for x in pos]
        with open("./data/margin.txt", "r") as fileStore:
            dic_data = fileStore.readline()
            fileStore.close()
        if isinstance(dic_data, str) and dic_data.strip() != "": 
                dic_data = ast.literal_eval(dic_data)
        for idx in dic_data:
            idxPosList = [x for x in pos if x.index == idx]
            index_data = dic_data[idx]['trades']
            _copy = index_data.copy()
            for _trd in index_data:
                trd_pos = []
                trd_flag = False
                for _po in _trd['position']:
                    if not trd_flag and _po['security_id'] in s_ids:
                        for po in idxPosList:
                            if po.security_id == _po['security_id']:
                                if po.quantity == _po['quantity']:
                                    trd_pos.append(po)
                                    posList.remove(po)
                                else:
                                    _copy.remove(_trd)
                                    trd_flag = True
                                    break
                    if trd_flag: break
                if not trd_flag:
                    _trade = Trade(trd_pos, idx, _trd['trade_id'])
                    self.enterTrade(_trade, _trd['margin'])
            dic_data[idx]['trades'] = _copy
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
        return idxList

    def update(self):  # sourcery skip: low-code-quality
        vix = oms.ohlc('INDIA VIX')
        self.vix = Vix(vix)
        pos = oms.positions()
        if len(self.trades) == 0: pos = self.loadTrades(pos)
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
        dframe = tabulate(note, tablefmt="simple_outline", floatfmt=".2f")
        logger.info('Notes response: ' + str(note))
        print(dframe)

    def print(self):
        self.update()
        for _ in range(4): print()
        self.printTrades()
        if self.openTrades > 0:
            data = [
                {
                    1: f"{'VIX ' + str(round(self.vix.close, 2)) + ': (' + str(round(self.vix.movePercent, 2)) + '%) ' + str(round(self.vix.move, 2))}",
                    2: f"{'P&L(' + str(round(self.openTrades)) + '): ' + str(round(self.pnl)) + ' (' + str(round(self.pnlPercent, 1)) + '%)'}",# Fund=' + str(round(self.utilized))}",
                    3: f"{'SL: ' + str(round(self.sl)) + ' (' + str(round(self.risk, 1)) + '%)'}",
                    4: f"{'TARGET: ' + str(round(self.target)) + ' (' + str(round(self.reward, 1)) + '%)'}",
                    5: f"{str(round(self.pnlMax)) + '(x)/' + str(round(self.pnlMin)) + '(n)'}",
                }
            ]
            df = pd.DataFrame(data)
            dframe = tabulate(df.values.tolist(), tablefmt="mixed_outline", floatfmt=".2f")
            print(dframe)
        
    def to_dict(self):
        return self.__dict__
    
if __name__ == "__main__": 
    pos = json.load(open('./data/positions.json'))['data']
