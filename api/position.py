import ast, logging, json, os, pymongo
from datetime import datetime, time
from time import sleep
from dhanhq import dhanhq
conf = json.load(open('./data/configuration.json'))
dhan = dhanhq(conf['dhan_id'], conf['dhan_token'])
now = datetime.now()
tm = now.strftime('%Y') + '-' + now.strftime('%m') + '-' + now.strftime('%d')
os.makedirs(f'./logs/{tm}', exist_ok=True)
os.makedirs(f'./data/', exist_ok=True)
logging.basicConfig(
    level=logging.INFO, filename=f'./logs/{tm}/application.log',
    filemode='a', format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()
client = pymongo.MongoClient(conf['db_url_lcl'])
dblist = client.list_database_names()
mydb = client['tradestore']
options = mydb['options']
option_live = mydb['option_live']
class Position:
    def __init__(self, pos, order=False, orderList=None):
        self.index = pos['index'] if 'index' in pos else None
        if self.index is None and 'tradingSymbol' in pos: 
            self.index = pos['tradingSymbol'].split('-')[0] if '-' in pos['tradingSymbol'] else '-'
        self.symbol = pos['tradingSymbol'] if 'tradingSymbol' in pos else 0
        self.security_id = pos['securityId'] if 'securityId' in pos else 0
        self.position_type = pos['positionType'] if 'positionType' in pos else 0
        self.exchange_segment = pos['exchangeSegment'] if 'exchangeSegment' in pos else 0
        self.product_type = pos['productType'] if 'productType' in pos else 'MARGIN'
        self.quantity = pos['netQty'] if 'netQty' in pos else 0
        # self.cost_price = pos['buyAvg'] if 'buyAvg' in pos else -1
        # if self.position_type == 'SHORT': self.cost_price = pos['sellAvg'] if 'sellAvg' in pos else -1

        # if orderList is not None:
        #     prc=qty=cnt=0
        #     for po in orderList:
        #         qty = qty + abs(po['quantity'])
        #         prc = prc + po['price']
        #         cnt = cnt + 1
        #         transactionType = 'SHORT' if po['transactionType'] == 'SELL' else 'LONG'
        #         if po['securityId'] == self.security_id and self.position_type == transactionType and abs(self.quantity) == qty:
        #             self.cost_price = prc/cnt
        #             break

        self.cost_price = pos['costPrice'] if 'costPrice' in pos else -1
                
        self.buy_avg = pos['buyAvg'] if 'buyAvg' in pos else 0
        self.buy_qty = pos['buyQty'] if 'buyQty' in pos else 0
        self.sell_avg = pos['sellAvg'] if 'sellAvg' in pos else 0
        self.sell_qty = pos['sellQty'] if 'sellQty' in pos else 0
        self.realized = pos['realizedProfit'] if 'realizedProfit' in pos else 0
        self.unrealized = pos['unrealizedProfit'] if 'unrealizedProfit' in pos else 0
        self.expiry_date = pos['drvExpiryDate'] if 'drvExpiryDate' in pos else '-'
        self.option_type = pos['drvOptionType'] if 'drvOptionType' in pos else 0
        self.strike_price = pos['drvStrikePrice'] if 'drvStrikePrice' in pos else 0
        if order: return
        opt = options.find_one({'oi': { '$gt': 0 }, 'security_id': int(self.security_id)}, sort=[('LTT', -1)])
        # option_live = options.find_one({'security_id': int(self.security_id)}, sort=[('_id', -1)])

        self.oi = self.oi_pre = self.total_buy_quantity = self.total_sell_quantity = self.total_buy_quantity_pre = self.total_sell_quantity_pre = 0

        if opt is not None: 
            self.oi = round(int(opt['oi'])/1000) if 'oi' in opt else 0
            # if self.oi == 0: self.oi = round(int(opt['OI'])/1000) if 'OI' in opt else 0
        
        if self.oi_pre == 0: self.oi_pre = self.oi

        if opt is not None: 
            self.total_buy_quantity = opt['total_buy_quantity'] if 'total_buy_quantity' in opt else 0
            self.total_buy_quantity = round(int(self.total_buy_quantity)/1000)

            self.total_sell_quantity = opt['total_sell_quantity'] if 'total_sell_quantity' in opt else 0
            self.total_sell_quantity = round(int(self.total_sell_quantity)/1000)
        
        res = options.find_one(
                { 'security_id' : int(self.security_id) },
                sort=[('LTT', -1)]
            )
        
        self.price = float(res['LTP']) if res is not None and 'LTP' in res else -1
        self.pnl = -1
        if self.price > 0: self.pnl = (self.price - self.cost_price) * abs(self.quantity)
        if self.position_type == 'SHORT': self.pnl = self.pnl*-1

    def update(self, pos):
        self.index = pos.index if hasattr(pos, 'index') else '-'
        self.symbol = pos.symbol if hasattr(pos, 'symbol') else '-'
        self.security_id = pos.security_id if hasattr(pos, 'security_id') else -1
        self.position_type = pos.position_type if hasattr(pos, 'position_type') else '-'
        self.exchange_segment = pos.exchange_segment if hasattr(pos, 'exchange_segment') else '-'
        self.product_type = pos.product_type if hasattr(pos, 'product_type') else '-'
        self.buy_avg = pos.buy_avg if hasattr(pos, 'buy_avg') else 0
        self.buy_qty = pos.buy_qty if hasattr(pos, 'buy_qty') else 0
        self.sell_avg = pos.sell_avg if hasattr(pos, 'sell_avg') else 0
        self.quantity = pos.quantity if hasattr(pos, 'quantity') else 0
        self.realized = pos.realized if hasattr(pos, 'realized') else 0
        self.unrealized = pos.unrealized if hasattr(pos, 'unrealized') else 0
        self.expiry_date = pos.expiry_date if hasattr(pos, 'expiry_date') else 0
        self.option_type = pos.option_type if hasattr(pos, 'option_type') else 0
        self.strike_price = pos.strike_price if hasattr(pos, 'strike_price') else 0

        opt = options.find_one({'oi': { '$gt': 0 }, 'security_id': int(self.security_id)}, sort=[('LTT', -1)])


        if opt is not None: 
            self.oi = round(int(opt['oi'])/1000) if 'oi' in opt else 0
            # if self.oi == 0: self.oi = round(int(opt['OI'])/1000) if 'OI' in opt else 0
            opt['oi'] = self.oi
            self.total_buy_quantity = opt['total_buy_quantity'] if 'total_buy_quantity' in opt else 0
            self.total_buy_quantity = round(int(opt['total_buy_quantity'])/1000)

            self.total_sell_quantity = opt['total_sell_quantity'] if 'total_sell_quantity' in opt else 0
            self.total_sell_quantity = round(int(opt['total_sell_quantity'])/1000)

        if self.oi > 0 and opt['oi'] > 0 and self.oi != opt['oi']:
            self.oi_pre = self.oi
            self.oi = round(int(opt['oi'])/1000)
            if self.total_buy_quantity > 0 and opt['total_buy_quantity'] > 0 and int(self.total_buy_quantity) != int(opt['total_buy_quantity']):
                self.total_buy_quantity_pre = round(int(self.total_buy_quantity)/1000)
                self.total_buy_quantity = round(int(opt['total_buy_quantity'])/1000)
            if self.total_sell_quantity > 0 and opt['total_sell_quantity'] > 0 and int(self.total_sell_quantity) != int(opt['total_sell_quantity']):
                self.total_sell_quantity_pre = round(int(self.total_sell_quantity)/1000)
                self.total_sell_quantity = round(int(opt['total_sell_quantity'])/1000)

        res = options.find_one(
                { 'security_id' : int(self.security_id) },
                sort=[('LTT', -1)]
            )
        
        self.price = float(res['LTP']) if res is not None and 'LTP' in res else -1
        self.pnl = -1#self.unrealized if self.price > 0 else -1
        if self.price > 0: self.pnl = (self.price - self.cost_price) * abs(self.quantity)
        if self.position_type == 'SHORT': self.pnl = self.pnl*-1

    def to_dict(self):
        return self.__dict__
        # return json.dumps(self.__dict__)

    def to_dict_order(self):
        res = {'index': self.index, 'symbol': self.symbol, 'security_id': 
                    self.security_id, 'position_type': self.position_type, 'quantity': 
                    self.quantity, 'strike_price': self.strike_price, 'option_type': self.option_type}
        return res
    
    def get(self, key):
        return self.__dict__[key]
    
if __name__ == '__main__': 
    # print('BANKNIFTY-Mar2024-48000-CE'.su)
    exit()
    for po in pos:
        print(po)
        position = Position(po)
        position.validate(pos)
        print(position.to_dict())
        