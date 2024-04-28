from position import Position
from utils import Utils
import traceback, json, logging
from datetime import datetime, time, timedelta
conf = json.load(open("./data/configuration.json"))
from time import sleep
from dhanhq import dhanhq
trade_headers=['SYMBOL', 'QUANTITY', 'COST', 'PRICE', 'P&L', 'REALIZED', 'UNREALIZED']
idx_list = {'NIFTY': '13', 'BANKNIFTY': '25', 'FINNIFTY': '27', 'INDIA VIX': '21', 'NIFTYMCAP50': '20', 'BANKEX': '69', 'SENSEX': '51'}
util = Utils()
token_list = [{"exchangeType": 1, "tokens": ["26009"]}]
now = datetime.now()
tm = now.strftime("%Y") + "-" + now.strftime("%m") + "-" + now.strftime("%d")
logging.basicConfig(
    level=logging.INFO, filename=f"./logs/{tm}/application.log",
    filemode="a", format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()
class OMS(): 
    def __init__(self):
        self.dhan = dhanhq(conf['dhan_id'], conf['dhan_token'])

    def refreshConnection(self, method):
        sleep(5)
        flag = True; cnt = 0;
        while flag:
            cnt += 1;
            print('Refresh Connection ' + method + ': ', cnt)
            result = self.getConnection()
            if result: flag = False
        return result

    def getConnection(self):
        try:
            self.dhan = dhanhq(conf['dhan_id'], conf['dhan_token'])
            return True 
        except Exception: return False

    def positions(self):
        sleep(1)
        res = {}; pos = []
        try:
            if conf['mock']: res = json.load(open('./data/positions.json'))
            else : res = self.dhan.get_positions()
            logger.info(f"OMS API position response: {json.dumps(res)}")
        except Exception:
            logger.info(f"OMS API  Exception positions response: {traceback.format_exc()}")
            self.refreshConnection('positions')
            res = self.dhan.get_positions()
        for po in res['data'] :
            if po["positionType"] not in ['CLOSED']:
                pos.append(Position(po))
        return [] if not pos else pos
    
    def getFundLimits(self):
        try:
            if conf['mock']: rms = json.load(open('./data/rms.json'))['data']
            else : rms = self.dhan.get_fund_limits()['data']
            rms = self.dhan.get_fund_limits()['data']
            logger.info(f"OMS API getFundLimits response: {json.dumps(rms)}")
        except Exception:
            logger.info(f"OMS API  Exception getFundLimits response: {traceback.format_exc()}")
            self.refreshConnection('getFundLimits')
            rms = self.dhan.rmsLimit()['data']
        return {} if rms is None else rms
    
    def orderBook(self, tradingsymbol):
        sleep(1)
        book_price = -1; book = []; order = []
        if conf['mock']: book = json.load(open('./data/order_book.json'))['data']
        else : book = self.dhan.orderBook()['data']
        logger.info(f"OMS API orderBook response: {json.dumps(book)}")
        if book:
            for bb in book:
                if bb['tradingsymbol'] == tradingsymbol: order.append(bb)
            order = sorted(order, key=lambda x: datetime.strptime(x['exchtime'], '%d-%b-%Y %H:%M:%S'))
            book_price = order[-1]['averageprice']
        return book_price
    
    def print(self) -> dict:
        pos = self.positions();resp = []
        for po in pos:
            tmppo = {
            "SYMBOL": po.symbol,
            "POSITION": po.position,
            "QUANTITY": self.quantity,
            "PRICE": po.price,
            "COST": po.cost_price,
            "P&L": po.pnl,
            "REALISED": po.realised,
            # "UNREALISED": po.unrealised,
            }
            resp.append(tmppo)
        logger.info(f"OMS API print response: {str(resp)}")
        return resp

    def execOrder(self, position, transaction_type) -> bool:
        # print(position)
        # json.loads(json.dumps(position), object_hook=Position)
        req = {
            "security_id": position.security_id, 
            "exchange_segment": self.dhan.NSE_FNO,
            "transaction_type": transaction_type,
            "quantity": abs(int(position.quantity)),
            "order_type": self.dhan.MARKET,
            "product_type": position.product_type,
            "price": "0"
        }
        try:
            logger.info(f"OMS API execOrder request: {str(req)}")
            res = req
            # res = self.dhan.placeOrder(req)
            logger.info(f"OMS API execOrder response: {str(res)}")
            print(res)
        except Exception:
            logger.info(f"OMS API  Exception execOrder response: {traceback.format_exc()}")
            self.refreshConnection('execOrder')
            # res = self.dhan.placeOrder(req)
        if not res:# is not None and res['status'] == True and res['message'].lower() == 'success':
            return True
        return False

    def matchOrder(self, index, position, m_price, direction):
        slab = 100 if index == "BANKNIFTY" else 50
        strike = position.strikeprice; di = 1000;final_stike;final_scripCode;tradingSymbol=''
        for idx in range(3):
            strike = (strike + (slab*(idx + 1))) if direction == "UP" else (strike - (slab*(idx + 1)))
            scripCode, symbol = util.getSymbolToken(index, strike, position.optiontype, position.expirydate)
            n_price = self.optionPrice(scripCode)
            dif = abs(n_price - m_price)
            if dif < di: 
                di = dif
                final_stike = strike
                final_scripCode = scripCode
                tradingSymbol = symbol
            else: 
                position.strikeprice = float(final_stike)
                position.symboltoken = final_scripCode
                position.tradingSymbol = tradingSymbol
                position.netprice = position.avgnetprice = position.ltp = n_price
        return position, 

    def spotStrike(self, index):
        slab = 100 if index == "BANKNIFTY" else 50
        # spot = util.dailyPrice(index)
        try:
            spot = self.dhan.ltpData(index)
        except Exception:
            logger.info(f"Positions API  Exception rmsLimit response: {traceback.format_exc()}")
            self.refreshConnection('spotStrike')

        strike = round(spot / slab) * slab
        return strike
    
    def spotPrice(self, index):
        try:
            res = self.dhan.ltpData('NSE', index, idx_list[index])
        except Exception:
            logger.info(f"OMS API  Exception spotPrice response: {traceback.format_exc()}")
            self.refreshConnection('spotPrice')
            res = self.dhan.ltpData('NSE', index, idx_list[index])
        # print(index + ': ' + json.dumps(res))
        return res['data']['ltp']
    
    def ohlc(self, security, isIndex=False):
        security_id = security
        if isIndex: 
            security_id = idx_list[security]
            exchange_segment = 'IDX_I'
        else: exchange_segment = 'NSE_FNO'
        try:
            res = self.dhan.intraday_minute_data(
            security_id=security_id, exchange_segment=exchange_segment, instrument_type='OPTIDX')
        except Exception:
            logger.info(f"OMS API  Exception ohlc response: {traceback.format_exc()}")
            self.refreshConnection('ohlc')
            res = self.dhan.intraday_minute_data(
            security_id=security_id, exchange_segment=exchange_segment, instrument_type='OPTIDX')
        
        res = res['data']
        if res == '':
            if security == 'BANKNIFTY':
                res = {'open': [48660], 'high': [48660], 'low': [48088], 'close': [48494]}
            else: res = {'open': [12.10], 'high': [12.45], 'low': [12.02], 'close': [12.21]}
        if 'open' not in res: return {}
        res = {'open': res['open'][0], 'high': max(res['high']), 
               'low': min(res['low']), 'close': res['close'][-1]}
        return res
    
    def histPrice(self, index):
        slab = 100 if index == "BANKNIFTY" else 50
        historicParam={
        "symbol": "NSE",
        "exchange_segment": "3045",
        "instrument_type": "THREE_MINUTE",
        "expiry_code": 0,
        "from_date": ((datetime.now()) + timedelta(days=-7)).strftime("%Y-%m-%d"),
        "to_date": (datetime.now()).strftime("%Y-%m-%d")
        }
        res = self.dhan.historical_daily_data(historicParam)
        return res   

    def closeAllTrade(self, book):
        for trd in book.trades: self.closeTrade(trd)

    def closeTrade(self, trade):
        flag = True
        for pos in trade.positions:
            if pos.position_type == 'SHORT':
                res = self.execOrder(pos, "BUY")
                if not res:
                    flag = False
                    break
        if flag:
            sleep(1)
            for pos in trade.positions:
                if int(pos['netqty']) > 0:
                    res = self.execOrder(pos, "SELL")
                    logger.info(res)
                    if not res:
                        flag = False
                        break
        return flag
    
def myOrder(tradingsymbol, symboltoken, transactiontype, quantity):
    oms = OMS()
    ord = {'tradingsymbol': tradingsymbol, 'symboltoken': symboltoken,
            'transactiontype': transactiontype, 'exchange': 'NFO', 'quantity': quantity}
    ord = Position(ord)
    res = oms.execOrder(ord, transactiontype)
    return res
    
if __name__ == "__main__": 
    tradingsymbol = 'NIFTY'  
    oms = OMS()
    pos = oms.dhan.get_positions()
    print((json.dumps(pos['data'])))
    
    # print(oms.ohlc('67534'))
    # print(oms.getFundLimits())
    exit()
    tradingsymbol = 'NIFTY25APR2422100PE'
    order_book = oms.orderBook()
    m_book = [x for x in order_book if x['tradingsymbol'] == tradingsymbol]
                  
    m_book = sorted(m_book, key=lambda x: datetime.strptime(x['exchtime'], '%d-%b-%Y %H:%M:%S'))
    book = m_book[-1]
    print(json.loads(json.dumps(m_book)))
    print(json.loads(json.dumps(book)))
    # res = myOrder(tradingsymbol='', symboltoken='', transactiontype='BUY', quantity='')
    # res = myOrder(tradingsymbol='', symboltoken='', transactiontype='SELL', quantity='')
    # res = myOrder(tradingsymbol='', symboltoken='', transactiontype='BUY', quantity='')
    # res = myOrder(tradingsymbol='', symboltoken='', transactiontype='SELL', quantity='')
    

    # date_str = '4APR2024'#'2023-02-28 14:30:00'
    # date_format = '%d%b%Y'
    # date_obj = datetime.strptime(date_str, '%d%b%Y')
    # print(date_obj)
    # exit()
    # date_obj = oms.optionPrice('67487')
    # print(date_obj)
    

