import json
conf = json.load(open("./data/configuration.json"))

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
    print("BANKNIFTY-Mar2024-48000-CE".su)
    # exit()
        