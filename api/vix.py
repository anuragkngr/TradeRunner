# import sys
# sys.path.append("../TradeRunner")
from startup import conf

class Vix:
    def __init__(self, vix, vix_trade_start=None):
        self.open = vix["open"] if "open" in vix else -1
        self.high = vix["high"] if "high" in vix else -1
        self.low = vix["low"] if "low" in vix else -1
        self.close = vix["close"] if "close" in vix else -1
        self.trend = "side"
        if vix_trade_start is not None: self.open = vix_trade_start
        travel = self.open - self.close
        if abs(travel) > (self.open * conf['vix_alert']):
            self.trend = "SELL" if travel < 0 else "BUY"
        
    def to_dict(self):
        return self.__dict__
        # return json.dumps(self.__dict__)
    
if __name__ == "__main__": 
    print("BANKNIFTY-Mar2024-48000-CE".su)
    # exit()
        