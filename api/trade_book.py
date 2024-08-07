import ast, traceback, numpy as np, json, pandas as pd, logging, pymongo, time
conf = json.load(open("./data/configuration.json"))
from tabulate import tabulate, SEPARATING_LINE
from datetime import datetime#, time
from time import sleep
from index import Index
from trade import Trade
from utils import Utils
from order_management_system import OMS, trade_headers, trade_columns, idx_list, option_headers
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
        # trades.delete_many({})
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
        self.reload_start_time_sec = time.time()

    def enterTrade(self, trd, fund=None): 
        self.trades.append(trd)
        self.totalTrades += 1
        self.openTrades += 1
        self.fundUpdate(trd, fund)
        if trd.rnr:
            trd.sl = trd.risk*trd.margin/100
            trd.target = trd.reward*trd.margin/100
            trd.rnr = False
        util.addTradeStats({'index': trd.index, 'trade_id': trd.trade_id, 
                    'sl': trd.sl, 'target': trd.target, 'margin': trd.margin})

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
                            po.price = position['price']
                            po.pnl = position['pnl']
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
                    if float(trd.pnl) > 100: trd.sl = float(trd.pnl) - 100.00
                    else : trd.sl = float(trd.pnl)
                    # trd.step = self.finalRisk
            self.finalFlag = True

    def exitTrade(self, trd):
        trd.status = "close"
        self.openTrades -= 1
        self.closeTrades += 1
        self.trades.remove(trd)
        self.fundUpdate(trd)
        util.deleteTradeStats(trd.trade_id)
        trd.updateTrade()

    def exitTrades(self):
        for trd in self.trades:
            if trd.status == 'open': 
                oms.closeTrade(trd)
                self.exitTrade(trd)

    def clean(self):
        trds = self.trades
        trade_update_list = []
        for trd in trds:
            if trd.status not in ["open"]:
                self.trades.remove(trd)
                self.totalTrades = self.totalTrades - 1
            else: trade_update_list.append(trd.trade_id)
        res = trades.find_one_and_update(
                { "trade_id" : {'$nin': trade_update_list} },
                { "$set": {'status': 'close'} }
            )
        
        trd_ar = [int(td.trade_id) for td in self.trades if trd.status in ["open"]]
        util.pnlCleanup(trd_ar)
            
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
        
        return copy_pos_idx

    def updateIndex(self):
        # if (time.time() - self.reload_start_time_sec) > conf['reload_start_time_sec']:
            self.vix = indexes.find_one({'security_id': int(idx_list['INDIA VIX'])})
            self.nifty = Index('NIFTY')
            self.bank_nifty = Index('BANKNIFTY')
            self.reload_start_time_sec = time.time()

    def update(self):  # sourcery skip: low-code-quality
        # if (time.time() - self.reload_start_time_sec) > conf['reload_start_time_sec']: 
        self.updateIndex()

        pos = oms.positions(True)
        if len(self.trades) == 0: 
            pos = self.loadTrades(pos)
        # tt = [td.index for td in self.trades if td.status == 'open']
        idx = list(set([po.index for po in pos]))
        if idx: 
            for idx in idx: self.validateTrade(idx, pos.copy())
        for trd in self.trades: 
            trd.update(pos, self.finalFlag)
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
        data = [
            {
                1: f"{'NIFT (' + str(self.nifty.trend) + '): ' + str(round(float(self.nifty.ltp))) + ' (' + str(round(float(self.nifty.move))) + '/' + str(round(float(self.nifty.gap_up_down))) + ') pcr=' + str(self.nifty.atm_pcr) + '/' + str(self.nifty.pcr)}",
                2: f"{'ATM: p=' + str(round(float(self.nifty.atm_price))) + ' v=' + str(round(float(self.nifty.vwap)))}",
                3: f"{'OTM: p=' + str(round(float(self.nifty.otm_price))) + ' v=' + str(round(float(self.nifty.vwap_otm)))}",
                4: f"{'PRE (' + str(self.nifty.pre_trend) + '): ' + str(round(float(self.nifty.pre_move)))}",
            },
            {
                1: f"{'BANK (' + str(self.bank_nifty.trend) + '): ' + str(round(float(self.bank_nifty.ltp))) + ' (' + str(round(float(self.bank_nifty.move))) + '/' + str(round(float(self.bank_nifty.gap_up_down))) + ') pcr=' + str(self.bank_nifty.atm_pcr) + '/' + str(self.bank_nifty.pcr)}",
                2: f"{'ATM: p=' + str(round(float(self.bank_nifty.atm_price))) + ' v=' + str(round(float(self.bank_nifty.vwap)))}",
                3: f"{'OTM: p=' + str(round(float(self.bank_nifty.otm_price))) + ' v=' + str(round(float(self.bank_nifty.vwap_otm)))}",
                    #  + ') EMA: ' + str(round(float(self.bank_nifty.ema_fast - self.bank_nifty.ema_slow)))}",
                # 4: f"{'O=H: (' + str(self.bank_nifty.open_high_list) + '), O=L: (' + str(self.bank_nifty.open_high_list) + ')'}",
                4: f"{'PRE (' + str(self.bank_nifty.pre_trend) + '): ' + str(round(float(self.bank_nifty.pre_move)))}",
                
            },
            {
                1: f"{'VIX: ' + str(round(float(self.vix['close'] if self.vix is not None else -1), 2)) + ' (' + str(round((float(self.vix['LTP'] if self.vix is not None else -1) - float(self.vix['open'] if self.vix is not None else -1)), 2)) + ')'}",
                2: f"{'P&L(' + str(round(self.openTrades)) + '): ' + str(round(self.pnl)) + ' (' + str(round(self.pnlPercent, 1)) + '%)'}",
                3: '--',
                4: '--'
                # 3: f"{'SL: ' + str(round(self.sl)) + ' (' + str(round(self.risk)) + '%) - TGT: ' + str(round(self.target))}",
                # 4: f"{'TARGET: ' + str(round(self.target)) + ' (' + str(round(self.reward)) + '%)'}",
                # 4: f"{'MAX/MIN: (' + str(round(self.pnlMax)) + ' / ' + str(round(self.pnlMin)) + ')'}",
            }
        ]
        df = pd.DataFrame(data)
        dframe = tabulate(df.values.tolist(), tablefmt="mixed_grid", floatfmt=".2f")
        print(dframe)
    
        if self.openTrades > 0: self.printTrades()

            # df = pd.concat([self.nifty.print(), self.bank_nifty.print()])
            # dframe = tabulate(df.values.tolist(), option_headers, tablefmt="simple_outline", floatfmt=".2f")
            # print(dframe)
        
    def to_dict(self):
        return self.__dict__
    
if __name__ == "__main__": 
    pos = json.load(open('./data/positions.json'))['data']
