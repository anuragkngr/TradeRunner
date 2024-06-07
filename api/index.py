import json, logging, pymongo, pandas as pd, numpy as np, pymongo
from order_management_system import OMS, idx_list
from datetime import datetime
from utils import Utils
from option import Option
from dateutil import parser
from time import sleep, time
from tabulate import tabulate
conf = json.load(open("./data/configuration.json"))
oms = OMS()
util = Utils()
now = datetime.now()
client = pymongo.MongoClient(conf['db_url_lcl'])
dblist = client.list_database_names()
mydb = client["tradestore"]
open_high_low = mydb["open_high_low"]
indexes = mydb["indexes"]
options = mydb["options"]
feed = mydb["feed"]

tm = now.strftime("%Y") + "-" + now.strftime("%m") + "-" + now.strftime("%d")
logging.basicConfig(
    level=logging.INFO, filename=f"./logs/{tm}/application_1.log",
    filemode="a", format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()
class Index:
    def __init__(self, index, index_trade_start=None):

        slab = 100 if index == "BANKNIFTY" else 50
        idx = indexes.find_one({'security_id': int(idx_list[index])}, sort=[('LTT', -1)])
        # print(idx)
        self.open = idx["open"] if idx is not None and "open" in idx else -1
        self.high = idx["high"] if idx is not None and "high" in idx else -1
        self.low = idx["low"] if idx is not None and "low" in idx else -1
        self.ltp = idx["LTP"] if idx is not None and "LTP" in idx else -1
        self.close = idx["close"] if idx is not None and "close" in idx else -1
        self.move = float(self.ltp) - float(self.open)
        self.movePercent = self.move * 100 / float(self.ltp)
        if index_trade_start is not None: self.open = index_trade_start
        self.ltt = idx['LTT'] if idx is not None and 'LTT' in idx else parser.parse(util.getDate() + ' ' + util.getTime()[:-3] + ':00')
        if self.move < ((-1)*slab): self.trend = 'D'
        elif self.move > slab: self.trend = 'U'
        else: self.trend = 'N'

        spot = oms.spotStrike(index)
        spot_atm = [spot, spot + slab, spot - slab]

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

            # if op_strike in [22600, 22800]:
            #     print(op_strike)

            if spot < op_strike:
                op = options.find_one({'oi': { '$gt': 0 }, 'security_id': security_id}, sort=[('LTT', -1)])
                # {'$and': [{'oi': { '$gt': 0 }}, {'security_id': 22600}]}
                # {$and: [{oi: { $gt: 0 }}, {security_id: 22600}]}
                op = Option(index, op, op_strike, op_type)
                bear_otm_options.append(op) 
            elif spot > op_strike:
                op = options.find_one({'oi': { '$gt': 0 }, 'security_id': security_id}, sort=[('LTT', -1)])
                op = Option(index, op, op_strike, op_type)
                bull_otm_options.append(op)
            else:
                op = options.find_one({'oi': { '$gt': 0 }, 'security_id': security_id}, sort=[('LTT', -1)])
                op = Option(index, op, op_strike, op_type)
                atm_options.append(op)
            count = count - 1

        all_options = bull_otm_options + atm_options + list(reversed(bear_otm_options))

        # l1 = [op.strike for op in all_options if op.open_high]
        # l2 = [op.strike for op in all_options if op.open_low]

        oi_call = sum(opt.oi for opt in all_options if hasattr(opt, 'oi') and opt.option_type in ['CALL'])
        oi_put = sum(opt.oi for opt in all_options if hasattr(opt, 'oi') and opt.option_type in ['PUT'])

        self.pcr = -1
        if oi_call > 0: self.pcr = round(oi_put/oi_call, 2)

        self.atm_price = sum(float(opt.ltp) for opt in atm_options if opt.strike in spot_atm)/len(spot_atm)

        
        atm_call_oi = sum(float(opt.oi) for opt in atm_options if opt.strike in spot_atm and opt.option_type == 'CALL')
        atm_put_oi = sum(float(opt.oi) for opt in atm_options if opt.strike  in spot_atm and opt.option_type == 'PUT')

        self.atm_pcr = -1

        if atm_call_oi > 0: self.atm_pcr = round(atm_put_oi/atm_call_oi, 2)

        self.indicators = None#oms.getIndicators(index, spot_atm)
        # ohlc_fut = self.indicators['ohlc']
        # self.ltp_fut = ohlc_fut['ltp']
        # self.move_fut = float(ohlc_fut['close']) - float(ohlc_fut['open'])
        # self.movePercent_fut = self.move_fut * 100 / float(ohlc_fut['close'])
        
        self.vwap = -1 if self.indicators is None else (self.indicators['vwap'])/len(spot_atm)
        sma = None if self.indicators is None else self.indicators['sma']
        ema = None if self.indicators is None else self.indicators['ema']
        
        
        self.sma_fast = sma['indicator'] if sma is not None else -1
        self.sma_slow = sma['indicator_2'] if sma is not None else -1
        self.ema_fast = ema['indicator'] if ema is not None else -1
        self.ema_slow = ema['indicator_2'] if ema is not None else -1

        index_ohlc = oms.price_history(index)
        self.pre_open = index_ohlc['open']
        self.pre_high = index_ohlc['high']
        self.pre_low = index_ohlc['low']
        self.pre_close = index_ohlc['close']
        self.pre_move = float(self.pre_close) - float(self.pre_open)
        if self.pre_move < ((-1)*slab): self.pre_trend = 'D'
        elif self.pre_move > slab: self.pre_trend = 'U'
        else: self.pre_trend = 'N'

        self.open_high_list = [opt.to_db() for opt in all_options if opt.open_high]

        # open_high_low.delete_many( {'index': index} )
        
        if len(self.open_high_list) > 0:
            llist = []
            for i in range(len(self.open_high_list)):
                if self.open_high_list[i] not in self.open_high_list[i + 1:]:
                    llist.append(self.open_high_list[i])
            self.open_high_list = llist

        self.open_low_list = [opt.to_db() for opt in all_options if opt.open_low]

        if len(self.open_low_list) > 0:
            llist = []
            for i in range(len(self.open_low_list)):
                if self.open_low_list[i] not in self.open_low_list[i + 1:]:
                    llist.append(self.open_low_list[i])
            self.open_low_list = llist
        
        op_st = op_ty = []

        if len(self.open_high_list) > 0:
            for ohl in self.open_high_list:
                res = open_high_low.find_one_and_update(
                    { 'index': ohl['index'], 'strike': ohl['strike'], 'option_type': ohl['option_type'] },
                    { "$set": ohl }, upsert=True
                )
                op_st.append(ohl['strike'])
                op_ty.append(ohl['option_type'])
            for idx, x in enumerate(op_st):
                open_high_low.delete_one( {'strike': op_st[idx], 'option_type': op_ty[idx]} )
        else: open_high_low.delete_many( {'index': index, 'open_high': True} )

        op_st = op_ty = []
        
        if len(self.open_low_list) > 0:
            for ohl in self.open_low_list:
                res = open_high_low.find_one_and_update(
                    { "strike" : ohl['strike'], 'option_type' : ohl['option_type'] },
                    { "$set": ohl },  upsert=True
                )
                op_st.append(ohl['strike'])
                op_ty.append(ohl['option_type'])
            for idx, x in enumerate(op_st):
                open_high_low.delete_one( {'strike': op_st[idx], 'option_type': op_ty[idx]} )
        else: open_high_low.delete_many( {'index': index, 'open_high': False} )

    def to_dict(self):
        dictObj = self.__dict__
        dictObj.pop('indicators', None)
        return dictObj
    
    def print(self):
        df_ol = pd.DataFrame(self.open_low_list)
        df_ol = df_ol.dropna()
        df_ol = df_ol.drop_duplicates()

        df_oh = pd.DataFrame(self.open_high_list)
        df_oh = df_oh.dropna()
        df_oh = df_oh.drop_duplicates()

        df = []
        if len(df_ol) > 0: df = df_ol.join(df_oh)
        else: df = df_oh.join(df_ol)
        # print(df)

        df = df.replace(np.nan, '--', regex=True)

        # df_ol = df_ol.fillna('NaN', inplace=' - ')
        print(df)
    
    
if __name__ == "__main__": 
    idx = Index('NIFTY')
    # idx.print()

    idx = Index('BANKNIFTY')
    # idx.print()

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