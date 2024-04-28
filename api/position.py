import ast, logging, json
from datetime import datetime, time
from time import sleep
now = datetime.now()
tm = now.strftime("%Y") + "-" + now.strftime("%m") + "-" + now.strftime("%d")
logging.basicConfig(
    level=logging.INFO, filename=f"./logs/{tm}/application.log",
    filemode="a", format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()
class Position:
    def __init__(self, pos, trade=False):
        self.index = pos["tradingSymbol"].split('-')[0] if "tradingSymbol" in pos else 0
        self.symbol = pos["tradingSymbol"] if "tradingSymbol" in pos else 0
        self.security_id = pos["securityId"] if "securityId" in pos else 0
        self.position_type = pos["positionType"] if "positionType" in pos else 0
        self.exchange_segment = pos["exchangeSegment"] if "exchangeSegment" in pos else 0
        self.product_type = pos["productType"] if "productType" in pos else 0
        self.cost_price = pos["costPrice"] if "costPrice" in pos else 0
        self.buy_avg = pos["buyAvg"] if "buyAvg" in pos else 0
        self.buy_qty = pos["buyQty"] if "buyQty" in pos else 0
        self.sell_avg = pos["sellAvg"] if "sellAvg" in pos else 0
        self.sell_qty = pos["sellQty"] if "sellQty" in pos else 0
        self.quantity = pos["netQty"] if "netQty" in pos else 0
        self.realized = pos["realizedProfit"] if "realizedProfit" in pos else 0
        self.unrealized = pos["unrealizedProfit"] if "unrealizedProfit" in pos else 0
        self.expiry_date = pos["drvExpiryDate"] if "drvExpiryDate" in pos else '-'
        self.option_type = pos["drvOptionType"] if "drvOptionType" in pos else 0
        self.strike_price = pos["drvStrikePrice"] if "drvStrikePrice" in pos else 0

        self.price = (float(self.unrealized)/float(self.quantity))
        if self.position_type == 'LONG':
            self.price = float(self.buy_avg) + self.price
            self.pnl = float(self.unrealized)
        else : 
            self.price = float(self.sell_avg) - self.price
            self.pnl = float(self.unrealized)*(-1)

    def update(self, pos):
        self.index = pos.index if hasattr(pos, 'index') else '-'
        self.symbol = pos.symbol if hasattr(pos, 'symbol') else '-'
        self.security_id = pos.security_id if hasattr(pos, 'security_id') else -1
        self.position_type = pos.position_type if hasattr(pos, 'position_type') else '-'
        self.exchange_segment = pos.exchange_segment if hasattr(pos, 'exchange_segment') else '-'
        self.product_type = pos.product_type if hasattr(pos, 'product_type') else '-'
        self.cost_price = pos.cost_price if hasattr(pos, 'cost_price') else 0
        self.buy_avg = pos.buy_avg if hasattr(pos, 'buy_avg') else 0
        self.buy_qty = pos.buy_qty if hasattr(pos, 'buy_qty') else 0
        self.sell_avg = pos.sell_avg if hasattr(pos, 'sell_avg') else 0
        self.quantity = pos.quantity if hasattr(pos, 'quantity') else 0
        self.realized = pos.realized if hasattr(pos, 'realized') else 0
        self.unrealized = pos.unrealized if hasattr(pos, 'unrealized') else 0
        self.expiry_date = pos.expiry_date if hasattr(pos, 'expiry_date') else 0
        self.option_type = pos.option_type if hasattr(pos, 'option_type') else 0
        self.strike_price = pos.strike_price if hasattr(pos, 'strike_price') else 0

        self.price = (float(self.unrealized)/abs(float(self.quantity)))
        if self.position_type == 'LONG':
            if float(self.sell_avg) > 0:
                self.pnl = float(self.unrealized) + float(self.realized)
            else:
                deltaPrice = (float(self.buy_avg) - float(self.cost_price))*abs(float(self.quantity))
                self.pnl = float(self.unrealized) + float(self.realized) + deltaPrice
            self.price = float(self.buy_avg) + self.price
        else : 
            if float(self.buy_avg) > 0:
                self.pnl = (float(self.unrealized) - float(self.realized))*(-1)
            else:
                deltaPrice = (float(self.sell_avg) - float(self.cost_price))*abs(float(self.quantity))
                self.pnl = (float(self.unrealized) - float(self.realized) + deltaPrice)*(-1)
            self.price = float(self.sell_avg) + self.price

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
        