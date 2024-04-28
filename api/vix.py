import json
conf = json.load(open("./data/configuration.json"))

class Vix:
    def __init__(self, vix, vix_trade_start=None):
        self.open = vix["open"] if "open" in vix else -1
        self.high = vix["high"] if "high" in vix else -1
        self.low = vix["low"] if "low" in vix else -1
        self.close = vix["close"] if "close" in vix else -1
        self.move = float(self.close) - float(self.open)
        self.movePercent = self.move * 100 / float(self.close)
        if vix_trade_start is not None: self.open = vix_trade_start
    def to_dict(self):
        return self.__dict__
        # return json.dumps(self.__dict__)
    
if __name__ == "__main__": 
    print("BANKNIFTY-Mar2024-48000-CE".su)
    # exit()
        