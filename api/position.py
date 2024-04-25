import ast, logging
from datetime import datetime, time
from time import sleep
now = datetime.now()
tm = now.strftime("%Y") + "-" + now.strftime("%m") + "-" + now.strftime("%d")
logging.basicConfig(
    level=logging.INFO, filename=f"./logs/{tm}/application{'_' + now.strftime("%H-%S")}.log",
    filemode="w", format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()
class Position:
    def __init__(self, pos):
        self.index = pos["tradingSymbol"].split('-')[0] if "tradingSymbol" in pos else -1
        self.symbol = pos["tradingSymbol"] if "tradingSymbol" in pos else -1
        self.security_id = pos["securityId"] if "securityId" in pos else -1
        self.position_type = pos["positionType"] if "positionType" in pos else -1
        self.exchange_segment = pos["exchangeSegment"] if "exchangeSegment" in pos else -1
        self.product_type = pos["productType"] if "productType" in pos else -1
        self.cost_price = pos["costPrice"] if "costPrice" in pos else -1
        self.buy_avg = pos["buyAvg"] if "buyAvg" in pos else -1
        self.buy_qty = pos["buyQty"] if "buyQty" in pos else -1
        self.sell_avg = pos["sellAvg"] if "sellAvg" in pos else -1
        self.sell_qty = pos["sellQty"] if "sellQty" in pos else -1
        self.quantity = pos["netQty"] if "netQty" in pos else -1
        self.realized = pos["realizedProfit"] if "realizedProfit" in pos else -1
        self.unrealized = pos["unrealizedProfit"] if "unrealizedProfit" in pos else -1
        self.expiry_date = pos["drvExpiryDate"] if "drvExpiryDate" in pos else -1
        self.option_type = pos["drvOptionType"] if "drvOptionType" in pos else -1
        self.strike_price = pos["drvStrikePrice"] if "drvStrikePrice" in pos else -1
        self.pnl = self.unrealized if self.position_type == 'LONG' else (float(self.unrealized)*-1)
        p = float(self.quantity)*float(self.cost_price)
        p = p + float(self.pnl)
        self.price = float(p/self.quantity)

    def update(self, pos):
        if hasattr(pos, 'pnl'): self.pnl = pos.pnl
        if hasattr(pos, 'symbol'): self.symbol = pos.symbol
        if hasattr(pos, 'quantity'): self.quantity = pos.quantity
        if hasattr(pos, 'price'): self.price = pos.price
        if hasattr(pos, 'realised'): self.realised = pos.realised
        if hasattr(pos, 'unrealised'): self.unrealised = pos.unrealised
        if hasattr(pos, 'position'): self.position = pos.position
        if hasattr(pos, 'cost_price'): self.cost_price
        # curVal = (abs(float(self.netqty)*(float(self.ltp))))
    def realizedPosition(self): 
        dic_data = [];realized=0.0
        with open("./data/realized.txt", "r") as fileStore:
            dic_data = fileStore.readline()
            fileStore.close()
        if isinstance(dic_data, str) and dic_data.strip() != "": 
                dic_data = ast.literal_eval(dic_data)
        if self.security_id in dic_data:
            realized = float(dic_data[self.security_id])
        return realized
    
    def savePosition(self): 
        dic_data = [];realized=0.0
        with open("./data/realized.txt", "r") as fileStore:
            dic_data = fileStore.readline()
            fileStore.close()
        if isinstance(dic_data, str) and dic_data.strip() != "": 
                dic_data = ast.literal_eval(dic_data)
        if self.security_id in dic_data:
            dic_data[self.security_id] = float(self.unrealized)
        with open("./data/realized.txt", "w") as fileStore:
                res = fileStore.write(str(dic_data))
                fileStore.close()
        
    def to_dict(self):
        return self.__dict__
        # return json.dumps(self.__dict__)
    
    def get(self, key):
        return self.__dict__[key]
    
if __name__ == "__main__": 
    # print("BANKNIFTY-Mar2024-48000-CE".su)
    exit()
    for po in pos:
        print(po)
        position = Position(po)
        position.validate(pos)
        print(position.to_dict())
        