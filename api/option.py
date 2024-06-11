import json, logging
from datetime import datetime
from dateutil import parser
conf = json.load(open("./data/configuration.json"))
now = datetime.now()
from utils import Utils
util = Utils()
tm = now.strftime("%Y") + "-" + now.strftime("%m") + "-" + now.strftime("%d")
logging.basicConfig(
    level=logging.INFO, filename=f"./logs/{tm}/application.log",
    filemode="a", format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()

class Option:
    def __init__(self, index, feed, strike, option_type='CE'):

        self.index = index if index is not None else '--'
        self.exchange_segment = feed['exchange_segment'] if feed is not None and 'exchange_segment' in feed else -1
        self.security_id = feed['security_id'] if feed is not None and 'security_id' in feed else -1
        self.strike = strike if strike is not None else -1
        self.ltt = feed['LTT'] if feed is not None and 'LTT' in feed else parser.parse(util.getDate() + ' ' + util.getTime()[:-3] + ':00')
        self.open = float(feed["open"]) if feed is not None and "open" in feed else -1
        self.high = float(feed["high"]) if feed is not None and "high" in feed else -1
        self.low = float(feed["low"]) if feed is not None and "low" in feed else -1
        self.close = float(feed["close"]) if feed is not None and "close" in feed else -1
        self.ltp = float(feed["LTP"]) if feed is not None and "LTP" in feed else -1
        self.oi = feed["oi"] if feed is not None and "oi" in feed else -1
        self.volume = feed["volume"] if feed is not None and "volume" in feed else -1
        self.move = self.close - self.open
        self.movePercent = self.move * 100 / self.close
        self.option_type = option_type

        self.total_buy_quantity = feed['total_buy_quantity'] if feed is not None and 'total_buy_quantity' in feed else 0
        self.total_sell_quantity = feed['total_sell_quantity'] if feed is not None and 'total_sell_quantity' in feed else 0
        self.volume = feed['volume'] if feed is not None and 'volume' in feed else 0
        self.oi = feed['oi'] if feed is not None and 'oi' in feed else 0
        if self.oi == 0: self.oi = feed['OI'] if feed is not None and 'OI' in feed else 0

        self.open_high = False
        self.open_low = False
        
        if round(float(self.open)) == round(float(self.low)): self.open_low = True
        if round(float(self.open)) == round(float(self.high)): self.open_high = True

        # if round(float(self.open)) == round(float(self.low) and float(self.ltp)) >= round(float(self.high)): self.open_low = True
        # if round(float(self.open)) == round(float(self.high) and float(self.ltp)) <= round(float(self.low)): self.open_high = True

    def to_dict(self, hl=None):
        if self.open_high:#hl is not None and hl=='high':# 
            return {'open(H)': self.open, 'high(H)': self.high, 'low(H)': self.low, 'LTP(H)': self.ltp,
                'strike(H)': self.strike, 'id(H)': self.security_id, 'option(H)': self.option_type}
        if self.open_low:#if hl is not None and hl=='low':#
            return {'index': self.index[:4], 'open(L)': self.open, 'low(L)': self.low, 'high(L)': self.high, 'LTP(H)': self.ltp,
                'strike(L)': self.strike, 'id(L)': self.security_id, 'option(L)': self.option_type}

    def to_db(self):
        if self.open_high:
            return {'index': self.index, 'ltp': self.ltp, 'ltt': self.ltt, 'open': self.open, 'high': self.high, 'low': self.low, 'ltp': self.ltp,
                  'strike': self.strike, 'security_id': self.security_id, 'oi': self.oi, 'volume': self.volume, 'option_type': self.option_type, 'close': self.close, 'open_high': True}
        if self.open_low:
            return {'index': self.index, 'ltp': self.ltp, 'ltt': self.ltt, 'open': self.open, 'high': self.high, 'low': self.low, 'ltp': self.ltp,
                  'strike': self.strike, 'security_id': self.security_id, 'oi': self.oi, 'volume': self.volume, 'option_type': self.option_type, 'close': self.close, 'open_high': False}
    
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
        