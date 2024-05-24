import json, logging
from datetime import datetime
conf = json.load(open("./data/configuration.json"))
now = datetime.now()
tm = now.strftime("%Y") + "-" + now.strftime("%m") + "-" + now.strftime("%d")
logging.basicConfig(
    level=logging.INFO, filename=f"./logs/{tm}/application.log",
    filemode="a", format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()

class Option:
    def __init__(self, index, feed, strike, option_type='CE'):

        self.index = index if index is not None else '--'
        self.exchange_segment = feed['exchange_segment'] if 'exchange_segment' in feed else -1
        self.security_id = feed['security_id'] if 'security_id' in feed else -1
        self.strike = strike if strike is not None else -1
        self.ltt = feed['LTT'] if 'LTT' in feed else None
        self.open = feed["open"] if "open" in feed else -1
        self.high = feed["high"] if "high" in feed else -1
        self.low = feed["low"] if "low" in feed else -1
        self.close = feed["close"] if "close" in feed else -1
        self.ltp = feed["LTP"] if "close" in feed else -1
        self.move = float(self.close) - float(self.open)
        self.movePercent = self.move * 100 / float(self.close)
        self.option_type = option_type

        self.total_buy_quantity = feed['total_buy_quantity'] if 'total_buy_quantity' in feed else 0
        self.total_sell_quantity = feed['total_sell_quantity'] if 'total_sell_quantity' in feed else 0
        self.volume = feed['volume'] if 'volume' in feed else 0
        self.oi = feed['oi'] if 'oi' in feed else 0
        if self.oi == 0: self.oi = feed['OI'] if 'OI' in feed else 0

        self.open_high = False
        self.open_low = False
        
        if round(float(self.open)) >= round(float(self.low)): self.open_low = True
        if round(float(self.open)) <= round(float(self.high)): self.open_low = True

    def to_dict(self):
        return self.__dict__
    
if __name__ == "__main__": 
    # print("BANKNIFTY-Mar2024-48000-CE")
    # f"{'NIFTY: ' + str(round(self.nifty.spot, 2)) + ' (' + str(round(self.nifty.move, 2)) + ')'}"
    index = 'BANKNIFTY'
    stk_sid = []
    exit(0)
    # for i in range(12):

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
        