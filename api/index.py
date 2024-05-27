import json, logging, pymongo, pandas as pd
from order_management_system import OMS, idx_list
from datetime import datetime
from utils import Utils
from option import Option
from tabulate import tabulate
conf = json.load(open("./data/configuration.json"))
oms = OMS()
util = Utils()
now = datetime.now()
tm = now.strftime("%Y") + "-" + now.strftime("%m") + "-" + now.strftime("%d")
logging.basicConfig(
    level=logging.INFO, filename=f"./logs/{tm}/application_1.log",
    filemode="a", format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()
client = pymongo.MongoClient(conf['db_url_lcl'])
dblist = client.list_database_names()
mydb = client["tradestore"]
indexes = mydb["indexes"]
options = mydb["options"]
feed = mydb["feed"]
class Index:
    def __init__(self, index, index_trade_start=None):

        slab = 100 if index == "BANKNIFTY" else 50
        idx = indexes.find_one({'security_id': int(idx_list[index])}, sort=[('_id', -1)])
        self.open = idx["open"] if "open" in idx else -1
        self.high = idx["high"] if "high" in idx else -1
        self.low = idx["low"] if "low" in idx else -1
        self.ltp = idx["LTP"] if "LTP" in idx else -1
        self.close = idx["close"] if "close" in idx else -1
        self.move = float(self.close) - float(self.open)
        self.movePercent = self.move * 100 / float(self.close)
        if index_trade_start is not None: self.open = index_trade_start
        self.ltt = idx["LTT"] if "LTT" in idx else -1
        if self.move < ((-1)*slab): self.trend = 'D'
        elif self.move > slab: self.trend = 'U'
        else: self.trend = 'N'

        spot = oms.spotStrike(index)
        
        s_id = int(idx_list[index])
        stk_sid = []
        
        res = list(feed.find({'index': index}, sort=[('strike', 1)]))
        
        for e in res: 
            stk_sid.append({'strike': e['strike'], 'security_id': e['security_id'], 'symbol': e['symbol']})
        
        bull_otm_options = atm_options = bear_otm_options = all_options = []
        
        count = len(stk_sid)

        for opt in stk_sid:
            security_id = int(opt['security_id'])
            op_type = opt['symbol']
            op_type = 'PUT' if op_type.endswith('PUT') else 'CALL'
            op_strike = opt['strike']

            if spot < op_strike:
                op = options.find_one({'$and': [{'oi': { '$gt': 0 }}, {'security_id': security_id}]}, sort=[('_id', -1)])
                # {'$and': [{'oi': { '$gt': 0 }}, {'security_id': security_id}]}
                op = Option(index, op, op_strike, op_type)
                bear_otm_options.append(op) 
            elif spot > op_strike:
                op = options.find_one({'$and': [{'oi': { '$gt': 0 }}, {'security_id': security_id}]}, sort=[('_id', -1)])
                op = Option(index, op, op_strike, op_type)
                bull_otm_options.append(op)
            else:
                op = options.find_one({'$and': [{'oi': { '$gt': 0 }}, {'security_id': security_id}]}, sort=[('_id', -1)])
                op = Option(index, op, op_strike, op_type)
                atm_options.append(op)
            count = count - 1

        all_options = bull_otm_options + atm_options + list(reversed(bear_otm_options))

        oi_call = sum(opt.oi for opt in all_options if hasattr(opt, 'oi') and opt.option_type in ['CALL'])
        oi_put = sum(opt.oi for opt in all_options if hasattr(opt, 'oi') and opt.option_type in ['PUT'])

        self.pcr = -1
        if oi_call > 0: self.pcr = round(oi_put/oi_call, 2)

        self.straddle_price = sum(float(opt.ltp) for opt in atm_options if opt.strike == spot)

        self.indicators = oms.getIndicators(index, spot)
        # ohlc_fut = self.indicators['ohlc']
        # self.ltp_fut = ohlc_fut['ltp']
        # self.move_fut = float(ohlc_fut['close']) - float(ohlc_fut['open'])
        # self.movePercent_fut = self.move_fut * 100 / float(ohlc_fut['close'])
        
        self.vwap = self.indicators['vwap']
        sma = self.indicators['sma']
        ema = self.indicators['ema']
        
        
        self.sma_fast = sma['indicator']
        self.sma_slow = sma['indicator_2']
        self.ema_fast = ema['indicator']
        self.ema_slow = ema['indicator_2']

        index_ohlc = oms.price_history(index)
        self.pre_open = index_ohlc['open']
        self.pre_high = index_ohlc['high']
        self.pre_low = index_ohlc['low']
        self.pre_close = index_ohlc['close']
        self.pre_move = float(self.pre_close) - float(self.pre_open)
        if self.pre_move < ((-1)*slab): self.pre_trend = 'D'
        elif self.pre_move > slab: self.pre_trend = 'U'
        else: self.pre_trend = 'N'

        self.open_high_list = [opt.to_dict() for opt in all_options if opt.open_high]
        self.open_low_list = [opt.to_dict() for opt in all_options if opt.open_low]
        

    def to_dict(self):
        dictObj = self.__dict__
        dictObj.pop('indicators', None)
        return dictObj
    
    def print(self):
        df_ol = pd.DataFrame(self.open_low_list)

        df_ol = df_ol.dropna()
        # return df_ol
        print(df_ol)
    
    
if __name__ == "__main__": 
    idx = Index('NIFTY')

    idx.print()
    exit(0)
    # print(idx)
    # top = idx.open_low_list
    # top = idx.open_high_list
    df_oh = pd.DataFrame(idx.open_high_list)
    df_ol = pd.DataFrame(idx.open_low_list)
    # print(df_ol)
    # exit()
    df_ol = df_ol.head(5).join(df_oh.head(5))

    oh_list = []; ol_list = []

    print(df_ol)
    exit()
    data = [
                {
                    1: f"",
                    2: f"{'PRE (' + str(self.nifty.trend) + '): ' + str(round(float(self.nifty.pre_close))) + ' (' + str(round(float(self.nifty.pre_move))) + ')'}",
                    3: f"{'ATM: ' + str(round(float(self.nifty.straddle_price))) + ', VWAP: ' + str(round(float(self.nifty.vwap))) 
                         + ', EMA: ' + str(round(float(self.nifty.ema_fast - self.nifty.ema_slow)))}",
                },
                {
                    1: f"{'BANKN (' + str(self.bank_nifty.trend) + '): ' + str(round(float(self.bank_nifty.close))) + ' (' + str(round(float(self.bank_nifty.move))) + ') [' + str(self.bank_nifty.pcr) + ']'}",
                    2: f"{'PRE (' + str(self.bank_nifty.trend) + '): ' + str(round(float(self.bank_nifty.pre_close))) + ' (' + str(round(float(self.bank_nifty.pre_move))) + ') '}",
                    3: f"{'ATM: ' + str(round(float(self.bank_nifty.straddle_price))) + ', VWAP: ' + str(round(float(self.bank_nifty.vwap))) 
                         + ', EMA: ' + str(round(float(self.bank_nifty.ema_fast - self.bank_nifty.ema_slow)))}",
                    # 4: f"{'O=H: (' + str(self.bank_nifty.open_high_list) + '), O=L: (' + str(self.bank_nifty.open_high_list) + ')'}",
                    
                }
        ]
    print(json.dumps(idx.to_dict()))