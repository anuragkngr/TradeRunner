import json, logging, pymongo
from order_management_system import OMS, idx_list
from datetime import datetime
from utils import Utils
from option import Option
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
        self.close = self.ltp#idx["close"] if "close" in idx else -1
        self.move = float(self.close) - float(self.open)
        self.movePercent = self.move * 100 / float(self.close)
        if index_trade_start is not None: self.open = index_trade_start
        self.ltt = idx["LTT"] if "LTT" in idx else -1
        if self.move < ((-1)*slab): self.trend = 'bear'
        elif self.move > slab: self.trend = 'bull'
        else: self.trend = 'neutral'

        spot = oms.spotStrike(index)
        
        s_id = int(idx_list[index])
        stk_sid = []
        
        res = list(feed.find({'index': index}, sort=[('strike', 1)]))
        
        for e in res: 
            stk_sid.append({'strike': e['strike'], 'security_id': e['security_id'], 'symbol': e['symbol']})
        
        # res = options.find_one({'security_id': s_id}, sort=[('_id', -1)])
        # res = options.find_one({'$and': [{'security_id': s_id}, 
        #                              {'$or': [{'oi': { '$gt': 0 }}, {'OI': { '$gt': 0 }}] }
        #                              ]}, sort=[('_id', -1)])
        
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

        self.indicators = oms.getIndicators(index)
        index_ohlc = conf[index]
        self.pre_open = index_ohlc['open']
        self.pre_high = index_ohlc['high']
        self.pre_low = index_ohlc['low']
        self.pre_close = index_ohlc['close']
        self.pre_move = float(self.pre_close) - float(self.pre_open)
        if self.pre_move < ((-1)*slab): self.pre_trend = 'bear'
        elif self.pre_move > slab: self.pre_trend = 'bull'
        else: self.pre_trend = 'neutral'

    def to_dict(self):
        return self.__dict__
    
if __name__ == "__main__": 
    print()