import json, logging
from order_management_system import OMS, fut_list
from datetime import datetime
from utils import Utils
conf = json.load(open("./data/configuration.json"))
oms = OMS()
util = Utils()
now = datetime.now()
tm = now.strftime("%Y") + "-" + now.strftime("%m") + "-" + now.strftime("%d")
logging.basicConfig(
    level=logging.INFO, filename=f"./logs/{tm}/application_1.log",
    filemode="a", format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()
class Index:
    def __init__(self, index, index_trade_start=None):
        self.open = index["open"] if "open" in index else -1
        self.high = index["high"] if "high" in index else -1
        self.low = index["low"] if "low" in index else -1
        self.spot = self.close = index["close"] if "close" in index else -1
        self.move = float(self.close) - float(self.open)
        self.movePercent = self.move * 100 / float(self.close)
        if index_trade_start is not None: self.open = index_trade_start
    def to_dict(self):
        return self.__dict__
        # return json.dumps(self.__dict__)
    
if __name__ == "__main__": 
    # print("BANKNIFTY-Mar2024-48000-CE")
    # f"{'NIFTY: ' + str(round(self.nifty.spot, 2)) + ' (' + str(round(self.nifty.move, 2)) + ')'}"
    index = 'BANKNIFTY'
    res = oms.price(fut_list[index], False, True, 'FUTIDX')
    # res = oms.price(index, True, True)
    logger.info('FUTIDX: ' + json.dumps(res))
    # print(res['close'][-1])
    # res = oms.price(fut_list[index], False, True, 'INDEX')
    # logger.info('INDEX: ' + json.dumps(res))
    # print(res['close'][-1])
    # res = oms.price(fut_list[index], False, True, 'FUTIDX')
    # logger.info('FUTIDX: ' + json.dumps(res))
    # print(res['close'][-1])      
    # print(json.dumps(res))
    # exit(0)
    # res = oms.price(index, True)

    spot = oms.price(index, True)    

    # print(res)
    # exit(0)

    idxObj = Index(spot)
    indicators = oms.getIndicators(index)
    res = util.read()
    spot = oms.spotStrike(index)
    security_ce = str(util.securityId(index, spot, 'CE'))
    security_pe = str(util.securityId(index, spot, 'PE'))
    ltp_ce = res[security_ce]['LTP'] if 'LTP' in res[security_pe] else 0
    ltp_pe = res[security_pe]['LTP'] if 'LTP' in res[security_pe] else 0
    straddle_price = float(ltp_ce) + float(ltp_pe)
    print(f"straddle_price: {str(round(straddle_price, 2))}")
    # vwap = indicators['vwap']['indicator']
    sma_1 = indicators['sma']['indicator']
    sma_2 = indicators['sma']['indicator_2']
    sma_cross = indicators['sma']['ind_1_cross_2']
    ema_1 = indicators['ema']['indicator']
    ema_2 = indicators['ema']['indicator_2']
    ema_cross = indicators['ema']['ind_1_cross_2']
    print(f"{index + ': ' + str(round(idxObj.spot, 2)) + ' (' + str(round(idxObj.move, 2)) + ')'}")
    print(f"{index + ': sma_1: ' + str(round(sma_1, 2)) + ' , sma_2: ' + str(round(sma_2, 2)) + ' , sma_cross: ' + str(round(sma_cross, 2))}")
    print(f"{index + ': ema_1: ' + str(round(ema_1, 2)) + ' , ema_2: ' + str(round(ema_2, 2)) + ' , ema_cross: ' + str(round(ema_cross, 2))}")
    # exit()
        